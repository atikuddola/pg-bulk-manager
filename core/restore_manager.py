import subprocess
import os


class RestoreManager:

    @staticmethod
    def restore_backup(server, backup_file):
        """
        Restores backup and auto-creates DB using original name
        """
        env = os.environ.copy()
        env["PGPASSWORD"] = server["password"]

        restore_command = [
            "pg_restore",
            "-h", server["host"],
            "-p", str(server["port"]),
            "-U", server["user"],
            "-C",              # create database
            "-d", "postgres",  # connect to default db
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

    @staticmethod
    def restore_into_existing_db(server, backup_file, target_db):
        """
        Restores backup into already existing database
        """
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