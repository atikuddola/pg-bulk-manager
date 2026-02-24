import subprocess
import os


class RestoreManager:

    @staticmethod
    def restore_backup(server, backup_file):

        dbname = os.path.basename(backup_file).replace(".backup", "")

        env = os.environ.copy()
        env["PGPASSWORD"] = server["password"]

        # Create DB
        create_command = [
            "createdb",
            "-h", server["host"],
            "-p", str(server["port"]),
            "-U", server["user"],
            dbname
        ]

        subprocess.run(create_command, env=env)

        # Restore
        restore_command = [
            "pg_restore",
            "-h", server["host"],
            "-p", str(server["port"]),
            "-U", server["user"],
            "-d", dbname,
            backup_file
        ]

        result = subprocess.run(restore_command, env=env, capture_output=True, text=True)

        if result.returncode != 0:
            raise Exception(result.stderr)

        return dbname