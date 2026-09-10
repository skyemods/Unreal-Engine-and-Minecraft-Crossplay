import os
import sys
import json
import threading
import subprocess
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse


# ============================================================
# MINECRAFT <-> UE4 CROSSPLAY SERVER
# ============================================================

HOST = "0.0.0.0"
HTTP_PORT = 25570

# Minecraft server files are inside ./server/
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SERVER_FOLDER = os.path.join(BASE_DIR, "server")
MINECRAFT_JAR = os.path.join(SERVER_FOLDER, "server.jar")

JAVA_MEMORY = "1G"

minecraft_ready = False
minecraft_process = None

players = {}
blocks = {}

state_lock = threading.Lock()


# ============================================================
# START MINECRAFT
# ============================================================

def start_minecraft():

    global minecraft_process

    print()
    print("==========================================")
    print(" STARTING MINECRAFT")
    print("==========================================")
    print()

    if not os.path.isdir(SERVER_FOLDER):

        print("[SERVER] ERROR: server folder not found:")
        print(SERVER_FOLDER)
        return None

    if not os.path.isfile(MINECRAFT_JAR):

        print("[SERVER] ERROR: server.jar not found:")
        print(MINECRAFT_JAR)
        return None

    print("[SERVER] Folder:")
    print(SERVER_FOLDER)

    print("[SERVER] Jar:")
    print(MINECRAFT_JAR)

    print("[SERVER] Memory:")
    print(JAVA_MEMORY)

    print()

    command = [
        "java",
        f"-Xms{JAVA_MEMORY}",
        f"-Xmx{JAVA_MEMORY}",
        "-jar",
        "server.jar",
        "nogui"
    ]

    try:

        minecraft_process = subprocess.Popen(
            command,
            cwd=SERVER_FOLDER,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )

    except FileNotFoundError:

        print()
        print("[SERVER] ERROR: Java was not found.")
        print("[SERVER] Make sure Java is installed.")
        print()

        return None

    except Exception as e:

        print()
        print("[SERVER] ERROR starting Minecraft:")
        print(e)
        print()

        return None

    return minecraft_process


# ============================================================
# MINECRAFT CONSOLE
# ============================================================

def minecraft_console(process):

    global minecraft_ready

    try:

        for line in process.stdout:

            line = line.rstrip()

            if line:
                print("[MINECRAFT]", line)

            # Minecraft prints "Done (...)" when fully started
            if "Done (" in line:

                minecraft_ready = True

                print()
                print("==========================================")
                print(" MINECRAFT IS READY")
                print("==========================================")
                print()
                print(
                    "[SERVER] UE4 API:"
                    " http://127.0.0.1:25570"
                )
                print()
                print("==========================================")
                print()

    except Exception as e:

        print("[MINECRAFT] Console error:", e)

    finally:

        minecraft_ready = False

        print()
        print("[MINECRAFT] Minecraft process stopped.")
        print()


# ============================================================
# SEND JSON
# ============================================================

def send_json(handler, data, status=200):

    try:

        body = json.dumps(
            data,
            indent=2
        ).encode("utf-8")

        handler.send_response(status)

        handler.send_header(
            "Content-Type",
            "application/json; charset=utf-8"
        )

        handler.send_header(
            "Content-Length",
            str(len(body))
        )

        handler.send_header(
            "Access-Control-Allow-Origin",
            "*"
        )

        handler.send_header(
            "Access-Control-Allow-Methods",
            "GET, POST, OPTIONS"
        )

        handler.send_header(
            "Access-Control-Allow-Headers",
            "Content-Type"
        )

        handler.end_headers()

        handler.wfile.write(body)

    except BrokenPipeError:
        pass

    except ConnectionResetError:
        pass


# ============================================================
# HTTP API
# ============================================================

