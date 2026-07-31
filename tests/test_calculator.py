import pytest
from datetime import date
from core.holidays import ColombiaHolidays
from core.calculator import LaborCalculator
from database.repository import DatabaseRepository

def test_colombia_holidays_fixed_and_emiliani():
    # 20 de Julio (Fijo)
    assert ColombiaHolidays.is_holiday_or_sunday(date(2026, 7, 20)) is True

    # 7 de Agosto (Fijo)
    assert ColombiaHolidays.is_holiday_or_sunday(date(2026, 8, 7)) is True

    # Domingo cualquiera
    assert ColombiaHolidays.is_holiday_or_sunday(date(2026, 6, 7)) is True

    # Miércoles común
    assert ColombiaHolidays.is_holiday_or_sunday(date(2026, 6, 3)) is False

def test_manual_holiday_persistence(tmp_path):
    db_file = tmp_path / "test_holidays.db"
    repo = DatabaseRepository(str(db_file))

    # Día hábil 2026-06-03
    dt_test = date(2026, 6, 3)
    assert ColombiaHolidays.is_holiday_or_sunday(dt_test, repo=repo) is False

    # Agregar festivo manual (ej. Día Cívico Frutand)
    repo.add_festivo("2026-06-03", "Día Cívico Corporativo Frutand", es_manual=1)
    assert ColombiaHolidays.is_holiday_or_sunday(dt_test, repo=repo) is True

def test_daily_calculator_standard_daytime_shift():
    # Turno 07:00 a 14:30 (7.5h brutas -> 7.0h netas con 30m almuerzo)
    rec = {
        "fecha": "2026-06-03",
        "hora_entrada": "07:00",
        "hora_salida": "14:30"
    }
    res = LaborCalculator.calculate_daily_record(rec)
    assert res["horas_ordinarias"] == 7.0
    assert res["extras_diurnas"] == 0.0
    assert res["horas_deuda"] == 0.0
    assert res["alerta_estado"] == "🟢 Ok"

def test_daily_calculator_night_shift_afternoon_no_lunch_deduction():
    # Turno 13:00 a 20:00 (7.0h brutas, ingreso >= 13:00 -> NO almuerzo)
    rec = {
        "fecha": "2026-06-03",
        "hora_entrada": "13:00",
        "hora_salida": "20:00"
    }
    res = LaborCalculator.calculate_daily_record(rec)
    assert res["horas_ordinarias"] == 6.0
    assert res["recargo_nocturno"] == 1.0
    assert res["horas_deuda"] == 0.0
    assert res["alerta_estado"] == "🟢 Ok"

def test_daily_calculator_overtime_and_debt():
    # Turno incompleto: 07:00 a 12:00 (5h netas -> Deuda 2h)
    rec = {
        "fecha": "2026-06-03",
        "hora_entrada": "07:00",
        "hora_salida": "12:00"
    }
    res = LaborCalculator.calculate_daily_record(rec)
    assert res["horas_deuda"] == 2.0
    assert res["alerta_estado"] == "🟡 Deuda"

def test_daily_calculator_sunday_holiday():
    # Domingo 2026-06-07 (7.5h brutas -> 7.0h netas festivo)
    rec = {
        "fecha": "2026-06-07",
        "hora_entrada": "07:00",
        "hora_salida": "14:30"
    }
    res = LaborCalculator.calculate_daily_record(rec)
    assert res["recargo_dominical_festivo"] == 7.0
    assert res["extras_dominical_festivo"] == 0.0
    assert res["horas_deuda"] == 0.0
    assert res["alerta_estado"] == "🟢 Ok"
