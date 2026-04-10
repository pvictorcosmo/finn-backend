from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, func
from sqlalchemy.orm import relationship

from app.core.db import Base


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False)
    emoji = Column(String, default="💰")
    goal_group = Column(String, default="desejos")  # essenciais, desejos, poupanca
    created_at = Column(DateTime, server_default=func.now())

    transactions = relationship("Transaction", back_populates="category")
    budget = relationship("Budget", back_populates="category", uselist=False)


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    amount = Column(Float, nullable=False)
    description = Column(String, nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    date = Column(DateTime, server_default=func.now())
    created_at = Column(DateTime, server_default=func.now())

    category = relationship("Category", back_populates="transactions")


class Budget(Base):
    __tablename__ = "budgets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    category_id = Column(Integer, ForeignKey("categories.id"), unique=True, nullable=False)
    limit = Column(Float, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    category = relationship("Category", back_populates="budget")


class Salary(Base):
    __tablename__ = "salaries"

    id = Column(Integer, primary_key=True, default=1)
    amount = Column(Float, nullable=False, default=0)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class BudgetGoal(Base):
    __tablename__ = "budget_goals"

    id = Column(Integer, primary_key=True, autoincrement=True)
    group_name = Column(String, unique=True, nullable=False)  # essenciais, desejos, poupanca
    label = Column(String, nullable=False)  # display name
    emoji = Column(String, default="🎯")
    percentage = Column(Float, nullable=False)  # 50, 30, 20
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class Installment(Base):
    __tablename__ = "installments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    description = Column(String, nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    total_amount = Column(Float, nullable=False)
    installment_amount = Column(Float, nullable=False)
    total_installments = Column(Integer, nullable=False)
    paid_installments = Column(Integer, nullable=False, default=1)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())

    category = relationship("Category")


class RecurringExpense(Base):
    __tablename__ = "recurring_expenses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    description = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())

    category = relationship("Category")
