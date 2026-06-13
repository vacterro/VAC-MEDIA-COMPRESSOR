def generate_stylesheet(palette: dict) -> str:
    """
    Generate dynamic stylesheet substituting CSS variables based on the active palette.
    """
    return """
/* Global Styles - Uses Native System Font */
QWidget {{
    background-color: {bg_base};
    color: {text_main};
    font-size: 14px;
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

/* Drop Zone */
QFrame#dropZone {{
    background-color: {bg_surface};
    border: 2px dashed {primary};
    border-radius: 12px;
}}
QFrame#dropZone:hover {{
    background-color: {bg_surface_hover};
    border: 2px dashed {secondary};
}}

/* Tab Widget */
QTabWidget::pane {{
    border: 1px solid {border};
    border-radius: 8px;
    background-color: {bg_header};
    top: -1px; 
}}
QTabBar::tab {{
    background-color: {bg_surface};
    color: {text_muted};
    border: 1px solid {border};
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    padding: 8px 16px;
    margin-right: 2px;
}}
QTabBar::tab:selected {{
    background-color: {primary};
    color: #000000;
    font-weight: bold;
    border-color: {primary};
}}
QTabBar::tab:hover:!selected {{
    background-color: {bg_surface_hover};
    color: {text_main};
}}

/* Buttons */
QPushButton {{
    background-color: {primary_button};
    color: {text_main};
    border: none;
    border-radius: 6px;
    padding: 10px 20px;
    font-weight: bold;
}}
QPushButton:hover {{
    background-color: {primary_button_hover};
}}
QPushButton:pressed {{
    background-color: {primary_pressed};
}}
QPushButton:disabled {{
    background-color: {bg_surface_hover};
    color: {text_muted};
}}

QPushButton#startBtn {{
    background-color: {secondary};
    color: #000000;
    font-size: 16px;
}}
QPushButton#startBtn:hover {{
    background-color: {secondary_hover};
    color: {text_main};
}}
QPushButton#cancelBtn {{
    background-color: {danger};
    color: #000000;
    font-size: 16px;
}}
QPushButton#cancelBtn:hover {{
    background-color: {danger_hover};
    color: {text_main};
}}
QPushButton#browseBtn {{
    background-color: transparent;
    color: {primary};
    border: 1px solid {primary};
    padding: 6px 12px;
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
    border: 1px solid {border};
    border-radius: 4px;
    padding: 6px;
    color: {text_main};
}}
QLineEdit:focus, QComboBox:focus {{
    border: 1px solid {primary};
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
    selection-background-color: {primary_button};
}}

/* Checkboxes */
QCheckBox {{
    spacing: 8px;
    background-color: transparent;
}}
QCheckBox::indicator {{
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 2px solid {primary};
    background-color: {bg_surface};
}}
QCheckBox::indicator:checked {{
    background-color: {primary};
}}
QCheckBox::indicator:hover {{
    border: 2px solid {secondary};
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
    border-radius: 8px;
    margin-top: 14px;
    padding-top: 10px;
    background-color: transparent;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 5px;
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
QHeaderView::section {{
    background-color: {bg_base};
    color: {primary};
    padding: 4px;
    border: 1px solid {border};
    font-weight: bold;
}}
""".format(**palette)
