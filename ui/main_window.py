from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QListWidget, QFileDialog,
    QMessageBox, QCheckBox, QListWidgetItem,
    QSizePolicy, QInputDialog
)
from PySide6.QtCore import Qt
from core.server_manager import ServerManager
from core.backup_manager import BackupManager
from core.restore_manager import RestoreManager
from concurrent.futures import ThreadPoolExecutor, as_completed
from PySide6.QtCore import QThreadPool
from core.workers.backup_worker import BackupWorker
from core.workers.restore_worker import RestoreWorker


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.threadpool = QThreadPool()
        self.threadpool.setMaxThreadCount(3)
        self.active_workers = []

        self.setWindowTitle("Postgres Bulk Manager")
        self.setMinimumSize(900, 500)

        self.servers = ServerManager.load_servers()
        self.current_server = None

        self.init_ui()

    def init_ui(self):
        main_widget = QWidget()
        main_layout = QHBoxLayout()

        # -----------------------------
        # Left Side
        # -----------------------------
        left_layout = QVBoxLayout()

        self.select_all_cb = QCheckBox("Select All Databases")
        self.select_all_cb.stateChanged.connect(self.toggle_select_all)

        self.db_list = QListWidget()
        self.db_list.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.db_list.setAlternatingRowColors(True)

        left_layout.addWidget(self.select_all_cb)
        left_layout.addWidget(self.db_list)


        # -----------------------------
        # Right Side Buttons
        # -----------------------------
        btn_layout = QVBoxLayout()

        top_btn_layout = QHBoxLayout()

        self.connect_btn = QPushButton("Connect")
        self.refresh_btn = QPushButton("Refresh")

        top_btn_layout.addWidget(self.connect_btn)
        top_btn_layout.addWidget(self.refresh_btn)

        self.backup_btn = QPushButton("Backup Selected")
        self.restore_btn = QPushButton("Restore Backups")
        self.cancel_btn = QPushButton("Cancel All")

        btn_layout.addLayout(top_btn_layout)
        btn_layout.addWidget(self.backup_btn)
        btn_layout.addWidget(self.restore_btn)
        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addStretch()

        # -----------------------------
        # Combine Layouts
        # -----------------------------
        main_layout.addLayout(left_layout, stretch=2)
        main_layout.addLayout(btn_layout, stretch=1)

        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

        # -----------------------------
        # Connect Signals
        # -----------------------------
        self.connect_btn.clicked.connect(self.connect_server)
        self.refresh_btn.clicked.connect(self.refresh_databases)
        self.backup_btn.clicked.connect(self.backup_selected)
        self.restore_btn.clicked.connect(self.restore_backups)
        self.cancel_btn.clicked.connect(self.cancel_all)

    # ---------------------------------
    # Select All
    # ---------------------------------
    def toggle_select_all(self, state):
        for i in range(self.db_list.count()):
            item = self.db_list.item(i)
            item.setCheckState(Qt.Checked if state == Qt.Checked else Qt.Unchecked)


    def cancel_all(self):
        for worker in self.active_workers:
            worker.cancel()
        self.active_workers.clear()


    # ---------------------------------
    # Connect to Server (Select Only)
    # ---------------------------------
    def connect_server(self):
        if not self.servers:
            QMessageBox.warning(self, "Error", "No servers configured.")
            return

        server_names = [s["name"] for s in self.servers]

        server_name, ok = QInputDialog.getItem(
            self, "Select Server", "Server:", server_names, 0, False
        )

        if not ok or not server_name:
            return

        self.current_server = next(
            s for s in self.servers if s["name"] == server_name
        )

        self.load_databases()

    # ---------------------------------
    # Refresh Databases
    # ---------------------------------
    def refresh_databases(self):
        if not self.current_server:
            QMessageBox.warning(self, "Error", "Connect to a server first.")
            return

        self.load_databases()

    # ---------------------------------
    # Load Databases
    # ---------------------------------
    def load_databases(self):
        try:
            dbs = ServerManager.get_databases(self.current_server)
        except Exception as e:
            QMessageBox.critical(self, "Connection Error", str(e))
            return

        self.db_list.clear()

        for db in dbs:
            item = QListWidgetItem(db)
            item.setCheckState(Qt.Unchecked)
            self.db_list.addItem(item)

        self.select_all_cb.setChecked(False)

    # ---------------------------------
    # Backup
    # ---------------------------------
    def backup_selected(self):
        if not self.current_server:
            QMessageBox.warning(self, "Error", "Connect first.")
            return

        folder = QFileDialog.getExistingDirectory(self, "Select Backup Folder")
        if not folder:
            return

        for i in range(self.db_list.count()):
            item = self.db_list.item(i)

            if item.checkState() == Qt.Checked:
                dbname = item.text()

                worker = BackupWorker(self.current_server, dbname, folder)

                worker.signals.progress.connect(
                    lambda db, val, it=item: it.setText(f"{db} ({val}%)")
                )

                worker.signals.finished.connect(
                    lambda db: QMessageBox.information(self, "Done", f"{db} backup finished.")
                )

                worker.signals.error.connect(
                    lambda db, err: QMessageBox.warning(self, "Error", f"{db}: {err}")
                )

                self.threadpool.start(worker)
                self.active_workers.append(worker)


    def restore_backups(self):
        if not self.current_server:
            QMessageBox.warning(self, "Error", "Connect first.")
            return

        files, _ = QFileDialog.getOpenFileNames(
            self, "Select Backup Folders", ""
        )

        if not files:
            return

        for path in files:
            worker = RestoreWorker(self.current_server, path)

            worker.signals.finished.connect(
                lambda p: QMessageBox.information(self, "Restore Done", f"{p} restored.")
            )

            worker.signals.error.connect(
                lambda p, err: QMessageBox.warning(self, "Error", f"{p}: {err}")
            )

            self.threadpool.start(worker)
            self.active_workers.append(worker)