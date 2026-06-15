def generate_stylesheet(palette: dict, font_family: str = "MS Sans Serif", font_size: int = 14) -> str:
    """
    Generate dynamic stylesheet substituting CSS variables based on the active palette.
    Vintage 1995 UI Edition, compliant with /vintage strict rules.
    """
    palette_copy = palette.copy()
    palette_copy['font_css'] = f"font-family: '{font_family}', 'Tahoma', 'Courier New';" if font_family else ""
    palette_copy['font_size'] = font_size

    return """
/* Global Styles */
QWidget {{
    background-color: {background};
    color: {textPrimary};
    font-size: {font_size}px;
    {font_css}
}}

/* Focus rings globally */
*:focus {{
    outline: none;
    border: 2px solid {accentTurquoise};
}}

/* Typography */
QLabel {{
    color: {textPrimary};
    background-color: transparent;
}}

QLabel#titleLabel {{
    font-family: 'Tahoma';
    font-size: 20px;
    font-weight: bold;
    color: {textPrimary};
}}

QLabel#subtitleLabel {{
    font-family: 'Tahoma';
    font-size: 16px;
    color: {textSecondary};
}}

QLabel#hintLabel {{
    font-size: 14px;
    color: {textMuted};
    font-style: italic;
}}

QLabel#previewLabel {{
    border: 2px solid;
    border-top-color: {borderSubtle};
    border-left-color: {borderSubtle};
    border-bottom-color: {borderHighlight};
    border-right-color: {borderHighlight};
    background-color: {surface};
    padding: 4px;
}}

/* Splitter */
QSplitter::handle {{
    background-color: {background};
    border-top: 1px solid {borderHighlight};
    border-left: 1px solid {borderHighlight};
    border-bottom: 1px solid {borderSubtle};
    border-right: 1px solid {borderSubtle};
}}

/* List and Tree Views (Data Views) */
QListView, QTreeView, QTableWidget {{
    background-color: {surfaceRaised};
    color: {textPrimary};
    font-family: 'Courier New'; /* Strict vintage rule: use Courier New for lists and data */
    border: 2px solid;
    border-top-color: {borderSubtle};
    border-left-color: {borderSubtle};
    border-bottom-color: {borderHighlight};
    border-right-color: {borderHighlight};
    outline: none;
}}

QListView::item, QTreeView::item, QTableWidget::item {{
    padding: 4px;
}}

QListView::item:selected, QTreeView::item:selected, QTableWidget::item:selected {{
    background-color: {bg_header};
    color: {borderHighlight};
}}

QListView::item:hover, QTreeView::item:hover, QTableWidget::item:hover {{
    background-color: {surfaceAlt};
    color: {textPrimary};
}}

/* Buttons */
QPushButton {{
    background-color: {surface};
    color: {textPrimary};
    border: 2px solid;
    border-top-color: {borderHighlight};
    border-left-color: {borderHighlight};
    border-bottom-color: {borderStrong};
    border-right-color: {borderStrong};
    padding: 4px 12px;
    min-height: 24px;
    border-radius: 0px; /* Windows 95 is boxes */
}}

QPushButton:hover {{
    background-color: {surfaceAlt};
}}

QPushButton:pressed, QPushButton:checked {{
    background-color: {surface};
    border-top-color: {borderStrong};
    border-left-color: {borderStrong};
    border-bottom-color: {borderHighlight};
    border-right-color: {borderHighlight};
    padding: 6px 10px 2px 14px; /* Shift text down-right */
}}

QPushButton:disabled {{
    color: {borderSubtle};
    border-top-color: {borderHighlight};
    border-left-color: {borderHighlight};
    border-bottom-color: {borderSubtle};
    border-right-color: {borderSubtle};
}}

/* Primary Action Buttons (Start/Cancel) */
QPushButton#actionButton {{
    background-color: {accentTurquoise};
    color: {borderHighlight};
    font-weight: bold;
    font-size: 16px;
    min-height: 44px; /* Touch target min 44x44px */
    border-top-color: {borderHighlight};
    border-left-color: {borderHighlight};
    border-bottom-color: {accentTealDeep};
    border-right-color: {accentTealDeep};
}}

QPushButton#actionButton:hover {{
    background-color: {accentTurquoiseDim};
}}

QPushButton#actionButton:pressed {{
    background-color: {accentTealDeep};
    border-top-color: {accentTealDeep};
    border-left-color: {accentTealDeep};
    border-bottom-color: {borderHighlight};
    border-right-color: {borderHighlight};
    color: {borderHighlight};
}}

QPushButton#actionButton:disabled {{
    background-color: {surface};
    color: {borderSubtle};
    border-top-color: {borderHighlight};
    border-left-color: {borderHighlight};
    border-bottom-color: {borderSubtle};
    border-right-color: {borderSubtle};
}}

/* Combo Box */
QComboBox {{
    background-color: {surfaceRaised};
    color: {textPrimary};
    border: 2px solid;
    border-top-color: {borderSubtle};
    border-left-color: {borderSubtle};
    border-bottom-color: {borderHighlight};
    border-right-color: {borderHighlight};
    padding: 4px;
    min-height: 24px;
}}

QComboBox:disabled {{
    background-color: {surface};
    color: {textMuted};
}}

QComboBox::drop-down {{
    border: 2px solid;
    border-top-color: {borderHighlight};
    border-left-color: {borderHighlight};
    border-bottom-color: {borderSubtle};
    border-right-color: {borderSubtle};
    background-color: {surface};
    width: 24px;
}}

QComboBox::down-arrow {{
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid {textPrimary};
    width: 0;
    height: 0;
    margin-top: 2px;
}}

QComboBox QAbstractItemView {{
    border: 2px solid {borderStrong};
    background-color: {surfaceRaised};
    selection-background-color: {bg_header};
    selection-color: {borderHighlight};
}}

/* Spin Box & Line Edit */
QSpinBox, QDoubleSpinBox, QLineEdit {{
    background-color: {surfaceRaised};
    color: {textPrimary};
    border: 2px solid;
    border-top-color: {borderSubtle};
    border-left-color: {borderSubtle};
    border-bottom-color: {borderHighlight};
    border-right-color: {borderHighlight};
    padding: 4px;
    min-height: 24px;
}}

QLineEdit:read-only {{
    background-color: {surface};
    color: {textMuted};
}}

/* Checkboxes and Radio Buttons */
QCheckBox, QRadioButton {{
    spacing: 8px;
    color: {textPrimary};
}}

QCheckBox::indicator, QRadioButton::indicator {{
    width: 16px;
    height: 16px;
    background-color: {surfaceRaised};
    border: 2px solid;
    border-top-color: {borderSubtle};
    border-left-color: {borderSubtle};
    border-bottom-color: {borderHighlight};
    border-right-color: {borderHighlight};
}}

QCheckBox::indicator:checked {{
    image: none; 
    background-color: {textPrimary};
    border: 4px solid {surfaceRaised};
}}

QRadioButton::indicator {{
    border-radius: 8px; 
}}

QRadioButton::indicator:checked {{
    background-color: {textPrimary};
    border: 5px solid {surfaceRaised};
}}

/* Group Boxes */
QGroupBox {{
    font-weight: bold;
    border: 2px solid;
    border-top-color: {borderSubtle};
    border-left-color: {borderSubtle};
    border-bottom-color: {borderHighlight};
    border-right-color: {borderHighlight};
    margin-top: 16px;
    padding-top: 16px;
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 4px;
    left: 12px;
    color: {textPrimary};
}}

/* Progress Bar */
QProgressBar {{
    border: 2px solid;
    border-top-color: {borderSubtle};
    border-left-color: {borderSubtle};
    border-bottom-color: {borderHighlight};
    border-right-color: {borderHighlight};
    background-color: {surfaceRaised};
    text-align: center;
    color: {textPrimary}; 
    font-weight: bold;
    min-height: 24px;
}}

QProgressBar::chunk {{
    background-color: {bg_header}; 
    width: 12px;
    margin: 1px;
}}

/* Tabs */
QTabWidget::pane {{
    border: 2px solid;
    border-top-color: {borderHighlight};
    border-left-color: {borderHighlight};
    border-bottom-color: {borderStrong};
    border-right-color: {borderStrong};
    top: -2px;
    background-color: {surface};
}}

QTabBar::tab {{
    background-color: {surface};
    color: {textPrimary};
    border: 2px solid;
    border-top-color: {borderHighlight};
    border-left-color: {borderHighlight};
    border-bottom-color: {borderStrong};
    border-right-color: {borderStrong};
    padding: 6px 12px;
    margin-right: 2px;
}}

QTabBar::tab:selected {{
    background-color: {surface};
    border-bottom-color: {surface}; /* Blend with pane */
    margin-top: 0px;
}}

QTabBar::tab:!selected {{
    margin-top: 4px;
    background-color: {surfaceAlt};
}}

/* Menus */
QMenuBar {{
    background-color: {surface};
    border-bottom: 2px solid {borderSubtle};
}}

QMenuBar::item {{
    background-color: transparent;
    padding: 4px 8px;
}}

QMenuBar::item:selected {{
    background-color: {bg_header};
    color: {borderHighlight};
}}

QMenu {{
    background-color: {surface};
    border: 2px solid;
    border-top-color: {borderHighlight};
    border-left-color: {borderHighlight};
    border-bottom-color: {borderStrong};
    border-right-color: {borderStrong};
}}

QMenu::item {{
    padding: 4px 24px;
}}

QMenu::item:selected {{
    background-color: {bg_header};
    color: {borderHighlight};
}}

/* Scrollbars */
QScrollBar:vertical {{
    background-color: {surfaceRaised};
    width: 20px;
    margin: 20px 0 20px 0;
}}

QScrollBar::handle:vertical {{
    background-color: {surface};
    min-height: 24px;
    border: 2px solid;
    border-top-color: {borderHighlight};
    border-left-color: {borderHighlight};
    border-bottom-color: {borderStrong};
    border-right-color: {borderStrong};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    background-color: {surface};
    height: 20px;
    subcontrol-origin: margin;
    border: 2px solid;
    border-top-color: {borderHighlight};
    border-left-color: {borderHighlight};
    border-bottom-color: {borderStrong};
    border-right-color: {borderStrong};
}}

QScrollBar::add-line:vertical {{
    subcontrol-position: bottom;
}}

QScrollBar::sub-line:vertical {{
    subcontrol-position: top;
}}

QScrollBar::up-arrow:vertical {{
    border-bottom: 5px solid {textPrimary};
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
}}

QScrollBar::down-arrow:vertical {{
    border-top: 5px solid {textPrimary};
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
}}

QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
    background: none;
}}
    """.format(**palette_copy)
