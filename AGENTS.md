# Agent Guide

## Purpose

PyQt6 desktop control GUI for a two-gate ion mobility spectrometry (IMS) system. It previews TTL timing and drives either an NI-6341 DAQ or a software simulation.

## Runtime Flow

- `main.py` creates the `QApplication`, applies the dark theme, and opens `src.gui.main_window.MainWindow`.
- `MainWindow` owns the active `ScanConfig`, DAQ controller, configuration validation, start/stop lifecycle, live diagram updates, and sweep state.
- `ControlPanelWidget` converts UI controls into a `ScanConfig` and emits `config_changed`, `start_requested`, and `stop_requested`.
- `StatusPanelWidget` displays controller status, trigger metrics, sweep progress, and the event log.
- `PulseDiagramWidget` renders the trigger, Gate 1, and Gate 2 timing preview with pyqtgraph.

## Architecture

- `src/models/config.py`: `ScanConfig` dataclass, `OperationalMode`, validation, and sweep-delay generation. Timing values are milliseconds.
- `src/hardware/daq_interface.py`: `AbstractDAQController` contract and Qt signal bridge. Controllers expose `start_session`, `stop_session`, `update_gate2_delay`, `update_config`, and `trigger_software`.
- `src/hardware/mock_daq_controller.py`: hardware-free implementation. In Test Mode, a `QTimer` emits simulated triggers using `auto_trigger_period_ms`.
- `src/hardware/ni_daq_controller.py`: NI-DAQmx implementation. Gate 1 uses `ctr0`, the additional delay stage uses `ctr2`, and Gate 2 uses `ctr1`. Windowed and Sweep modes select different timing paths inside the controller. External-mode Gate 1 output events are forwarded to the GUI for sweep progression.
- `src/gui/styles.py`: application QSS theme.

## Modes

- **Windowed**: Gate 2 uses the `ctr2` delay stage and one `gate2_delay_ms`; in Test Mode the delay is applied as the delay-stage task's initial delay on each software restart.
- **Sweep**: `MainWindow` obtains `ScanConfig.get_sweep_delays()`, holds each delay for `sweep_dwell_count` triggers, then calls `update_gate2_delay`. The sweep stops automatically after the final step.
- **Test Mode** enables timer-generated trigger events at `auto_trigger_period_ms` (default 250 ms). The controller restarts the required finite tasks for each simulated pulse. Without it, Gate 1 arms on `external_trigger_terminal` (default `/Dev1/PFI0`).
- Sweep external callbacks are debounced over most of `scan_time_ms` so one hardware generation advances the GUI once.

## Development Rules

- Use Mock DAQ for development unless real NI hardware testing is specifically required.
- Keep hardware-specific behavior inside `NIDAQController`; preserve the abstract controller API so the mock remains usable.
- Validate `ScanConfig` before starting a session. Preserve millisecond units in the model/UI and convert to seconds only at the NI-DAQmx boundary.
- Stop sessions before replacing controllers or changing task configuration. `MainWindow.closeEvent` also stops the active session.
- Keep GUI updates on Qt signals/callbacks; do not put blocking DAQ work in widget code.

## Commands

From the repository root, install dependencies with `python -m pip install -r requirements.txt`, then run the GUI with `python main.py`. For a hardware-free smoke run, select `Mock DAQ (Simulation)` and enable `Test Mode (Auto Trigger)`. Check Python syntax with `python -m compileall main.py src`.

There are currently no automated tests in the repository. Changes affecting sweep progression, signal handling, or DAQ task setup should be manually checked in Mock DAQ mode and, when available, on NI hardware.

## Counter Routing and Wiring

The V1.0 controller uses three counters: `ctr0` for Gate 1, `ctr2` as the delayed timing stage, and `ctr1` for Gate 2. On an NI-6341/USB-6341-style X-Series device, the default counter output PFI terminals are typically `ctr0 -> PFI12`, `ctr1 -> PFI13`, `ctr2 -> PFI14`, and `ctr3 -> PFI15`; verify the exact device pinout before wiring.

Required signal routing is internal in DAQmx: Gate 1 (`ctr0InternalOutput`) triggers the delay stage (`ctr2`), and the delay stage (`ctr2InternalOutput`) triggers Gate 2 (`ctr1`). The external trigger remains `/Dev1/PFI0` into Gate 1. Connect the physical outputs as `PFI12` for Gate 1 and `PFI13` for Gate 2; `PFI14` is the optional exposed delay-stage output for probing, while the internal routes should be used for counter-to-counter triggering.
