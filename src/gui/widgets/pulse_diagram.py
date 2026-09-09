"""
Pulse Diagram Widget for visual rendering of 2-Gate IMS TTL timing sequence.
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt
import pyqtgraph as pg
import numpy as np
from ...models.config import ScanConfig, OperationalMode


class PulseDiagramWidget(QWidget):
    """
    Renders live waveform timing diagram for:
    - Channel 0: External Trigger Input
    - Channel 1: Gate 1 TTL Pulse Output
    - Channel 2: Gate 2 TTL Pulse Output
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        # Pyqtgraph plot widget
        pg.setConfigOption('background', '#18181f')
        pg.setConfigOption('foreground', '#e0e0e0')
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setLabel('bottom', 'Time', units='ms')
        self.plot_widget.setLabel('left', 'TTL Channels')
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)
        self.plot_widget.setYRange(-0.5, 3.5)
        
        # Hide left axis ticks (custom Y offset labels)
        ay = self.plot_widget.getAxis('left')
        ay.setTicks([[(0, 'Trigger'), (1, 'Gate 1'), (2, 'Gate 2')]])

        layout.addWidget(self.plot_widget)

        # Plot curves
        self.curve_trig = self.plot_widget.plot(pen=pg.mkPen('#00ff66', width=2), name="External Trigger")
        self.curve_g1 = self.plot_widget.plot(pen=pg.mkPen('#ffcc00', width=2), name="Gate 1 Pulse")
        self.curve_g2 = self.plot_widget.plot(pen=pg.mkPen('#00d2ff', width=2), name="Gate 2 Pulse")

        # Shaded region / cursor line for Gate 2 Delay
        self.delay_line = pg.InfiniteLine(angle=90, pen=pg.mkPen('#00d2ff', width=1, style=Qt.PenStyle.DashLine))
        self.plot_widget.addItem(self.delay_line)

    def update_diagram(self, config: ScanConfig, active_delay_ms: float = None):
        """Re-draw TTL pulse waveforms based on current scan config."""
        scan_time = max(1.0, config.scan_time_ms)
        g1_width = config.gate1_width_ms
        g2_width = config.gate2_width_ms

        if active_delay_ms is not None:
            g2_delay = active_delay_ms
        elif config.mode == OperationalMode.WINDOWED:
            g2_delay = config.gate2_delay_ms
        else:
            g2_delay = config.sweep_start_delay_ms

        def pulse_waveform(start: float, width: float, baseline: float):
            end = min(scan_time, start + width)
            times = np.array([0.0, start, start, end, end, scan_time])
            levels = np.array([
                baseline,
                baseline,
                baseline + 0.8,
                baseline + 0.8,
                baseline,
                baseline,
            ])
            return times, levels

        # Explicit duplicate transition points create rectangular TTL pulses.
        trig_t, trig_y = pulse_waveform(0.0, 0.05, 0.0)
        g1_t, g1_y = pulse_waveform(0.0, g1_width, 1.0)
        g2_t, g2_y = pulse_waveform(g2_delay, g2_width, 2.0)

        self.curve_trig.setData(trig_t, trig_y)
        self.curve_g1.setData(g1_t, g1_y)
        self.curve_g2.setData(g2_t, g2_y)

        self.delay_line.setValue(g2_delay)
        self.plot_widget.setXRange(-0.5, scan_time * 1.05)
