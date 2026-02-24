import json
import os
import psycopg2

SERVERS_FILE = os.path.join("data", "servers.json")


class ServerManager:

    @staticmethod
    def load_servers():
        if not os.path.exists(SERVERS_FILE):
            return []

        with open(SERVERS_FILE, "r") as f:
            return json.load(f)

    @staticmethod
    def save_servers(servers):
        with open(SERVERS_FILE, "w") as f:
            json.dump(servers, f, indent=4)

    @staticmethod
    def get_databases(server):
        conn = psycopg2.connect(
            host=server["host"],
            port=server["port"],
            user=server["user"],
            password=server["password"],
            dbname="postgres"
        )

        cur = conn.cursor()
        cur.execute("""
            SELECT datname
            FROM pg_database
            WHERE datistemplate = false;
        """)

        dbs = [row[0] for row in cur.fetchall()]

        cur.close()
        conn.close()

        return dbs