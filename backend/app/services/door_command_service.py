door_command = {
    "open": False,
    "source": None,
}


def trigger_open(source: str = "dashboard"):
    door_command["open"] = True
    door_command["source"] = source


def consume_command():
    if door_command["open"]:
        door_command["open"] = False
        return {
            "command": "open",
            "source": door_command["source"],
        }

    return {
        "command": "none",
        "source": None,
    }