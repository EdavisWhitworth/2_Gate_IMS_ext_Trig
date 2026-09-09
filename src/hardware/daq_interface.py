"""
Abstract base class for DAQ hardware controller interface.
"""

from abc import ABC, abstractmethod
from typing import Callable, Optional
from PyQt6.QtCore import QObject, pyqtSignal
from ..models.config import ScanConfig


class DAQSignalBridge(QObject):
    """Qt signal bridge for hardware callbacks to thread-safe GUI updates."""
    trigger_occurred = pyqtSignal(int, float)  # (trigger_count, current_delay_ms)
    error_occurred = pyqtSignal(str)           # error message
    status_changed = pyqtSignal(str)           # state description


class AbstractDAQController(ABC):
    """Abstract interface for NI-6341 counter output operations."""

    def __init__(self):
        self.signals = DAQSignalBridge()
        self.is_running = False
        self.current_config: Optional[ScanConfig] = None
        self.trigger_count = 0

    @abstractmethod
    def start_session(self, config: ScanConfig) -> bool:
        """Initialize and start counter tasks for Gate 1 and Gate 2."""
        pass

    @abstractmethod
    def stop_session(self) -> None:
        """Stop and close counter tasks."""
        pass

    @abstractmethod
    def update_gate2_delay(self, delay_ms: float) -> bool:
        """Dynamically update Gate 2 initial delay (used in Windowed & Sweep modes)."""
        pass

    @abstractmethod
    def update_config(self, config: ScanConfig) -> bool:
        """Update full configuration parameters."""
        pass

    @abstractmethod
    def trigger_software(self) -> None:
        """Simulate or execute a software trigger (Test Mode)."""
        pass
