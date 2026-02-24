import subprocess
import os


class BackupManager:

    @staticmethod
    def backup_database(server, dbname, output_folder):
        output_file = os.path.join(output_folder, f"{dbname}.backup")

        env = os.environ.copy()
        env["PGPASSWORD"] = server["password"]

        command = [
            "pg_dump",
            "-h", server["host"],
            "-p", str(server["port"]),
            "-U", server["user"],
            "-F", "c",
            "-d", dbname,
            "-f", output_file
        ]

        result = subprocess.run(command, env=env, capture_output=True, text=True)

        if result.returncode != 0:
            raise Exception(result.stderr)

        return output_file