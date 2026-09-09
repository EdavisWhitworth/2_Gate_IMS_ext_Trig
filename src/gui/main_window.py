"""
Main Window application container for 2-Gate IMS Control System.
"""

from typing import Optional
import numpy as np
from PyQt6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QSplitter, QMessageBox
from PyQt6.QtCore import Qt, QTimer

from .widgets.control_panel import ControlPanelWidget
from .widgets.pulse_diagram import PulseDiagramWidget
from .widgets.status_panel import StatusPanelWidget
from .styles import DARK_THEME_QSS
from ..models.config import ScanConfig, OperationalMode
from ..hardware import AbstractDAQController, NIDAQController, MockDAQController


class MainWindow(QMainWindow):
    """Main application window for 2-Gate IMS Control System."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("2-Gate Ion Mobility Spectrometry System Control (NI-6341)")
        self.resize(1150, 720)

        self.daq: Optional[AbstractDAQController] = None
        self.current_config: ScanConfig = ScanConfig()

        # Sweep tracking variables
        self.sweep_delays: np.ndarray = np.array([])
        self.sweep_step_idx: int = 0
        self.sweep_dwell_counter: int = 0

        self._init_ui()
        self._setup_daq(use_mock=True) # Default to simulation or auto-detect
        self._on_config_changed()

    def _init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QHBoxLayout(central_widget)
        layout.setContentsMargins(6, 6, 6, 6)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left panel: Controls + Status
        left_widget = QWidget()
        left_layout = QHBoxLayout(left_widget) if False else None
        from PyQt6.QtWidgets import QVBoxLayout
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)

        self.ctrl_panel = ControlPanelWidget()
        self.status_panel = StatusPanelWidget()

        left_layout.addWidget(self.ctrl_panel)
        left_layout.addWidget(self.status_panel)

        # Right panel: Pulse Timing Diagram
        self.diagram_panel = PulseDiagramWidget()

        splitter.addWidget(left_widget)
        splitter.addWidget(self.diagram_panel)
        splitter.setStretchFactor(0, 4)
        splitter.setStretchFactor(1, 6)

        layout.addWidget(splitter)

        # Connect Control Panel signals
        self.ctrl_panel.config_changed.connect(self._on_config_changed)
        self.ctrl_panel.start_requested.connect(self.start_system)
        self.ctrl_panel.stop_requested.connect(self.stop_system)

        # Check if hardware DAQmx is available
        if NIDAQController.is_hardware_available():
            self.ctrl_panel.combo_hardware.setCurrentIndex(0)
            self.status_panel.log("NI-6341 hardware detected and ready.")
        else:
            self.ctrl_panel.combo_hardware.setCurrentIndex(1)
            self.status_panel.log("NI DAQmx hardware not detected. Loaded in Simulation Mode.")

    def _setup_daq(self, use_mock: bool):
        """Instantiate and wire up real or mock DAQ controller."""
        if self.daq is not None:
            self.daq.stop_session()

        if use_mock:
            self.daq = MockDAQController()
            self.status_panel.log("Switched driver to Mock DAQ (Simulation).")
        else:
            self.daq = NIDAQController()
            self.status_panel.log("Switched driver to NI-6341 (DAQmx).")

        # Wire hardware callbacks
        self.daq.signals.trigger_occurred.connect(self._on_trigger_occurred)
        self.daq.signals.error_occurred.connect(self._on_daq_error)
        self.daq.signals.status_changed.connect(self._on_daq_status_changed)

    def _on_config_changed(self):
        """Handle control panel adjustments and update diagram preview."""
        config = self.ctrl_panel.get_config()
        valid, msg = config.validate()

        if not valid:
            self.status_panel.log(f"Config Warning: {msg}")
            return

        self.current_config = config

        # Handle hardware selection change
        use_mock = self.ctrl_panel.is_mock_hardware()
        if type(self.daq) is MockDAQController if not use_mock else type(self.daq) is NIDAQController:
            self._setup_daq(use_mock)

        # Update diagram preview
        if self.daq and self.daq.is_running:
            # If running in windowed mode, dynamically push delay update to DAQ
            if config.mode == OperationalMode.WINDOWED:
                self.daq.update_gate2_delay(config.gate2_delay_ms)
                self.diagram_panel.update_diagram(config, config.gate2_delay_ms)
        else:
            self.diagram_panel.update_diagram(config)

    def start_system(self):
        """Start Windowed or Sweep operation."""
        config = self.ctrl_panel.get_config()
        valid, msg = config.validate()

        if not valid:
            QMessageBox.warning(self, "Invalid Parameters", msg)
            return

        self.current_config = config
        use_mock = self.ctrl_panel.is_mock_hardware()
        self._setup_daq(use_mock)

        if config.mode == OperationalMode.SWEEP:
            self.sweep_delays = config.get_sweep_delays()
            self.sweep_step_idx = 0
            self.sweep_dwell_counter = 0

            # Override initial gate2 delay to sweep start delay
            config.gate2_delay_ms = self.sweep_delays[0]
            self.status_panel.reset_sweep_progress()
            self.status_panel.update_sweep_progress(1, len(self.sweep_delays), self.sweep_delays[0])
            self.status_panel.log(f"Starting Sweep Mode: {len(self.sweep_delays)} delay steps.")
        else:
            self.status_panel.log("Starting Windowed Mode.")

        success = self.daq.start_session(config)

        if success:
            self.ctrl_panel.set_system_running(True)
            is_sweep = config.mode == OperationalMode.SWEEP
            self.status_panel.set_system_state("RUNNING", True, is_sweep)
            self.diagram_panel.update_diagram(config, config.gate2_delay_ms)

    def stop_system(self):
        """Stop current operation."""
        if self.daq:
            self.daq.stop_session()
        self.ctrl_panel.set_system_running(False)
        self.status_panel.set_system_state("STOPPED", False)
        self.status_panel.log("System stopped by user.")

    def _on_trigger_occurred(self, trigger_count: int, active_delay_ms: float):
        """Callback fired on hardware/software trigger event."""
        self.status_panel.update_metrics(active_delay_ms, trigger_count)

        # Handle sweep delay progression
        if self.current_config.mode == OperationalMode.SWEEP and self.daq and self.daq.is_running:
            self.sweep_dwell_counter += 1

            if self.sweep_dwell_counter >= self.current_config.sweep_dwell_count:
                self.sweep_dwell_counter = 0
                self.sweep_step_idx += 1

                if self.sweep_step_idx < len(self.sweep_delays):
                    next_delay = self.sweep_delays[self.sweep_step_idx]
                    # Let the current Gate 2 pulse finish before rebuilding its
                    # finite task for the next sweep delay.
                    update_delay_ms = max(
                        1,
                        int(active_delay_ms + self.current_config.gate2_width_ms + 1)
                    )
                    QTimer.singleShot(
                        update_delay_ms,
                        lambda delay=next_delay: self._apply_sweep_delay(delay)
                    )
                    self.diagram_panel.update_diagram(self.current_config, next_delay)
                    self.status_panel.update_sweep_progress(
                        self.sweep_step_idx + 1,
                        len(self.sweep_delays),
                        next_delay
                    )
                else:
                    # Sweep finished!
                    self.status_panel.log("Sweep sequence completed successfully.")
                    self.stop_system()

    def _apply_sweep_delay(self, delay_ms: float):
        """Apply a sweep delay after the active Gate 2 pulse is complete."""
        if self.daq and self.daq.is_running and self.current_config.mode == OperationalMode.SWEEP:
            self.current_config.gate2_delay_ms = delay_ms
            if not self.daq.update_gate2_delay(delay_ms):
                self.status_panel.log(f"ERROR: Failed to apply sweep delay {delay_ms:.2f} ms.")

    def _on_daq_error(self, message: str):
        self.status_panel.log(f"ERROR: {message}")
        QMessageBox.critical(self, "Hardware Error", message)
        self.stop_system()

    def _on_daq_status_changed(self, status: str):
        self.status_panel.log(status)

    def closeEvent(self, event):
        """Ensure DAQ resources are cleanly released when app closes."""
        if self.daq:
            self.daq.stop_session()
        event.accept()
