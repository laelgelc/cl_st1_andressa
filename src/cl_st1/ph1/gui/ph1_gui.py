# Python
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from PySide6 import QtCore, QtWidgets

from cl_st1.ph1.collect_service import collect


def _epoch_utc(dt: datetime) -> int:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return int(dt.timestamp())


def _epoch_from_qdate_utc(d) -> int:
    # QDate -> UTC midnight at start of that day
    py = d.toPython()
    return _epoch_utc(datetime(py.year, py.month, py.day, tzinfo=timezone.utc))


class CollectorWorker(QtCore.QObject):
    progress = QtCore.Signal(str)
    counts = QtCore.Signal(int, int)
    finished = QtCore.Signal(bool)
    error = QtCore.Signal(str)

    def __init__(self, params: dict):
        super().__init__()
        self._params = params
        self._stop = False

    @QtCore.Slot()
    def run(self):
        try:
            def p(msg: str):
                if not self._stop:
                    self.progress.emit(msg)

            def c(posts: int, comments: int):
                if not self._stop:
                    self.counts.emit(posts, comments)

            collect(progress=p, counts=c, **self._params)
            if not self._stop:
                self.finished.emit(True)
        except Exception as e:
            self.error.emit(str(e))
            self.finished.emit(False)

    def cancel(self):
        self._stop = True  # checked between operations in collect()


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Phase 1 — Reddit Data Collection")
        self._setup_ui()
        self._thread: Optional[QtCore.QThread] = None
        self._worker: Optional[CollectorWorker] = None

    def _setup_ui(self):
        w = QtWidgets.QWidget()
        layout = QtWidgets.QFormLayout()

        self.subreddits = QtWidgets.QLineEdit("lonely,loneliness")

        # Time window mode: Year OR Date range (UTC)
        self.time_mode_year = QtWidgets.QRadioButton("Year (UTC)")
        self.time_mode_range = QtWidgets.QRadioButton("Date range (UTC)")
        self.time_mode_year.setChecked(True)

        mode_row = QtWidgets.QHBoxLayout()
        mode_row.addWidget(self.time_mode_year)
        mode_row.addWidget(self.time_mode_range)
        mode_row.addStretch(1)

        self.year = QtWidgets.QSpinBox()
        self.year.setRange(2005, 2100)
        self.year.setValue(datetime.now(timezone.utc).year)

        self.after_date = QtWidgets.QDateEdit()
        self.after_date.setCalendarPopup(True)
        self.after_date.setDisplayFormat("yyyy-MM-dd")
        self.after_date.setDate(QtCore.QDate.currentDate().addMonths(-1))

        self.before_date = QtWidgets.QDateEdit()
        self.before_date.setCalendarPopup(True)
        self.before_date.setDisplayFormat("yyyy-MM-dd")
        self.before_date.setDate(QtCore.QDate.currentDate())
        self.before_enabled = QtWidgets.QCheckBox("Use end date")
        self.before_enabled.setChecked(True)

        before_row = QtWidgets.QHBoxLayout()
        before_row.addWidget(self.before_date)
        before_row.addWidget(self.before_enabled)
        before_row.addStretch(1)

        # Resolved epoch (read-only, for transparency/provenance)
        self.after_epoch_lbl = QtWidgets.QLabel("—")
        self.before_epoch_lbl = QtWidgets.QLabel("—")

        self.sort = QtWidgets.QComboBox()
        self.sort.addItems(["new", "top"])

        self.include_comments = QtWidgets.QCheckBox()
        self.include_comments.setChecked(False)

        self.comments_limit = QtWidgets.QSpinBox()
        self.comments_limit.setRange(0, 10000)
        self.comments_limit.setValue(300)

        self.per_limit = QtWidgets.QSpinBox()
        self.per_limit.setRange(1, 100000)
        self.per_limit.setValue(1000)

        self.out_dir = QtWidgets.QLineEdit("data/ph1")
        self.out_dir.setReadOnly(True)

        layout.addRow("Subreddits (comma-separated)", self.subreddits)
        layout.addRow("Time window mode", mode_row)
        layout.addRow("Year", self.year)
        layout.addRow("After date (UTC)", self.after_date)
        layout.addRow("Before date (UTC)", before_row)
        layout.addRow("Resolved after_utc (epoch)", self.after_epoch_lbl)
        layout.addRow("Resolved before_utc (epoch)", self.before_epoch_lbl)
        layout.addRow("Sort", self.sort)
        layout.addRow("Include comments", self.include_comments)
        layout.addRow("Comments limit per post", self.comments_limit)
        layout.addRow("Per-subreddit limit", self.per_limit)
        layout.addRow("Output dir", self.out_dir)

        self.start_btn = QtWidgets.QPushButton("Start")
        self.cancel_btn = QtWidgets.QPushButton("Cancel")
        self.cancel_btn.setEnabled(False)
        btns = QtWidgets.QHBoxLayout()
        btns.addWidget(self.start_btn)
        btns.addWidget(self.cancel_btn)

        self.log = QtWidgets.QPlainTextEdit()
        self.log.setReadOnly(True)
        self.posts_lbl = QtWidgets.QLabel("Posts: 0")
        self.comments_lbl = QtWidgets.QLabel("Comments: 0")
        self.progress = QtWidgets.QProgressBar()
        self.progress.setRange(0, 0)  # indeterminate

        layout.addRow(btns)
        layout.addRow("Progress log", self.log)
        layout.addRow(self.posts_lbl, self.comments_lbl)
        layout.addRow(self.progress)

        w.setLayout(layout)
        self.setCentralWidget(w)

        self.start_btn.clicked.connect(self.start_run)
        self.cancel_btn.clicked.connect(self.cancel_run)

        # Keep epoch labels + enabled/disabled state in sync
        self.time_mode_year.toggled.connect(self._sync_time_controls)
        self.before_enabled.toggled.connect(self._sync_time_controls)
        self.year.valueChanged.connect(self._sync_time_controls)
        self.after_date.dateChanged.connect(self._sync_time_controls)
        self.before_date.dateChanged.connect(self._sync_time_controls)

        self._sync_time_controls()

    def _sync_time_controls(self):
        year_mode = self.time_mode_year.isChecked()

        self.year.setEnabled(year_mode)

        self.after_date.setEnabled(not year_mode)
        self.before_date.setEnabled((not year_mode) and self.before_enabled.isChecked())
        self.before_enabled.setEnabled(not year_mode)

        try:
            after_utc, before_utc = self._resolve_time_window_to_epoch()
            self.after_epoch_lbl.setText(str(after_utc))
            self.before_epoch_lbl.setText("" if before_utc is None else str(before_utc))
        except Exception:
            self.after_epoch_lbl.setText("—")
            self.before_epoch_lbl.setText("—")

    def _resolve_time_window_to_epoch(self) -> tuple[int, Optional[int]]:
        if self.time_mode_year.isChecked():
            y = int(self.year.value())
            start = _epoch_utc(datetime(y, 1, 1, tzinfo=timezone.utc))
            next_year = _epoch_utc(datetime(y + 1, 1, 1, tzinfo=timezone.utc))
            return start, next_year - 1

        after = _epoch_from_qdate_utc(self.after_date.date())

        if self.before_enabled.isChecked():
            # inclusive end-of-day: start_of_next_day - 1
            end_next_day = _epoch_from_qdate_utc(self.before_date.date().addDays(1))
            before = end_next_day - 1
        else:
            before = None

        if before is not None and before < after:
            raise ValueError("before must be >= after")
        return after, before

    def append_log(self, msg: str):
        self.log.appendPlainText(msg)

    def start_run(self):
        subs = [s.strip() for s in self.subreddits.text().split(",") if s.strip()]
        if not subs:
            QtWidgets.QMessageBox.warning(self, "Input error", "Please provide at least one subreddit.")
            return

        try:
            after_utc, before_utc = self._resolve_time_window_to_epoch()
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, "Input error", str(e))
            return

        params = dict(
            subreddits=subs,
            out_dir=self.out_dir.text(),
            sort=self.sort.currentText(),
            per_subreddit_limit=int(self.per_limit.value()),
            include_comments=bool(self.include_comments.isChecked()),
            comments_limit_per_post=int(self.comments_limit.value()),
            after_utc=int(after_utc),
            before_utc=None if before_utc is None else int(before_utc),
        )

        self.start_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        self.append_log("Starting collection...")
        self.progress.setRange(0, 0)

        self._thread = QtCore.QThread()
        self._worker = CollectorWorker(params)
        self._worker.moveToThread(self._thread)

        self._thread.started.connect(self._worker.run)
        self._worker.progress.connect(self.append_log)
        self._worker.counts.connect(self.update_counts)
        self._worker.error.connect(self.on_error)
        self._worker.finished.connect(self.on_finished)

        self._thread.start()

    def cancel_run(self):
        if self._worker:
            self._worker.cancel()
        self.append_log("Cancel requested.")

    @QtWidgets.Slot(int, int)
    def update_counts(self, posts: int, comments: int):
        self.posts_lbl.setText(f"Posts: {posts}")
        self.comments_lbl.setText(f"Comments: {comments}")

    @QtWidgets.Slot(str)
    def on_error(self, msg: str):
        self.append_log(f"Error: {msg}")

    @QtWidgets.Slot(bool)
    def on_finished(self, ok: bool):
        self.append_log("Finished." if ok else "Finished with errors.")
        self.progress.setRange(0, 1)
        self.start_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        if self._thread:
            self._thread.quit()
            self._thread.wait()


def main():
    app = QtWidgets.QApplication([])
    win = MainWindow()
    win.resize(760, 700)
    win.show()
    app.exec()