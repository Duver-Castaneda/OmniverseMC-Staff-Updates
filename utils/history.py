import json
import os
from datetime import datetime, timezone

DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "infractions.json")


def _cargar_datos():
    if not os.path.exists(DATA_PATH):
        return {}
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}


def _guardar_datos(data):
    os.makedirs(os.path.dirname(DATA_PATH), exist_ok=True)
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def add_infraction(guild_id: int, user_id: int, moderator_id: int, action: str, reason: str):
    """Agrega una sancion al historial de un usuario"""
    data = _cargar_datos()
    guild_key = str(guild_id)
    user_key = str(user_id)

    data.setdefault(guild_key, {})
    data[guild_key].setdefault(user_key, [])

    entry = {
        "action": action,
        "reason": reason,
        "moderator_id": moderator_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    data[guild_key][user_key].append(entry)
    _guardar_datos(data)
    return entry


def get_history(guild_id: int, user_id: int):
    """Devuelve la lista de sanciones de un usuario en un servidor"""
    data = _cargar_datos()
    return data.get(str(guild_id), {}).get(str(user_id), [])