class CrossplayAPI(BaseHTTPRequestHandler):

    # --------------------------------------------------------
    # LOGGING
    # --------------------------------------------------------

    def log_message(self, format, *args):

        print(
            "[HTTP]",
            self.address_string(),
            "-",
            format % args
        )

    # --------------------------------------------------------
    # OPTIONS
    # --------------------------------------------------------

    def do_OPTIONS(self):

        self.send_response(200)

        self.send_header(
            "Access-Control-Allow-Origin",
            "*"
        )

        self.send_header(
            "Access-Control-Allow-Methods",
            "GET, POST, OPTIONS"
        )

        self.send_header(
            "Access-Control-Allow-Headers",
            "Content-Type"
        )

        self.send_header(
            "Content-Length",
            "0"
        )

        self.end_headers()

    # ========================================================
    # GET
    # ========================================================

    def do_GET(self):

        path = urlparse(self.path).path

        print("[HTTP] GET", path)

        # ----------------------------------------------------
        # ROOT
        # ----------------------------------------------------

        if path == "/":

            send_json(
                self,
                {
                    "name": "Minecraft UE4 Crossplay Server",
                    "server": "online",
                    "minecraft": minecraft_ready,
                    "http_port": HTTP_PORT,
                    "api": [
                        "GET /",
                        "GET /status",
                        "GET /player",
                        "GET /players",
                        "GET /blocks",
                        "POST /player",
                        "POST /ue4/connect",
                        "POST /block/place",
                        "POST /block/break"
                    ]
                }
            )

            return

        # ----------------------------------------------------
        # STATUS
        # ----------------------------------------------------

        if path == "/status":

            send_json(
                self,
                {
                    "server": "online",

                    "minecraft": (
                        "ready"
                        if minecraft_ready
                        else "starting"
                    ),

                    "ue4": "waiting",

                    "protocol": "crossplay-v1"
                }
            )

            return

        # ----------------------------------------------------
        # PLAYER
        # ----------------------------------------------------

        if path == "/player":

            with state_lock:

                player_list = list(
                    players.values()
                )

            if len(player_list) > 0:

                send_json(
                    self,
                    player_list[0]
                )

            else:

                send_json(
                    self,
                    {
                        "id": "ue4_player",
                        "name": "UE4Player",
                        "x": 0.0,
                        "y": 0.0,
                        "z": 0.0,
                        "type": "ue4"
                    }
                )

            return

        # ----------------------------------------------------
        # PLAYERS
        # ----------------------------------------------------

        if path == "/players":

            with state_lock:

                player_list = list(
                    players.values()
                )

            send_json(
                self,
                {
                    "count": len(player_list),
                    "players": player_list
                }
            )

            return

        # ----------------------------------------------------
        # BLOCKS
        # ----------------------------------------------------

        if path == "/blocks":

            with state_lock:

                block_list = list(
                    blocks.values()
                )

            send_json(
                self,
                {
                    "count": len(block_list),
                    "blocks": block_list
                }
            )

            return

        # ----------------------------------------------------
        # UNKNOWN GET
        # ----------------------------------------------------

        send_json(
            self,
            {
                "error": "Endpoint not found",
                "path": path
            },
            404
        )

    # ========================================================
    # POST
    # ========================================================

    def do_POST(self):

        path = urlparse(self.path).path

        print("[HTTP] POST", path)

        # ----------------------------------------------------
        # READ JSON
        # ----------------------------------------------------

        try:

            content_length = int(
                self.headers.get(
                    "Content-Length",
                    "0"
                )
            )

        except ValueError:

            content_length = 0

        raw_data = self.rfile.read(
            content_length
        )

        if content_length == 0:

            data = {}

        else:

            try:

                data = json.loads(
                    raw_data.decode("utf-8")
                )

            except Exception as e:

                print(
                    "[HTTP] JSON error:",
                    e
                )

                send_json(
                    self,
                    {
                        "success": False,
                        "error": "Invalid JSON"
                    },
                    400
                )

                return

        # ----------------------------------------------------
        # UE4 PLAYER UPDATE
        # ----------------------------------------------------

        if path == "/player":

            try:

                player_id = str(
                    data.get(
                        "id",
                        "ue4_player"
                    )
                )

                player_name = str(
                    data.get(
                        "name",
                        "UE4Player"
                    )
                )

                x = float(
                    data.get(
                        "x",
                        0.0
                    )
                )

                y = float(
                    data.get(
                        "y",
                        0.0
                    )
                )

                z = float(
                    data.get(
                        "z",
                        0.0
                    )
                )

            except Exception as e:

                send_json(
                    self,
                    {
                        "success": False,
                        "error": "Invalid player data",
                        "details": str(e)
                    },
                    400
                )

                return

            player = {
                "id": player_id,
                "name": player_name,
                "x": x,
                "y": y,
                "z": z,
                "type": "ue4"
            }

            with state_lock:

                players[player_id] = player

            print()
            print("[UE4] Player position received:")
            print(
                f"[UE4] X={x:.2f} "
                f"Y={y:.2f} "
                f"Z={z:.2f}"
            )
            print()

            send_json(
                self,
                {
                    "success": True,
                    "player": player
                }
            )

            return

        # ----------------------------------------------------
        # UE4 CONNECT
        # ----------------------------------------------------

        if path == "/ue4/connect":

            print()
            print("[UE4] UE4 client connected.")
            print()

            send_json(
                self,
                {
                    "success": True,
                    "message": "UE4 connected",
                    "minecraft": minecraft_ready
                }
            )

            return

        # ----------------------------------------------------
        # BLOCK PLACE
        # ----------------------------------------------------

        if path == "/block/place":

            try:

                x = int(
                    data.get(
                        "x",
                        0
                    )
                )

                y = int(
                    data.get(
                        "y",
                        0
                    )
                )

                z = int(
                    data.get(
                        "z",
                        0
                    )
                )

                block_type = str(
                    data.get(
                        "block",
                        "stone"
                    )
                )

            except Exception as e:

                send_json(
                    self,
                    {
                        "success": False,
                        "error": "Invalid block data",
                        "details": str(e)
                    },
                    400
                )

                return

            key = f"{x},{y},{z}"

            block = {
                "x": x,
                "y": y,
                "z": z,
                "block": block_type
            }

            with state_lock:

                blocks[key] = block

            print(
                f"[BLOCK] Placed {block_type} "
                f"at X={x} Y={y} Z={z}"
            )

            send_json(
                self,
                {
                    "success": True,
                    "action": "place",
                    "block": block
                }
            )

            return

        # ----------------------------------------------------
        # BLOCK BREAK
        # ----------------------------------------------------

        if path == "/block/break":

            try:

                x = int(
                    data.get(
                        "x",
                        0
                    )
                )

                y = int(
                    data.get(
                        "y",
                        0
                    )
                )

                z = int(
                    data.get(
                        "z",
                        0
                    )
                )

            except Exception as e:

                send_json(
                    self,
                    {
                        "success": False,
                        "error": "Invalid block position",
                        "details": str(e)
                    },
                    400
                )

                return

            key = f"{x},{y},{z}"

            with state_lock:

                existed = key in blocks

                if existed:

                    del blocks[key]

            print(
                f"[BLOCK] Broke block "
                f"at X={x} Y={y} Z={z}"
            )

            send_json(
                self,
                {
                    "success": True,
                    "action": "break",
                    "x": x,
                    "y": y,
                    "z": z,
                    "existed": existed
                }
            )

            return

        # ----------------------------------------------------
        # UNKNOWN POST
        # ----------------------------------------------------

        send_json(
            self,
            {
                "success": False,
                "error": "Endpoint not found",
                "path": path
            },
            404
        )


