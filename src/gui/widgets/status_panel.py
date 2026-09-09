"""
Status Panel Widget displaying DAQ state, trigger metrics, and sweep progress.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel,
    QProgressBar, QTextEdit
)
from PyQt6.QtCore import Qt
from ...models.config import ScanConfig, OperationalMode


class StatusPanelWidget(QWidget):
    """Monitors system operation, hardware feedback, and sweep progress."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)

        # Status & Metrics Group
        grp_status = QGroupBox("System Status & Metrics")
        lay_status = QVBoxLayout(grp_status)

        # System State Badge
        state_layout = QHBoxLayout()
        state_layout.addWidget(QLabel("Hardware State:"))
        self.lbl_state = QLabel("STOPPED")
        self.lbl_state.setStyleSheet(
            "font-weight: bold; padding: 4px 12px; border-radius: 4px; "
            "background-color: #331111; color: #ff5555; border: 1px solid #ff5555;"
        )
        state_layout.addWidget(self.lbl_state)
        state_layout.addStretch()
        lay_status.addLayout(state_layout)

        # Metrics Readout Grid
        metrics_layout = QHBoxLayout()

        self.lbl_active_delay = QLabel("Gate 2 Delay: 0.00 ms")
        self.lbl_active_delay.setStyleSheet("font-size: 11pt; font-weight: bold; color: #00d2ff;")
        
        self.lbl_trigger_count = QLabel("Triggers: 0")
        self.lbl_trigger_count.setStyleSheet("font-size: 11pt; font-weight: bold; color: #ffcc00;")

        metrics_layout.addWidget(self.lbl_active_delay)
        metrics_layout.addSpacing(20)
        metrics_layout.addWidget(self.lbl_trigger_count)
        metrics_layout.addStretch()

        lay_status.addLayout(metrics_layout)

        # Sweep Progress Bar
        self.lbl_sweep_info = QLabel("Sweep Progress: N/A")
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)

        lay_status.addWidget(self.lbl_sweep_info)
        lay_status.addWidget(self.progress_bar)

        main_layout.addWidget(grp_status)

        # Console Log
        grp_log = QGroupBox("Event Log")
        lay_log = QVBoxLayout(grp_log)
        self.txt_log = QTextEdit()
        self.txt_log.setReadOnly(True)
        self.txt_log.setMaximumHeight(120)
        lay_log.addWidget(self.txt_log)

        main_layout.addWidget(grp_log)

    def set_system_state(self, state: str, running: bool, is_sweep: bool = False):
        self.lbl_state.setText(state.upper())
        if running:
            color = "#00ffcc" if is_sweep else "#00ff66"
            bg = "#003322"
        else:
            color = "#ff5555"
            bg = "#331111"
            
        self.lbl_state.setStyleSheet(
            f"font-weight: bold; padding: 4px 12px; border-radius: 4px; "
            f"background-color: {bg}; color: {color}; border: 1px solid {color};"
        )

    def update_metrics(self, active_delay_ms: float, trigger_count: int):
        self.lbl_active_delay.setText(f"Gate 2 Delay: {active_delay_ms:.2f} ms")
        self.lbl_trigger_count.setText(f"Triggers: {trigger_count}")

    def update_sweep_progress(self, current_step: int, total_steps: int, current_delay_ms: float):
        if total_steps <= 0:
            self.progress_bar.setValue(0)
            self.lbl_sweep_info.setText("Sweep Progress: N/A")
            return

        pct = int((current_step / total_steps) * 100)
        self.progress_bar.setValue(pct)
        self.lbl_sweep_info.setText(
            f"Sweep Step: {current_step} / {total_steps} ({pct}%) - Active Delay: {current_delay_ms:.2f} ms"
        )

    def reset_sweep_progress(self):
        self.progress_bar.setValue(0)
        self.lbl_sweep_info.setText("Sweep Progress: Ready")

    def log(self, message: str):
        self.txt_log.append(message)
