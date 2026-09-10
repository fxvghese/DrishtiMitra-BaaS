"""Test for PostgreSQL upsert construction regression."""

import pytest
from unittest.mock import MagicMock, patch
from sqlalchemy.dialects.postgresql import insert as pg_insert
from backend.services.catalogue.importer import _bulk_upsert, _to_column_names
from backend.models.entities import ReferenceProduct


def test_bulk_upsert_postgresql_constructs_correct_statement():
    """Test that PostgreSQL upsert constructs correct ON CONFLICT statement."""
    # Mock a PostgreSQL session
    mock_db = MagicMock()
    mock_db.bind.dialect.name = "postgresql"
    
    items = [
        {
            "source": "open_food_facts",
            "external_id": "12345",
            "product_name": "Test Product",
            "generic_name": "Generic",
            "brand": "Test Brand",
            "category": "Test Category",
            "quantity": "100g",
            "mrp": None,
            "description": None,
            "image_url": None,
            "source_url": None,
            "metadata": '{"test": "data"}',
        }
    ]
    
    # Mock the execute result
    mock_result = MagicMock()
    mock_db.execute.return_value = mock_result
    mock_result.rowcount = 1
    
    # This should not raise an exception about MetaData or _bulk_update_tuples
    inserted, updated = _bulk_upsert(mock_db, items)
    
    # Verify the execute was called with a pg_insert statement
    mock_db.execute.assert_called_once()
    call_args = mock_db.execute.call_args[0][0]
    
    # Verify it's a PostgreSQL insert with ON CONFLICT
    assert "ON CONFLICT" in str(call_args.compile(compile_kwargs={"literal_binds": True}))
    assert "ON CONFLICT (source, external_id) DO UPDATE" in str(call_args.compile(compile_kwargs={"literal_binds": True}))
    
    # Should have called commit
    # (Note: commit is called by the caller, not _bulk_upsert)


def test_to_column_names_mapping():
    """Test that attribute names are correctly mapped to column names."""
    items = [
        {
            "source": "open_food_facts",
            "external_id": "12345",
            "product_name": "Test Product",
            "product_metadata": '{"test": "data"}',  # attribute name
        }
    ]
    
    result = _to_column_names(items)
    
    # Should map product_metadata -> metadata
    assert "product_metadata" not in result[0]
    assert "metadata" in result[0]
    assert result[0]["metadata"] == '{"test": "data"}'
    
    # Other fields should remain unchanged
    assert result[0]["source"] == "open_food_facts"
    assert result[0]["external_id"] == "12345"


def test_to_column_names_preserves_other_fields():
    """Test that other fields are preserved correctly."""
    items = [
        {
            "source": "flipkart",
            "external_id": "fk_123",
            "product_name": "Test Product",
            "brand": "Test Brand",
            "mrp": 100.0,
        }
    ]
    
    result = _to_column_names(items)
    
    assert result[0]["source"] == "flipkart"
    assert result[0]["external_id"] == "fk_123"
    assert result[0]["product_name"] == "Test Product"
    assert result[0]["brand"] == "Test Brand"
    assert result[0]["mrp"] == 100.0