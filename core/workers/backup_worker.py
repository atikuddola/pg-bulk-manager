from PySide6.QtCore import QObject, Signal, QRunnable
from PySide6.QtCore import QProcess
import os


class BackupSignals(QObject):
    progress = Signal(str, int)
    finished = Signal(str)
    error = Signal(str, str)
    cancelled = Signal(str)


class BackupWorker(QRunnable):
    def __init__(self, server, dbname, output_folder):
        super().__init__()
        self.server = server
        self.dbname = dbname
        self.output_folder = output_folder
        self.signals = BackupSignals()
        self.process = None
        self._cancelled = False

    def run(self):
        output_path = os.path.join(self.output_folder, self.dbname)

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
            "-F", "d",          # directory format
            "-j", "4",          # parallel jobs
            "-d", self.dbname,
            "-f", output_path
        ]

        self.process.start("pg_dump", args)
        self.process.waitForFinished(-1)

        if self._cancelled:
            self.signals.cancelled.emit(self.dbname)
            return

        if self.process.exitCode() != 0:
            error = self.process.readAllStandardError().data().decode()
            self.signals.error.emit(self.dbname, error)
        else:
            self.signals.progress.emit(self.dbname, 100)
            self.signals.finished.emit(self.dbname)

    def cancel(self):
        self._cancelled = True
        if self.process:
            self.process.kill()