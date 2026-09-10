import botmine
import time
import json
import urllib.request


# ============================================================
# CONFIG
# ============================================================

MINECRAFT_HOST = "127.0.0.1"
MINECRAFT_PORT = 25565

HTTP_URL = "http://127.0.0.1:25570/player"

BOT_NAME = "UE4Player"
MINECRAFT_VERSION = "26.2"


# ============================================================
# START BOT
# ============================================================

print("[CROSSPLAY] Starting BotMine...")
print("[CROSSPLAY] Connecting to Minecraft...")

bot = botmine.Bot(
    MINECRAFT_HOST,
    MINECRAFT_PORT,
    nickname=BOT_NAME,
    version=MINECRAFT_VERSION
)

bot.reconnect(True)

print("[CROSSPLAY] Minecraft bot connected!")
print("[CROSSPLAY] Bot name:", BOT_NAME)

try:
    print(
        "[CROSSPLAY] Minecraft position:",
        bot.position()
    )
except Exception as e:
    print(
        "[CROSSPLAY] Position error:",
        e
    )

try:
    bot.say("UE4Player connected!")
except Exception as e:
    print(
        "[CROSSPLAY] Chat error:",
        e
    )


# ============================================================
# READ UE4 POSITION
# ============================================================

def get_ue4_position():

    try:

        request = urllib.request.Request(
            HTTP_URL,
            method="GET"
        )

        with urllib.request.urlopen(
            request,
            timeout=1
        ) as response:

            data = json.loads(
                response.read().decode("utf-8")
            )

        x = float(data.get("x", 0.0))
        y = float(data.get("y", 0.0))
        z = float(data.get("z", 0.0))

        return x, y, z

    except Exception as e:

        print(
            "[CROSSPLAY] HTTP error:",
            e
        )

        return None


# ============================================================
# MOVEMENT
# ============================================================

last_position = None


def update_movement():

    global last_position

    position = get_ue4_position()

    if position is None:
        return

    ue_x, ue_y, ue_z = position

    # UE4 centimetres -> Minecraft blocks
    #
    # UE4 X -> Minecraft X
    # UE4 Z -> Minecraft Y
    # UE4 Y -> Minecraft Z
    #
    mc_x = ue_x / 100.0
    mc_y = ue_z / 100.0
    mc_z = ue_y / 100.0

    current = (
        mc_x,
        mc_y,
        mc_z
    )

    if last_position is not None:

        if (
            abs(mc_x - last_position[0]) < 0.05
            and
            abs(mc_y - last_position[1]) < 0.05
            and
            abs(mc_z - last_position[2]) < 0.05
        ):

            return

    print(
        "[CROSSPLAY] UE4:",
        f"X={ue_x:.2f}",
        f"Y={ue_y:.2f}",
        f"Z={ue_z:.2f}"
    )

    print(
        "[CROSSPLAY] Minecraft target:",
        f"X={mc_x:.2f}",
        f"Y={mc_y:.2f}",
        f"Z={mc_z:.2f}"
    )

    try:

        bot.goto(
            x=mc_x,
            y=mc_y,
            z=mc_z
        )

        print(
            "[CROSSPLAY] goto() sent successfully."
        )

        last_position = current

    except Exception as e:

        print(
            "[CROSSPLAY] Movement error:",
            e
        )


# ============================================================
# MAIN LOOP
# ============================================================

print("[CROSSPLAY] Movement loop started.")
print("[CROSSPLAY] Movement: ENABLED")

while True:

    try:

        update_movement()

        # IMPORTANT:
        # Let BotMine process its network packets.
        bot.wait(0.05)

    except KeyboardInterrupt:

        print()
        print("[CROSSPLAY] Stopping bot...")

        try:
            bot.leave()
        except Exception:
            pass

        break

    except Exception as e:

        print(
            "[CROSSPLAY] Loop error:",
            e
        )

        time.sleep(0.2)