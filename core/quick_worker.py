from PyQt6.QtCore import QThread, pyqtSignal
from pathlib import Path
from .quick_converter import QuickConverter
from .utils import cancel_all_subprocesses

class QuickWorker(QThread):
    progress_updated = pyqtSignal(int, int) # current, total
    log_message = pyqtSignal(str)
    item_status_updated = pyqtSignal(int, str) # row_index, status_string
    processing_finished = pyqtSignal(int, int) # success_count, total

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

        for i, task in enumerate(self.tasks):
            if self._is_cancelled:
                self.log_message.emit("[INFO] Quick Conversion cancelled by user.")
                break
                
            row = task['row']
            path = task['path']
            ftype = task['type']
            action = task['action']
            option = task['option']

            self.item_status_updated.emit(row, "Processing...")

            if ftype == "Image":
                success, msg = self.converter.process_image(path, action, option)
            else:
                success, msg = self.converter.process_video(path, action, option)

            status_str = "OK" if success else "FAIL"
            self.item_status_updated.emit(row, status_str)
            self.log_message.emit(f"[{status_str}] {Path(path).name} : {msg}")

            if success:
                success_count += 1
            
            self.progress_updated.emit(i + 1, total)

        self.processing_finished.emit(success_count, total)
