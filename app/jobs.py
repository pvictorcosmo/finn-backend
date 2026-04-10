"""Cron jobs agendados."""

from app.core.db import SessionLocal
from app.services.summary import build_daily
from app.services.installment import process_monthly as process_installments
from app.services.recurring import process_monthly as process_recurring


def daily_summary_job():
    db = SessionLocal()
    try:
        summary = build_daily(db)
        print(f"Resumo diario:\n{summary}")
    finally:
        db.close()


def monthly_billing_job():
    db = SessionLocal()
    try:
        r1 = process_installments(db)
        r2 = process_recurring(db)
        print(f"Parcelas: {r1}")
        print(f"Fixos: {r2}")
    finally:
        db.close()
