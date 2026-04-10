"""Testes para app/services/category.py"""

from app.services.category import find_or_create, list_all
from app.core.models import Category


def test_find_existing_category(db):
    cat = find_or_create(db, "alimentação")
    assert cat.name == "alimentação"
    assert cat.id == 1


def test_find_category_case_insensitive(db):
    cat = find_or_create(db, "  Alimentação  ")
    assert cat.name == "alimentação"


def test_create_new_category(db):
    cat = find_or_create(db, "investimentos")
    assert cat.name == "investimentos"
    assert cat.id is not None
    # Verify it persisted
    found = db.query(Category).filter(Category.name == "investimentos").first()
    assert found is not None


def test_list_all(db):
    result = list_all(db)
    assert "Categorias:" in result
    assert "alimentação" in result
    assert "transporte" in result
