import sys
import os
from pathlib import Path
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFrame, QCheckBox, QComboBox, QLineEdit, 
    QProgressBar, QTextEdit, QGroupBox, QFileDialog, QTabWidget,
    QAbstractItemView, QListView, QTreeView, QTableWidget, QTableWidgetItem,
    QHeaderView, QColorDialog
)
from PyQt6.QtCore import Qt, QSettings
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
    "Palette 512 colors", "Palette 2048 colors", "DDS -> PNG (texconv / Pillow)", 
    "PNG -> DDS (texconv BC7_UNORM)", "PIC -> TGA (8x Upscale Nearest)"
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

class DropZone(QFrame):
    def __init__(self, on_drop_callback, text="Drag & Drop Files or Folders Here"):
        super().__init__()
        self.setObjectName("dropZone")
        self.setAcceptDrops(True)
        self.on_drop_callback = on_drop_callback
        
        layout = QVBoxLayout()
        self.label = QLabel(text)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setStyleSheet("color: #BB86FC; font-size: 16px; font-weight: bold;")
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
            self.setStyleSheet("background-color: #2C2C2C; border: 2px dashed #03DAC6;")

    def dragLeaveEvent(self, event):
        self.setStyleSheet("") 

    def dropEvent(self, event):
        self.setStyleSheet("")
        urls = event.mimeData().urls()
        paths = [url.toLocalFile() for url in urls if url.isLocalFile()]
        if paths:
            self.on_drop_callback(paths)

    def browse_files(self):
        dialog = QFileDialog(self)
        dialog.setFileMode(QFileDialog.FileMode.ExistingFiles)
        if dialog.exec():
            paths = dialog.selectedFiles()
            if paths:
                self.on_drop_callback(paths)

    def browse_dirs(self):
        dialog = QFileDialog(self)
        dialog.setFileMode(QFileDialog.FileMode.Directory)
        dialog.setOption(QFileDialog.Option.DontUseNativeDialog, True)
        dialog.setOption(QFileDialog.Option.ShowDirsOnly, True)
        for view in dialog.findChildren((QListView, QTreeView)):
            if isinstance(view.model(), type(dialog.findChild(QListView).model())):
                view.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)

        if dialog.exec():
            paths = dialog.selectedFiles()
            if paths:
                self.on_drop_callback(paths)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SMART VAC MEDIA COMPRESSOR")
        self.setMinimumSize(950, 750)

        self.theme_manager = ThemeManager()
        self.setStyleSheet(generate_stylesheet(self.theme_manager.get_palette()))

        self.batch_paths = set()
        self.quick_files = [] # list of dicts: {'path', 'type', 'action_cmb', 'option_cmb', 'status_item'}
        self.worker = None
        self.quick_converter = QuickConverter()

        self.settings = QSettings("SmartVac", "MediaCompressor")

        self._init_ui()
        self.load_settings()

    def _init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(15, 15, 15, 15)

        header_label = QLabel("SMART VAC MEDIA COMPRESSOR")
        header_label.setObjectName("titleLabel")
        header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(header_label)

        self.tabs = QTabWidget()
        self.tab_batch = QWidget()
        self.tab_quick = QWidget()
        self.tab_appearance = QWidget()
        
        self.tabs.addTab(self.tab_batch, "Batch Compressor")
        self.tabs.addTab(self.tab_quick, "Quick Converter")
        self.tabs.addTab(self.tab_appearance, "Appearance")
        
        self._setup_batch_tab()
        self._setup_quick_tab()
        self._setup_appearance_tab()

        main_layout.addWidget(self.tabs)

        progress_layout = QHBoxLayout()
        self.cancel_btn = QPushButton("CANCEL")
        self.cancel_btn.setObjectName("cancelBtn")
        self.cancel_btn.clicked.connect(self.cancel_processing)
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.setMinimumWidth(100)
        progress_layout.addWidget(self.cancel_btn)

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        progress_layout.addWidget(self.progress_bar)
        
        main_layout.addLayout(progress_layout)

        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setMaximumHeight(150)
        main_layout.addWidget(self.log_view)

    def _setup_batch_tab(self):
        layout = QVBoxLayout(self.tab_batch)
        self.batch_drop_zone = DropZone(self.on_batch_dropped, "Drag & Drop Files or Folders Here")
        layout.addWidget(self.batch_drop_zone)

        paths_layout = QHBoxLayout()
        self.batch_paths_label = QLabel("No files selected")
        self.batch_paths_label.setObjectName("subtitleLabel")
        clear_btn = QPushButton("Clear Selection")
        clear_btn.setObjectName("browseBtn")
        clear_btn.clicked.connect(self.clear_batch_selection)
        paths_layout.addWidget(self.batch_paths_label)
        paths_layout.addStretch()
        paths_layout.addWidget(clear_btn)
        layout.addLayout(paths_layout)

        # General Options goes on top, spanning full width
        gen_group = QGroupBox("General Options")
        gen_layout = QVBoxLayout()
        
        # Row 1: Overwrite and Recursive
        chk_layout = QHBoxLayout()
        self.chk_recursive = QCheckBox("Recursive directory scan")
        self.chk_recursive.setChecked(True)
        self.chk_overwrite = QCheckBox("Replace original (Overwrite)")
        chk_layout.addWidget(self.chk_recursive)
        chk_layout.addWidget(self.chk_overwrite)
        chk_layout.addStretch()
        gen_layout.addLayout(chk_layout)

        # Row 2: Target folder and Suffix
        target_suffix_layout = QHBoxLayout()
        
        self.chk_target = QCheckBox("Output to Target Folder:")
        self.inp_target = QLineEdit()
        self.inp_target.setPlaceholderText("Original directory (default)")
        self.inp_target.setEnabled(False)
        self.btn_target = QPushButton("Browse")
        self.btn_target.setEnabled(False)
        self.chk_target.toggled.connect(self.inp_target.setEnabled)
        self.chk_target.toggled.connect(self.btn_target.setEnabled)
        self.btn_target.clicked.connect(self.browse_target_folder)
        
        target_suffix_layout.addWidget(self.chk_target)
        target_suffix_layout.addWidget(self.inp_target)
        target_suffix_layout.addWidget(self.btn_target)

        target_suffix_layout.addSpacing(20)

        self.chk_suffix = QCheckBox("Add suffix:")
        self.chk_suffix.setChecked(True)
        self.inp_suffix = QLineEdit("_compressed")
        self.inp_suffix.setPlaceholderText("e.g. _compressed")
        self.chk_suffix.toggled.connect(self.inp_suffix.setEnabled)
        
        target_suffix_layout.addWidget(self.chk_suffix)
        target_suffix_layout.addWidget(self.inp_suffix)
        
        gen_layout.addLayout(target_suffix_layout)
        gen_group.setLayout(gen_layout)
        layout.addWidget(gen_group)

        # Media Processing Split
        media_options_layout = QHBoxLayout()
        media_options_layout.setSpacing(15)

        img_group = QGroupBox("Image Processing")
        img_layout = QVBoxLayout()
        self.chk_process_img = QCheckBox("Process Images")
        self.chk_process_img.setChecked(True)
        self.cmb_img_preset = QComboBox()
        self.cmb_img_preset.addItems(list(IMG_HINTS.keys()))
        self.img_hint_label = QLabel(IMG_HINTS["Lossless"])
        self.img_hint_label.setObjectName("hintLabel")
        self.img_hint_label.setWordWrap(True)
        def on_img_preset_changed(text):
            self.img_hint_label.setText(IMG_HINTS.get(text, ""))
                
        self.cmb_img_preset.currentTextChanged.connect(on_img_preset_changed)
        
        self.chk_smart_img = QCheckBox("Smart Auto (Best Balance)")
        self.chk_smart_img.setChecked(False)
        self.chk_smart_img.setToolTip("Automatically selects the ideal compression method and output format based on the file's extension.")
        
        def on_smart_img_toggled(checked):
            self.cmb_img_preset.setEnabled(not checked)
            self.chk_force_img_format.setEnabled(not checked)
            if checked:
                self.cmb_img_format.setEnabled(False)
            else:
                self.cmb_img_format.setEnabled(self.chk_force_img_format.isChecked())
                
        self.chk_smart_img.toggled.connect(on_smart_img_toggled)
        
        format_layout = QHBoxLayout()
        self.chk_force_img_format = QCheckBox("Force Output Format:")
        self.chk_force_img_format.setChecked(False)
        self.chk_force_img_format.toggled.connect(
            lambda checked: self.cmb_img_format.setEnabled(checked and not self.chk_smart_img.isChecked())
        )
        
        self.cmb_img_format = QComboBox()
        self.cmb_img_format.addItems([
            "Keep Original Extension", "Convert to WebP", 
            "Convert to AVIF", "Convert to JPG", "Convert to PNG"
        ])
        self.cmb_img_format.setEnabled(False)
        
        format_layout.addWidget(self.chk_force_img_format)
        format_layout.addWidget(self.cmb_img_format)
        
        img_layout.addWidget(self.chk_process_img)
        img_layout.addWidget(self.chk_smart_img)
        img_layout.addWidget(QLabel("Preset:"))
        img_layout.addWidget(self.cmb_img_preset)
        img_layout.addWidget(self.img_hint_label)
        img_layout.addSpacing(10)
        img_layout.addLayout(format_layout)
        img_layout.addStretch()
        img_group.setLayout(img_layout)
        media_options_layout.addWidget(img_group)

        vid_group = QGroupBox("Video Processing")
        vid_layout = QVBoxLayout()
        self.chk_process_vid = QCheckBox("Process Videos")
        self.chk_process_vid.setChecked(True)
        self.cmb_vid_preset = QComboBox()
        self.cmb_vid_preset.addItems(list(VID_HINTS.keys()))
        self.vid_hint_label = QLabel(VID_HINTS["Main AV1"])
        self.vid_hint_label.setObjectName("hintLabel")
        self.vid_hint_label.setWordWrap(True)
        def on_vid_preset_changed(text):
            self.vid_hint_label.setText(VID_HINTS.get(text, ""))
                
        self.cmb_vid_preset.currentTextChanged.connect(on_vid_preset_changed)
        
        self.chk_smart_vid = QCheckBox("Smart Auto (Best Balance)")
        self.chk_smart_vid.setChecked(False)
        self.chk_smart_vid.setToolTip("Automatically adjusts AV1 presets, framerate, and resolution limits based on the container type.")
        
        def on_smart_vid_toggled(checked):
            self.cmb_vid_preset.setEnabled(not checked)
            self.inp_vid_crf.setEnabled(not checked)
            self.inp_vid_fps.setEnabled(not checked)
            self.inp_vid_res.setEnabled(not checked)
            
        self.chk_smart_vid.toggled.connect(on_smart_vid_toggled)
        
        vid_layout.addWidget(self.chk_process_vid)
        vid_layout.addWidget(self.chk_smart_vid)
        vid_layout.addWidget(QLabel("Preset:"))
        vid_layout.addWidget(self.cmb_vid_preset)
        vid_layout.addWidget(self.vid_hint_label)
        vid_layout.addSpacing(10)
        
        self.chk_compile_seq = QCheckBox("Compile Image Sequences to Transparent Video")
        vid_layout.addWidget(self.chk_compile_seq)
        
        vid_overrides_layout = QHBoxLayout()
        vid_overrides_layout.addWidget(QLabel("CRF:"))
        self.inp_vid_crf = QLineEdit()
        self.inp_vid_crf.setPlaceholderText("Default")
        vid_overrides_layout.addWidget(self.inp_vid_crf)
        
        vid_overrides_layout.addWidget(QLabel("FPS:"))
        self.inp_vid_fps = QLineEdit()
        self.inp_vid_fps.setPlaceholderText("Orig")
        vid_overrides_layout.addWidget(self.inp_vid_fps)
        
        vid_overrides_layout.addWidget(QLabel("Res:"))
        self.inp_vid_res = QLineEdit()
        self.inp_vid_res.setPlaceholderText("1080p")
        vid_overrides_layout.addWidget(self.inp_vid_res)
        
        vid_layout.addLayout(vid_overrides_layout)
        vid_layout.addStretch() 
        vid_group.setLayout(vid_layout)
        media_options_layout.addWidget(vid_group)

        layout.addLayout(media_options_layout)

        controls_layout = QHBoxLayout()
        self.start_btn = QPushButton("START BATCH COMPRESSION")
        self.start_btn.setObjectName("startBtn")
        self.start_btn.setEnabled(False)  # Disabled until files are dropped
        self.start_btn.clicked.connect(self.start_batch_processing)
        
        controls_layout.addWidget(self.start_btn)
        layout.addLayout(controls_layout)

    def _setup_quick_tab(self):
        layout = QVBoxLayout(self.tab_quick)
        
        info_label = QLabel("Quick Converter automatically detects file types and offers individual context actions.")
        info_label.setObjectName("subtitleLabel")
        layout.addWidget(info_label)

        # Actions Row
        top_bar = QHBoxLayout()
        add_files_btn = QPushButton("Add Files")
        add_files_btn.clicked.connect(self.add_quick_files)
        add_dirs_btn = QPushButton("Add Folders")
        add_dirs_btn.clicked.connect(self.add_quick_dirs)
        clear_btn = QPushButton("Clear Table")
        clear_btn.clicked.connect(self.clear_quick_table)
        
        self.chk_quick_recursive = QCheckBox("Recursive scan")
        self.chk_quick_recursive.setChecked(True)

        top_bar.addWidget(add_files_btn)
        top_bar.addWidget(add_dirs_btn)
        top_bar.addWidget(clear_btn)
        top_bar.addWidget(self.chk_quick_recursive)
        top_bar.addStretch()
        
        apply_img_btn = QPushButton("Sync Image Actions")
        apply_img_btn.setToolTip("Applies the first image's action to all other images")
        apply_img_btn.clicked.connect(self.sync_image_actions)
        
        apply_vid_btn = QPushButton("Sync Video Actions")
        apply_vid_btn.setToolTip("Applies the first video's action to all other videos")
        apply_vid_btn.clicked.connect(self.sync_video_actions)
        
        top_bar.addWidget(apply_img_btn)
        top_bar.addWidget(apply_vid_btn)
        layout.addLayout(top_bar)

        # Table
        self.q_table = QTableWidget(0, 5)
        self.q_table.setHorizontalHeaderLabels(["Filename", "Type", "Action", "Options", "Status"])
        self.q_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.q_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.q_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.q_table.setAcceptDrops(True)
        # Hack to allow drops directly on table by overriding its drop events dynamically or just relying on parent
        layout.addWidget(self.q_table)

        # Controls
        controls_layout = QHBoxLayout()
        self.quick_start_btn = QPushButton("START QUICK CONVERSION")
        self.quick_start_btn.setObjectName("startBtn")
        self.quick_start_btn.setEnabled(False)
        self.quick_start_btn.clicked.connect(self.start_quick_processing)
        controls_layout.addWidget(self.quick_start_btn)
        layout.addLayout(controls_layout)

        # Allow main window drop events to catch it if they land on the table
        self.q_table.dragEnterEvent = self.q_table_dragEnterEvent
        self.q_table.dragMoveEvent = self.q_table_dragMoveEvent
        self.q_table.dropEvent = self.q_table_dropEvent

    def _setup_appearance_tab(self):
        layout = QVBoxLayout(self.tab_appearance)
        
        info_label = QLabel("Customize the look and feel of the application.")
        info_label.setObjectName("subtitleLabel")
        layout.addWidget(info_label)

        # Theme selection
        theme_layout = QHBoxLayout()
        theme_layout.addWidget(QLabel("Preset Theme:"))
        self.cmb_theme = QComboBox()
        self.cmb_theme.addItems(list(self.theme_manager.themes.keys()))
        self.cmb_theme.setCurrentText(self.theme_manager.get_active_theme_name())
        self.cmb_theme.currentTextChanged.connect(self.on_theme_changed)
        theme_layout.addWidget(self.cmb_theme)
        theme_layout.addStretch()
        layout.addLayout(theme_layout)

        # Custom colors group
        self.grp_custom_colors = QGroupBox("Custom Palette Colors")
        custom_layout = QHBoxLayout()
        
        self.btn_primary_color = QPushButton()
        self.btn_primary_color.setObjectName("colorSwatchBtn")
        self.btn_primary_color.setFixedSize(30, 30)
        self.btn_primary_color.clicked.connect(lambda: self.pick_custom_color('primary'))
        
        self.btn_secondary_color = QPushButton()
        self.btn_secondary_color.setObjectName("colorSwatchBtn")
        self.btn_secondary_color.setFixedSize(30, 30)
        self.btn_secondary_color.clicked.connect(lambda: self.pick_custom_color('secondary'))

        custom_layout.addWidget(QLabel("Primary Accent:"))
        custom_layout.addWidget(self.btn_primary_color)
        custom_layout.addSpacing(20)
        custom_layout.addWidget(QLabel("Secondary Accent:"))
        custom_layout.addWidget(self.btn_secondary_color)
        custom_layout.addStretch()
        
        self.grp_custom_colors.setLayout(custom_layout)
        layout.addWidget(self.grp_custom_colors)
        
        self.update_custom_swatches()
        self.grp_custom_colors.setVisible(self.cmb_theme.currentText() == "Custom")

        layout.addStretch()

        apply_btn = QPushButton("APPLY THEME")
        apply_btn.setObjectName("startBtn")
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
        pri = self.theme_manager.themes["Custom"]["primary"]
        sec = self.theme_manager.themes["Custom"]["secondary"]
        self.btn_primary_color.setStyleSheet(f"background-color: {pri};")
        self.btn_secondary_color.setStyleSheet(f"background-color: {sec};")

    def apply_theme(self):
        theme_name = self.cmb_theme.currentText()
        self.theme_manager.set_active_theme(theme_name)
        palette = self.theme_manager.get_palette()
        self.setStyleSheet(generate_stylesheet(palette))
        self.log(f"[INFO] Theme changed to {theme_name}")

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

    # --- Batch Handlers ---
    def on_batch_dropped(self, paths):
        self.batch_paths.update(paths)
        self.update_batch_label()

    def clear_batch_selection(self):
        self.batch_paths.clear()
        self.update_batch_label()

    def update_batch_label(self):
        count = len(self.batch_paths)
        if count > 0:
            self.batch_paths_label.setText(f"Selected: {count} items ready for processing")
            self.start_btn.setEnabled(True)
        else:
            self.batch_paths_label.setText("No files selected. Drag & drop files to begin.")
            self.start_btn.setEnabled(False)

    def browse_target_folder(self):
        dialog = QFileDialog(self)
        dialog.setFileMode(QFileDialog.FileMode.Directory)
        dialog.setOption(QFileDialog.Option.ShowDirsOnly, True)
        if dialog.exec():
            paths = dialog.selectedFiles()
            if paths:
                self.inp_target.setText(paths[0])

    def start_batch_processing(self):
        if not self.batch_paths:
            self.log("[ERROR] No files or directories selected for Batch Compression.")
            return

        options = {
            'recursive': self.chk_recursive.isChecked(),
            'overwrite': self.chk_overwrite.isChecked(),
            'use_target': self.chk_target.isChecked(),
            'target_dir': self.inp_target.text(),
            'use_suffix': self.chk_suffix.isChecked(),
            'suffix': self.inp_suffix.text(),
            
            'process_images': self.chk_process_img.isChecked(),
            'smart_auto_image': self.chk_smart_img.isChecked(),
            'image_preset': self.cmb_img_preset.currentText(),
            'force_image_format': getattr(self, 'chk_force_img_format', None) and self.chk_force_img_format.isChecked(),
            'image_format': self.cmb_img_format.currentText(),
            
            'process_videos': self.chk_process_vid.isChecked(),
            'smart_auto_video': self.chk_smart_vid.isChecked(),
            'compile_sequences': self.chk_compile_seq.isChecked(),
            'video_preset': self.cmb_vid_preset.currentText(),
            'video_crf': self.inp_vid_crf.text().strip(),
            'video_fps': self.inp_vid_fps.text().strip(),
            'video_res': self.inp_vid_res.text().strip()
        }

        self.log("\n--- Starting Batch Job ---")
        self.tabs.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        self.progress_bar.setValue(0)

        self.worker = BatchManager(list(self.batch_paths), options)
        self.worker.progress_updated.connect(self.update_progress)
        self.worker.log_message.connect(self.log)
        self.worker.processing_finished.connect(self.on_processing_finished)
        self.worker.start()

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

    def add_quick_files(self):
        dialog = QFileDialog(self)
        dialog.setFileMode(QFileDialog.FileMode.ExistingFiles)
        if dialog.exec():
            paths = dialog.selectedFiles()
            self.gather_quick_files(paths)

    def add_quick_dirs(self):
        dialog = QFileDialog(self)
        dialog.setFileMode(QFileDialog.FileMode.Directory)
        dialog.setOption(QFileDialog.Option.DontUseNativeDialog, True)
        dialog.setOption(QFileDialog.Option.ShowDirsOnly, True)
        for view in dialog.findChildren((QListView, QTreeView)):
            if isinstance(view.model(), type(dialog.findChild(QListView).model())):
                view.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)

        if dialog.exec():
            paths = dialog.selectedFiles()
            self.gather_quick_files(paths)

    def gather_quick_files(self, paths):
        recursive = self.chk_quick_recursive.isChecked()
        for p in paths:
            path_obj = Path(p)
            if path_obj.is_file():
                self.add_file_to_table(p)
            elif path_obj.is_dir():
                if recursive:
                    for root, _, files in os.walk(p):
                        for file in files:
                            self.add_file_to_table(os.path.join(root, file))
                else:
                    for item in path_obj.iterdir():
                        if item.is_file():
                            self.add_file_to_table(str(item))

    def clear_quick_table(self):
        self.q_table.setRowCount(0)
        self.quick_files.clear()
        self.quick_start_btn.setEnabled(False)

    def add_file_to_table(self, path):
        ftype = self.quick_converter.get_file_type(path)
        if ftype == "Unknown":
            self.log(f"[WARN] Unknown file type for quick convert: {path}")
            return

        row = self.q_table.rowCount()
        self.q_table.insertRow(row)

        name_item = QTableWidgetItem(Path(path).name)
        name_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
        self.q_table.setItem(row, 0, name_item)

        type_item = QTableWidgetItem(ftype)
        type_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
        self.q_table.setItem(row, 1, type_item)

        cmb_action = QComboBox()
        cmb_option = QComboBox()

        if ftype == "Image":
            cmb_action.addItems(IMAGE_ACTIONS)
            cmb_option.addItems(IMAGE_OPTIONS)
        elif ftype == "Video":
            cmb_action.addItems(VIDEO_ACTIONS)
            cmb_option.addItems(VIDEO_OPTIONS)
            
        action_val, opt_val = SmartHeuristics.get_quick_suggestion(Path(path).suffix, ftype)
        cmb_action.setCurrentText(action_val)
        cmb_option.setCurrentText(opt_val)

        self.q_table.setCellWidget(row, 2, cmb_action)
        self.q_table.setCellWidget(row, 3, cmb_option)

        status_item = QTableWidgetItem("Pending")
        status_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
        self.q_table.setItem(row, 4, status_item)
        self.quick_files.append({
            'row': row,
            'path': path,
            'type': ftype,
            'action_cmb': cmb_action,
            'option_cmb': cmb_option,
            'status_item': status_item
        })
        self.quick_start_btn.setEnabled(True)

    def sync_image_actions(self):
        first_img = next((f for f in self.quick_files if f['type'] == 'Image'), None)
        if first_img:
            target_act = first_img['action_cmb'].currentIndex()
            target_opt = first_img['option_cmb'].currentIndex()
            for f in self.quick_files:
                if f['type'] == 'Image':
                    f['action_cmb'].setCurrentIndex(target_act)
                    f['option_cmb'].setCurrentIndex(target_opt)

    def sync_video_actions(self):
        first_vid = next((f for f in self.quick_files if f['type'] == 'Video'), None)
        if first_vid:
            target_act = first_vid['action_cmb'].currentIndex()
            target_opt = first_vid['option_cmb'].currentIndex()
            for f in self.quick_files:
                if f['type'] == 'Video':
                    f['action_cmb'].setCurrentIndex(target_act)
                    f['option_cmb'].setCurrentIndex(target_opt)

    def start_quick_processing(self):
        if not self.quick_files:
            self.log("[ERROR] No files in table.")
            return

        self.log("\n--- Starting Quick Conversion ---")
        self.tabs.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        self.progress_bar.setValue(0)

        # Prepare tasks (extracting data from UI components safely)
        tasks = []
        for f in self.quick_files:
            tasks.append({
                'row': f['row'],
                'path': f['path'],
                'type': f['type'],
                'action': f['action_cmb'].currentText(),
                'option': f['option_cmb'].currentText()
            })

        self.worker = QuickWorker(tasks)
        self.worker.progress_updated.connect(self.update_progress)
        self.worker.log_message.connect(self.log)
        self.worker.item_status_updated.connect(self.update_quick_item_status)
        self.worker.processing_finished.connect(self.on_quick_processing_finished)
        self.worker.start()

    def update_quick_item_status(self, row: int, status: str):
        # Update the specific row's status item
        for f in self.quick_files:
            if f['row'] == row:
                f['status_item'].setText(status)
                break

    def on_quick_processing_finished(self, success_count: int, total: int):
        self.log(f"--- Quick Conversion Finished ({success_count}/{total} OK) ---\n")
        self.tabs.setEnabled(True)
        self.cancel_btn.setEnabled(False)

    def update_progress(self, current, total):
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)

    def save_settings(self):
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("windowState", self.saveState())
        
        # Batch tab settings
        self.settings.setValue("chk_recursive", self.chk_recursive.isChecked())
        self.settings.setValue("chk_overwrite", self.chk_overwrite.isChecked())
        self.settings.setValue("chk_target", self.chk_target.isChecked())
        self.settings.setValue("inp_target", self.inp_target.text())
        self.settings.setValue("chk_suffix", self.chk_suffix.isChecked())
        self.settings.setValue("inp_suffix", self.inp_suffix.text())
        
        self.settings.setValue("chk_process_img", self.chk_process_img.isChecked())
        self.settings.setValue("cmb_img_preset", self.cmb_img_preset.currentText())
        self.settings.setValue("cmb_img_format", self.cmb_img_format.currentText())
        
        self.settings.setValue("chk_process_vid", self.chk_process_vid.isChecked())
        self.settings.setValue("chk_compile_seq", self.chk_compile_seq.isChecked())
        self.settings.setValue("cmb_vid_preset", self.cmb_vid_preset.currentText())
        self.settings.setValue("inp_vid_crf", self.inp_vid_crf.text())
        self.settings.setValue("inp_vid_fps", self.inp_vid_fps.text())
        self.settings.setValue("inp_vid_res", self.inp_vid_res.text())

    def load_settings(self):
        if self.settings.value("geometry"):
            self.restoreGeometry(self.settings.value("geometry"))
        if self.settings.value("windowState"):
            self.restoreState(self.settings.value("windowState"))
            
        def str_to_bool(val, default):
            if val is None:
                return default
            return val.lower() == 'true' if isinstance(val, str) else bool(val)

        # Batch tab settings
        self.chk_recursive.setChecked(str_to_bool(self.settings.value("chk_recursive"), True))
        self.chk_overwrite.setChecked(str_to_bool(self.settings.value("chk_overwrite"), False))
        self.chk_target.setChecked(str_to_bool(self.settings.value("chk_target"), False))
        if self.settings.value("inp_target"):
            self.inp_target.setText(self.settings.value("inp_target"))
            
        self.chk_suffix.setChecked(str_to_bool(self.settings.value("chk_suffix"), True))
        if self.settings.value("inp_suffix"):
            self.inp_suffix.setText(self.settings.value("inp_suffix"))
            
        self.chk_process_img.setChecked(str_to_bool(self.settings.value("chk_process_img"), True))
        if self.settings.value("cmb_img_preset"):
            self.cmb_img_preset.setCurrentText(self.settings.value("cmb_img_preset"))
        if self.settings.value("cmb_img_format"):
            self.cmb_img_format.setCurrentText(self.settings.value("cmb_img_format"))
            
        self.chk_process_vid.setChecked(str_to_bool(self.settings.value("chk_process_vid"), True))
        self.chk_compile_seq.setChecked(str_to_bool(self.settings.value("chk_compile_seq"), False))
        if self.settings.value("cmb_vid_preset"):
            self.cmb_vid_preset.setCurrentText(self.settings.value("cmb_vid_preset"))
        if self.settings.value("inp_vid_crf"):
            self.inp_vid_crf.setText(self.settings.value("inp_vid_crf"))
        if self.settings.value("inp_vid_fps"):
            self.inp_vid_fps.setText(self.settings.value("inp_vid_fps"))
        if self.settings.value("inp_vid_res"):
            self.inp_vid_res.setText(self.settings.value("inp_vid_res"))

    def closeEvent(self, event):
        self.save_settings()
        event.accept()

    def cancel_processing(self):
        if self.worker and self.worker.isRunning():
            self.worker.cancel()
            self.log("[INFO] Cancellation requested...")
            self.cancel_btn.setEnabled(False)

    def on_processing_finished(self):
        self.tabs.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        self.log("--- Batch Job Finished ---\n")
