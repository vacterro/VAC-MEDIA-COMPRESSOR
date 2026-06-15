def generate_stylesheet(palette: dict, font_family: str = "", font_size: int = 14) -> str:
    """
    Generate dynamic stylesheet substituting CSS variables based on the active palette.
    """
    palette_copy = palette.copy()
    palette_copy['font_css'] = f"font-family: '{font_family}';" if font_family else ""
    palette_copy['font_size'] = font_size

    return """
/* Global Styles */
QWidget {{
    background-color: {bg_base};
    color: {text_main};
    font-size: {font_size}px;
    {font_css}
}}

/* Typography */
QLabel {{
    color: {text_main};
    background-color: transparent;
}}

QLabel#titleLabel {{
    font-size: 24px;
    font-weight: bold;
    color: {primary};
}}

QLabel#subtitleLabel {{
    font-size: 14px;
    color: {text_muted};
}}

QLabel#hintLabel {{
    font-size: 13px;
    color: {secondary};
    font-style: italic;
}}

QLabel#previewLabel {{
    border: 1px solid {border};
    background-color: {bg_surface};
    border-radius: 4px;
    padding: 4px;
}}

/* Splitter */
QSplitter::handle {{
    background-color: {border};
    margin: 2px;
    border-radius: 2px;
}}
QSplitter::handle:hover {{
    background-color: {primary};
}}

/* Drop Zone */
QFrame#dropZone {{
    background-color: {bg_surface};
    border: 2px dashed {border};
    border-radius: 10px;
}}
QFrame#dropZone:hover {{
    border-color: {primary};
}}

/* Rewards Dashboard */
QFrame#rewardsBoard {{
    background-color: {bg_header};
    border: 1px solid {primary};
    border-radius: 4px;
    margin-top: 6px;
}}
QLabel#originalText, QLabel#newText {{
    font-size: 14px;
    font-weight: bold;
    color: {text_main};
}}
QLabel#savedText {{
    font-size: 16px;
    font-weight: bold;
    color: {primary};
}}

/* Tab Widget */
QTabWidget::pane {{
    border: none;
    border-top: 1px solid {border};
    background-color: transparent;
    padding-top: 10px;
}}
QTabBar::tab {{
    background-color: transparent;
    color: {text_muted};
    border: none;
    padding: 6px 12px;
    margin-right: 2px;
    font-size: 14px;
    font-weight: bold;
}}
QTabBar::tab:selected {{
    color: {primary};
    border-bottom: 2px solid {primary};
}}
QTabBar::tab:hover:!selected {{
    color: {text_main};
}}

/* Group Box */
QGroupBox {{
    background-color: transparent;
    border: none;
    margin-top: 24px; /* leaves space at the top for the title */
    font-size: 15px;
    font-weight: bold;
    color: {primary};
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 0 8px 0;
}}

/* Buttons */
QPushButton {{
    background-color: {bg_surface};
    color: {text_main};
    border: 1px solid {border};
    border-radius: 4px;
    padding: 4px 8px;
    font-weight: bold;
    min-height: 26px;
}}
QPushButton:focus {{
    border: 2px solid {primary};
    background-color: {bg_surface_hover};
    outline: none;
}}
QPushButton:hover {{
    background-color: {bg_surface_hover};
    border: 1px solid {primary};
}}
QPushButton:pressed {{
    background-color: {primary_pressed};
}}
QPushButton:disabled {{
    background-color: {bg_base};
    color: {text_muted};
    border: 1px solid {border};
}}

QPushButton#startBtn {{
    background-color: {secondary};
    color: #000000;
    font-size: 14px;
    border: 1px solid #000000;
}}
QPushButton#startBtn:hover {{
    background-color: {secondary_hover};
    color: {text_main};
    border: 1px solid {text_main};
}}
QPushButton#cancelBtn {{
    background-color: {danger};
    color: #000000;
    font-size: 14px;
    border: 1px solid #000000;
}}
QPushButton#cancelBtn:hover {{
    background-color: {danger_hover};
    color: {text_main};
    border: 1px solid {text_main};
}}
QPushButton#browseBtn {{
    background-color: transparent;
    color: {primary};
    border: 1px solid {primary};
    padding: 4px 8px;
}}
QPushButton#browseBtn:hover {{
    background-color: rgba(187, 134, 252, 0.1);
}}
QPushButton#colorSwatchBtn {{
    border: 2px solid {border};
    border-radius: 4px;
    padding: 0;
}}

/* Inputs & Combos */
QLineEdit, QComboBox {{
    background-color: {bg_surface};
    border: 2px solid {border};
    border-radius: 4px;
    padding: 4px 6px;
    color: {text_main};
    min-height: 26px;
}}
QLineEdit:focus, QComboBox:focus {{
    border: 2px solid {primary};
    background-color: {bg_surface_hover};
    outline: none;
}}
QLineEdit:disabled, QComboBox:disabled {{
    background-color: {bg_surface_hover};
    color: {text_muted};
    border: 1px solid {border};
}}
QComboBox::drop-down {{
    border: none;
}}
QComboBox QAbstractItemView {{
    background-color: {bg_surface};
    color: {text_main};
    selection-background-color: {primary};
    selection-color: {bg_base};
    border: 1px solid {border};
    outline: none;
}}

/* Checkboxes */
QCheckBox {{
    spacing: 6px;
    background-color: transparent;
    min-height: 26px;
}}
QCheckBox:focus {{
    outline: none;
}}
QCheckBox::indicator {{
    width: 16px;
    height: 16px;
    border-radius: 4px;
    border: 2px solid {primary};
    background-color: {bg_surface};
}}
QCheckBox::indicator:focus {{
    border: 2px solid {primary};
    background-color: {bg_surface_hover};
}}
QCheckBox::indicator:checked {{
    background-color: {primary};
}}
QCheckBox::indicator:hover {{
    border: 2px solid {secondary};
}}

/* Sliders */
QSlider::groove:horizontal {{
    border: none;
    height: 6px;
    background: {bg_surface_hover};
    border-radius: 3px;
    margin: 2px 0;
}}
QSlider::sub-page:horizontal {{
    background: {primary};
    border-radius: 3px;
}}
QSlider::handle:horizontal {{
    background: {primary};
    border: 2px solid {bg_base};
    width: 20px;
    height: 20px;
    margin: -8px 0;
    border-radius: 10px;
}}
QSlider::handle:horizontal:hover, QSlider::handle:horizontal:focus {{
    background: {secondary};
    border: 2px solid {text_main};
}}

/* Progress Bar */
QProgressBar {{
    background-color: {bg_surface};
    border: 1px solid {border};
    border-radius: 4px;
    text-align: center;
    color: {text_main};
    font-weight: bold;
}}
QProgressBar::chunk {{
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {primary}, stop:1 {secondary});
    border-radius: 3px;
}}

/* Log View */
QTextEdit {{
    background-color: {bg_log};
    border: 1px solid {border};
    border-radius: 6px;
    padding: 8px;
    color: #00FF00;
    font-family: "Consolas", monospace;
    font-size: 12px;
}}

/* Group Boxes */
QGroupBox {{
    border: 1px solid {border};
    border-radius: 6px;
    margin-top: 10px;
    padding-top: 6px;
    background-color: transparent;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 4px;
    color: {primary};
    font-weight: bold;
    background-color: transparent;
}}

/* Table Widget */
QTableWidget {{
    background-color: {bg_surface};
    color: {text_main};
    gridline-color: {border};
    border: 1px solid {border};
    border-radius: 4px;
}}
QTableWidget::item:selected {{
    background-color: {primary};
    color: {bg_base};
}}
QHeaderView::section {{
    background-color: {bg_base};
    color: {primary};
    padding: 4px;
    border: 1px solid {border};
    font-weight: bold;
}}

/* ScrollBar */
QScrollBar:vertical {{
    border: none;
    background: {bg_base};
    width: 10px;
    margin: 0px 0px 0px 0px;
}}
QScrollBar::handle:vertical {{
    background: {border};
    min-height: 20px;
    border-radius: 5px;
}}
QScrollBar::handle:vertical:hover {{
    background: {primary};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}
QScrollBar:horizontal {{
    border: none;
    background: {bg_base};
    height: 10px;
    margin: 0px 0px 0px 0px;
}}
QScrollBar::handle:horizontal {{
    background: {border};
    min-width: 20px;
    border-radius: 5px;
}}
QScrollBar::handle:horizontal:hover {{
    background: {primary};
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0px;
}}
""".format(**palette_copy)
