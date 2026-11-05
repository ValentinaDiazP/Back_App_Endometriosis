import os
import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/calendar']

def _obtener_servicio_calendar():
    """
    Intenta autenticarse con la API de Google Calendar usando credentials.json
    o variables de entorno. Retorna el servicio de calendar o None si falla.
    """
    credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS', 'credentials.json')
    if os.path.exists(credentials_path):
        try:
            creds = service_account.Credentials.from_service_account_file(
                credentials_path, scopes=SCOPES
            )
            service = build('calendar', 'v3', credentials=creds)
            return service
        except Exception as e:
            print(f"Error al inicializar credenciales de Google Calendar: {e}")
    return None

def obtener_horarios_disponibles(calendar_id, fecha_str):
    """
    Retorna una lista de horarios disponibles para la fecha indicada (YYYY-MM-DD).
    Usa la zona horaria local America/Bogota (UTC-5).
    Consulta la API freebusy de Google Calendar.
    """
    print(f"--- CONSULTANDO CALENDAR ID: '{calendar_id}' PARA FECHA: '{fecha_str}' ---")

    # Jornada base: 08:00 AM a 05:00 PM (turnos de 1 hora)
    jornada_base = ['08:00', '09:00', '10:00', '11:00', '12:00', '14:00', '15:00', '16:00']

    if not fecha_str:
        fecha_str = datetime.date.today().strftime('%Y-%m-%d')

    if not calendar_id:
        print("ADVERTENCIA: Profesional no tiene Google Calendar ID configurado.")
        return jornada_base

    service = _obtener_servicio_calendar()
    if not service:
        return jornada_base

    try:
        # Ventana con zona horaria America/Bogota (UTC-5)
        time_min = f"{fecha_str}T00:00:00-05:00"
        time_max = f"{fecha_str}T23:59:59-05:00"

        body = {
            "timeMin": time_min,
            "timeMax": time_max,
            "items": [{"id": calendar_id}]
        }

        freebusy_result = service.freebusy().query(body=body).execute()
        calendars = freebusy_result.get('calendars', {})
        busy_slots = calendars.get(calendar_id, {}).get('busy', [])

        # Filtrar los bloques ocupados de la jornada base
        horarios_disponibles = []
        for hora in jornada_base:
            hora_dt = datetime.datetime.strptime(f"{fecha_str} {hora}", '%Y-%m-%d %H:%M')
            hora_fin_dt = hora_dt + datetime.timedelta(hours=1)
            
            ocupado = False
            for slot in busy_slots:
                start_busy = datetime.datetime.fromisoformat(slot['start'].replace('Z', '+00:00')).replace(tzinfo=None)
                end_busy = datetime.datetime.fromisoformat(slot['end'].replace('Z', '+00:00')).replace(tzinfo=None)
                
                # Comprobar solapamiento para rangos parciales (ej: 15:00 a 16:00 se elimina si hay evento de 15:00 a 15:30)
                if max(hora_dt, start_busy) < min(hora_fin_dt, end_busy):
                    ocupado = True
                    break
            
            if not ocupado:
                horarios_disponibles.append(hora)

        print(f"BLOQUES FINALES DEVUELTOS A LA APP: {horarios_disponibles}")
        return horarios_disponibles

    except Exception as e:
        print(f"Error consultando FreeBusy de Google Calendar: {e}")
        return jornada_base

def crear_evento_cita(calendar_id, resumen, inicio_datetime, fin_datetime, descripcion=""):
    """
    Inserta un evento real en el Google Calendar especificado.
    """
    if not calendar_id:
        print("No se proporcionó calendar_id para crear el evento.")
        return None

    service = _obtener_servicio_calendar()
    if not service:
        print("Servicio de Google Calendar no disponible.")
        return None

    try:
        evento = {
            'summary': resumen,
            'description': descripcion,
            'start': {
                'dateTime': inicio_datetime.isoformat(),
                'timeZone': 'America/Bogota',
            },
            'end': {
                'dateTime': fin_datetime.isoformat(),
                'timeZone': 'America/Bogota',
            },
        }

        evento_creado = service.events().insert(calendarId=calendar_id, body=evento).execute()
        print(f"Evento creado en Google Calendar: {evento_creado.get('htmlLink')}")
        return evento_creado

    except Exception as e:
        print(f"Error al crear evento en Google Calendar: {e}")
        return None
