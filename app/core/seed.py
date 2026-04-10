from sqlalchemy import text, inspect

from app.core.db import SessionLocal, engine, Base
from app.core.models import Category, Salary, BudgetGoal

CATEGORIES = [
    {"name": "alimentação", "emoji": "🍔", "goal_group": "essenciais"},
    {"name": "transporte", "emoji": "🚗", "goal_group": "essenciais"},
    {"name": "lazer", "emoji": "🎮", "goal_group": "desejos"},
    {"name": "saúde", "emoji": "💊", "goal_group": "essenciais"},
    {"name": "educação", "emoji": "📚", "goal_group": "desejos"},
    {"name": "moradia", "emoji": "🏠", "goal_group": "essenciais"},
    {"name": "assinaturas", "emoji": "📱", "goal_group": "desejos"},
    {"name": "outros", "emoji": "💰", "goal_group": "desejos"},
]

DEFAULT_GOALS = [
    {"group_name": "essenciais", "label": "Necessidades Essenciais", "emoji": "🏠", "percentage": 50},
    {"group_name": "desejos", "label": "Desejos", "emoji": "🎮", "percentage": 30},
    {"group_name": "poupanca", "label": "Poupança e Investimentos", "emoji": "💰", "percentage": 20},
]


def _migrate(db):
    """Adiciona colunas/tabelas novas que create_all não consegue em tabelas existentes."""
    inspector = inspect(engine)
    # Adicionar goal_group na tabela categories se não existir
    if "categories" in inspector.get_table_names():
        columns = [col["name"] for col in inspector.get_columns("categories")]
        if "goal_group" not in columns:
            db.execute(text("ALTER TABLE categories ADD COLUMN goal_group VARCHAR DEFAULT 'desejos'"))
            db.commit()
            print("✅ Coluna goal_group adicionada em categories")


def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        _migrate(db)
        for cat in CATEGORIES:
            existing = db.query(Category).filter(Category.name == cat["name"]).first()
            if not existing:
                db.add(Category(**cat))
            elif not existing.goal_group or existing.goal_group == "desejos":
                existing.goal_group = cat["goal_group"]

        if not db.query(Salary).first():
            db.add(Salary(id=1, amount=0))

        for goal in DEFAULT_GOALS:
            existing = db.query(BudgetGoal).filter(BudgetGoal.group_name == goal["group_name"]).first()
            if not existing:
                db.add(BudgetGoal(**goal))

        db.commit()
        print("✅ Seed concluído!")
    finally:
        db.close()
