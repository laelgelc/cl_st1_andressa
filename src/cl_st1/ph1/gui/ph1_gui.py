# Python
from __future__ import annotations

from typing import Optional

from PySide6 import QtCore, QtWidgets

from cl_st1.ph1.collect_service import collect


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
        self.after = QtWidgets.QLineEdit("")
        self.before = QtWidgets.QLineEdit("")
        self.sort = QtWidgets.QComboBox()
        self.sort.addItems(["new", "top"])
        self.include_comments = QtWidgets.QCheckBox()
        self.include_comments.setChecked(True)
        self.comments_limit = QtWidgets.QSpinBox()
        self.comments_limit.setRange(0, 10000)
        self.comments_limit.setValue(300)
        self.per_limit = QtWidgets.QSpinBox()
        self.per_limit.setRange(1, 100000)
        self.per_limit.setValue(1000)
        self.out_dir = QtWidgets.QLineEdit("data/ph1")
        self.out_dir.setReadOnly(True)

        layout.addRow("Subreddits (comma-separated)", self.subreddits)
        layout.addRow("After UTC (epoch seconds)", self.after)
        layout.addRow("Before UTC (epoch seconds, optional)", self.before)
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

    def append_log(self, msg: str):
        self.log.appendPlainText(msg)

    def start_run(self):
        subs = [s.strip() for s in self.subreddits.text().split(",") if s.strip()]
        if not subs:
            QtWidgets.QMessageBox.warning(self, "Input error", "Please provide at least one subreddit.")
            return
        try:
            after = int(self.after.text())
        except ValueError:
            QtWidgets.QMessageBox.warning(self, "Input error", "After UTC must be an integer epoch seconds.")
            return
        before_text = self.before.text().strip()
        before = int(before_text) if before_text else None

        params = dict(
            subreddits=subs,
            out_dir=self.out_dir.text(),
            sort=self.sort.currentText(),
            per_subreddit_limit=int(self.per_limit.value()),
            include_comments=bool(self.include_comments.isChecked()),
            comments_limit_per_post=int(self.comments_limit.value()),
            after_utc=after,
            before_utc=before,
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
    win.resize(700, 600)
    win.show()
    app.exec()