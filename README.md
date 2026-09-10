# 2-Gate IMS Control System

This software is used to interface a two-gate ion mobility spectrometry (IMS) system with an external instrument such as a mass spectrometer or other acquisition device that requires a start-scan pulse.

It provides a simple Windows desktop interface for configuring the gate timing and triggering behavior of the IMS hardware, while generating the timing signals needed to coordinate with an external acquisition system.

The application is intended for operators who need to:

- set the IMS gate timing for a measurement
- trigger the system from an external signal
- define a windowed or swept Gate 2 delay
- coordinate an IMS scan with an external device start pulse
- monitor the trigger count and system state in real time

---

## What this software does

The system controls the timing relationship between the IMS gate pulses and an external instrument trigger.

In practical use, this allows a two-gate IMS system to operate as part of a larger experiment in which the IMS scan must be synchronized with a downstream device such as a mass spectrometer. The external device can trigger the IMS acquisition, or the IMS system can provide the signal that tells the external system when to begin a scan.

This interface is designed to make that timing setup straightforward and repeatable without needing to manually configure low-level DAQ timing during an experiment.

---

## Use cases

This application is intended for:

- IMS acquisition timing setup
- synchronization between IMS and mass spectrometric acquisition
- external triggering of IMS scans
- windowed gate timing adjustments
- sweep-based delay scans across multiple gate delays

---

## Installation

### Requirements

Before running the software, install:

- Python 3.10 or newer
- NI DAQmx drivers if using real hardware
- A Windows desktop environment

### Install dependencies

From the project root, run:

```powershell
python -m pip install -r requirements.txt
```

The required packages are listed in `requirements.txt` and include:

- PyQt6
- nidaqmx
- pyqtgraph
- numpy

### Recommended startup method

A launcher script is included at `run_app.bat`.

This script will:

1. create a local virtual environment if needed,
2. install the dependencies from `requirements.txt`,
3. launch the application immediately.

---

## Basic operation

When the program opens, the user can configure the IMS timing behavior and select the operating mode:

- Windowed mode: a fixed Gate 2 delay for a single scan window
- Sweep mode: automatically steps through a series of delay values across a range

The user can also select whether to operate with:

- real NI DAQ hardware, or
- simulation mode for testing and setup without hardware

The interface includes live status information and a pulse timing preview so the operator can confirm that the timing is aligned before starting an experiment.

---

## External trigger and synchronization

The software is designed to work with external trigger hardware and timing signals. For an external-instrument workflow, this means the IMS system can be aligned with a device such as a mass spectrometer using a shared trigger or scan start pulse.

Typical use is:

- external hardware tells the IMS system when to begin a scan,
- the IMS gate timing is configured for the experiment,
- the trigger count and status are monitored in the GUI,
- the external device is synchronized with the IMS timing sequence.

This is the purpose of the application: to provide a stable control interface for a two-gate IMS setup that must integrate with another system.

---

## Notes for users

- Use the simulation mode when checking the interface or when no DAQ hardware is available.
- Install the NI DAQmx drivers before using real hardware.
- Validate the timing values before starting a run.
- Keep the external trigger wiring and scan timing aligned with the experiment requirements.

---

## Support and troubleshooting

If the software fails to start:

- confirm Python is installed,
- confirm the dependencies are installed,
- confirm NI DAQmx is installed if using real hardware,
- run the batch launcher to ensure the environment is created properly.

If your system is running without hardware, the software can still be used in simulation mode for setup and verification.

---

## Summary

This application is a user-facing control interface for running a two-gate IMS system in synchronization with an external device, such as a mass spectrometer, using a start-scan pulse and configurable gate timing. It is designed to make setup, monitoring, and external synchronization straightforward and reliable.

.venv\Scripts\python.exe -m pytest tests/test_windowed_trigger_debounce.py -q
```

This ensures the controller does not incorrectly count duplicate callback edges as multiple external triggers.

---

## Important Notes for Use

- Use Mock DAQ for development unless real NI hardware testing is specifically required.
- Keep hardware-specific behavior inside the DAQ controller implementation.
- Validate configuration before starting an acquisition.
- Stop sessions before replacing or reconfiguring tasks.
- Keep Qt GUI updates on signal/callback paths rather than blocking hardware code in widgets.

---

## Example Usage

1. Launch the application.
2. Choose the appropriate DAQ driver (Mock DAQ or NI-6341).
3. Select Windowed or Sweep mode.
4. Set the timing values.
5. Validate the configuration.
6. Start the session.
7. Monitor trigger count and timing preview.

---

## Summary

This software provides control, monitoring, and live pulse visualization for a two-gate IMS system. It bridges experimental timing configuration to actual NI DAQmx hardware while keeping a simulation path available for testing and development. The software is especially useful for timing-critical gating experiments where precise delay and trigger relationships matter.
