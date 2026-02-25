from PySide6.QtCore import QObject, Signal, QRunnable
from PySide6.QtCore import QProcess
import os


class RestoreSignals(QObject):
    progress = Signal(str, int)
    finished = Signal(str)
    error = Signal(str, str)
    cancelled = Signal(str)


class RestoreWorker(QRunnable):
    def __init__(self, server, backup_path):
        super().__init__()
        self.server = server
        self.backup_path = backup_path
        self.signals = RestoreSignals()
        self.process = None
        self._cancelled = False

    def run(self):
        self.process = QProcess()

        env = os.environ.copy()
        env["PGPASSWORD"] = self.server["password"]

        process_env = self.process.processEnvironment()
        for k, v in env.items():
            process_env.insert(k, v)
        self.process.setProcessEnvironment(process_env)

        args = [
            "-h", self.server["host"],
            "-p", str(self.server["port"]),
            "-U", self.server["user"],
            "-d", "postgres",
            self.backup_path
        ]

        self.process.start("pg_restore", args)
        self.process.waitForFinished(-1)

        if self._cancelled:
            self.signals.cancelled.emit(self.backup_path)
            return

        if self.process.exitCode() != 0:
            error = self.process.readAllStandardError().data().decode()
            self.signals.error.emit(self.backup_path, error)
        else:
            self.signals.progress.emit(self.backup_path, 100)
            self.signals.finished.emit(self.backup_path)

    def cancel(self):
        self._cancelled = True
        if self.process:
            self.process.kill()