from PyQt6.QtCore import QThread, pyqtSignal
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from .image_processor import ImageProcessor
from .video_processor import VideoProcessor
from .sequence_detector import detect_sequences
from .smart_heuristics import SmartHeuristics
from .utils import cancel_all_subprocesses
import os

class BatchManager(QThread):
    # Signals to communicate with the GUI
    progress_updated = pyqtSignal(int, int) # current, total
    log_message = pyqtSignal(str)
    processing_finished = pyqtSignal()
    stats_updated = pyqtSignal(int, int) # original_size, new_size

    def __init__(self, paths, options):
        super().__init__()
        self.paths = paths
        self.options = options
        self.image_proc = ImageProcessor()
        self.video_proc = VideoProcessor()
        self._is_cancelled = False

    def cancel(self):
        self._is_cancelled = True
        cancel_all_subprocesses()

    def run(self):
        self.log_message.emit("Scanning for files...")
        files_to_process = self._gather_files()
        
        compile_sequences = self.options.get('compile_sequences', False)
        sequences = []
        if compile_sequences:
            self.log_message.emit("Detecting image sequences...")
            sequences, files_to_process = detect_sequences(files_to_process)
            if sequences:
                self.log_message.emit(f"Detected {len(sequences)} image sequences.")
        
        total_files = len(files_to_process) + len(sequences)
        if total_files == 0:
            self.log_message.emit("No files found to process.")
            self.processing_finished.emit()
            return

        self.log_message.emit(f"Found {total_files} items to process.")
        self.progress_updated.emit(0, total_files)

        workers = os.cpu_count() or 4
        # Use ThreadPoolExecutor to process files in parallel
        processed_count = 0

        successful_outputs = []

        with ThreadPoolExecutor(max_workers=workers) as executor:
            # Submit single files
            future_to_task = {
                executor.submit(self._process_single_file, path): path.name
                for path in files_to_process
            }
            
            # Submit sequences
            for seq in sequences:
                future = executor.submit(self._process_sequence, seq)
                future_to_task[future] = seq['base_name']

            for future in as_completed(future_to_task):
                if self._is_cancelled:
                    self.log_message.emit("Processing cancelled by user.")
                    break

                task_name = future_to_task[future]
                try:
                    result = future.result()
                    # Backward compatibility for tuple length (in case sequences or something else returns 3 items)
                    if len(result) == 3:
                        success, msg, out_path = result
                        orig_size, new_size = 0, 0
                    else:
                        success, msg, out_path, orig_size, new_size = result
                        
                    status = "OK" if success else "FAIL"
                    if success:
                        successful_outputs.append(Path(out_path))
                        self.log_message.emit(f"[{status}] {task_name} -> {Path(out_path).name}")
                        if orig_size > 0 or new_size > 0:
                            self.stats_updated.emit(orig_size, new_size)
                    else:
                        self.log_message.emit(f"[{status}] {task_name} : {msg}")
                except Exception as exc:
                    self.log_message.emit(f"[ERROR] {task_name} generated an exception: {exc}")

                processed_count += 1
                self.progress_updated.emit(processed_count, total_files)

        if self.options.get('zip_output', False) and successful_outputs and not self._is_cancelled:
            self.log_message.emit("Zipping successful outputs...")
            import zipfile
            from datetime import datetime
            
            first_out = successful_outputs[0]
            zip_name = f"Batch_Compress_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
            zip_path = first_out.parent / zip_name
            
            try:
                with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                    for out_file in successful_outputs:
                        if out_file.exists():
                            zf.write(out_file, out_file.name)
                self.log_message.emit(f"[ZIP OK] Created {zip_path.name}")
            except Exception as e:
                self.log_message.emit(f"[ZIP ERROR] Failed to create zip: {e}")

        self.log_message.emit("Processing complete.")
        self.processing_finished.emit()

    def _gather_files(self) -> list[Path]:
        files = set()
        is_recursive = self.options.get('recursive', False)
        process_images = self.options.get('process_images', True)
        process_videos = self.options.get('process_videos', True)

        use_suffix = self.options.get('use_suffix', True)
        suffix = self.options.get('suffix', '_compressed') if use_suffix else ''
        skip_existing = self.options.get('skip_existing', False)

        img_check = self.image_proc.is_supported
        vid_check = self.video_proc.is_supported
        
        use_skip = self.options.get('use_skip_pattern', False)
        skip_mode = self.options.get('skip_pattern_mode', 'Contains')
        skip_case = self.options.get('skip_pattern_case', False)
        skip_patterns = [p.strip() for p in self.options.get('skip_patterns', '').split(',') if p.strip()]
        
        import re
        regex_patterns = []
        if use_skip and skip_patterns and skip_mode == "Regex":
            flags = 0 if skip_case else re.IGNORECASE
            for pat in skip_patterns:
                try:
                    regex_patterns.append(re.compile(pat, flags))
                except re.error:
                    pass

        def should_skip(name: str) -> bool:
            if not use_skip or not skip_patterns:
                return False
                
            n = name if skip_case else name.lower()
            for pat in skip_patterns:
                p = pat if skip_case else pat.lower()
                
                if skip_mode == "Contains" and p in n: return True
                if skip_mode == "Exact Match" and p == n: return True
                if skip_mode == "Starts With" and n.startswith(p): return True
                if skip_mode == "Ends With" and n.endswith(p): return True
                
            if skip_mode == "Regex":
                for rx in regex_patterns:
                    if rx.search(name): return True
                    
            return False

        def add_file_if_supported(p: Path):
            if skip_existing and suffix and p.stem.endswith(suffix):
                return
            if should_skip(p.name):
                return
                
            p_str = str(p)
            if process_images and img_check(p_str):
                files.add(p)
            elif process_videos and vid_check(p_str):
                files.add(p)

        for path_str in self.paths:
            p = Path(path_str)
            if p.is_file():
                add_file_if_supported(p)
            elif p.is_dir():
                if is_recursive:
                    for root, _, filenames in os.walk(p):
                        for name in filenames:
                            add_file_if_supported(Path(root) / name)
                else:
                    for child in p.iterdir():
                        if child.is_file():
                            add_file_if_supported(child)
        
        # Convert back to list
        return list(files)

    def _process_single_file(self, path: Path) -> tuple[bool, str, str, int, int]:
        if self._is_cancelled:
            return False, "Cancelled", "", 0, 0
            
        orig_size = 0
        if path.exists():
            orig_size = path.stat().st_size

        overwrite = self.options.get('overwrite', False)
        use_suffix = self.options.get('use_suffix', True)
        suffix = self.options.get('suffix', '_compressed') if use_suffix else ''
        use_target = self.options.get('use_target', False)
        target_dir = self.options.get('target_dir', '') if use_target else None
        skip_existing = self.options.get('skip_existing', False)
        
        is_img = self.image_proc.is_supported(str(path))
        is_vid = self.video_proc.is_supported(str(path))
        
        if is_img:
            if self.options.get('smart_auto_image', False):
                _, img_format = SmartHeuristics.get_batch_image_suggestion(path.suffix)
                preset = "Custom"
            else:
                img_format = self.options.get('image_format', "Keep Original Extension")
                preset = self.options.get('image_preset', "Lossless")
            
            img_quality = int(self.options.get('img_quality', 85))

            res_success, res_msg, res_out = self.image_proc.process(
                str(path),
                preset,
                overwrite,
                suffix,
                target_dir,
                img_format,
                skip_existing,
                img_quality
            )
            new_size = Path(res_out).stat().st_size if res_success and Path(res_out).exists() else 0
            return res_success, res_msg, res_out, orig_size, new_size
        elif is_vid:
            preset = self.options.get('video_preset', "Main AV1")
            crf_val = self.options.get('video_crf', "")
            if self.options.get('smart_auto_video', False):
                preset, crf_val, _, _ = SmartHeuristics.get_batch_video_suggestion(path.suffix)
                
            codec = self.options.get('video_codec', 'AV1')
            out_container = self.options.get('video_container', '.mkv')
            remove_audio = self.options.get('remove_audio', False)
            save_metadata = self.options.get('save_metadata', True)
            extract_audio = self.options.get('extract_audio', False)

            res_success, res_msg, res_out = self.video_proc.process(
                str(path),
                preset,
                overwrite,
                suffix,
                target_dir,
                crf_val,
                self.options.get('video_fps', ""),
                self.options.get('video_res', ""),
                skip_existing,
                codec,
                out_container,
                remove_audio,
                save_metadata,
                extract_audio
            )
            new_size = Path(res_out).stat().st_size if res_success and Path(res_out).exists() else 0
            return res_success, res_msg, res_out, orig_size, new_size
        
        return False, "Unsupported file", "", 0, 0

    def _process_sequence(self, seq: dict) -> tuple[bool, str, str]:
        if self._is_cancelled:
            return False, "Cancelled", ""

        overwrite = self.options.get('overwrite', False)
        use_suffix = self.options.get('use_suffix', True)
        suffix = self.options.get('suffix', '_compressed') if use_suffix else ''
        use_target = self.options.get('use_target', False)
        target_dir = self.options.get('target_dir', '') if use_target else None
        
        # Sequences are processed via VideoProcessor
        crf = self.options.get('video_crf', '')
        fps = self.options.get('video_fps', '')
        res = self.options.get('video_res', '')
        
        orig_size = 0
        try:
            from .sequence_detector import get_sequence_files
            seq_files = get_sequence_files(seq)
            for sf in seq_files:
                if Path(sf).exists():
                    orig_size += Path(sf).stat().st_size
        except Exception as e:
            print(f"[WARN] Failed to read sequence size: {e}")
        
        res_success, res_msg, res_out = self.video_proc.process_sequence(seq, overwrite, suffix, target_dir, crf, fps, res)
        new_size = Path(res_out).stat().st_size if res_success and Path(res_out).exists() else 0
        return res_success, res_msg, res_out, orig_size, new_size
