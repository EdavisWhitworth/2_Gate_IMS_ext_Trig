"""
Production DAQmx hardware controller for NI-6341 counter/timer pulse generation.
"""

from typing import Optional
from PyQt6.QtCore import QTimer
from .daq_interface import AbstractDAQController
from ..models.config import ScanConfig, OperationalMode

try:
    import nidaqmx
    from nidaqmx.constants import (
        AcquisitionType,
        TimeUnits,
        Level,
        Edge,
        TaskMode,
    )
    HAS_NIDAQMX = True
except ImportError:
    HAS_NIDAQMX = False


class NIDAQController(AbstractDAQController):
    """
    Controls NI-6341 Counter 0 (Gate 1) and Counter 1 (Gate 2).
    - Counter 0 output: Gate 1 TTL pulse (triggered by external input /Dev1/PFI0 or auto-trigger).
    - Counter 1 output: Gate 2 TTL pulse (triggered by rising edge of Counter 0 Internal Output).
    """

    def __init__(self):
        super().__init__()
        self._task_g1: Optional[object] = None
        self._task_g2: Optional[object] = None
        self._test_timer = QTimer()
        self._test_timer.timeout.connect(self._on_auto_trigger)
        self.current_delay_ms = 1.0

    @staticmethod
    def is_hardware_available() -> bool:
        """Check if nidaqmx module and hardware drivers are installed."""
        if not HAS_NIDAQMX:
            return False
        try:
            system = nidaqmx.system.System.local()
            return len(system.devices) > 0
        except Exception:
            return False

    def start_session(self, config: ScanConfig) -> bool:
        if not HAS_NIDAQMX:
            msg = "nidaqmx package is not installed. Please install nidaqmx or use Mock DAQ mode."
            self.signals.error_occurred.emit(msg)
            return False

        self.current_config = config
        self.trigger_count = 0

        # Close existing tasks if open
        self.stop_session()

        dev = config.device_name
        g1_width_sec = max(0.000001, config.gate1_width_ms / 1000.0)
        g2_width_sec = max(0.000001, config.gate2_width_ms / 1000.0)

        if config.mode == OperationalMode.WINDOWED:
            self.current_delay_ms = config.gate2_delay_ms
        else:
            self.current_delay_ms = config.sweep_start_delay_ms

        g2_delay_sec = max(0.000001, self.current_delay_ms / 1000.0)

        try:
            # 1. Configure Counter 0 (Gate 1)
            self._task_g1 = nidaqmx.Task("Gate1_CTR0_Task")
            ctr0_path = f"{dev}/{config.gate1_counter}"
            self._task_g1.co_channels.add_co_pulse_chan_time(
                counter=ctr0_path,
                units=TimeUnits.SECONDS,
                idle_state=Level.LOW,
                initial_delay=0.0,
                low_time=0.0001,
                high_time=g1_width_sec
            )
            self._task_g1.timing.cfg_implicit_timing(
                sample_mode=AcquisitionType.FINITE,
                samps_per_chan=1
            )

            if not config.test_mode:
                # External trigger on PFI0 (rising edge)
                self._task_g1.triggers.start_trigger.cfg_dig_edge_start_trig(
                    trigger_source=config.external_trigger_terminal,
                    trigger_edge=Edge.RISING
                )
                self._task_g1.triggers.start_trigger.retriggerable = True

            # 2. Configure Counter 1 (Gate 2)
            self._task_g2 = nidaqmx.Task("Gate2_CTR1_Task")
            ctr1_path = f"{dev}/{config.gate2_counter}"
            self._task_g2.co_channels.add_co_pulse_chan_time(
                counter=ctr1_path,
                units=TimeUnits.SECONDS,
                idle_state=Level.LOW,
                initial_delay=g2_delay_sec,
                low_time=0.0001,
                high_time=g2_width_sec
            )
            self._task_g2.timing.cfg_implicit_timing(
                sample_mode=AcquisitionType.FINITE,
                samps_per_chan=1
            )

            # Gate 2 triggers on the rising edge of Gate 1's internal output.
            self._task_g2.triggers.start_trigger.cfg_dig_edge_start_trig(
                trigger_source=f"/{dev}/{config.gate1_counter}InternalOutput",
                trigger_edge=Edge.RISING
            )
            self._task_g2.triggers.start_trigger.retriggerable = True

            # Commit both tasks before starting either one. This ensures Gate 2
            # is fully armed before Gate 1 can respond to the first external edge.
            self._task_g2.control(TaskMode.TASK_COMMIT)
            self._task_g1.control(TaskMode.TASK_COMMIT)

            # Start tasks in reverse order (Gate 2 first so it's armed when Gate 1 fires)
            self._task_g2.start()
            if not config.test_mode:
                self._task_g1.start()

            self.is_running = True
            self.signals.status_changed.emit(
                f"NI-6341 Active ({config.mode.value.capitalize()} Mode" + 
                (" - Auto Trigger" if config.test_mode else " - Armed on PFI0") + ")"
            )

            if config.test_mode:
                period = max(20, int(config.auto_trigger_period_ms))
                self._test_timer.start(period)
            else:
                self._test_timer.stop()

            return True

        except Exception as e:
            self.stop_session()
            msg = f"Failed to start NI DAQmx tasks: {str(e)}"
            self.signals.error_occurred.emit(msg)
            return False

    def stop_session(self) -> None:
        self._test_timer.stop()
        self.is_running = False

        if self._task_g1 is not None:
            try:
                self._task_g1.stop()
                self._task_g1.close()
            except Exception:
                pass
            self._task_g1 = None

        if self._task_g2 is not None:
            try:
                self._task_g2.stop()
                self._task_g2.close()
            except Exception:
                pass
            self._task_g2 = None

        self.signals.status_changed.emit("NI DAQmx Stopped")

    def update_gate2_delay(self, delay_ms: float) -> bool:
        """Dynamically reconfigures Counter 1 initial delay."""
        self.current_delay_ms = delay_ms
        if not self.is_running or self._task_g2 is None:
            return True

        delay_sec = max(0.000001, delay_ms / 1000.0)
        config = self.current_config
        if config is None:
            return False

        try:
            gate1_was_running = self._task_g1 is not None and not config.test_mode
            if self._task_g1 is not None:
                self._task_g1.stop()

            self._task_g2.stop()
            self._task_g2.close()

            dev = config.device_name
            g2_width_sec = max(0.000001, config.gate2_width_ms / 1000.0)
            self._task_g2 = nidaqmx.Task("Gate2_CTR1_Task")
            self._task_g2.co_channels.add_co_pulse_chan_time(
                counter=f"{dev}/{config.gate2_counter}",
                units=TimeUnits.SECONDS,
                idle_state=Level.LOW,
                initial_delay=delay_sec,
                low_time=0.0001,
                high_time=g2_width_sec
            )
            self._task_g2.timing.cfg_implicit_timing(
                sample_mode=AcquisitionType.FINITE,
                samps_per_chan=1
            )
            self._task_g2.triggers.start_trigger.cfg_dig_edge_start_trig(
                trigger_source=f"/{dev}/{config.gate1_counter}InternalOutput",
                trigger_edge=Edge.RISING
            )
            self._task_g2.triggers.start_trigger.retriggerable = True
            self._task_g2.control(TaskMode.TASK_COMMIT)
            self._task_g2.start()

            if gate1_was_running:
                self._task_g1.start()
            return True
        except Exception as e:
            self.signals.error_occurred.emit(f"Error updating Gate 2 delay: {str(e)}")
            return False

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

        if self._task_g1 is not None and self.current_config is not None and self.current_config.test_mode:
            try:
                # Reset both finite tasks so Gate 2 is armed for every simulated
                # Gate 1 pulse and cannot fall out of phase after one trigger.
                self._task_g2.stop()
                self._task_g2.start()
                self._task_g1.stop()
                self._task_g1.start()
            except Exception as e:
                self.signals.error_occurred.emit(f"Error generating test trigger: {str(e)}")
                return

        self.trigger_count += 1
        self.signals.trigger_occurred.emit(self.trigger_count, self.current_delay_ms)
