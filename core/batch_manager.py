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
                    success, msg, out_path = future.result()
                    status = "OK" if success else "FAIL"
                    if success:
                        self.log_message.emit(f"[{status}] {task_name} -> {Path(out_path).name}")
                    else:
                        self.log_message.emit(f"[{status}] {task_name} : {msg}")
                except Exception as exc:
                    self.log_message.emit(f"[ERROR] {task_name} generated an exception: {exc}")

                processed_count += 1
                self.progress_updated.emit(processed_count, total_files)

        self.log_message.emit("Processing complete.")
        self.processing_finished.emit()

    def _gather_files(self) -> list[Path]:
        files = []
        is_recursive = self.options.get('recursive', False)
        process_images = self.options.get('process_images', True)
        process_videos = self.options.get('process_videos', True)

        def add_file_if_supported(p: Path):
            if process_images and self.image_proc.is_supported(str(p)):
                files.append(p)
            elif process_videos and self.video_proc.is_supported(str(p)):
                files.append(p)

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
        
        # Deduplicate
        return list(set(files))

    def _process_single_file(self, path: Path) -> tuple[bool, str, str]:
        if self._is_cancelled:
            return False, "Cancelled", ""

        overwrite = self.options.get('overwrite', False)
        use_suffix = self.options.get('use_suffix', True)
        suffix = self.options.get('suffix', '_compressed') if use_suffix else ''
        use_target = self.options.get('use_target', False)
        target_dir = self.options.get('target_dir', '') if use_target else None
        
        if self.image_proc.is_supported(str(path)):
            preset = self.options.get('image_preset', 'Lossless')
            
            force_format = self.options.get('force_image_format', False)
            out_format = self.options.get('image_format', '') if force_format else "Keep Original Extension"
            
            if self.options.get('smart_auto_image', False):
                preset, out_format = SmartHeuristics.get_batch_image_suggestion(path.suffix)
                
            return self.image_proc.process(str(path), preset, overwrite, suffix, target_dir, out_format)
            
        elif self.video_proc.is_supported(str(path)):
            preset = self.options.get('video_preset', 'Main AV1')
            crf = self.options.get('video_crf', '')
            fps = self.options.get('video_fps', '')
            res = self.options.get('video_res', '')
            
            if self.options.get('smart_auto_video', False):
                preset, crf, fps, res = SmartHeuristics.get_batch_video_suggestion(path.suffix)
                
            return self.video_proc.process(str(path), preset, overwrite, suffix, target_dir, crf, fps, res)
        
        return False, "Unsupported file", ""

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
        
        return self.video_proc.process_sequence(seq, overwrite, suffix, target_dir, crf, fps, res)
