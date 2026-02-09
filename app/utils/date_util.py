from datetime import datetime
from zoneinfo import ZoneInfo
from flask import current_app

def get_now():
    """Retorna la fecha y hora actual en la zona horaria configurada."""
    tz_name = current_app.config.get('TIMEZONE', 'America/Santo_Domingo')
    return datetime.now(ZoneInfo(tz_name))

def to_local(dt):
    """Convierte un objeto datetime a la zona horaria local."""
    if dt is None:
        return None
    
    tz_name = current_app.config.get('TIMEZONE', 'America/Santo_Domingo')
    local_tz = ZoneInfo(tz_name)

    if dt.tzinfo is None:
        # Si es naive, asumimos que es UTC si se guardó así, 
        # O si se guardó como local del servidor, esto puede ser truculento.
        # Para este MVP, si el sistema corre localmente, asumimos que ya está en la hora correcta
        # pero para "pulir", lo ideal es hacerlos aware.
        return dt.replace(tzinfo=local_tz) 
    
    return dt.astimezone(local_tz)
