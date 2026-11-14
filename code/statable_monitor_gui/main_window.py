"""StaTable Monitor GUI main window.

Flow:
  Simulator (default) or real COM -> Connect -> LIST -> Poll 200ms
  -> Live table updates -> Start Log (psblog) -> auto-stop at N samples
  -> session.psblog ready for PowerSimBuilder.
"""
import os
import sys
import time
from datetime import datetime
from pathlib import Path

_CODE_DIR = Path(__file__).resolve().parent.parent
if str(_CODE_DIR) not in sys.path:
    sys.path.insert(0, str(_CODE_DIR))

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QComboBox, QCheckBox,
    QTableWidget, QTableWidgetItem, QFileDialog, QMessageBox,
    QGroupBox, QListWidget, QListWidgetItem, QSpinBox,
    QHeaderView,
)

from statable_monitor import StaTableMonitor
from statable_monitor.psblog_logger import PStaBlogLogger, LogOptions

try:
    from .simulator import SimulatedSerial
except ImportError:
    from statable_monitor_gui.simulator import SimulatedSerial


DEFAULT_PERIOD_MS = 200


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("StaTable Monitor GUI v0.1.0")
        self.resize(900, 600)

        self.monitor = None
        self.logger = None
        self.simulator = None
        self.selected = []
        self.latest = {}
        self._registry = []
        self._id_to_name = {}
        self._name_to_id = {}
        self._var_info = {}
        self.t0 = 0.0
        self.sample_count = 0
        self.log_started_at = None

        self.timer = QTimer(self)
        self.timer.setInterval(DEFAULT_PERIOD_MS)
        self.timer.timeout.connect(self._on_tick)

        self._build_ui()
        self._set_connected_state(False)
        self._refresh_ports()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------
    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)

        # ---- Connection group ----
        conn_box = QGroupBox("Connection")
        conn_layout = QHBoxLayout(conn_box)

        self.sim_check = QCheckBox("Simulator")
        self.sim_check.setChecked(True)
        self.sim_check.toggled.connect(self._on_sim_toggled)
        conn_layout.addWidget(self.sim_check)

        conn_layout.addWidget(QLabel("Port:"))
        self.port_combo = QComboBox()
        self.port_combo.setEditable(True)
        self.port_combo.setMinimumWidth(200)
        conn_layout.addWidget(self.port_combo)

        self.port_refresh_btn = QPushButton("R")
        self.port_refresh_btn.setToolTip("Rescan COM ports")
        self.port_refresh_btn.setMaximumWidth(32)
        self.port_refresh_btn.clicked.connect(self._refresh_ports)
        conn_layout.addWidget(self.port_refresh_btn)

        conn_layout.addWidget(QLabel("Baud:"))
        self.baud_combo = QComboBox()
        self.baud_combo.addItems(["9600", "115200", "230400", "460800"])
        self.baud_combo.setCurrentText("115200")
        conn_layout.addWidget(self.baud_combo)

        self.connect_btn = QPushButton("Connect")
        self.connect_btn.clicked.connect(self._on_connect)
        conn_layout.addWidget(self.connect_btn)

        self.status_label = QLabel("Disconnected")
        conn_layout.addWidget(self.status_label)
        conn_layout.addStretch()

        root.addWidget(conn_box)

        # ---- Middle: variables + live table ----
        mid = QHBoxLayout()

        # Left: variables list
        var_box = QGroupBox("Variables (LIST)")
        var_layout = QVBoxLayout(var_box)
        self.var_list = QListWidget()
        var_layout.addWidget(self.var_list)

        refresh_btn = QPushButton("Refresh LIST")
        refresh_btn.clicked.connect(self._on_refresh_list)
        var_layout.addWidget(refresh_btn)

        sel_all_btn = QPushButton("Select all")
        sel_all_btn.clicked.connect(self._select_all_vars)
        var_layout.addWidget(sel_all_btn)

        mid.addWidget(var_box, 1)

        # Right: live values table
        live_box = QGroupBox("Live values")
        live_layout = QVBoxLayout(live_box)
        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Variable", "Value", "Updated"])
        self.table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeToContents)
        live_layout.addWidget(self.table)

        self.sample_label = QLabel("Samples: 0")
        live_layout.addWidget(self.sample_label)

        mid.addWidget(live_box, 2)
        root.addLayout(mid, 1)

        # ---- Logging group ----
        log_box = QGroupBox("psblog Logging")
        log_layout = QHBoxLayout(log_box)

        log_layout.addWidget(QLabel("Period (ms):"))
        self.period_spin = QSpinBox()
        self.period_spin.setRange(100, 60000)
        self.period_spin.setValue(DEFAULT_PERIOD_MS)
        self.period_spin.setSingleStep(100)
        log_layout.addWidget(self.period_spin)

        log_layout.addWidget(QLabel("Max samples:"))
        self.max_spin = QSpinBox()
        self.max_spin.setRange(10, 100000)
        self.max_spin.setValue(100)
        log_layout.addWidget(self.max_spin)

        self.start_log_btn = QPushButton("Start Log...")
        self.start_log_btn.clicked.connect(self._on_start_log)
        log_layout.addWidget(self.start_log_btn)

        self.stop_log_btn = QPushButton("Stop Log")
        self.stop_log_btn.clicked.connect(self._on_stop_log)
        log_layout.addWidget(self.stop_log_btn)

        self.log_label = QLabel("Not logging")
        log_layout.addWidget(self.log_label)
        log_layout.addStretch()

        root.addWidget(log_box)

        self._on_sim_toggled(True)

    # ------------------------------------------------------------------
    # Connection
    # ------------------------------------------------------------------
    def _refresh_ports(self):
        """Enumerate actual COM ports via pyserial."""
        current = self._current_port()
        self.port_combo.clear()
        try:
            from serial.tools import list_ports
            ports = [(p.device, p.description) for p in list_ports.comports()]
        except ImportError:
            ports = []
        if not ports:
            self.port_combo.addItem("(no COM ports - use Simulator)", "")
        else:
            for device, desc in ports:
                self.port_combo.addItem(f"{device}  ({desc})", device)
            for i in range(self.port_combo.count()):
                if self.port_combo.itemData(i) == current:
                    self.port_combo.setCurrentIndex(i)
                    break

    def _current_port(self):
        data = self.port_combo.currentData()
        if data:
            return str(data)
        text = self.port_combo.currentText().strip()
        if not text or text.startswith("("):
            return ""
        return text.split()[0]

    def _on_sim_toggled(self, enabled):
        self.port_combo.setEnabled(not enabled)
        self.port_refresh_btn.setEnabled(not enabled)
        self.baud_combo.setEnabled(not enabled)

    def _on_connect(self):
        if self.monitor is not None:
            self._on_disconnect()
            return

        try:
            if self.sim_check.isChecked():
                self.simulator = SimulatedSerial()
                factory = lambda **kw: self.simulator
                self.monitor = StaTableMonitor(serial_factory=factory)
                port = "SIM"
                baud = 115200
            else:
                self.monitor = StaTableMonitor()
                port = self._current_port()
                if not port:
                    raise ValueError(
                        "No COM port selected. Use Simulator or select a port.")
                baud = int(self.baud_combo.currentText())

            self.monitor.connect(port, baudrate=baud)
            self.status_label.setText(f"Connected: {port}@{baud}")
            self.connect_btn.setText("Disconnect")
            self._set_connected_state(True)
            self.t0 = time.monotonic()

            # Auto-refresh LIST (no XML; names come from LIST)
            self._on_refresh_list()
        except Exception as e:
            QMessageBox.critical(self, "Connect failed", str(e))
            self.monitor = None
            self.simulator = None
            self.connect_btn.setText("Connect")
            self.status_label.setText("Disconnected")
            self._set_connected_state(False)
            self.connect_btn.setText("Connect")
            self.status_label.setText("Disconnected")
            self._set_connected_state(False)

    def _on_disconnect(self):
        self._on_stop_log()
        self.timer.stop()
        try:
            if self.monitor:
                self.monitor.close()
        except Exception:
            pass
        self.monitor = None
        self.simulator = None
        self.status_label.setText("Disconnected")
        self.connect_btn.setText("Connect")
        self._set_connected_state(False)

    def _set_connected_state(self, connected):
        self.start_log_btn.setEnabled(connected)
        self.stop_log_btn.setEnabled(False)

    # ------------------------------------------------------------------
    # Variable list
    # ------------------------------------------------------------------
    def _on_refresh_list(self):
        if not self.monitor:
            return
        try:
            info = self.monitor.list_variables()
        except Exception as e:
            QMessageBox.warning(self, "LIST failed", str(e))
            return

        variables = getattr(info, "variables", info)
        try:
            self._registry = list(variables)
        except TypeError:
            QMessageBox.warning(
                self, "LIST failed",
                f"Unexpected type: {type(info).__name__}")
            return

        self._id_to_name = {v.id: v.name for v in self._registry}
        self._name_to_id = {v.name: v.id for v in self._registry}
        self._var_info = {v.id: v for v in self._registry}

        self.var_list.clear()
        for v in self._registry:
            item = QListWidgetItem(f"{v.name}  ({v.c_type})")
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Checked)
            item.setData(Qt.UserRole, v.name)
            self.var_list.addItem(item)

        self._rebuild_table()

    def _select_all_vars(self):
        for i in range(self.var_list.count()):
            self.var_list.item(i).setCheckState(Qt.Checked)
        self._rebuild_table()

    def _selected_names(self):
        names = []
        for i in range(self.var_list.count()):
            item = self.var_list.item(i)
            if item.checkState() == Qt.Checked:
                names.append(item.data(Qt.UserRole))
        return names

    def _rebuild_table(self):
        names = self._selected_names()
        self.table.setRowCount(len(names))
        for row, name in enumerate(names):
            self.table.setItem(row, 0, QTableWidgetItem(name))
            self.table.setItem(row, 1, QTableWidgetItem(""))
            self.table.setItem(row, 2, QTableWidgetItem(""))

    # ------------------------------------------------------------------
    # Polling tick
    # ------------------------------------------------------------------
    def _on_tick(self):
        if not self.monitor:
            return
        names = self._selected_names()
        if not names:
            return
        try:
            raw = self.monitor.get_many(names)
        except Exception as e:
            self.status_label.setText(f"Polling error: {e}")
            return

        vals = {}
        if isinstance(raw, dict):
            for k, v in raw.items():
                if isinstance(k, int):
                    name = self._id_to_name.get(k, str(k))
                    vals[name] = v
                else:
                    vals[k] = v
        now = time.monotonic()

        # Update internal state + table (use log-relative time if logging)
        if self.logger is not None and self.log_started_at is not None:
            t_rel = now - self.log_started_at
        else:
            t_rel = now - self.t0
        for row, name in enumerate(names):
            v = vals.get(name, "")
            self.latest[name] = v
            self.table.setItem(row, 1, QTableWidgetItem(str(v)))
            self.table.setItem(
                row, 2,
                QTableWidgetItem(f"{t_rel:.2f}s"))

        # Write to psblog as one batched Data line per sample
        if self.logger is not None and self.log_started_at is not None:
            t_log = now - self.log_started_at
            try:
                self.logger.write_many(vals, t_log)
            except Exception:
                pass
            self.sample_count += 1
            self._update_sample_label()
            max_n = self.max_spin.value()
            if self.sample_count >= max_n:
                self._on_stop_log()

    @staticmethod
    def _normalize_get_many(raw, names):
        """Convert get_many return value to {name: value}."""
        if raw is None:
            return {}
        if isinstance(raw, dict):
            out = {}
            for k, v in raw.items():
                if isinstance(v, dict):
                    out[k] = v.get("value", v)
                else:
                    out[k] = v
            return out
        if isinstance(raw, (list, tuple)):
            if all(isinstance(x, tuple) and len(x) == 2 for x in raw):
                return dict(raw)
            if len(raw) == len(names):
                return dict(zip(names, raw))
        return {}

    def _update_sample_label(self):
        elapsed = ""
        if self.log_started_at is not None:
            dur = time.monotonic() - self.log_started_at
            elapsed = f"  Elapsed: {dur:.1f}s"
        self.sample_label.setText(
            f"Samples: {self.sample_count} / "
            f"{self.max_spin.value()}{elapsed}")

    # ------------------------------------------------------------------
    # Logging
    # ------------------------------------------------------------------
    def _on_start_log(self):
        if not self.monitor:
            return
        names = self._selected_names()
        if not names:
            QMessageBox.information(
                self, "No variables",
                "Please select at least one variable.")
            return

        # Default file name: session_YYYYmmdd_HHMMSS.psblog
        default_name = f"session_{datetime.now():%Y%m%d_%H%M%S}.psblog"
        path, _ = QFileDialog.getSaveFileName(
            self, "Save psblog",
            str(Path.cwd() / default_name),
            "psblog files (*.psblog)")
        if not path:
            return

        if not self._registry:
            QMessageBox.warning(
                self, "No registry",
                "Please click Refresh LIST first.")
            return

        info = {}
        for v in self._registry:
            info[v.name] = {
                "name": v.name, "type": v.c_type,
                "unit": v.unit, "group": v.group,
                "description": v.description,
            }

        variables = [info[n] for n in names if n in info]

        try:
            self.logger = PStaBlogLogger(
                path=path,
                source=("SIM" if self.sim_check.isChecked()
                        else self._current_port() or "unknown"),
                firmware=f"StaTable v3.6.0",
                period_ms=self.period_spin.value(),
                variables=variables,
                options=LogOptions(),
            )
            self.logger.start()
        except Exception as e:
            QMessageBox.critical(self, "Log start failed", str(e))
            self.logger = None
            return

        self.sample_count = 0
        self.log_started_at = time.monotonic()
        # [v3.6] emit t=0 sample immediately (QTimer fires after 1 interval)
        self._on_tick()
        if self.sample_count < self.max_spin.value():
            self.timer.setInterval(self.period_spin.value())
            self.timer.start()
        self.start_log_btn.setEnabled(False)
        self.stop_log_btn.setEnabled(True)
        self.log_label.setText(f"Logging → {Path(path).name}")
        self._update_sample_label()

    def _on_stop_log(self):
        if self.logger is None:
            return
        self.timer.stop()
        try:
            self.logger.stop()
        except Exception as e:
            QMessageBox.warning(self, "Log stop warning", str(e))
        self.log_label.setText(
            f"Stopped ({self.sample_count} samples)")
        self.logger = None
        self.log_started_at = None
        self.start_log_btn.setEnabled(True)
        self.stop_log_btn.setEnabled(False)

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------
    def closeEvent(self, event):
        self._on_disconnect()
        super().closeEvent(event)


def main():
    # [v3.6] guard: pytest may leave QT_QPA_PLATFORM=offscreen in the
    # parent shell; clear it so the GUI renders on the visible desktop.
    if os.environ.get('QT_QPA_PLATFORM') == 'offscreen':
        del os.environ['QT_QPA_PLATFORM']
        sys.stderr.write('[monitor-gui] cleared QT_QPA_PLATFORM=offscreen\n')

    app = QApplication.instance() or QApplication(sys.argv)
    w = MainWindow()
    w.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