# ============================================================
# START HTTP SERVER
# ============================================================

def start_http_server():

    print()
    print("==========================================")
    print(" STARTING UE4 HTTP API")
    print("==========================================")
    print()

    try:

        server = ThreadingHTTPServer(
            (HOST, HTTP_PORT),
            CrossplayAPI
        )

    except OSError as e:

        print()
        print("[HTTP] ERROR:")
        print(e)
        print()
        print(
            f"Is another program already using port "
            f"{HTTP_PORT}?"
        )
        print()

        return

    print(
        f"[HTTP] Listening on "
        f"http://127.0.0.1:{HTTP_PORT}"
    )

    print()
    print("GET endpoints:")
    print("  /")
    print("  /status")
    print("  /player")
    print("  /players")
    print("  /blocks")

    print()
    print("POST endpoints:")
    print("  /player")
    print("  /ue4/connect")
    print("  /block/place")
    print("  /block/break")

    print()
    print("==========================================")
    print()

    try:

        server.serve_forever()

    except KeyboardInterrupt:

        print()
        print("[HTTP] Server stopped.")

    finally:

        server.server_close()


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("==========================================")
    print(" MINECRAFT <-> UE4 CROSSPLAY")
    print(" SERVER.PY")
    print("==========================================")
    print()

    print("[SERVER] Base directory:")
    print(BASE_DIR)

    print()
    print("[SERVER] Minecraft directory:")
    print(SERVER_FOLDER)

    print()
    print("[SERVER] Minecraft jar:")
    print(MINECRAFT_JAR)

    print()

    # Start Minecraft
    minecraft = start_minecraft()

    if minecraft is None:

        print()
        print("[SERVER] Minecraft failed to start.")
        print()

        sys.exit(1)

    # Minecraft console thread
    console_thread = threading.Thread(
        target=minecraft_console,
        args=(minecraft,),
        daemon=True
    )

    console_thread.start()

    # Start HTTP API
    start_http_server()


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    main()