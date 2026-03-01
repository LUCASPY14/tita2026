"""
Utilidades para manejo de fechas
"""
from datetime import datetime, timedelta
from django.utils import timezone


def get_current_datetime():
    """Retorna la fecha y hora actual con timezone"""
    return timezone.now()


def format_date(date, format_string='%d/%m/%Y'):
    """Formatea una fecha según el formato especificado"""
    if isinstance(date, str):
        return date
    return date.strftime(format_string) if date else None


def get_month_range(year, month):
    """
    Retorna el primer y último día de un mes específico
    """
    first_day = datetime(year, month, 1)
    if month == 12:
        last_day = datetime(year + 1, 1, 1) - timedelta(days=1)
    else:
        last_day = datetime(year, month + 1, 1) - timedelta(days=1)
    return first_day, last_day
