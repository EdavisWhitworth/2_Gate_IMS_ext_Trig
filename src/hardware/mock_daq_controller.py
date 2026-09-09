"""
Mock DAQ controller for hardware-free development and debugging.
"""

from PyQt6.QtCore import QTimer
from .daq_interface import AbstractDAQController
from ..models.config import ScanConfig, OperationalMode


class MockDAQController(AbstractDAQController):
    """Simulates NI-6341 counter tasks and trigger events."""

    def __init__(self):
        super().__init__()
        self._test_timer = QTimer()
        self._test_timer.timeout.connect(self._on_auto_trigger)
        self.current_delay_ms = 1.0

    def start_session(self, config: ScanConfig) -> bool:
        self.current_config = config
        self.trigger_count = 0
        self.is_running = True
        
        if config.mode == OperationalMode.WINDOWED:
            self.current_delay_ms = config.gate2_delay_ms
        else:
            self.current_delay_ms = config.sweep_start_delay_ms

        self.signals.status_changed.emit(
            f"Mock DAQ Active ({config.mode.value.capitalize()} Mode" + 
            (" - Test Mode Auto-Triggering" if config.test_mode else " - Waiting External Trigger") + ")"
        )

        if config.test_mode:
            # Auto-trigger periodically after set scan time + buffer
            period = max(20, int(config.auto_trigger_period_ms))
            self._test_timer.start(period)
        else:
            self._test_timer.stop()

        return True

    def stop_session(self) -> None:
        self._test_timer.stop()
        self.is_running = False
        self.signals.status_changed.emit("Mock DAQ Stopped")

    def update_gate2_delay(self, delay_ms: float) -> bool:
        self.current_delay_ms = delay_ms
        return True

    def update_config(self, config: ScanConfig) -> bool:
        was_running = self.is_running
        if was_running:
            self.stop_session()
        return self.start_session(config) if was_running else True

    def trigger_software(self) -> None:
        if self.is_running:
            self._on_auto_trigger()

    def _on_auto_trigger(self) -> None:
        if not self.is_running:
            return
        self.trigger_count += 1
        self.signals.trigger_occurred.emit(self.trigger_count, self.current_delay_ms)
