from datetime import datetime, timedelta


def format_brl(value: float) -> str:
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def get_date_range(period: str) -> tuple[datetime, datetime]:
    now = datetime.now()

    if period == "today":
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end = now.replace(hour=23, minute=59, second=59, microsecond=999999)
        return start, end

    if period == "week":
        day = now.weekday()
        start = (now - timedelta(days=day)).replace(hour=0, minute=0, second=0, microsecond=0)
        return start, now

    start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    return start, now


MONTH_NAMES = {
    1: "janeiro", 2: "fevereiro", 3: "março", 4: "abril",
    5: "maio", 6: "junho", 7: "julho", 8: "agosto",
    9: "setembro", 10: "outubro", 11: "novembro", 12: "dezembro",
}


def get_month_name(dt: datetime) -> str:
    return f"{MONTH_NAMES[dt.month]} de {dt.year}"


def format_date(dt: datetime) -> str:
    return dt.strftime("%d/%m/%Y")
