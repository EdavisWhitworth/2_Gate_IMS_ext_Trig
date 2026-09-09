"""
QSS Stylesheets for 2-Gate IMS Control System GUI.
"""

DARK_THEME_QSS = """
QMainWindow, QWidget {
    background-color: #1e1e24;
    color: #e0e0e0;
    font-family: "Segoe UI", Arial, sans-serif;
    font-size: 10pt;
}

QGroupBox {
    border: 1px solid #3a3a46;
    border-radius: 6px;
    margin-top: 12px;
    font-weight: bold;
    color: #4da6ff;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 6px;
}

QTabWidget::pane {
    border: 1px solid #3a3a46;
    border-radius: 6px;
    background-color: #252530;
}

QTabBar::tab {
    background: #1e1e24;
    color: #a0a0a0;
    padding: 8px 16px;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    border: 1px solid #3a3a46;
    margin-right: 2px;
    font-weight: bold;
}

QTabBar::tab:selected {
    background: #252530;
    color: #00d2ff;
    border-bottom: 2px solid #00d2ff;
}

QSlider::groove:horizontal {
    height: 6px;
    background: #3a3a46;
    border-radius: 3px;
}

QSlider::sub-page:horizontal {
    background: #00d2ff;
    border-radius: 3px;
}

QSlider::handle:horizontal {
    background: #ffffff;
    border: 1px solid #00d2ff;
    width: 16px;
    height: 16px;
    margin: -5px 0;
    border-radius: 8px;
}

QSlider::handle:horizontal:hover {
    background: #00d2ff;
}

QDoubleSpinBox, QSpinBox, QLineEdit {
    background-color: #18181f;
    color: #ffffff;
    border: 1px solid #3a3a46;
    border-radius: 4px;
    padding: 4px 8px;
    font-weight: bold;
}

QDoubleSpinBox:focus, QSpinBox:focus, QLineEdit:focus {
    border: 1px solid #00d2ff;
}

QPushButton {
    background-color: #2b2b36;
    color: #ffffff;
    border: 1px solid #3a3a46;
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: bold;
}

QPushButton:hover {
    background-color: #383846;
    border-color: #00d2ff;
}

QPushButton#btn_start {
    background-color: #008855;
    color: #ffffff;
    border: 1px solid #00aa66;
    font-size: 11pt;
}

QPushButton#btn_start:hover {
    background-color: #00aa66;
}

QPushButton#btn_stop {
    background-color: #aa2233;
    color: #ffffff;
    border: 1px solid #cc3344;
    font-size: 11pt;
}

QPushButton#btn_stop:hover {
    background-color: #cc3344;
}

QProgressBar {
    border: 1px solid #3a3a46;
    border-radius: 6px;
    text-align: center;
    background-color: #18181f;
    color: #ffffff;
    font-weight: bold;
}

QProgressBar::chunk {
    background-color: #00d2ff;
    border-radius: 5px;
}

QCheckBox {
    spacing: 8px;
    font-weight: bold;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 1px solid #3a3a46;
    background-color: #18181f;
}

QCheckBox::indicator:checked {
    background-color: #00d2ff;
    border-color: #00d2ff;
}
"""
