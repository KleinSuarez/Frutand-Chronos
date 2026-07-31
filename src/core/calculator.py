from datetime import datetime, date, time, timedelta
from typing import Dict, Any, Optional
from core.holidays import ColombiaHolidays

class LaborCalculator:
    """
    Motor Core de Cálculo Horario para Frutand Chronos bajo la normativa laboral colombiana.
    Jornada ordinaria: 7 horas diarias / 42 horas semanales.
    Corte nocturno: 19:00 (7:00 p.m.) a 06:00 (6:00 a.m.).
    Descuento de almuerzo: 30 min (0.5h) solo en jornadas con ingreso <= 12:00.
    """

    HORAS_JORNADA_DIARIA = 7.0
    HORA_INICIO_NOCTURNO = time(19, 0)  # 7:00 PM
    HORA_FIN_NOCTURNO = time(6, 0)     # 6:00 AM

    @classmethod
    def calculate_daily_record(cls, record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calcula las 9 métricas horarias y la alerta de estado para un registro de marcación diaria.
        """
        fecha_str = record.get("fecha", "")
        hora_ent_str = record.get("hora_entrada", "--:--")
        hora_sal_str = record.get("hora_salida", "--:--")

        # Alerta inicial por marcación incompleta
        if hora_ent_str in ("--:--", "", None) or hora_sal_str in ("--:--", "", None):
            return {
                "horas_ordinarias": 0.0,
                "extras_diurnas": 0.0,
                "extras_nocturnas": 0.0,
                "recargo_nocturno": 0.0,
                "recargo_dominical_festivo": 0.0,
                "extras_dominical_festivo": 0.0,
                "horas_deuda": cls.HORAS_JORNADA_DIARIA,
                "tardanza_minutos": 0,
                "salida_anticipada_minutos": 0,
                "alerta_estado": "🔴 Incompleto",
                "alerta_color": "#EF4444"
            }

        dt_fecha = datetime.strptime(fecha_str, "%Y-%m-%d").date()
        es_festivo = ColombiaHolidays.is_holiday_or_sunday(dt_fecha)

        h_ent = datetime.strptime(f"{fecha_str} {hora_ent_str}", "%Y-%m-%d %H:%M")
        h_sal = datetime.strptime(f"{fecha_str} {hora_sal_str}", "%Y-%m-%d %H:%M")

        if h_sal <= h_ent:
            h_sal += timedelta(days=1)

        total_minutos_brutos = (h_sal - h_ent).total_seconds() / 60.0
        horas_brutas = total_minutos_brutos / 60.0

        # Regla de descuento de alimentación (30 min si ingresa <= 12:00 PM y dura >= 7h)
        descuento_almuerzo = 0.5 if (h_ent.time() <= time(12, 0) and horas_brutas >= 7.0) else 0.0
        horas_netas = max(0.0, horas_brutas - descuento_almuerzo)

        # Mapeo de minutos diurnos y nocturnos
        minutos_diurnos = 0
        minutos_nocturnos = 0
        current = h_ent

        # Ajuste de 30m de almuerzo al final si aplica
        duracion_efectiva = (h_sal - h_ent) - timedelta(minutes=30 if descuento_almuerzo > 0 else 0)

        step = timedelta(minutes=1)
        curr = h_ent
        while curr < h_ent + duracion_efectiva:
            t = curr.time()
            if t >= cls.HORA_INICIO_NOCTURNO or t < cls.HORA_FIN_NOCTURNO:
                minutos_nocturnos += 1
            else:
                minutos_diurnos += 1
            curr += step

        horas_diurnas_netas = minutos_diurnos / 60.0
        horas_nocturnas_netas = minutos_nocturnos / 60.0

        # Distribución de Métricas según festivo o día hábil
        if es_festivo:
            recargo_dom = min(cls.HORAS_JORNADA_DIARIA, horas_netas)
            extras_dom = max(0.0, horas_netas - cls.HORAS_JORNADA_DIARIA)
            h_ord = 0.0
            ext_diur = 0.0
            ext_noct = 0.0
            rec_noct = 0.0
        else:
            recargo_dom = 0.0
            extras_dom = 0.0
            
            # Jornada Ordinaria vs Horas Extras
            if horas_netas <= cls.HORAS_JORNADA_DIARIA:
                h_ord = horas_diurnas_netas
                rec_noct = horas_nocturnas_netas
                ext_diur = 0.0
                ext_noct = 0.0
            else:
                # Primeras 7 horas son ordinarias (diurnas / recargo nocturno)
                proporcion_ordinaria = cls.HORAS_JORNADA_DIARIA / horas_netas
                h_ord = round(horas_diurnas_netas * proporcion_ordinaria, 2)
                rec_noct = round(horas_nocturnas_netas * proporcion_ordinaria, 2)
                
                # Excedente son horas extras
                horas_extras_totales = horas_netas - cls.HORAS_JORNADA_DIARIA
                ext_diur = round(horas_diurnas_netas * (1 - proporcion_ordinaria), 2)
                ext_noct = round(horas_nocturnas_netas * (1 - proporcion_ordinaria), 2)

        horas_deuda = max(0.0, cls.HORAS_JORNADA_DIARIA - horas_netas) if not es_festivo else 0.0

        # Determinación del Semáforo Visual
        if horas_deuda > 0.05:
            alerta_estado = "🟡 Deuda"
            alerta_color = "#F59E0B"
        else:
            alerta_estado = "🟢 Ok"
            alerta_color = "#10B981"

        return {
            "horas_ordinarias": round(h_ord, 2),
            "extras_diurnas": round(ext_diur, 2),
            "extras_nocturnas": round(ext_noct, 2),
            "recargo_nocturno": round(rec_noct, 2),
            "recargo_dominical_festivo": round(recargo_dom, 2),
            "extras_dominical_festivo": round(extras_dom, 2),
            "horas_deuda": round(horas_deuda, 2),
            "tardanza_minutos": 0,
            "salida_anticipada_minutos": 0,
            "alerta_estado": alerta_estado,
            "alerta_color": alerta_color
        }
