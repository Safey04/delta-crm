"""Tests for Cycle domain model."""

from datetime import datetime

import pytest

from app.services.harvest.domain import (
    Cycle,
    Farm,
    EntityNotFoundError,
)


class TestCycle:
    """Test suite for Cycle class."""

    def test_create_cycle(self, sample_cycle: Cycle) -> None:
        """Test basic cycle creation."""
        assert sample_cycle.cycle_number == 1
        assert sample_cycle.year == 2025
        assert len(sample_cycle.farms) == 1

    def test_cycle_id(self, sample_cycle: Cycle) -> None:
        """Test cycle ID generation."""
        assert sample_cycle.cycle_id == "2025-01"

    def test_get_farm(self, sample_cycle: Cycle) -> None:
        """Test getting a farm by ID."""
        farm = sample_cycle.get_farm("W03")
        assert farm.farm_id == "W03"

    def test_get_farm_not_found(self, sample_cycle: Cycle) -> None:
        """Test that EntityNotFoundError is raised for invalid farm."""
        with pytest.raises(EntityNotFoundError):
            sample_cycle.get_farm("W99")

    def test_has_farm(self, sample_cycle: Cycle) -> None:
        """Test farm existence check."""
        assert sample_cycle.has_farm("W03") is True
        assert sample_cycle.has_farm("W99") is False

    def test_get_house(self, sample_cycle: Cycle) -> None:
        """Test getting a house by farm and house ID."""
        house = sample_cycle.get_house("W03", "H01")
        assert house.house_id == "H01"
        assert house.farm_id == "W03"

    def test_get_total_stock(self, sample_cycle: Cycle) -> None:
        """Test total initial stock calculation."""
        # 1 farm with 3 houses, 30000 each
        assert sample_cycle.get_total_stock() == 90000

    def test_get_current_stock(self, sample_cycle: Cycle) -> None:
        """Test total current stock calculation."""
        assert sample_cycle.get_current_stock() == 90000

    def test_get_harvested_stock(self, sample_cycle: Cycle) -> None:
        """Test total harvested calculation."""
        assert sample_cycle.get_harvested_stock() == 0

        house = sample_cycle.get_house("W03", "H01")
        house.apply_harvest(quantity=5000, date=datetime(2025, 9, 15))

        assert sample_cycle.get_harvested_stock() == 5000

    def test_get_all_houses(self, sample_cycle: Cycle) -> None:
        """Test getting all houses across all farms."""
        houses = sample_cycle.get_all_houses()
        assert len(houses) == 3

    def test_get_houses_with_stock(self, sample_cycle: Cycle) -> None:
        """Test filtering houses by available stock."""
        houses = sample_cycle.get_houses_with_stock(datetime(2025, 9, 15))
        assert len(houses) == 3

    def test_get_farm_count(self, sample_cycle: Cycle) -> None:
        """Test farm count."""
        assert sample_cycle.get_farm_count() == 1

    def test_get_house_count(self, sample_cycle: Cycle) -> None:
        """Test house count."""
        assert sample_cycle.get_house_count() == 3

    def test_validate_stock_balance_valid(self, sample_cycle: Cycle) -> None:
        """Test stock balance validation with valid state."""
        is_valid, error = sample_cycle.validate_stock_balance()
        assert is_valid is True
        assert error is None

    def test_validate_stock_balance_after_harvest(self, sample_cycle: Cycle) -> None:
        """Test stock balance validation after harvesting."""
        house = sample_cycle.get_house("W03", "H01")
        house.apply_harvest(quantity=5000, date=datetime(2025, 9, 15))

        is_valid, error = sample_cycle.validate_stock_balance()
        assert is_valid is True

    def test_to_dict(self, sample_cycle: Cycle) -> None:
        """Test dictionary conversion."""
        data = sample_cycle.to_dict()

        assert data["cycle_id"] == "2025-01"
        assert data["cycle_number"] == 1
        assert data["year"] == 2025
        assert data["farm_count"] == 1
        assert data["house_count"] == 3
        assert data["total_stock"] == 90000
