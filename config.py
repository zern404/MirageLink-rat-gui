import json, uuid
import os

SETTINGS_FILE = "settings.json"
DEFAULT_SETTINGS = {
    "key": 0,
    "host": "127.0.0.1",
    "port": 5552,
    "theme": "default"
}

def create_key():
    try:
        data = load_settings()
        if data["key"] == 0:
            unique_key = str(uuid.uuid4())
            data["key"] = unique_key
            with open(SETTINGS_FILE, "w", encoding="utf-8") as file:
                json.dump(data, file, indent=4, ensure_ascii=False)
            
    except Exception as e:
        print(f"Error in create key! {e}")

def load_settings():
    if not os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "w", encoding="utf-8") as file:
            json.dump(DEFAULT_SETTINGS, file, indent=4, ensure_ascii=False)

    with open(SETTINGS_FILE, "r", encoding="utf-8") as file:
        return json.load(file)

def set_host(host, port):
    settings = load_settings()

    settings["host"] = host
    settings["port"] = port

    with open(SETTINGS_FILE, "w", encoding="utf-8") as file:
        json.dump(settings, file, indent=4, ensure_ascii=False)