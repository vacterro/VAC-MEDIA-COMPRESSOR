import sys
import os
from pathlib import Path
from PyQt6.QtWidgets import (
    QStackedWidget, QSplitter,
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFrame, QCheckBox, QComboBox, QLineEdit, 
    QProgressBar, QTextEdit, QGroupBox, QFileDialog, QTabWidget,
    QAbstractItemView, QListView, QTreeView, QTableWidget, QTableWidgetItem,
    QHeaderView, QColorDialog, QSlider, QButtonGroup, QGridLayout,
    QSystemTrayIcon, QMenu, QSpinBox, QListWidget, QListWidgetItem
)
from PyQt6.QtCore import Qt, QSettings, pyqtSignal
from PyQt6.QtGui import QIcon, QAction
from core.batch_manager import BatchManager
from core.quick_converter import QuickConverter
from core.quick_worker import QuickWorker
from core.theme_manager import ThemeManager
from core.smart_heuristics import SmartHeuristics
from gui.styles import generate_stylesheet

IMG_HINTS = {
    "Lossless": "Re-optimizes files without losing quality. Best for archiving originals.",
    "Web": "Lossy compression (Quality 80). Balances size and quality. Best for general web use.",
    "Quality > Size": "Lossy compression (Quality 92). Prioritizes visual fidelity. Best for high-res photos.",
    "Size > Quality": "Lossy compression (Quality 60). Aggressive compression. Best for thumbnails/low-bandwidth."
}

VID_HINTS = {
    "Main AV1": "CRF 28, Preset 6. Strong general-purpose compression retaining high visual quality.",
    "Course AV1": "CRF 30, Preset 5, 1080p Max, 24fps. Best for screen recordings, lectures, and tutorials."
}

IMAGE_ACTIONS = [
    "Convert to JPG", "Convert to WEBP", "Lossy Compress", "Web Compress",
    "Palette 512 colors", "Palette 2048 colors", 
    "DDS -> PNG (texconv / Pillow)", 
    "PNG -> DDS (texconv BC7_UNORM)", 
    "PNG -> DDS (texconv BC3_UNORM)",
    "PNG -> DDS (texconv BC1_UNORM)",
    "PNG -> DDS Normal Map (BC5_UNORM)",
    "PIC -> TGA (8x Upscale Nearest)",
    "TGA -> PNG (Lossless)",
    "PNG -> TGA (Lossless)",
    "2x Upscale (Nearest / Pixel Art)",
    "4x Upscale (Nearest / Pixel Art)",
    "8x Upscale (Nearest / Pixel Art)",
    "2x Upscale (Lanczos / Smooth)",
    "4x Upscale (Lanczos / Smooth)",
    "8x Upscale (Lanczos / Smooth)"
]
IMAGE_OPTIONS = ["Default", "Resize 50%", "Resize 200%"]

VIDEO_ACTIONS = [
    "Extract Audio (MP3)", "Extract Audio (WAV)", "Remove Audio (Fast / Copy)", 
    "Remove Audio (Slow / Compress)", "Extract Frames", "Make GIF (High Quality)", 
    "Make GIF (Small)", "Compress MKV (AV1)", "Compress MP4 (AV1)", 
    "Convert Format (AVI)", "Convert Format (M4V)", "Convert Format (MOV)", 
    "Convert Format (MP4)", "Convert Format (WebM)"
]
VIDEO_OPTIONS = ["Default"]

class SegmentedControl(QWidget):
    currentTextChanged = pyqtSignal(str)

    def __init__(self, items, default=None):
        super().__init__()
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        
        self.button_group = QButtonGroup(self)
        self.button_group.setExclusive(True)
        self.button_group.buttonClicked.connect(self._on_button_clicked)
        
        self.buttons = []
        for i, item in enumerate(items):
            btn = QPushButton(item)
            btn.setCheckable(True)
            btn.setMinimumHeight(44)
            # Style them so they look grouped
            btn.setStyleSheet("""
                QPushButton {
                    border-radius: 0px;
                    margin: 0px;
                }
                QPushButton:checked {
                    background-color: #008080;
                    color: #FFFFFF;
                }
            """)
            if i == 0:
                btn.setStyleSheet(btn.styleSheet() + "QPushButton { border-top-left-radius: 4px; border-bottom-left-radius: 4px; border-right: none; }")
            elif i == len(items) - 1:
                btn.setStyleSheet(btn.styleSheet() + "QPushButton { border-top-right-radius: 4px; border-bottom-right-radius: 4px; border-left: none; }")
            else:
                btn.setStyleSheet(btn.styleSheet() + "QPushButton { border-left: none; border-right: none; }")
                
            self.button_group.addButton(btn)
            self.layout.addWidget(btn)
            self.buttons.append(btn)
            
        if default:
            self.setCurrentText(default)
        elif self.buttons:
            self.buttons[0].setChecked(True)
            
    def _on_button_clicked(self, btn):
        self.currentTextChanged.emit(btn.text())
        
    def currentText(self):
        btn = self.button_group.checkedButton()
        return btn.text() if btn else ""
        
    def setCurrentText(self, text):
        for btn in self.buttons:
            if btn.text() == text:
                btn.setChecked(True)
                break

class DropZone(QFrame):
    def __init__(self, on_drop_callback, text="Drag & Drop Files or Folders Here"):
        super().__init__()
        self.setObjectName("dropZone")
        self.setAcceptDrops(True)
        self.on_drop_callback = on_drop_callback
        
        layout = QVBoxLayout()
        self.label = QLabel(text)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(self.label)
        
        self.browse_btn = QPushButton("Browse Files")
        self.browse_btn.setObjectName("browseBtn")
        self.browse_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.browse_btn.clicked.connect(self.browse_files)
        
        self.browse_dir_btn = QPushButton("Add Folder(s)")
        self.browse_dir_btn.setObjectName("browseBtn")
        self.browse_dir_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.browse_dir_btn.clicked.connect(self.browse_dirs)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(self.browse_btn)
        btn_layout.addWidget(self.browse_dir_btn)
        btn_layout.addStretch()
        
        layout.addLayout(btn_layout)
        self.setLayout(layout)
        self.setMinimumHeight(150)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.setStyleSheet("background-color: #E0E0E0;")

    def dragLeaveEvent(self, event):
        self.setStyleSheet("") 

    def dropEvent(self, event):
        self.setStyleSheet("")
        urls = event.mimeData().urls()
        paths = [url.toLocalFile() for url in urls if url.isLocalFile()]
        if paths:
            self.on_drop_callback(paths)

    def browse_files(self):
        from PyQt6.QtCore import QSettings
        settings = QSettings("VAC", "SmartVacMediaCompressor")
        last_dir = settings.value("last_dir", "")
        dialog = QFileDialog(self, "Select Files", last_dir)
        dialog.setFileMode(QFileDialog.FileMode.ExistingFiles)
        if dialog.exec():
            settings.setValue("last_dir", dialog.directory().absolutePath())
            paths = dialog.selectedFiles()
            if paths:
                self.on_drop_callback(paths)

    def browse_dirs(self):
        from PyQt6.QtCore import QSettings
        settings = QSettings("VAC", "SmartVacMediaCompressor")
        last_dir = settings.value("last_dir", "")
        dialog = QFileDialog(self, "Select Directories", last_dir)
        dialog.setFileMode(QFileDialog.FileMode.Directory)
        dialog.setOption(QFileDialog.Option.DontUseNativeDialog, True)
        dialog.setOption(QFileDialog.Option.ShowDirsOnly, True)
        for view in dialog.findChildren((QListView, QTreeView)):
            if isinstance(view.model(), type(dialog.findChild(QListView).model())):
                view.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)

        if dialog.exec():
            settings.setValue("last_dir", dialog.directory().absolutePath())
            paths = dialog.selectedFiles()
            if paths:
                self.on_drop_callback(paths)


from PyQt6.QtGui import QPainter, QColor

class DefragProgressBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.total = 0
        self.progress = 0
        self.setMinimumHeight(24)

    def setMaximum(self, total):
        self.total = total
        self.update()

    def setTextVisible(self, visible):
        pass

    def setValue(self, progress):
        self.progress = progress
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        
        # Draw vintage inset border and background
        painter.fillRect(self.rect(), QColor("#C0C0C0"))
        
        # Draw 3D inset border
        painter.setPen(QColor("#808080"))
        painter.drawLine(0, 0, self.width()-1, 0)
        painter.drawLine(0, 0, 0, self.height()-1)
        
        painter.setPen(QColor("#404040"))
        painter.drawLine(1, 1, self.width()-2, 1)
        painter.drawLine(1, 1, 1, self.height()-2)
        
        painter.setPen(QColor("#FFFFFF"))
        painter.drawLine(0, self.height()-1, self.width()-1, self.height()-1)
        painter.drawLine(self.width()-1, 0, self.width()-1, self.height()-1)
        
        painter.setPen(QColor("#E6E6E6"))
        painter.drawLine(1, self.height()-2, self.width()-2, self.height()-2)
        painter.drawLine(self.width()-2, 1, self.width()-2, self.height()-2)
        
        # Inner drawing area
        inner_rect = self.rect().adjusted(2, 2, -2, -2)
        painter.fillRect(inner_rect, QColor("#FFFFFF"))
        
        if self.total <= 0:
            return
            
        cell_w = 8
        cell_h = inner_rect.height() - 4
        margin = 2
        
        # Max cells that can fit
        max_cells = (inner_rect.width() - 4) // (cell_w + margin)
        
        if max_cells <= 0: return
        
        if self.total > max_cells:
            filled_cells = int((self.progress / self.total) * max_cells)
            total_cells_drawn = max_cells
        else:
            filled_cells = self.progress
            total_cells_drawn = self.total
            
        start_x = inner_rect.left() + 2
        start_y = inner_rect.top() + 2
        
        color_done = QColor("#008080")
        color_remaining = QColor("#FF0000")
        
        for i in range(total_cells_drawn):
            cx = start_x + i * (cell_w + margin)
            if i < filled_cells:
                painter.fillRect(cx, start_y, cell_w, cell_h, color_done)
            else:
                painter.fillRect(cx, start_y, cell_w, cell_h, color_remaining)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SMART VAC MEDIA COMPRESSOR")
        self.setMinimumSize(600, 400)

        self.theme_manager = ThemeManager()
        palette = self.theme_manager.get_palette()
        font_family = self.theme_manager.get_font_family()
        font_size = self.theme_manager.get_font_size()
        self.setStyleSheet(generate_stylesheet(palette, font_family, font_size))

        self.total_original_bytes = 0
        self.total_compressed_bytes = 0

        self.batch_paths = set()
        self.worker = None
        self.quick_converter = QuickConverter()
        
        self.setup_system_tray()

        self.settings = QSettings("SmartVac", "MediaCompressor")

        self._init_ui()
        self.load_settings()

        from PyQt6.QtCore import QTimer
        self.autosave_timer = QTimer(self)
        self.autosave_timer.timeout.connect(self.save_settings)
        self.autosave_timer.start(5000)

    def setup_system_tray(self):
        self.tray_icon = QSystemTrayIcon(self)
        icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "icon.png")
        if os.path.exists(icon_path):
            self.app_icon = QIcon(icon_path)
            self.setWindowIcon(self.app_icon)
            self.tray_icon.setIcon(self.app_icon)
        
        show_action = QAction("Show", self)
        quit_action = QAction("Exit", self)
        
        show_action.triggered.connect(self.showNormal)
        quit_action.triggered.connect(self.force_quit)
        
        tray_menu = QMenu()
        tray_menu.addAction(show_action)
        tray_menu.addAction(quit_action)
        self.tray_icon.setContextMenu(tray_menu)
        
        self.tray_icon.activated.connect(self.tray_icon_activated)
        self.tray_icon.show()

    def tray_icon_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            if self.isHidden() or self.isMinimized():
                self.showNormal()
                self.activateWindow()
            else:
                self.hide()

    def changeEvent(self, event):
        if event.type() == event.Type.WindowStateChange:
            if self.windowState() & Qt.WindowState.WindowMinimized:
                # If a worker is running (batch or quick)
                is_working = (self.worker and self.worker.isRunning())
                if is_working:
                    self.hide()
                    self.tray_icon.showMessage(
                        "Compressor Running",
                        "Minimized to system tray to save resources.",
                        QSystemTrayIcon.MessageIcon.Information,
                        2000
                    )
        super().changeEvent(event)

    def _init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(4, 4, 4, 4)

        # Build Sidebar and Main Area layout
        self.content_layout = QHBoxLayout()
        
        # 1. Sidebar Menu (Vintage style)
        self.sidebar = QListWidget()
        self.sidebar.setObjectName("sidebarMenu")
        self.sidebar.setFixedWidth(180)
        self.sidebar.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.sidebar.addItems(["General Settings", "Image Processing", "Video Processing", "Quick Converter", "Appearance"])
        
        # 2. Main Area Stack
        self.main_stack = QStackedWidget()
        
        # Create the containers for each section
        self.page_general = QWidget()
        self.page_image = QWidget()
        self.page_video = QWidget()
        self.page_quick = QWidget()
        self.page_appearance = QWidget()
        
        self.main_stack.addWidget(self.page_general)
        self.main_stack.addWidget(self.page_image)
        self.main_stack.addWidget(self.page_video)
        self.main_stack.addWidget(self.page_quick)
        self.main_stack.addWidget(self.page_appearance)
        
        self.sidebar.currentRowChanged.connect(self.main_stack.setCurrentIndex)
        
        # Build the architecture: 
        # Batch (General, Image, Video) share the same bottom queue visually, 
        # but since they are separate pages, we need a clever layout.
        
        # Wait, the plan was: Left Sidebar -> Right Side (Top: Settings, Bottom: Queue).
        # We can create a Right Side VBox. 
        self.right_widget = QWidget()
        self.right_layout = QVBoxLayout(self.right_widget)
        self.right_layout.setContentsMargins(0,0,0,0)
        
        # Top Split (Settings Stack)
        self.settings_stack = QStackedWidget()
        self.settings_stack.addWidget(self.page_general)
        self.settings_stack.addWidget(self.page_image)
        self.settings_stack.addWidget(self.page_video)
        self.settings_stack.addWidget(self.page_quick)
        self.settings_stack.addWidget(self.page_appearance)
        
        # Bottom Split (Queue Stack - to switch between Batch Queue and Quick Queue)
        self.queue_stack = QStackedWidget()
        self.batch_queue_container = QWidget()
        self.quick_queue_container = QWidget()
        self.appearance_empty_container = QWidget() # empty for appearance
        
        self.queue_stack.addWidget(self.batch_queue_container) # index 0 (general)
        self.queue_stack.addWidget(self.batch_queue_container) # index 1 (image)
        self.queue_stack.addWidget(self.batch_queue_container) # index 2 (video)
        self.queue_stack.addWidget(self.quick_queue_container) # index 3 (quick)
        self.queue_stack.addWidget(self.appearance_empty_container) # index 4 (appearance)
        
        # QSplitter to allow resizing Settings vs Queue
        self.main_splitter = QSplitter(Qt.Orientation.Vertical)
        self.main_splitter.addWidget(self.settings_stack)
        self.main_splitter.addWidget(self.queue_stack)
        self.main_splitter.setSizes([300, 400])
        self.right_layout.addWidget(self.main_splitter)
        
        def on_sidebar_change(idx):
            self.settings_stack.setCurrentIndex(idx)
            # Route the queue stack appropriately
            if idx in [0, 1, 2]:
                self.queue_stack.setCurrentWidget(self.batch_queue_container)
            elif idx == 3:
                self.queue_stack.setCurrentWidget(self.quick_queue_container)
            elif idx == 4:
                self.queue_stack.setCurrentWidget(self.appearance_empty_container)
                
        self.sidebar.currentRowChanged.connect(on_sidebar_change)
        
        self.content_layout.addWidget(self.sidebar)
        self.content_layout.addWidget(self.right_widget, stretch=1)
        
        main_layout.addLayout(self.content_layout, stretch=1)

        self._setup_batch_tab()
        self._setup_quick_tab()
        self._setup_appearance_tab()

        progress_layout = QHBoxLayout()
        self.cancel_btn = QPushButton("Cancel Operation")
        self.cancel_btn.setObjectName("cancelBtn")
        self.cancel_btn.clicked.connect(self.cancel_processing)
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.setMinimumHeight(44)
        progress_layout.addWidget(self.cancel_btn)

        self.progress_bar = DefragProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setMinimumHeight(44)
        progress_layout.addWidget(self.progress_bar)
        
        main_layout.addLayout(progress_layout)

        # Size Rewards Dashboard
        self.rewards_board = QFrame()
        self.rewards_board.setObjectName("rewardsBoard")
        rewards_layout = QHBoxLayout(self.rewards_board)
        
        self.lbl_orig_size = QLabel("Original: 0.0 MB")
        self.lbl_orig_size.setObjectName("originalText")
        
        self.lbl_new_size = QLabel("New: 0.0 MB")
        self.lbl_new_size.setObjectName("newText")
        
        self.lbl_saved_size = QLabel("🏆 Total Saved: 0.0 MB (0%)")
        self.lbl_saved_size.setObjectName("savedText")
        
        rewards_layout.addWidget(self.lbl_orig_size)
        rewards_layout.addStretch()
        rewards_layout.addWidget(self.lbl_saved_size)
        rewards_layout.addStretch()
        rewards_layout.addWidget(self.lbl_new_size)
        
        main_layout.addWidget(self.rewards_board)

        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setMaximumHeight(80)
        main_layout.addWidget(self.log_view)
        
        # Set default tab
        self.sidebar.setCurrentRow(0)

    def _setup_batch_tab(self):
        # We build the batch queue container for the bottom split
        right_layout = QVBoxLayout(self.batch_queue_container)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        self.batch_drop_zone = DropZone(self.on_batch_dropped, "Drop media here to begin")
        right_layout.addWidget(self.batch_drop_zone, stretch=1)
        
        paths_layout = QHBoxLayout()
        self.batch_paths_label = QLabel("0 files queued")
        self.batch_paths_label.setObjectName("subtitleLabel")
        clear_btn = QPushButton("Clear Queue")
        clear_btn.setObjectName("browseBtn")
        clear_btn.clicked.connect(self.clear_batch_selection)
        clear_btn.setMinimumHeight(44)
        paths_layout.addWidget(self.batch_paths_label)
        paths_layout.addStretch()
        paths_layout.addWidget(clear_btn)
        right_layout.addLayout(paths_layout)

        self.queue_list = QListWidget()
        self.queue_list.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.queue_list.setAlternatingRowColors(True)
        self.queue_list.itemChanged.connect(self._on_queue_item_changed)
        self.queue_list.installEventFilter(self)
        right_layout.addWidget(self.queue_list, stretch=2)

        buttons_layout = QHBoxLayout()
        self.start_btn = QPushButton("Compress Files")
        self.start_btn.setObjectName("startBtn")
        self.start_btn.setEnabled(False)
        self.start_btn.clicked.connect(self.start_batch_processing)
        self.start_btn.setMinimumHeight(44) 

        self.pause_btn = QPushButton("Pause")
        self.pause_btn.setObjectName("pauseBtn")
        self.pause_btn.setEnabled(False)
        self.pause_btn.clicked.connect(self.toggle_pause)
        self.pause_btn.setMinimumHeight(44)

        buttons_layout.addWidget(self.start_btn)
        buttons_layout.addWidget(self.pause_btn)
        right_layout.addLayout(buttons_layout)
        
        # Build the top settings pages
        self._setup_batch_general_tab()
        self._setup_batch_image_tab()
        self._setup_batch_video_tab()

    def _setup_batch_general_tab(self):
        gen_layout = QGridLayout(self.page_general)
        gen_layout.setSpacing(4)
        
        self.chk_recursive = QCheckBox("Recursive scan")
        self.chk_recursive.setChecked(True)
        self.chk_overwrite = QCheckBox("Overwrite original")
        
        self.chk_skip_existing = QCheckBox("Skip Existing")
        self.chk_skip_existing.setChecked(True)
        self.chk_auto_process = QCheckBox("Auto-process")
        
        gen_layout.addWidget(self.chk_recursive, 0, 0)
        gen_layout.addWidget(self.chk_overwrite, 0, 1)
        gen_layout.addWidget(self.chk_skip_existing, 1, 0)
        gen_layout.addWidget(self.chk_auto_process, 1, 1)
        
        # Target
        self.chk_target = QCheckBox("Output Target:")
        self.inp_target = QLineEdit()
        self.inp_target.setEnabled(False)
        self.btn_target = QPushButton("Browse")
        self.btn_target.setMinimumSize(44, 44)
        self.btn_target.setEnabled(False)
        self.btn_target.clicked.connect(self.browse_target_folder)
        self.chk_target.toggled.connect(self.inp_target.setEnabled)
        self.chk_target.toggled.connect(self.btn_target.setEnabled)
        
        gen_layout.addWidget(self.chk_target, 2, 0)
        gen_layout.addWidget(self.inp_target, 2, 1)
        gen_layout.addWidget(self.btn_target, 2, 2)
        
        # Suffix
        self.chk_suffix = QCheckBox("Add suffix:")
        self.chk_suffix.setChecked(True)
        self.inp_suffix = QLineEdit("_compressed")
        self.chk_suffix.toggled.connect(self.inp_suffix.setEnabled)
        gen_layout.addWidget(self.chk_suffix, 3, 0)
        gen_layout.addWidget(self.inp_suffix, 3, 1, 1, 2)
        
        # Skip Pattern
        self.chk_skip_pattern = QCheckBox("Skip if name:")
        self.cmb_skip_mode = QComboBox()
        self.cmb_skip_mode.addItems(["Contains", "Exact Match", "Starts With", "Ends With", "Regex"])
        self.chk_skip_case = QCheckBox("Case")
        self.inp_skip_pattern = QLineEdit()
        
        self.inp_skip_pattern.setEnabled(False)
        self.cmb_skip_mode.setEnabled(False)
        self.chk_skip_case.setEnabled(False)
        def on_skip_toggled(checked):
            self.inp_skip_pattern.setEnabled(checked)
            self.cmb_skip_mode.setEnabled(checked)
            self.chk_skip_case.setEnabled(checked)
        self.chk_skip_pattern.toggled.connect(on_skip_toggled)
        
        gen_layout.addWidget(self.chk_skip_pattern, 4, 0)
        gen_layout.addWidget(self.cmb_skip_mode, 4, 1)
        gen_layout.addWidget(self.chk_skip_case, 4, 2)
        gen_layout.addWidget(self.inp_skip_pattern, 5, 0, 1, 3)
        
        # CPU
        gen_layout.addWidget(QLabel("Max CPU Cores:"), 6, 0)
        self.spin_cpu_cores = QSpinBox()
        self.spin_cpu_cores.setMinimum(1)
        self.spin_cpu_cores.setMaximum(os.cpu_count() or 4)
        self.spin_cpu_cores.setValue(os.cpu_count() or 4)
        gen_layout.addWidget(self.spin_cpu_cores, 6, 1)
        
        gen_layout.setRowStretch(7, 1)
        

    def _setup_batch_image_tab(self):
        img_layout = QGridLayout(self.page_image)
        img_layout.setSpacing(4)
        
        self.chk_process_img = QCheckBox("Process Images")
        self.chk_process_img.setChecked(True)
        self.chk_smart_img = QCheckBox("Smart Auto")
        
        img_layout.addWidget(self.chk_process_img, 0, 0)
        img_layout.addWidget(self.chk_smart_img, 0, 1)
        
        img_layout.addWidget(QLabel("Preset:"), 1, 0)
        self.cmb_img_preset = SegmentedControl(list(IMG_HINTS.keys()) + ["Custom"], "Lossless")
        img_layout.addWidget(self.cmb_img_preset, 1, 1, 1, 2)
        
        self.img_hint_label = QLabel(IMG_HINTS["Lossless"])
        self.img_hint_label.setObjectName("hintLabel")
        self.img_hint_label.setWordWrap(True)
        img_layout.addWidget(self.img_hint_label, 2, 0, 1, 3)
        
        img_layout.addWidget(QLabel("Quality:"), 3, 0)
        self.sld_img_quality = QSlider(Qt.Orientation.Horizontal)
        self.sld_img_quality.setRange(10, 100)
        self.sld_img_quality.setValue(85)
        self.lbl_img_quality_val = QLabel("85")
        self.sld_img_quality.valueChanged.connect(lambda v: self.lbl_img_quality_val.setText(str(v)))
        self.btn_reset_img_quality = QPushButton("⟲")
        self.btn_reset_img_quality.setFixedSize(44, 44)
        self.btn_reset_img_quality.clicked.connect(lambda: self.sld_img_quality.setValue(85))
        
        img_layout.addWidget(self.sld_img_quality, 3, 1)
        img_layout.addWidget(self.lbl_img_quality_val, 3, 2)
        img_layout.addWidget(self.btn_reset_img_quality, 3, 3)
        
        def on_img_preset_changed(text):
            if text in IMG_HINTS:
                self.img_hint_label.setText(IMG_HINTS[text])
            else:
                self.img_hint_label.setText("Custom manual quality slider.")
            self.sld_img_quality.setEnabled(text != "Lossless")
                
        self.cmb_img_preset.currentTextChanged.connect(on_img_preset_changed)
        
        self.chk_force_img_format = QCheckBox("Force Output Format:")
        self.chk_force_img_format.setChecked(False)
        self.cmb_img_format = SegmentedControl(["Keep Original", "WebP", "AVIF", "JPG", "PNG", "TIFF", "ICO"], "Keep Original")
        self.cmb_img_format.setEnabled(False)
        
        self.chk_force_img_format.toggled.connect(
            lambda checked: self.cmb_img_format.setEnabled(checked and not self.chk_smart_img.isChecked())
        )
        
        def on_smart_img_toggled(checked):
            self.cmb_img_preset.setEnabled(not checked)
            self.chk_force_img_format.setEnabled(not checked)
            if checked:
                self.cmb_img_format.setEnabled(False)
            else:
                self.cmb_img_format.setEnabled(self.chk_force_img_format.isChecked())
                
        self.chk_smart_img.toggled.connect(on_smart_img_toggled)
        
        img_layout.addWidget(self.chk_force_img_format, 4, 0)
        img_layout.addWidget(self.cmb_img_format, 4, 1, 1, 3)
        
        img_layout.setRowStretch(5, 1)
        

    def _setup_batch_video_tab(self):
        vid_layout = QGridLayout(self.page_video)
        vid_layout.setSpacing(4)
        
        self.chk_process_vid = QCheckBox("Process Videos")
        self.chk_process_vid.setChecked(True)
        self.chk_smart_vid = QCheckBox("Smart Auto")
        self.chk_compile_seq = QCheckBox("Compile Images")
        
        vid_layout.addWidget(self.chk_process_vid, 0, 0)
        vid_layout.addWidget(self.chk_smart_vid, 0, 1)
        vid_layout.addWidget(self.chk_compile_seq, 0, 2)
        
        vid_layout.addWidget(QLabel("Preset:"), 1, 0)
        self.cmb_vid_preset = SegmentedControl(list(VID_HINTS.keys()), "Main AV1")
        vid_layout.addWidget(self.cmb_vid_preset, 1, 1, 1, 2)
        
        self.vid_hint_label = QLabel(VID_HINTS["Main AV1"])
        self.vid_hint_label.setObjectName("hintLabel")
        self.vid_hint_label.setWordWrap(True)
        self.cmb_vid_preset.currentTextChanged.connect(lambda t: self.vid_hint_label.setText(VID_HINTS.get(t, "")))
        vid_layout.addWidget(self.vid_hint_label, 2, 0, 1, 3)
        
        vid_layout.addWidget(QLabel("Container:"), 3, 0)
        self.cmb_vid_container = SegmentedControl([".mkv", ".mp4", ".webm"], ".mkv")
        vid_layout.addWidget(self.cmb_vid_container, 3, 1)
        
        vid_layout.addWidget(QLabel("Codec:"), 4, 0)
        self.cmb_vid_codec = SegmentedControl(["AV1", "HEVC", "H.264"], "AV1")
        vid_layout.addWidget(self.cmb_vid_codec, 4, 1)
        
        self.chk_remove_audio = QCheckBox("Remove Audio")
        self.chk_save_metadata = QCheckBox("Save Metadata")
        self.chk_save_metadata.setChecked(True)
        vid_layout.addWidget(self.chk_remove_audio, 5, 0)
        vid_layout.addWidget(self.chk_save_metadata, 5, 1)
        
        vid_layout.addWidget(QLabel("CRF:"), 6, 0)
        self.sld_vid_crf = QSlider(Qt.Orientation.Horizontal)
        self.sld_vid_crf.setRange(0, 63)
        self.sld_vid_crf.setValue(28)
        self.lbl_vid_crf_val = QLabel("28")
        self.sld_vid_crf.valueChanged.connect(lambda v: self.lbl_vid_crf_val.setText(str(v)))
        self.btn_reset_vid_crf = QPushButton("⟲")
        self.btn_reset_vid_crf.setFixedSize(44, 44)
        vid_layout.addWidget(self.sld_vid_crf, 6, 1)
        vid_layout.addWidget(self.lbl_vid_crf_val, 6, 2)
        vid_layout.addWidget(self.btn_reset_vid_crf, 6, 3)
        
        self.codec_defaults = {
            "AV1": {"range": (0, 63), "default": 28},
            "HEVC": {"range": (0, 51), "default": 24},
            "H.264": {"range": (0, 51), "default": 20}
        }
        
        def reset_crf():
            current_codec = self.cmb_vid_codec.currentText()
            default_val = self.codec_defaults.get(current_codec, {}).get("default", 28)
            self.sld_vid_crf.setValue(default_val)
            
        self.btn_reset_vid_crf.clicked.connect(reset_crf)
        
        def on_vid_codec_changed(codec):
            settings = self.codec_defaults.get(codec, {"range": (0, 63), "default": 28})
            self.sld_vid_crf.setRange(settings["range"][0], settings["range"][1])
            self.sld_vid_crf.setValue(settings["default"])
            
        self.cmb_vid_codec.currentTextChanged.connect(on_vid_codec_changed)
        
        vid_layout.addWidget(QLabel("FPS:"), 7, 0)
        self.inp_vid_fps = QLineEdit()
        self.inp_vid_fps.setPlaceholderText("Orig")
        self.btn_reset_fps = QPushButton("⟲")
        self.btn_reset_fps.setFixedSize(44, 44)
        self.btn_reset_fps.clicked.connect(lambda: self.inp_vid_fps.setText(""))
        vid_layout.addWidget(self.inp_vid_fps, 7, 1)
        vid_layout.addWidget(self.btn_reset_fps, 7, 2)
        
        vid_layout.addWidget(QLabel("Res:"), 8, 0)
        self.inp_vid_res = QLineEdit()
        self.inp_vid_res.setPlaceholderText("1080p")
        self.btn_reset_res = QPushButton("⟲")
        self.btn_reset_res.setFixedSize(44, 44)
        self.btn_reset_res.clicked.connect(lambda: self.inp_vid_res.setText(""))
        vid_layout.addWidget(self.inp_vid_res, 8, 1)
        vid_layout.addWidget(self.btn_reset_res, 8, 2)
        
        def on_smart_vid_toggled(checked):
            self.cmb_vid_preset.setEnabled(not checked)
            self.sld_vid_crf.setEnabled(not checked)
            self.inp_vid_fps.setEnabled(not checked)
            self.inp_vid_res.setEnabled(not checked)
            
        self.chk_smart_vid.toggled.connect(on_smart_vid_toggled)
        
        vid_layout.setRowStretch(9, 1)
        
    def _setup_quick_tab(self):
        # Settings part for Top Stack (self.page_quick)
        quick_settings_layout = QVBoxLayout(self.page_quick)
        
        group_general = QGroupBox("Fast Conversions (Single Click)")
        g_layout = QGridLayout(group_general)
        
        self.btn_convert_mp4 = QPushButton("Convert to MP4 (x264, AAC)")
        self.btn_convert_av1 = QPushButton("Convert to AV1 (.mkv)")
        self.btn_convert_webp = QPushButton("Convert to WebP")
        self.btn_convert_jpg = QPushButton("Convert to JPG")
        
        for btn in [self.btn_convert_mp4, self.btn_convert_av1, self.btn_convert_webp, self.btn_convert_jpg]:
            btn.setMinimumHeight(44)
            btn.setObjectName("quickActionBtn")
            
        g_layout.addWidget(self.btn_convert_mp4, 0, 0)
        g_layout.addWidget(self.btn_convert_av1, 0, 1)
        g_layout.addWidget(self.btn_convert_webp, 1, 0)
        g_layout.addWidget(self.btn_convert_jpg, 1, 1)
        
        quick_settings_layout.addWidget(group_general)
        quick_settings_layout.addStretch()

        # Queue part for Bottom Stack (self.quick_queue_container)
        queue_layout = QVBoxLayout(self.quick_queue_container)
        queue_layout.setContentsMargins(0,0,0,0)
        
        self.quick_drop_zone = DropZone(self.on_quick_dropped, "Drop files for quick convert")
        queue_layout.addWidget(self.quick_drop_zone, stretch=1)
        
        table_layout = QHBoxLayout()
        self.queue_table = QTableWidget()
        self.queue_table.setColumnCount(4)
        self.queue_table.setHorizontalHeaderLabels(["Filename", "Size", "Type", "Status"])
        self.queue_table.horizontalHeader().setStretchLastSection(True)
        self.queue_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.queue_table.installEventFilter(self)
        table_layout.addWidget(self.queue_table)
        
        btn_layout = QVBoxLayout()
        add_files_btn = QPushButton("Add Files")
        add_files_btn.setMinimumHeight(44)
        add_files_btn.clicked.connect(self.add_quick_files)
        
        add_dirs_btn = QPushButton("Add Folders")
        add_dirs_btn.setMinimumHeight(44)
        add_dirs_btn.clicked.connect(self.add_quick_dirs)
        
        clear_btn = QPushButton("Clear Table")
        clear_btn.setMinimumHeight(44)
        clear_btn.clicked.connect(self.clear_quick_table)
        
        btn_layout.addWidget(add_files_btn)
        btn_layout.addWidget(add_dirs_btn)
        btn_layout.addWidget(clear_btn)
        btn_layout.addStretch()
        table_layout.addLayout(btn_layout)
        
        queue_layout.addLayout(table_layout, stretch=2)
        
        # We need the custom action UI 
        custom_action_layout = QHBoxLayout()
        self.quick_start_btn = QPushButton("Convert Files")
        self.quick_start_btn.setMinimumHeight(44)
        self.quick_start_btn.setObjectName("startBtn")
        self.quick_start_btn.clicked.connect(self.start_quick_processing)
        
        self.btn_advanced_edit = QPushButton("Advanced Edit")
        self.btn_advanced_edit.setMinimumHeight(44)
        
        
        custom_action_layout.addWidget(self.quick_start_btn)
        custom_action_layout.addWidget(self.btn_advanced_edit)
        self.btn_advanced_edit.clicked.connect(self.open_advanced_editor)
        
        queue_layout.addLayout(custom_action_layout)

    def _setup_appearance_tab(self):
        from PyQt6.QtWidgets import QFontComboBox, QSpinBox, QGridLayout
        from PyQt6.QtGui import QFont
        
        layout = QVBoxLayout(self.page_appearance)
        
        info_label = QLabel("Customize the look and feel of the application.")
        info_label.setObjectName("subtitleLabel")
        layout.addWidget(info_label)

        # Theme selection
        theme_layout = QHBoxLayout()
        theme_layout.addWidget(QLabel("Preset Theme:"))
        self.cmb_theme = QComboBox()
        self.cmb_theme.setToolTip("Select a curated color palette for the application interface.")
        self.cmb_theme.addItems(list(self.theme_manager.themes.keys()))
        self.cmb_theme.setCurrentText(self.theme_manager.get_active_theme_name())
        self.cmb_theme.currentTextChanged.connect(self.on_theme_changed)
        theme_layout.addWidget(self.cmb_theme)
        theme_layout.addStretch()
        layout.addLayout(theme_layout)

        # Typography
        type_group = QGroupBox("Typography")
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("Font Family:"))
        self.cmb_font = QFontComboBox()
        
        current_font = self.theme_manager.get_font_family()
        if current_font:
            self.cmb_font.setCurrentFont(QFont(current_font))
            
        type_layout.addWidget(self.cmb_font)
        
        type_layout.addSpacing(6)
        type_layout.addWidget(QLabel("Font Size:"))
        self.spn_font_size = QSpinBox()
        self.spn_font_size.setRange(8, 36)
        self.spn_font_size.setValue(self.theme_manager.get_font_size())
        type_layout.addWidget(self.spn_font_size)
        type_layout.addStretch()
        type_group.setLayout(type_layout)
        layout.addWidget(type_group)

        # Custom colors group
        self.grp_custom_colors = QGroupBox("Custom Palette Colors")
        custom_layout = QGridLayout()
        
        self.color_buttons = {}
        
        colors_to_expose = [
            ("bg_base", "Base Background"),
            ("bg_surface", "Surface Background"),
            ("text_main", "Main Text"),
            ("text_muted", "Muted Text"),
            ("primary", "Primary Accent"),
            ("secondary", "Secondary Accent"),
            ("danger", "Danger Accent")
        ]
        
        row, col = 0, 0
        for key, name in colors_to_expose:
            btn = QPushButton()
            btn.setObjectName("colorSwatchBtn")
            btn.setFixedSize(24, 24)
            btn.clicked.connect(lambda checked, k=key: self.pick_custom_color(k))
            self.color_buttons[key] = btn
            
            sub_layout = QHBoxLayout()
            sub_layout.addWidget(QLabel(f"{name}:"))
            sub_layout.addWidget(btn)
            sub_layout.addStretch()
            
            custom_layout.addLayout(sub_layout, row, col)
            col += 1
            if col > 1:
                col = 0
                row += 1

        self.grp_custom_colors.setLayout(custom_layout)
        layout.addWidget(self.grp_custom_colors)
        
        self.update_custom_swatches()
        self.grp_custom_colors.setVisible(self.cmb_theme.currentText() == "Custom")

        layout.addStretch()

        apply_btn = QPushButton("APPLY SETTINGS")
        apply_btn.setObjectName("startBtn")
        apply_btn.setToolTip("Save the current appearance settings and reload the user interface.")
        apply_btn.clicked.connect(self.apply_theme)
        layout.addWidget(apply_btn)

    def on_theme_changed(self, text):
        self.grp_custom_colors.setVisible(text == "Custom")

    def pick_custom_color(self, key):
        from PyQt6.QtGui import QColor
        current_hex = self.theme_manager.themes["Custom"][key]
        color = QColorDialog.getColor(QColor(current_hex), self, "Select Color")
        if color.isValid():
            hex_code = color.name().upper()
            self.theme_manager.update_custom_color(key, hex_code)
            self.update_custom_swatches()

    def update_custom_swatches(self):
        for key, btn in self.color_buttons.items():
            hex_color = self.theme_manager.themes["Custom"].get(key, "#000000")
            btn.setStyleSheet(f"background-color: {hex_color};")

    def apply_theme(self):
        theme_name = self.cmb_theme.currentText()
        font_family = self.cmb_font.currentFont().family()
        font_size = self.spn_font_size.value()
        
        self.theme_manager.set_active_theme(theme_name)
        self.theme_manager.set_font_family(font_family)
        self.theme_manager.set_font_size(font_size)
        
        palette = self.theme_manager.get_palette()
        self.setStyleSheet(generate_stylesheet(palette, font_family, font_size))
        self.log(f"[INFO] Appearance settings applied")

    def log(self, msg: str):
        import datetime
        self.log_view.append(msg)
        sb = self.log_view.verticalScrollBar()
        sb.setValue(sb.maximum())
        try:
            with open("session_log.txt", "a", encoding="utf-8") as f:
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                f.write(f"[{timestamp}] {msg}\n")
        except Exception:
            pass

    def _on_queue_item_changed(self, item):
        self.update_batch_label()

    # --- Batch Handlers ---
    def on_batch_dropped(self, paths):
        for p in paths:
            if p not in self.batch_paths:
                self.batch_paths.add(p)
                item = QListWidgetItem(Path(p).name)
                item.setData(Qt.ItemDataRole.UserRole, p)
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                item.setCheckState(Qt.CheckState.Checked)
                self.queue_list.addItem(item)
                
        self.update_batch_label()
        
        if self.chk_auto_process.isChecked() and (self.worker is None or not self.worker.isRunning()):
            self.start_batch_processing()

    def clear_batch_selection(self):
        self.batch_paths.clear()
        self.queue_list.clear()
        self.update_batch_label()

    def update_batch_label(self):
        checked_count = 0
        for i in range(self.queue_list.count()):
            if self.queue_list.item(i).checkState() == Qt.CheckState.Checked:
                checked_count += 1
                
        if checked_count > 0:
            self.batch_paths_label.setText(f"{checked_count} files queued for processing")
            self.start_btn.setEnabled(True)
        else:
            self.batch_paths_label.setText("0 files queued")
            self.start_btn.setEnabled(False)

    def browse_target_folder(self):
        dialog = QFileDialog(self)
        dialog.setFileMode(QFileDialog.FileMode.Directory)
        dialog.setOption(QFileDialog.Option.ShowDirsOnly, True)
        if dialog.exec():
            paths = dialog.selectedFiles()
            if paths:
                self.inp_target.setText(paths[0])


    def is_engine_running(self):
        if self.worker is not None and self.worker.isRunning():
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Engine Busy", "The compression engine is currently running. Please wait for it to finish or cancel the current job.")
            return True
        return False

    def open_advanced_editor(self):
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.information(self, "Advanced Edit", "Advanced editing features will be available in a future update.")

    def start_batch_processing(self):
        if self.is_engine_running(): return
        if not self.batch_paths:
            self.log("[ERROR] No files or directories selected for Batch Compression.")
            return

        options = {
            'recursive': self.chk_recursive.isChecked(),
            'overwrite': self.chk_overwrite.isChecked(),
            'skip_existing': getattr(self, 'chk_skip_existing', None) and self.chk_skip_existing.isChecked(),
            'use_target': self.chk_target.isChecked(),
            'target_dir': self.inp_target.text(),
            'use_suffix': self.chk_suffix.isChecked(),
            'suffix': self.inp_suffix.text(),
            
            'process_images': self.chk_process_img.isChecked(),
            'smart_auto_image': self.chk_smart_img.isChecked(),
            'image_preset': self.cmb_img_preset.currentText(),
            'img_quality': self.sld_img_quality.value(),
            'force_image_format': getattr(self, 'chk_force_img_format', None) and self.chk_force_img_format.isChecked(),
            'image_format': self.cmb_img_format.currentText(),
            
            'process_videos': self.chk_process_vid.isChecked(),
            'smart_auto_video': self.chk_smart_vid.isChecked(),
            'compile_sequences': self.chk_compile_seq.isChecked(),
            'video_container': self.cmb_vid_container.currentText(),
            'video_codec': self.cmb_vid_codec.currentText(),
            'remove_audio': self.chk_remove_audio.isChecked(),
            'save_metadata': self.chk_save_metadata.isChecked(),
            'video_preset': self.cmb_vid_preset.currentText(),
            'video_crf': str(self.sld_vid_crf.value()),
            'video_fps': self.inp_vid_fps.text().strip(),
            'video_res': self.inp_vid_res.text().strip(),
            
            'use_skip_pattern': getattr(self, 'chk_skip_pattern', None) and self.chk_skip_pattern.isChecked(),
            'skip_pattern_mode': self.cmb_skip_mode.currentText() if hasattr(self, 'cmb_skip_mode') else "Contains",
            'skip_pattern_case': getattr(self, 'chk_skip_case', None) and self.chk_skip_case.isChecked(),
            'skip_patterns': self.inp_skip_pattern.text() if hasattr(self, 'inp_skip_pattern') else "",
            'cpu_cores': self.spin_cpu_cores.value()
        }

        self.log("\n--- Starting Batch Job ---")
        self.cancel_btn.setEnabled(True)
        self.cancel_btn.setText("Cancel Operation")
        self.start_btn.setEnabled(False)
        self.start_btn.setText("Processing...")
        self.pause_btn.setEnabled(True)
        self.pause_btn.setText("Pause")
        self.progress_bar.setValue(0)

        # Snapshot the current queue (only checked items)
        self.current_batch_snapshot = []
        for i in range(self.queue_list.count()):
            item = self.queue_list.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                self.current_batch_snapshot.append(item.data(Qt.ItemDataRole.UserRole))

        self.worker = BatchManager(self.current_batch_snapshot, options)
        self.worker.progress_updated.connect(self.update_progress)
        self.worker.log_message.connect(self.log)
        self.worker.stats_updated.connect(self.update_rewards)
        self.worker.processing_finished.connect(self.on_processing_finished)
        self.worker.start()

    def toggle_pause(self):
        if self.worker and self.worker.isRunning():
            self.worker.toggle_pause()
            if self.worker.is_paused():
                self.pause_btn.setText("Resume")
                self.log("[INFO] Pausing batch processing... (Waiting for active threads to finish)")
            else:
                self.pause_btn.setText("Pause")
                self.log("[INFO] Resuming batch processing...")

    # --- Quick Handlers ---
    def q_table_dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
    def q_table_dragMoveEvent(self, event):
        event.acceptProposedAction()
    def q_table_dropEvent(self, event):
        urls = event.mimeData().urls()
        paths = [url.toLocalFile() for url in urls if url.isLocalFile()]
        self.gather_quick_files(paths)

    def on_quick_dropped(self, paths):
        if self.is_engine_running(): return
        self.gather_quick_files(paths)

    def add_quick_files(self):
        if self.is_engine_running(): return
        last_dir = self.settings.value("last_dir", "")
        dialog = QFileDialog(self, "Select Files", last_dir)
        dialog.setFileMode(QFileDialog.FileMode.ExistingFiles)
        if dialog.exec():
            self.settings.setValue("last_dir", dialog.directory().absolutePath())
            paths = dialog.selectedFiles()
            self.gather_quick_files(paths)

    def add_quick_dirs(self):
        if self.is_engine_running(): return
        last_dir = self.settings.value("last_dir", "")
        dialog = QFileDialog(self, "Select Directories", last_dir)
        dialog.setFileMode(QFileDialog.FileMode.Directory)
        dialog.setOption(QFileDialog.Option.DontUseNativeDialog, True)
        dialog.setOption(QFileDialog.Option.ShowDirsOnly, True)
        for view in dialog.findChildren((QListView, QTreeView)):
            if isinstance(view.model(), type(dialog.findChild(QListView).model())):
                view.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)

        if dialog.exec():
            self.settings.setValue("last_dir", dialog.directory().absolutePath())
            paths = dialog.selectedFiles()
            self.gather_quick_files(paths)

    def gather_quick_files(self, paths):
        recursive = self.chk_recursive.isChecked()
        added_any = False
        for p in paths:
            path_obj = Path(p)
            if path_obj.is_file():
                self.add_file_to_table(p)
                added_any = True
            elif path_obj.is_dir():
                if recursive:
                    for root, _, files in os.walk(p):
                        for file in files:
                            self.add_file_to_table(os.path.join(root, file))
                            added_any = True
                else:
                    for item in path_obj.iterdir():
                        if item.is_file():
                            self.add_file_to_table(str(item))
                            added_any = True
                            
        if added_any and not self.queue_table.selectedItems():
            self.queue_table.selectRow(0)

        if self.chk_auto_process.isChecked() and (self.worker is None or not self.worker.isRunning()):
            if self.queue_table.rowCount() > 0:
                self.start_quick_processing()

    def clear_quick_table(self):
        self.queue_table.setRowCount(0)
        self.quick_start_btn.setEnabled(False)

    def add_file_to_table(self, path):
        ftype = self.quick_converter.get_file_type(path)
        if ftype == "Unknown":
            self.log(f"[WARN] Unknown file type for quick convert: {path}")
            return

        row = self.queue_table.rowCount()
        self.queue_table.insertRow(row)

        name_item = QTableWidgetItem(Path(path).name)
        name_item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
        name_item.setData(Qt.ItemDataRole.UserRole, str(path))
        self.queue_table.setItem(row, 0, name_item)

        type_item = QTableWidgetItem(ftype)
        type_item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
        self.queue_table.setItem(row, 1, type_item)

        cmb_action = QComboBox()
        cmb_option = QComboBox()
        cmb_option.setEditable(True)  # Allow custom resize percentage

        if ftype == "Image":
            cmb_action.addItems(IMAGE_ACTIONS)
            cmb_option.addItems(IMAGE_OPTIONS)
        elif ftype == "Video":
            cmb_action.addItems(VIDEO_ACTIONS)
            cmb_option.addItems(VIDEO_OPTIONS)
            
        action_val, opt_val = SmartHeuristics.get_quick_suggestion(Path(path).suffix, ftype)
        cmb_action.setCurrentText(action_val)
        cmb_option.setCurrentText(opt_val)

        self.queue_table.setCellWidget(row, 2, cmb_action)
        self.queue_table.setCellWidget(row, 3, cmb_option)

        status_item = QTableWidgetItem("Pending")
        status_item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
        self.queue_table.setItem(row, 4, status_item)
        self.quick_start_btn.setEnabled(True)

    def sync_image_actions(self):
        target_act = None
        target_opt = None
        for row in range(self.queue_table.rowCount()):
            if self.queue_table.item(row, 1).text() == 'Image':
                if target_act is None:
                    target_act = self.queue_table.cellWidget(row, 2).currentIndex()
                    target_opt = self.queue_table.cellWidget(row, 3).currentIndex()
                else:
                    self.queue_table.cellWidget(row, 2).setCurrentIndex(target_act)
                    self.queue_table.cellWidget(row, 3).setCurrentIndex(target_opt)

    def sync_video_actions(self):
        target_act = None
        target_opt = None
        for row in range(self.queue_table.rowCount()):
            if self.queue_table.item(row, 1).text() == 'Video':
                if target_act is None:
                    target_act = self.queue_table.cellWidget(row, 2).currentIndex()
                    target_opt = self.queue_table.cellWidget(row, 3).currentIndex()
                else:
                    self.queue_table.cellWidget(row, 2).setCurrentIndex(target_act)
                    self.queue_table.cellWidget(row, 3).setCurrentIndex(target_opt)

    def start_quick_processing(self):
        if self.is_engine_running(): return
        if self.queue_table.rowCount() == 0:
            self.log("[ERROR] No files in table.")
            return

        self.log("\n--- Starting Quick Conversion ---")
        self.cancel_btn.setEnabled(True)
        self.cancel_btn.setText("Cancel Operation")
        self.quick_start_btn.setEnabled(False)
        self.quick_start_btn.setText("Processing...")
        self.progress_bar.setValue(0)

        # Prepare tasks (extracting data from UI components safely)
        tasks = []
        for row in range(self.queue_table.rowCount()):
            path = self.queue_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
            ftype = self.queue_table.item(row, 1).text()
            act_cmb = self.queue_table.cellWidget(row, 2)
            opt_cmb = self.queue_table.cellWidget(row, 3)
            tasks.append({
                'row': row,
                'path': path,
                'type': ftype,
                'action': act_cmb.currentText(),
                'option': opt_cmb.currentText()
            })

        self.worker = QuickWorker(tasks)
        self.worker.progress_updated.connect(self.update_progress)
        self.worker.log_message.connect(self.log)
        self.worker.stats_updated.connect(self.update_rewards)
        self.worker.item_status_updated.connect(self.update_quick_item_status)
        self.worker.processing_finished.connect(self.on_quick_processing_finished)
        self.worker.start()

    def update_quick_item_status(self, row: int, status: str):
        # Update the specific row's status item
        status_item = self.queue_table.item(row, 4)
        if status_item:
            status_item.setText(status)

    def on_quick_processing_finished(self, success_count: int, total: int):
        self.log(f"--- Quick Conversion Finished ({success_count}/{total} OK) ---\n")
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.setText("Cancel Operation")
        self.quick_start_btn.setText("Convert Files")
        self.quick_start_btn.setEnabled(True)
        
        if getattr(self.worker, '_is_cancelled', False) == False:
            # Remove completed rows
            for row in range(self.queue_table.rowCount() - 1, -1, -1):
                status_item = self.queue_table.item(row, 4)
                if status_item and status_item.text() in ["OK", "FAIL"]:
                    self.queue_table.removeRow(row)

            # Auto-restart if there are pending files
            has_pending = False
            for row in range(self.queue_table.rowCount()):
                status_item = self.queue_table.item(row, 4)
                if status_item and status_item.text() == "Ready":
                    has_pending = True
                    break
                    
            if self.chk_auto_process.isChecked() and has_pending:
                self.log("[INFO] Auto-queue triggered for remaining quick files...")
                self.start_quick_processing()

    def update_progress(self, current, total):
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)

    def save_settings(self):
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("windowState", self.saveState())
        
        # Batch tab settings
        self.settings.setValue("chk_recursive", self.chk_recursive.isChecked())
        self.settings.setValue("chk_overwrite", self.chk_overwrite.isChecked())
        self.settings.setValue("chk_skip_existing", self.chk_skip_existing.isChecked())
        self.settings.setValue("chk_auto_process", self.chk_auto_process.isChecked())
        self.settings.setValue("chk_target", self.chk_target.isChecked())
        self.settings.setValue("inp_target", self.inp_target.text())
        self.settings.setValue("chk_suffix", self.chk_suffix.isChecked())
        self.settings.setValue("inp_suffix", self.inp_suffix.text())
        
        self.settings.setValue("chk_process_img", self.chk_process_img.isChecked())
        self.settings.setValue("chk_smart_img", self.chk_smart_img.isChecked())
        if hasattr(self, 'chk_force_img_format'):
            self.settings.setValue("chk_force_img_format", self.chk_force_img_format.isChecked())
        self.settings.setValue("cmb_img_preset", self.cmb_img_preset.currentText())
        self.settings.setValue("sld_img_quality", self.sld_img_quality.value())
        self.settings.setValue("cmb_img_format", self.cmb_img_format.currentText())
        
        self.settings.setValue("chk_process_vid", self.chk_process_vid.isChecked())
        self.settings.setValue("chk_smart_vid", self.chk_smart_vid.isChecked())
        self.settings.setValue("chk_compile_seq", self.chk_compile_seq.isChecked())
        self.settings.setValue("cmb_vid_container", self.cmb_vid_container.currentText())
        self.settings.setValue("cmb_vid_codec", self.cmb_vid_codec.currentText())
        self.settings.setValue("chk_remove_audio", self.chk_remove_audio.isChecked())
        self.settings.setValue("chk_save_metadata", self.chk_save_metadata.isChecked())
        self.settings.setValue("cmb_vid_preset", self.cmb_vid_preset.currentText())
        self.settings.setValue("sld_vid_crf", self.sld_vid_crf.value())
        self.settings.setValue("inp_vid_fps", self.inp_vid_fps.text())
        self.settings.setValue("inp_vid_res", self.inp_vid_res.text())

        # Skip Pattern Settings
        if hasattr(self, 'chk_skip_pattern'):
            self.settings.setValue("chk_skip_pattern", self.chk_skip_pattern.isChecked())
            self.settings.setValue("cmb_skip_mode", self.cmb_skip_mode.currentText())
            self.settings.setValue("chk_skip_case", self.chk_skip_case.isChecked())
            self.settings.setValue("inp_skip_pattern", self.inp_skip_pattern.text())

        if hasattr(self, 'spin_cpu_cores'):
            self.settings.setValue("spin_cpu_cores", self.spin_cpu_cores.value())

        # Queue List state
        queue_paths = []
        queue_states = []
        for i in range(self.queue_list.count()):
            item = self.queue_list.item(i)
            queue_paths.append(str(item.data(Qt.ItemDataRole.UserRole)))
            queue_states.append(item.checkState() == Qt.CheckState.Checked)
        self.settings.setValue("queue_paths", queue_paths)
        self.settings.setValue("queue_states", queue_states)

    def load_settings(self):
        if self.settings.value("geometry"):
            self.restoreGeometry(self.settings.value("geometry"))
        if self.settings.value("windowState"):
            self.restoreState(self.settings.value("windowState"))
            
        def str_to_bool(val, default):
            if val is None: return default
            return str(val).lower() == 'true'

        self.chk_recursive.setChecked(str_to_bool(self.settings.value("chk_recursive"), False))
        self.chk_overwrite.setChecked(str_to_bool(self.settings.value("chk_overwrite"), False))
        self.chk_skip_existing.setChecked(str_to_bool(self.settings.value("chk_skip_existing"), False))
        self.chk_auto_process.setChecked(str_to_bool(self.settings.value("chk_auto_process"), False))
        self.chk_target.setChecked(str_to_bool(self.settings.value("chk_target"), False))
        self.inp_target.setText(str(self.settings.value("inp_target", "")))
        self.chk_suffix.setChecked(str_to_bool(self.settings.value("chk_suffix"), True))
        self.inp_suffix.setText(str(self.settings.value("inp_suffix", "_compressed")))
        
        self.chk_process_img.setChecked(str_to_bool(self.settings.value("chk_process_img"), True))
        self.chk_smart_img.setChecked(str_to_bool(self.settings.value("chk_smart_img"), False))
        if hasattr(self, 'chk_force_img_format'):
            self.chk_force_img_format.setChecked(str_to_bool(self.settings.value("chk_force_img_format"), False))
        
        saved_img_preset = str(self.settings.value("cmb_img_preset", "Lossless"))
        if saved_img_preset:
            self.cmb_img_preset.setCurrentText(saved_img_preset)
        
        try:
            val = int(self.settings.value("sld_img_quality", 85))
            self.sld_img_quality.setValue(val)
        except ValueError:
            pass
            
        saved_img_fmt = str(self.settings.value("cmb_img_format", "Keep Original Extension"))
        if saved_img_fmt:
            self.cmb_img_format.setCurrentText(saved_img_fmt)

        self.chk_process_vid.setChecked(str_to_bool(self.settings.value("chk_process_vid"), True))
        self.chk_smart_vid.setChecked(str_to_bool(self.settings.value("chk_smart_vid"), False))
        self.chk_compile_seq.setChecked(str_to_bool(self.settings.value("chk_compile_seq"), False))
        
        saved_vid_cont = str(self.settings.value("cmb_vid_container", ".mkv"))
        if saved_vid_cont:
            self.cmb_vid_container.setCurrentText(saved_vid_cont)
            
        saved_vid_codec = str(self.settings.value("cmb_vid_codec", "AV1"))
        if saved_vid_codec:
            self.cmb_vid_codec.setCurrentText(saved_vid_codec)
            
        self.chk_remove_audio.setChecked(str_to_bool(self.settings.value("chk_remove_audio"), False))
        self.chk_save_metadata.setChecked(str_to_bool(self.settings.value("chk_save_metadata"), True))
        
        saved_vid_preset = str(self.settings.value("cmb_vid_preset", "Main AV1"))
        if saved_vid_preset:
            self.cmb_vid_preset.setCurrentText(saved_vid_preset)
            
        try:
            val = int(self.settings.value("sld_vid_crf", 28))
            self.sld_vid_crf.setValue(val)
        except ValueError:
            pass
            
        self.inp_vid_fps.setText(str(self.settings.value("inp_vid_fps", "")))
        self.inp_vid_res.setText(str(self.settings.value("inp_vid_res", "")))

        if hasattr(self, 'chk_skip_pattern'):
            self.chk_skip_pattern.setChecked(str_to_bool(self.settings.value("chk_skip_pattern"), False))
            self.cmb_skip_mode.setCurrentText(str(self.settings.value("cmb_skip_mode", "Contains")))
            self.chk_skip_case.setChecked(str_to_bool(self.settings.value("chk_skip_case"), False))
            self.inp_skip_pattern.setText(str(self.settings.value("inp_skip_pattern", "")))

        if hasattr(self, 'spin_cpu_cores'):
            try:
                self.spin_cpu_cores.setValue(int(self.settings.value("spin_cpu_cores", os.cpu_count() or 4)))
            except ValueError:
                pass

        # Load Queue
        q_paths = self.settings.value("queue_paths", [])
        q_states = self.settings.value("queue_states", [])
        
        if not isinstance(q_paths, list):
            q_paths = [q_paths] if q_paths else []
        if not isinstance(q_states, list):
            # Because bool is also int, checking for not list is safer
            q_states = [q_states] if q_states is not None else []

        if q_paths and q_states and len(q_paths) == len(q_states):
            self.queue_list.clear()
            self.batch_paths.clear()
            for p, state in zip(q_paths, q_states):
                path_obj = Path(p)
                self.batch_paths.add(p)
                item = QListWidgetItem(path_obj.name)
                item.setData(Qt.ItemDataRole.UserRole, p)
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                item.setCheckState(Qt.CheckState.Checked if str_to_bool(state, True) else Qt.CheckState.Unchecked)
                self.queue_list.addItem(item)
            self.update_batch_label()

    def eventFilter(self, source, event):
        from PyQt6.QtCore import QEvent
        if source == self.queue_list and event.type() == QEvent.Type.KeyPress:
            if event.key() == Qt.Key.Key_Delete:
                selected_items = self.queue_list.selectedItems()
                for item in selected_items:
                    path = item.data(Qt.ItemDataRole.UserRole)
                    if path in self.batch_paths:
                        self.batch_paths.remove(path)
                    self.queue_list.takeItem(self.queue_list.row(item))
                self.update_batch_label()
                return True
        return super().eventFilter(source, event)

    def force_quit(self):
        if self.worker and self.worker.isRunning():
            self.worker.cancel()
            self.worker.wait(1000)
        from core.utils import cancel_all_subprocesses
        cancel_all_subprocesses()
        self.save_settings()
        from PyQt6.QtWidgets import QApplication
        QApplication.instance().quit()

    def closeEvent(self, event):
        is_working = (self.worker and self.worker.isRunning())
        if is_working:
            event.ignore()
            self.hide()
            self.tray_icon.showMessage(
                "Compressor Running",
                "Minimized to system tray because files are still processing.",
                QSystemTrayIcon.MessageIcon.Information,
                2000
            )
        else:
            event.accept()
            self.force_quit()

    def cancel_processing(self):
        if self.worker and self.worker.isRunning():
            self.worker.cancel()
            self.log("[INFO] Cancellation requested...")
            self.cancel_btn.setText("Cancelling...")
            self.cancel_btn.setEnabled(False)

    def on_processing_finished(self):
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.setText("Cancel Operation")
        self.start_btn.setText("Compress Files")
        self.log("--- Batch Job Finished ---\n")
        
        # Remove processed files from queue if not cancelled
        if getattr(self.worker, '_is_cancelled', False) == False:
            for p in getattr(self, 'current_batch_snapshot', []):
                self.batch_paths.discard(p)
            self.update_batch_label()
            
            # Auto-restart if new files were added to the queue
            if self.chk_auto_process.isChecked() and len(self.batch_paths) > 0:
                self.log("[INFO] Auto-queue triggered for remaining files...")
                self.start_batch_processing()
        else:
            self.start_btn.setEnabled(len(self.batch_paths) > 0)

        self.worker = None

    def update_rewards(self, orig_bytes, comp_bytes):
        self.total_original_bytes += orig_bytes
        self.total_compressed_bytes += comp_bytes
        
        def format_size(size_in_bytes):
            if size_in_bytes < 1024 * 1024:
                return f"{size_in_bytes / 1024:.1f} KB"
            elif size_in_bytes < 1024 * 1024 * 1024:
                return f"{size_in_bytes / (1024 * 1024):.1f} MB"
            else:
                return f"{size_in_bytes / (1024 * 1024 * 1024):.2f} GB"
                
        self.lbl_orig_size.setText(f"Original: {format_size(self.total_original_bytes)}")
        self.lbl_new_size.setText(f"New: {format_size(self.total_compressed_bytes)}")
        
        saved_bytes = self.total_original_bytes - self.total_compressed_bytes
        if self.total_original_bytes > 0:
            saved_pct = (saved_bytes / self.total_original_bytes) * 100
        else:
            saved_pct = 0
            
        if saved_bytes > 0:
            self.lbl_saved_size.setText(f"🏆 Total Saved: {format_size(saved_bytes)} ({saved_pct:.1f}%)")
        else:
            self.lbl_saved_size.setText(f"🏆 Total Saved: 0 MB (0%)")
