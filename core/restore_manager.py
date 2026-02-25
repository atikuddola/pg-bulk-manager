import subprocess
import os


class RestoreManager:

    @staticmethod
    def restore_backups(self):
        if not self.current_server:
            QMessageBox.warning(self, "Error", "Connect to target server first.")
            return

        files, _ = QFileDialog.getOpenFileNames(
            self, "Select Backup Files", "", "Backup Files (*.backup)"
        )

        if not files:
            return

        # Get selected databases (checkbox checked)
        selected_dbs = [
            self.db_list.item(i).text()
            for i in range(self.db_list.count())
            if self.db_list.item(i).checkState() == Qt.Checked
        ]

        errors = []

        # ------------------------------------------
        # 1v1 Restore Mode
        # ------------------------------------------
        if len(files) == 1 and len(selected_dbs) == 1:
            backup_file = files[0]
            target_db = selected_dbs[0]

            try:
                RestoreManager.restore_into_existing_db(
                    self.current_server,
                    backup_file,
                    target_db
                )
            except Exception as e:
                errors.append(str(e))

        # ------------------------------------------
        # Bulk Restore Mode (Auto-create)
        # ------------------------------------------
        else:
            for file in files:
                try:
                    RestoreManager.restore_backup(
                        self.current_server,
                        file
                    )
                except Exception as e:
                    errors.append(f"{file}: {str(e)}")

        if errors:
            QMessageBox.warning(self, "Restore Completed With Errors", "\n".join(errors))
        else:
            QMessageBox.information(self, "Restore Completed", "Restore operation finished successfully.")


    @staticmethod
    def restore_into_existing_db(server, backup_file, target_db):

        env = os.environ.copy()
        env["PGPASSWORD"] = server["password"]

        restore_command = [
            "pg_restore",
            "-h", server["host"],
            "-p", str(server["port"]),
            "-U", server["user"],
            "-d", target_db,
            backup_file
        ]

        result = subprocess.run(
            restore_command,
            env=env,
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            raise Exception(result.stderr)

        return target_db