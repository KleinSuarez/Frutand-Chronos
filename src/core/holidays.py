import json
import urllib.request
from datetime import date, timedelta
from typing import Set, List, Dict, Any, Optional

class ColombiaHolidays:
    """
    Calculador y Gestor de Festivos de Colombia (Ley Emiliani 51 de 1983 + Sincronización Web + Persistencia SQLite).
    """

    @staticmethod
    def _easter_date(year: int) -> date:
        """Calcula el Domingo de Pascua (Algoritmo de Butcher)."""
        a = year % 19
        b = year // 100
        c = year % 100
        d = b // 4
        e = b % 4
        f = (b + 8) // 25
        g = (b - f + 1) // 3
        h = (19 * a + b - d - g + 15) % 30
        i = c // 4
        k = c % 4
        l = (32 + 2 * e + 2 * i - h - k) % 7
        m = (a + 11 * h + 22 * l) // 451
        month = (h + l - 7 * m + 114) // 31
        day = ((h + l - 7 * m + 114) % 31) + 1
        return date(year, month, day)

    @staticmethod
    def _move_to_next_monday(d: date) -> date:
        """Aplica la Ley Emiliani desplazando el festivo al siguiente lunes si no cae en lunes."""
        if d.weekday() == 0:
            return d
        days_ahead = 7 - d.weekday()
        return d + timedelta(days=days_ahead)

    @classmethod
    def get_calculated_holidays(cls, year: int) -> Dict[date, str]:
        """Genera el diccionario de festivos calculados (Ley Emiliani) con sus descripciones."""
        h_dict = {}

        # Fijos
        h_dict[date(year, 1, 1)] = "Año Nuevo"
        h_dict[date(year, 5, 1)] = "Día del Trabajo"
        h_dict[date(year, 7, 20)] = "Día de la Independencia"
        h_dict[date(year, 8, 7)] = "Batalla de Boyacá"
        h_dict[date(year, 12, 8)] = "Inmaculada Concepción"
        h_dict[date(year, 12, 25)] = "Navidad"

        # Ley Emiliani
        emiliani = [
            (date(year, 1, 6), "Reyes Magos"),
            (date(year, 3, 19), "San José"),
            (date(year, 6, 29), "San Pedro y San Pablo"),
            (date(year, 8, 15), "Asunción de la Virgen"),
            (date(year, 10, 12), "Día de la Raza"),
            (date(year, 11, 1), "Todos los Santos"),
            (date(year, 11, 11), "Independencia de Cartagena"),
        ]
        for dt_orig, desc in emiliani:
            dt_moved = cls._move_to_next_monday(dt_orig)
            h_dict[dt_moved] = f"{desc} (Emiliani)"

        # Pascua
        pascua = cls._easter_date(year)
        h_dict[pascua - timedelta(days=3)] = "Jueves Santo"
        h_dict[pascua - timedelta(days=2)] = "Viernes Santo"
        h_dict[cls._move_to_next_monday(pascua + timedelta(days=39))] = "Ascensión del Señor"
        h_dict[cls._move_to_next_monday(pascua + timedelta(days=60))] = "Corpus Christi"
        h_dict[cls._move_to_next_monday(pascua + timedelta(days=67))] = "Sagrado Corazón de Jesús"

        return h_dict

    @classmethod
    def sync_online_holidays(cls, year: int, repo=None) -> List[Dict[str, Any]]:
        """
        Sincroniza los festivos oficiales desde el API web remoto (Nager.Date).
        Si repo está definido, persiste cada festivo en la base de datos SQLite.
        """
        fetched = []
        try:
            url = f"https://date.nager.at/api/v3/PublicHolidays/{year}/CO"
            req = urllib.request.Request(url, headers={'User-Agent': 'FrutandChronos/1.0'})
            with urllib.request.urlopen(req, timeout=5) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode('utf-8'))
                    for item in data:
                        f_str = item.get("date")
                        desc = item.get("localName") or item.get("name") or "Festivo"
                        fetched.append({"fecha": f_str, "descripcion": desc, "es_manual": 0})
                        if repo:
                            repo.add_festivo(f_str, desc, es_manual=0)
        except Exception:
            # Fallback en caso de sin conexión a internet
            calc_dict = cls.get_calculated_holidays(year)
            for d, desc in calc_dict.items():
                f_str = d.strftime("%Y-%m-%d")
                fetched.append({"fecha": f_str, "descripcion": desc, "es_manual": 0})
                if repo:
                    repo.add_festivo(f_str, desc, es_manual=0)

        return fetched

    @classmethod
    def is_holiday_or_sunday(cls, d: date, repo=None) -> bool:
        """Verifica si una fecha es Domingo, Festivo Emiliani o Festivo Manual en SQLite."""
        if d.weekday() == 6:  # Domingo
            return True

        if repo:
            db_festivos = {r["fecha"] for r in repo.get_festivos()}
            if d.strftime("%Y-%m-%d") in db_festivos:
                return True

        return d in cls.get_calculated_holidays(d.year)
