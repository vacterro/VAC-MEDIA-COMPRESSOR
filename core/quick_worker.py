import os
from PyQt6.QtCore import QThread, pyqtSignal
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from .quick_converter import QuickConverter
from .utils import cancel_all_subprocesses

class QuickWorker(QThread):
    progress_updated = pyqtSignal(int, int) # current, total
    log_message = pyqtSignal(str)
    item_status_updated = pyqtSignal(int, str) # row_index, status_string
    processing_finished = pyqtSignal(int, int) # success_count, total
    stats_updated = pyqtSignal(int, int) # original_size, new_size

    def __init__(self, tasks):
        """
        tasks is a list of dicts:
        {
            'row': int,
            'path': str,
            'type': str,
            'action': str,
            'option': str
        }
        """
        super().__init__()
        self.tasks = tasks
        self.converter = QuickConverter()
        self._is_cancelled = False

    def cancel(self):
        self._is_cancelled = True
        cancel_all_subprocesses()

    def run(self):
        total = len(self.tasks)
        success_count = 0
        self.progress_updated.emit(0, total)

        workers = os.cpu_count() or 4

        with ThreadPoolExecutor(max_workers=workers) as executor:
            future_to_task = {
                executor.submit(self._process_task, task): task
                for task in self.tasks
            }

            processed = 0
            for future in as_completed(future_to_task):
                if self._is_cancelled:
                    self.log_message.emit("[INFO] Quick Conversion cancelled by user.")
                    break

                task = future_to_task[future]
                try:
                    result = future.result()
                    if len(result) == 2:
                        success, msg = result
                        orig_size, new_size = 0, 0
                    else:
                        success, msg, orig_size, new_size = result
                        
                    status_str = "OK" if success else "FAIL"
                    self.item_status_updated.emit(task['row'], status_str)
                    self.log_message.emit(f"[{status_str}] {Path(task['path']).name} : {msg}")
                    if success:
                        success_count += 1
                        if orig_size > 0 or new_size > 0:
                            self.stats_updated.emit(orig_size, new_size)
                except Exception as exc:
                    self.log_message.emit(f"[ERROR] {Path(task['path']).name} generated an exception: {exc}")
                    self.item_status_updated.emit(task['row'], "ERROR")

                processed += 1
                self.progress_updated.emit(processed, total)

        self.processing_finished.emit(success_count, total)

    def _process_task(self, task) -> tuple[bool, str, int, int]:
        if self._is_cancelled:
            return False, "Cancelled", 0, 0
            
        orig_size = 0
        path_obj = Path(task['path'])
        if path_obj.exists():
            orig_size = path_obj.stat().st_size

        self.item_status_updated.emit(task['row'], "Processing...")
        if task['type'] == "Image":
            result = self.converter.process_image(task['path'], task['action'], task['option'], task.get('adjustments'))
        else:
            result = self.converter.process_video(task['path'], task['action'], task['option'], task.get('adjustments'))
            
        if len(result) == 3:
            success, msg, out_path = result
            new_size = Path(out_path).stat().st_size if success and out_path and Path(out_path).exists() else 0
        else:
            success, msg = result[:2]
            new_size = 0
            
        return success, msg, orig_size, new_size
