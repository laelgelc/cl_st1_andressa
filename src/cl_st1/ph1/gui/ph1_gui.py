# Python
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from PySide6 import QtCore, QtWidgets

from cl_st1.ph1.collect_service import collect


def _make_safe_subdir(name: str) -> str:
    cleaned: list[str] = []
    for ch in name.strip():
        if ch.isalnum() or ch in ("-", "_", "."):
            cleaned.append(ch)
        else:
            cleaned.append("_")
    return "".join(cleaned).strip("_") or "run"


def _subreddits_label(subreddits: list[str], max_len: int = 64) -> str:
    joined = "+".join(subreddits)
    safe = _make_safe_subdir(joined)
    if len(safe) <= max_len:
        return safe
    return safe[: max_len - len("_etc")] + "_etc"


def _default_run_subdir(*, listing: str, limit: int, subreddits: list[str]) -> str:
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    sr = _subreddits_label(subreddits)
    return _make_safe_subdir(f"{listing}_{limit}_{sr}_{ts}")


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

            collect(
                progress=p,
                counts=c,
                should_cancel=lambda: self._stop,
                **self._params,
            )

            # Always emit finished so UI can clean up the thread.
            if self._stop:
                self.progress.emit("Collection cancelled.")
                self.finished.emit(False)
            else:
                self.finished.emit(True)

        except Exception as e:
            self.error.emit(str(e))
            self.finished.emit(False)

    def cancel(self):
        self._stop = True  # checked by collect_service via should_cancel()


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Phase 1 — Reddit Data Collection (listing + limit)")
        self._setup_ui()
        self._thread: Optional[QtCore.QThread] = None
        self._worker: Optional[CollectorWorker] = None

    def _setup_ui(self):
        w = QtWidgets.QWidget()
        layout = QtWidgets.QFormLayout()

        self.subreddits = QtWidgets.QLineEdit("loneliness")

        self.listing = QtWidgets.QComboBox()
        self.listing.addItems(["new", "top"])

        self.per_limit = QtWidgets.QSpinBox()
        self.per_limit.setRange(1, 100000)
        self.per_limit.setValue(1000)

        self.include_comments = QtWidgets.QCheckBox()
        self.include_comments.setChecked(False)

        self.comments_limit = QtWidgets.QSpinBox()
        self.comments_limit.setRange(0, 10000)
        self.comments_limit.setValue(300)

        # Output directory configuration (base + optional run subdir)
        self.out_dir_base = QtWidgets.QLineEdit("data/ph1")
        self.out_dir_base.setReadOnly(False)

        self.run_subdir = QtWidgets.QLineEdit("")
        self.run_subdir.setPlaceholderText("Optional (leave blank for auto name)")

        self.resolved_out_dir = QtWidgets.QLineEdit("")
        self.resolved_out_dir.setReadOnly(True)

        layout.addRow("Subreddits (comma-separated)", self.subreddits)
        layout.addRow("Listing", self.listing)
        layout.addRow("Limit per subreddit (N)", self.per_limit)
        layout.addRow("Include comments", self.include_comments)
        layout.addRow("Comments limit per post", self.comments_limit)
        layout.addRow("Output base dir", self.out_dir_base)
        layout.addRow("Run subdir", self.run_subdir)
        layout.addRow("Resolved output dir", self.resolved_out_dir)

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

        # Keep resolved output dir in sync
        self.subreddits.textChanged.connect(self._sync_resolved_out_dir)
        self.listing.currentTextChanged.connect(self._sync_resolved_out_dir)
        self.per_limit.valueChanged.connect(self._sync_resolved_out_dir)
        self.out_dir_base.textChanged.connect(self._sync_resolved_out_dir)
        self.run_subdir.textChanged.connect(self._sync_resolved_out_dir)

        self._sync_resolved_out_dir()

    def _sync_resolved_out_dir(self):
        subs = [s.strip() for s in self.subreddits.text().split(",") if s.strip()]
        listing = self.listing.currentText()
        limit = int(self.per_limit.value())
        base = Path(self.out_dir_base.text().strip() or "data/ph1")
        run_subdir = self.run_subdir.text().strip()

        if not subs:
            self.resolved_out_dir.setText("")
            return

        if run_subdir:
            out_dir = base / run_subdir
        else:
            out_dir = base / _default_run_subdir(listing=listing, limit=limit, subreddits=subs)

        self.resolved_out_dir.setText(str(out_dir))

    def append_log(self, msg: str):
        self.log.appendPlainText(msg)

    def start_run(self):
        subs = [s.strip() for s in self.subreddits.text().split(",") if s.strip()]
        if not subs:
            QtWidgets.QMessageBox.warning(self, "Input error", "Please provide at least one subreddit.")
            return

        listing = self.listing.currentText()
        limit = int(self.per_limit.value())

        out_dir = self.resolved_out_dir.text().strip()
        if not out_dir:
            QtWidgets.QMessageBox.warning(self, "Input error", "Output directory could not be resolved.")
            return

        params = dict(
            subreddits=subs,
            out_dir=out_dir,
            listing=listing,
            per_subreddit_limit=limit,
            include_comments=bool(self.include_comments.isChecked()),
            comments_limit_per_post=int(self.comments_limit.value()),
        )

        self.start_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        self.append_log(f"Starting collection → {out_dir}")
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

    @QtCore.Slot(int, int)
    def update_counts(self, posts: int, comments: int):
        self.posts_lbl.setText(f"Posts: {posts}")
        self.comments_lbl.setText(f"Comments: {comments}")

    @QtCore.Slot(str)
    def on_error(self, msg: str):
        self.append_log(f"Error: {msg}")

    @QtCore.Slot(bool)
    def on_finished(self, ok: bool):
        self.append_log("Finished." if ok else "Finished with errors or cancellation.")
        self.progress.setRange(0, 1)
        self.start_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        if self._thread:
            self._thread.quit()
            self._thread.wait()


def main():
    app = QtWidgets.QApplication([])
    win = MainWindow()
    win.resize(760, 640)
    win.show()
    app.exec()


if __name__ == "__main__":
    main()