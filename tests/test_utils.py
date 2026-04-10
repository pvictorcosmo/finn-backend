"""Testes para app/core/utils.py"""

from datetime import datetime
from app.core.utils import format_brl, get_date_range, get_month_name, format_date


def test_format_brl_simple():
    assert format_brl(50) == "R$ 50,00"


def test_format_brl_thousands():
    assert format_brl(1500.5) == "R$ 1.500,50"


def test_format_brl_zero():
    assert format_brl(0) == "R$ 0,00"


def test_format_brl_large():
    assert format_brl(123456.78) == "R$ 123.456,78"


def test_get_date_range_today():
    start, end = get_date_range("today")
    now = datetime.now()
    assert start.year == now.year
    assert start.month == now.month
    assert start.day == now.day
    assert start.hour == 0 and start.minute == 0
    assert end.hour == 23 and end.minute == 59


def test_get_date_range_week():
    start, end = get_date_range("week")
    assert start.weekday() == 0  # Monday


def test_get_date_range_month():
    start, end = get_date_range("month")
    assert start.day == 1
    assert start.hour == 0


def test_get_month_name():
    dt = datetime(2026, 4, 15)
    assert get_month_name(dt) == "abril de 2026"


def test_get_month_name_january():
    dt = datetime(2026, 1, 1)
    assert get_month_name(dt) == "janeiro de 2026"


def test_format_date():
    dt = datetime(2026, 4, 9, 14, 30)
    assert format_date(dt) == "09/04/2026"
