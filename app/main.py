from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler

from app.core.db import engine, Base, SessionLocal
from app.core.seed import seed
from app.routers import messages, data, goals
from app.routers.actions import build_daily_summary, process_monthly_installments, process_monthly_recurring

scheduler = BackgroundScheduler(timezone="America/Sao_Paulo")


def daily_summary_job():
    db = SessionLocal()
    try:
        summary = build_daily_summary(db)
        print(f"📊 Resumo diário:\n{summary}")
    finally:
        db.close()


def monthly_installments_job():
    db = SessionLocal()
    try:
        result1 = process_monthly_installments(db)
        result2 = process_monthly_recurring(db)
        print(f"Parcelas: {result1}")
        print(f"Fixos: {result2}")
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    seed()
    scheduler.add_job(daily_summary_job, "cron", hour=20, minute=0)
    scheduler.add_job(monthly_installments_job, "cron", day=1, hour=8, minute=0)
    scheduler.start()
    print("⏰ Cron agendado (resumo 20h, parcelas dia 1 às 8h)")
    yield
    scheduler.shutdown()


app = FastAPI(title="ZapFinance API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(messages.router)
app.include_router(data.router)
app.include_router(goals.router)


@app.get("/health")
def health():
    return {"status": "ok"}
