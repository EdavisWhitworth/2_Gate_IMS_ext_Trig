"""
Control Panel Widget containing Mode selectors, Sliders, SpinBoxes, and Run controls.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QTabWidget,
    QLabel, QSlider, QDoubleSpinBox, QSpinBox, QCheckBox, QPushButton, QComboBox
)
from PyQt6.QtCore import pyqtSignal, Qt, QSignalBlocker
from ...models.config import ScanConfig, OperationalMode


class SliderSpinBox(QWidget):
    """Helper widget pairing a horizontal QSlider with a QDoubleSpinBox."""

    valueChanged = pyqtSignal(float)

    def __init__(self, title: str, min_val: float, max_val: float, default_val: float, step: float = 0.01, decimals: int = 2, unit: str = "ms", parent=None):
        super().__init__(parent)
        self.scale = int(1.0 / step) if step > 0 else 100
        self.min_val = min_val
        self.max_val = max_val

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 2, 0, 2)

        self.label = QLabel(title)
        self.label.setMinimumWidth(130)

        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(int(min_val * self.scale), int(max_val * self.scale))
        self.slider.setValue(int(default_val * self.scale))

        self.spin = QDoubleSpinBox()
        self.spin.setRange(min_val, max_val)
        self.spin.setSingleStep(step)
        self.spin.setDecimals(decimals)
        self.spin.setValue(default_val)
        self.spin.setSuffix(f" {unit}")
        self.spin.setMinimumWidth(100)

        layout.addWidget(self.label)
        layout.addWidget(self.slider, 1)
        layout.addWidget(self.spin)

        # Sync signals
        self.slider.valueChanged.connect(self._on_slider_changed)
        self.spin.valueChanged.connect(self._on_spin_changed)

    def _on_slider_changed(self, int_val: int):
        float_val = int_val / float(self.scale)
        with QSignalBlocker(self.spin):
            self.spin.setValue(float_val)
        self.valueChanged.emit(float_val)

    def _on_spin_changed(self, float_val: float):
        int_val = int(float_val * self.scale)
        with QSignalBlocker(self.slider):
            self.slider.setValue(int_val)
        self.valueChanged.emit(float_val)

    def value(self) -> float:
        return self.spin.value()

    def setValue(self, val: float):
        with QSignalBlocker(self.slider), QSignalBlocker(self.spin):
            self.spin.setValue(val)
            self.slider.setValue(int(val * self.scale))


class ControlPanelWidget(QWidget):
    """Main control panel containing scan parameters and hardware controls."""

    config_changed = pyqtSignal()
    start_requested = pyqtSignal()
    stop_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(10)

        # Hardware & Execution Mode Box
        hw_group = QGroupBox("Hardware & Execution Settings")
        hw_layout = QHBoxLayout(hw_group)

        hw_layout.addWidget(QLabel("Device Driver:"))
        self.combo_hardware = QComboBox()
        self.combo_hardware.addItems(["NI-6341 (Hardware DAQmx)", "Mock DAQ (Simulation)"])
        hw_layout.addWidget(self.combo_hardware)

        self.check_test_mode = QCheckBox("Test Mode (Auto Trigger)")
        hw_layout.addWidget(self.check_test_mode)

        main_layout.addWidget(hw_group)

        # Tab Widget for Windowed vs Sweep Mode
        self.tab_widget = QTabWidget()

        # ------------------ WINDOWED MODE TAB ------------------
        self.tab_windowed = QWidget()
        win_layout = QVBoxLayout(self.tab_windowed)

        self.ss_g1_width = SliderSpinBox("Gate 1 Width:", 0.01, 10.0, 0.20, step=0.01)
        self.ss_g2_delay = SliderSpinBox("Gate 2 Initial Delay:", 0.0, 100.0, 1.00, step=0.05)
        self.ss_g2_width = SliderSpinBox("Gate 2 Width:", 0.01, 10.0, 0.20, step=0.01)

        win_layout.addWidget(self.ss_g1_width)
        win_layout.addWidget(self.ss_g2_delay)
        win_layout.addWidget(self.ss_g2_width)
        win_layout.addStretch()

        self.tab_widget.addTab(self.tab_windowed, "Windowed Mode")

        # ------------------ SWEEP MODE TAB ------------------
        self.tab_sweep = QWidget()
        sw_layout = QVBoxLayout(self.tab_sweep)

        self.ss_sw_g1_width = SliderSpinBox("Gate 1 Width:", 0.01, 10.0, 0.20, step=0.01)
        self.ss_sw_g2_width = SliderSpinBox("Gate 2 Constant Width:", 0.01, 10.0, 0.20, step=0.01)
        self.ss_sw_start_delay = SliderSpinBox("Initial Delay (tStart):", 0.0, 100.0, 0.00, step=0.05)
        self.ss_sw_stop_delay = SliderSpinBox("Final Delay (tStop):", 0.0, 100.0, 50.00, step=0.05)
        self.ss_sw_step = SliderSpinBox("Time Step (Δt):", 0.01, 20.0, 0.50, step=0.01)

        # Dwell count layout
        dwell_layout = QHBoxLayout()
        dwell_layout.addWidget(QLabel("Dwell Count (Triggers/Step):"))
        self.spin_dwell = QSpinBox()
        self.spin_dwell.setRange(1, 1000)
        self.spin_dwell.setValue(1)
        dwell_layout.addWidget(self.spin_dwell)
        dwell_layout.addStretch()

        sw_layout.addWidget(self.ss_sw_g1_width)
        sw_layout.addWidget(self.ss_sw_g2_width)
        sw_layout.addWidget(self.ss_sw_start_delay)
        sw_layout.addWidget(self.ss_sw_stop_delay)
        sw_layout.addWidget(self.ss_sw_step)
        sw_layout.addLayout(dwell_layout)
        sw_layout.addStretch()

        self.tab_widget.addTab(self.tab_sweep, "Sweep Mode")

        main_layout.addWidget(self.tab_widget)

        # Action Buttons Layout
        btn_layout = QHBoxLayout()
        self.btn_start = QPushButton("Start System")
        self.btn_start.setObjectName("btn_start")
        self.btn_stop = QPushButton("Stop System")
        self.btn_stop.setObjectName("btn_stop")
        self.btn_stop.setEnabled(False)

        btn_layout.addWidget(self.btn_start)
        btn_layout.addWidget(self.btn_stop)

        main_layout.addLayout(btn_layout)

        # Connect signals for live updates
        self.tab_widget.currentChanged.connect(lambda _: self.config_changed.emit())
        self.combo_hardware.currentIndexChanged.connect(lambda _: self.config_changed.emit())
        self.check_test_mode.toggled.connect(lambda _: self.config_changed.emit())

        self.ss_g1_width.valueChanged.connect(lambda _: self.config_changed.emit())
        self.ss_g2_delay.valueChanged.connect(lambda _: self.config_changed.emit())
        self.ss_g2_width.valueChanged.connect(lambda _: self.config_changed.emit())

        self.ss_sw_g1_width.valueChanged.connect(lambda _: self.config_changed.emit())
        self.ss_sw_g2_width.valueChanged.connect(lambda _: self.config_changed.emit())
        self.ss_sw_start_delay.valueChanged.connect(lambda _: self.config_changed.emit())
        self.ss_sw_stop_delay.valueChanged.connect(lambda _: self.config_changed.emit())
        self.ss_sw_step.valueChanged.connect(lambda _: self.config_changed.emit())
        self.spin_dwell.valueChanged.connect(lambda _: self.config_changed.emit())

        self.btn_start.clicked.connect(self.start_requested.emit)
        self.btn_stop.clicked.connect(self.stop_requested.emit)

    def get_config(self) -> ScanConfig:
        """Construct a ScanConfig dataclass from current UI controls."""
        is_windowed = self.tab_widget.currentIndex() == 0
        cfg = ScanConfig()
        cfg.mode = OperationalMode.WINDOWED if is_windowed else OperationalMode.SWEEP
        cfg.test_mode = self.check_test_mode.isChecked()

        if is_windowed:
            cfg.gate1_width_ms = self.ss_g1_width.value()
            cfg.gate2_delay_ms = self.ss_g2_delay.value()
            cfg.gate2_width_ms = self.ss_g2_width.value()
        else:
            cfg.gate1_width_ms = self.ss_sw_g1_width.value()
            cfg.gate2_width_ms = self.ss_sw_g2_width.value()
            cfg.sweep_start_delay_ms = self.ss_sw_start_delay.value()
            cfg.sweep_stop_delay_ms = self.ss_sw_stop_delay.value()
            cfg.sweep_step_ms = self.ss_sw_step.value()
            cfg.sweep_dwell_count = self.spin_dwell.value()

        return cfg

    def is_mock_hardware(self) -> bool:
        return self.combo_hardware.currentIndex() == 1

    def set_system_running(self, running: bool):
        """Update Start/Stop button states based on DAQ status."""
        self.btn_start.setEnabled(not running)
        self.btn_stop.setEnabled(running)
        self.tab_widget.setEnabled(not running)
        self.combo_hardware.setEnabled(not running)
