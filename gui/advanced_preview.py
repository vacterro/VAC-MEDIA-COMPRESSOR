import sys
import os
from pathlib import Path
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QSlider, QGroupBox, QLineEdit, QWidget, QSizePolicy
)
from PyQt6.QtCore import Qt, QUrl, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QPixmap, QImage
from PyQt6.QtMultimedia import QMediaPlayer
from PyQt6.QtMultimediaWidgets import QVideoWidget
from PIL import Image, ImageEnhance
import io

class AdvancedPreviewDialog(QDialog):
    def __init__(self, file_data, parent=None):
        super().__init__(parent)
        self.file_data = file_data
        self.p = Path(file_data['path'])
        self.ftype = file_data['type']
        
        # Stored adjustments
        self.adjustments = file_data.get('adjustments', {})
        
        self.setWindowTitle(f"Advanced Preview Engine - {self.p.name}")
        self.resize(600, 450)
        
        self.layout = QVBoxLayout(self)
        
        if self.ftype == "Image":
            self.setup_image_engine()
        elif self.ftype == "Video":
            self.setup_video_engine()
        else:
            self.layout.addWidget(QLabel("Advanced preview not supported for this file type."))
            
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.clicked.connect(self.reject)
        self.btn_apply = QPushButton("Apply Adjustments")
        self.btn_apply.setObjectName("startBtn")
        self.btn_apply.clicked.connect(self.accept)
        
        btn_layout.addWidget(self.btn_cancel)
        btn_layout.addWidget(self.btn_apply)
        self.layout.addLayout(btn_layout)

    # --- IMAGE ENGINE ---
    def setup_image_engine(self):
        try:
            self.original_img = Image.open(str(self.p))
            self.original_img.thumbnail((1200, 1200)) # Keep it manageable for live preview
        except Exception as e:
            self.layout.addWidget(QLabel(f"Failed to load image: {e}"))
            return
            
        self.lbl_image = QLabel()
        self.lbl_image.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_image.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.layout.addWidget(self.lbl_image, stretch=1)
        
        ctrl_group = QGroupBox("Photoshop Engine Adjustments")
        ctrl_layout = QVBoxLayout()
        
        # Sliders (0 to 200, default 100 which is 1.0)
        self.sld_bright = self.create_slider("Brightness", ctrl_layout, self.adjustments.get('brightness', 100))
        self.sld_bright.setToolTip("Adjust the overall lightness or darkness of the image (0-200%).")
        
        self.sld_contrast = self.create_slider("Contrast", ctrl_layout, self.adjustments.get('contrast', 100))
        self.sld_contrast.setToolTip("Increase or decrease the difference between dark and light areas (0-200%).")
        
        self.sld_sat = self.create_slider("Saturation", ctrl_layout, self.adjustments.get('saturation', 100))
        self.sld_sat.setToolTip("Adjust the intensity of the colors. 0% is grayscale, 200% is hyper-vibrant.")
        
        self.sld_bright.valueChanged.connect(self.update_image_preview)
        self.sld_contrast.valueChanged.connect(self.update_image_preview)
        self.sld_sat.valueChanged.connect(self.update_image_preview)
        
        reset_btn = QPushButton("Reset All")
        reset_btn.setToolTip("Revert all image adjustments back to their original 100% state.")
        reset_btn.clicked.connect(self.reset_image_adjustments)
        ctrl_layout.addWidget(reset_btn)
        
        ctrl_group.setLayout(ctrl_layout)
        self.layout.addWidget(ctrl_group)
        
        self.update_image_preview()

    def create_slider(self, name, layout, default_val):
        row = QHBoxLayout()
        row.addWidget(QLabel(name))
        sld = QSlider(Qt.Orientation.Horizontal)
        sld.setRange(0, 200)
        sld.setValue(default_val)
        val_lbl = QLabel(str(default_val) + "%")
        sld.valueChanged.connect(lambda v: val_lbl.setText(f"{v}%"))
        row.addWidget(sld)
        row.addWidget(val_lbl)
        layout.addLayout(row)
        return sld

    def reset_image_adjustments(self):
        self.sld_bright.setValue(100)
        self.sld_contrast.setValue(100)
        self.sld_sat.setValue(100)
        
    def update_image_preview(self):
        b_val = self.sld_bright.value() / 100.0
        c_val = self.sld_contrast.value() / 100.0
        s_val = self.sld_sat.value() / 100.0
        
        img = self.original_img.copy()
        
        if b_val != 1.0:
            enhancer = ImageEnhance.Brightness(img)
            img = enhancer.enhance(b_val)
        if c_val != 1.0:
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(c_val)
        if s_val != 1.0:
            enhancer = ImageEnhance.Color(img)
            img = enhancer.enhance(s_val)
            
        # Convert to QPixmap
        try:
            byte_arr = io.BytesIO()
            img.save(byte_arr, format='PNG')
            pixmap = QPixmap()
            pixmap.loadFromData(byte_arr.getvalue())
            
            # Scale to fit label
            scaled_pixmap = pixmap.scaled(self.lbl_image.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.lbl_image.setPixmap(scaled_pixmap)
        except Exception as e:
            pass
            
    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.ftype == "Image" and hasattr(self, 'lbl_image'):
            self.update_image_preview()

    # --- VIDEO ENGINE ---
    def setup_video_engine(self):
        self.video_widget = QVideoWidget()
        self.layout.addWidget(self.video_widget, stretch=1)
        
        self.media_player = QMediaPlayer()
        self.media_player.setVideoOutput(self.video_widget)
        self.media_player.setSource(QUrl.fromLocalFile(str(self.p)))
        
        ctrl_layout = QHBoxLayout()
        
        self.btn_play = QPushButton("▶ Play")
        self.btn_play.setToolTip("Play or pause the video.")
        self.btn_play.clicked.connect(self.toggle_play)
        
        self.btn_stop = QPushButton("⏹ Stop")
        self.btn_stop.setToolTip("Stop playback and return to the beginning.")
        self.btn_stop.clicked.connect(self.media_player.stop)
        
        ctrl_layout.addWidget(self.btn_play)
        ctrl_layout.addWidget(self.btn_stop)
        
        self.timeline = QSlider(Qt.Orientation.Horizontal)
        self.timeline.setToolTip("Scrub through the video timeline.")
        self.timeline.setRange(0, 0)
        self.timeline.sliderMoved.connect(self.set_position)
        
        ctrl_layout.addWidget(self.timeline)
        
        self.lbl_time = QLabel("00:00 / 00:00")
        ctrl_layout.addWidget(self.lbl_time)
        
        self.layout.addLayout(ctrl_layout)
        
        # Trim Controls
        trim_group = QGroupBox("Premiere Trimming (Cut Video)")
        trim_layout = QHBoxLayout()
        
        trim_layout.addWidget(QLabel("Start Time (e.g. 00:01:23):"))
        self.inp_start = QLineEdit(self.adjustments.get('trim_start', ""))
        self.inp_start.setToolTip("The exact timestamp where the exported video should begin.\nFormat: HH:MM:SS or seconds.")
        trim_layout.addWidget(self.inp_start)
        
        self.btn_set_start = QPushButton("Set Current")
        self.btn_set_start.setToolTip("Grab the current playback time and set it as the Start Time.")
        self.btn_set_start.clicked.connect(lambda: self.set_trim_time(self.inp_start))
        trim_layout.addWidget(self.btn_set_start)
        
        trim_layout.addSpacing(20)
        
        trim_layout.addWidget(QLabel("End Time:"))
        self.inp_end = QLineEdit(self.adjustments.get('trim_end', ""))
        self.inp_end.setToolTip("The exact timestamp where the exported video should end.\nFormat: HH:MM:SS or seconds.")
        trim_layout.addWidget(self.inp_end)
        
        self.btn_set_end = QPushButton("Set Current")
        self.btn_set_end.setToolTip("Grab the current playback time and set it as the End Time.")
        self.btn_set_end.clicked.connect(lambda: self.set_trim_time(self.inp_end))
        trim_layout.addWidget(self.btn_set_end)
        
        trim_group.setLayout(trim_layout)
        self.layout.addWidget(trim_group)
        
        self.media_player.positionChanged.connect(self.position_changed)
        self.media_player.durationChanged.connect(self.duration_changed)
        self.media_player.playbackStateChanged.connect(self.state_changed)

    def toggle_play(self):
        if self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.media_player.pause()
        else:
            self.media_player.play()
            
    def state_changed(self, state):
        if state == QMediaPlayer.PlaybackState.PlayingState:
            self.btn_play.setText("⏸ Pause")
        else:
            self.btn_play.setText("▶ Play")
            
    def position_changed(self, position):
        self.timeline.setValue(position)
        self.update_time_label()
        
    def duration_changed(self, duration):
        self.timeline.setRange(0, duration)
        self.update_time_label()
        
    def set_position(self, position):
        self.media_player.setPosition(position)
        
    def update_time_label(self):
        pos = self.media_player.position() // 1000
        dur = self.media_player.duration() // 1000
        self.lbl_time.setText(f"{pos//60:02}:{pos%60:02} / {dur//60:02}:{dur%60:02}")
        
    def set_trim_time(self, line_edit):
        pos = self.media_player.position() // 1000
        h = pos // 3600
        m = (pos % 3600) // 60
        s = pos % 60
        line_edit.setText(f"{h:02}:{m:02}:{s:02}")

    # --- RESULTS ---
    def get_adjustments(self):
        res = {}
        if self.ftype == "Image":
            res['brightness'] = self.sld_bright.value()
            res['contrast'] = self.sld_contrast.value()
            res['saturation'] = self.sld_sat.value()
        elif self.ftype == "Video":
            res['trim_start'] = self.inp_start.text().strip()
            res['trim_end'] = self.inp_end.text().strip()
        return res
