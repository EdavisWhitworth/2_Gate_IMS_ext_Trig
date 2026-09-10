import time
from unittest.mock import MagicMock

from src.hardware.ni_daq_controller import NIDAQController
from src.models.config import OperationalMode, ScanConfig


def test_windowed_external_trigger_counts_once_for_duplicate_callbacks():
    controller = NIDAQController()
    controller.is_running = True
    controller.current_config = ScanConfig(
        mode=OperationalMode.WINDOWED,
        test_mode=False,
        gate1_width_ms=0.2,
        gate2_delay_ms=1.0,
    )
    controller.signals.trigger_occurred = MagicMock()

    controller._on_hardware_trigger(None, None, None)
    assert controller.trigger_count == 1

    # Simulate the duplicate callback that arrives immediately after the real edge.
    controller._last_hardware_trigger_time = time.monotonic()
    controller._on_hardware_trigger(None, None, None)

    assert controller.trigger_count == 1
