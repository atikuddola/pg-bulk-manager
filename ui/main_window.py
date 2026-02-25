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


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

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

        btn_layout.addLayout(top_btn_layout)
        btn_layout.addWidget(self.backup_btn)
        btn_layout.addWidget(self.restore_btn)
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

    # ---------------------------------
    # Select All
    # ---------------------------------
    def toggle_select_all(self, state):
        for i in range(self.db_list.count()):
            item = self.db_list.item(i)
            item.setCheckState(Qt.Checked if state == Qt.Checked else Qt.Unchecked)

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
            QMessageBox.warning(self, "Error", "Connect to server first.")
            return

        selected = [
            self.db_list.item(i).text()
            for i in range(self.db_list.count())
            if self.db_list.item(i).checkState() == Qt.Checked
        ]

        if not selected:
            QMessageBox.information(self, "No Selection", "No databases selected.")
            return

        folder = QFileDialog.getExistingDirectory(self, "Select Backup Folder")
        if not folder:
            return

        errors = []

        for db in selected:
            try:
                BackupManager.backup_database(self.current_server, db, folder)
            except Exception as e:
                errors.append(f"{db}: {str(e)}")

        if errors:
            QMessageBox.warning(self, "Backup Completed With Errors", "\n".join(errors))
        else:
            QMessageBox.information(self, "Backup Completed", "All selected databases backed up successfully.")

    # ---------------------------------
    # Restore
    # ---------------------------------
    def restore_backups(self):
        if not self.current_server:
            QMessageBox.warning(self, "Error", "Connect to target server first.")
            return

        files, _ = QFileDialog.getOpenFileNames(
            self, "Select Backup Files", "", "Backup Files (*.backup)"
        )

        if not files:
            return

        errors = []

        for file in files:
            try:
                RestoreManager.restore_backup(self.current_server, file)
            except Exception as e:
                errors.append(f"{file}: {str(e)}")

        if errors:
            QMessageBox.warning(self, "Restore Completed With Errors", "\n".join(errors))
        else:
            QMessageBox.information(self, "Restore Completed", "All backups restored successfully.")