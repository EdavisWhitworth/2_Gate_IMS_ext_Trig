"""
Scan and hardware configuration models for 2-Gate IMS system.
"""

from dataclasses import dataclass, field
from enum import Enum
import numpy as np


class OperationalMode(Enum):
    WINDOWED = "windowed"
    SWEEP = "sweep"


@dataclass
class ScanConfig:
    # Mode selection
    mode: OperationalMode = OperationalMode.WINDOWED
    test_mode: bool = False
    
    # Timing limits (ms)
    scan_time_ms: float = 100.0          # Max spectral time window (0 - 100 ms)
    auto_trigger_period_ms: float = 250.0 # Test mode trigger interval
    
    # Gate 1 Parameters
    gate1_width_ms: float = 0.2          # Default 0.2 ms
    
    # Gate 2 Windowed Parameters
    gate2_width_ms: float = 0.2
    gate2_delay_ms: float = 1.0          # Initial delay relative to Gate 1 (0 to 100 ms)
    
    # Gate 2 Sweep Parameters
    sweep_start_delay_ms: float = 0.0    # Initial delay for sweep
    sweep_stop_delay_ms: float = 100.0   # Final delay for sweep
    sweep_step_ms: float = 0.5           # Time step parameter
    sweep_dwell_count: int = 1           # Dwell N triggers per delay step
    
    # Hardware Configuration (NI-6341)
    device_name: str = "Dev1"
    external_trigger_terminal: str = "/Dev1/PFI0"
    gate1_counter: str = "ctr0"          # Output pin default PFI12
    delay_counter: str = "ctr2"          # Delay-stage output pin default PFI14
    gate2_counter: str = "ctr1"          # Gate 2 output pin default PFI13

    def validate(self) -> tuple[bool, str]:
        """Validate parameter boundaries and timing constraints."""
        if self.gate1_width_ms <= 0:
            return False, "Gate 1 pulse width must be greater than 0 ms."
            
        if self.gate2_width_ms <= 0:
            return False, "Gate 2 pulse width must be greater than 0 ms."
            
        if self.scan_time_ms <= 0:
            return False, "Scan time must be greater than 0 ms."
            
        if self.mode == OperationalMode.WINDOWED:
            if self.gate2_delay_ms < 0 or self.gate2_delay_ms > self.scan_time_ms:
                return False, f"Gate 2 delay must be between 0 and {self.scan_time_ms} ms."
            if (self.gate2_delay_ms + self.gate2_width_ms) > self.scan_time_ms:
                return False, f"Gate 2 pulse end ({self.gate2_delay_ms + self.gate2_width_ms:.2f} ms) exceeds scan window ({self.scan_time_ms} ms)."
        else: # SWEEP mode
            if self.sweep_start_delay_ms < 0 or self.sweep_start_delay_ms > self.scan_time_ms:
                return False, f"Sweep start delay must be between 0 and {self.scan_time_ms} ms."
            if self.sweep_stop_delay_ms < self.sweep_start_delay_ms or self.sweep_stop_delay_ms > self.scan_time_ms:
                return False, f"Sweep stop delay must be between start delay ({self.sweep_start_delay_ms} ms) and {self.scan_time_ms} ms."
            if self.sweep_step_ms <= 0:
                return False, "Sweep time step must be greater than 0 ms."
            if self.sweep_dwell_count < 1:
                return False, "Sweep dwell count must be at least 1 trigger per step."
                
        return True, "Valid configuration"

    def get_sweep_delays(self) -> np.ndarray:
        """Generate the array of delay values (in ms) for the sweep sequence."""
        if self.sweep_step_ms <= 0 or self.sweep_start_delay_ms >= self.sweep_stop_delay_ms:
            return np.array([self.sweep_start_delay_ms])
        delays = np.arange(
            self.sweep_start_delay_ms,
            self.sweep_stop_delay_ms + (self.sweep_step_ms * 0.5), # include end point
            self.sweep_step_ms
        )
        return np.clip(delays, 0.0, self.scan_time_ms)

    def total_sweep_steps(self) -> int:
        """Calculate total delay steps in the sweep."""
        return len(self.get_sweep_delays())
