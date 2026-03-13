"""Tests for Farm domain model."""

from datetime import datetime

import pytest

from app.services.harvest.domain import (
    Farm,
    House,
    EntityNotFoundError,
)


class TestFarm:
    """Test suite for Farm class."""

    def test_create_farm(self, sample_farm: Farm) -> None:
        """Test basic farm creation."""
        assert sample_farm.farm_id == "W03"
        assert sample_farm.name == "Farm W03"
        assert len(sample_farm.houses) == 3

    def test_get_house(self, sample_farm: Farm) -> None:
        """Test getting a house by ID."""
        house = sample_farm.get_house("H01")
        assert house.house_id == "H01"

    def test_get_house_not_found(self, sample_farm: Farm) -> None:
        """Test that EntityNotFoundError is raised for invalid house."""
        with pytest.raises(EntityNotFoundError):
            sample_farm.get_house("H99")

    def test_has_house(self, sample_farm: Farm) -> None:
        """Test house existence check."""
        assert sample_farm.has_house("H01") is True
        assert sample_farm.has_house("H99") is False

    def test_get_initial_stock(self, sample_farm: Farm) -> None:
        """Test total initial stock calculation."""
        # 3 houses with 30000 each
        assert sample_farm.get_initial_stock() == 90000

    def test_get_current_stock(self, sample_farm: Farm) -> None:
        """Test total current stock calculation."""
        assert sample_farm.get_current_stock() == 90000

        # Harvest from one house
        house = sample_farm.get_house("H01")
        house.apply_harvest(quantity=5000, date=datetime(2025, 9, 15))

        assert sample_farm.get_current_stock() == 85000

    def test_get_total_harvested(self, sample_farm: Farm) -> None:
        """Test total harvested calculation."""
        assert sample_farm.get_total_harvested() == 0

        house1 = sample_farm.get_house("H01")
        house2 = sample_farm.get_house("H02")

        house1.apply_harvest(quantity=5000, date=datetime(2025, 9, 15))
        house2.apply_harvest(quantity=3000, date=datetime(2025, 9, 15))

        assert sample_farm.get_total_harvested() == 8000

    def test_get_available_stock(self, sample_farm: Farm) -> None:
        """Test available stock aggregation across houses."""
        available = sample_farm.get_available_stock(datetime(2025, 9, 15))
        # 3 houses with 30000 each
        assert available == 90000

    def test_get_harvested_summary(self, sample_farm: Farm) -> None:
        """Test harvest summary generation."""
        house = sample_farm.get_house("H01")
        house.apply_harvest(quantity=5000, date=datetime(2025, 9, 15))

        summary = sample_farm.get_harvested_summary()

        assert summary.farm_id == "W03"
        assert summary.total_harvested == 5000
        assert summary.house_count == 3
        assert summary.houses_with_harvest == 1
        assert summary.harvest_events == 1

    def test_get_houses_with_stock(self, sample_farm: Farm) -> None:
        """Test filtering houses by available stock."""
        houses = sample_farm.get_houses_with_stock(datetime(2025, 9, 15))
        assert len(houses) == 3

        # Deplete one house
        house = sample_farm.get_house("H01")
        for _ in range(6):  # Harvest all stock in chunks
            remaining = house.current_stock
            if remaining > 0:
                house.apply_harvest(
                    quantity=min(5000, remaining),
                    date=datetime(2025, 9, 15),
                )

        # Now only 2 houses with stock
        houses = sample_farm.get_houses_with_stock(
            datetime(2025, 9, 15), min_stock=1000
        )
        # Note: available stock calculation is based on projected - harvested
        # After harvesting 30000, available should be 0 or negative
        assert len(houses) == 2

    def test_to_dict(self, sample_farm: Farm) -> None:
        """Test dictionary conversion."""
        data = sample_farm.to_dict()

        assert data["farm_id"] == "W03"
        assert data["name"] == "Farm W03"
        assert data["house_count"] == 3
        assert data["initial_stock"] == 90000
        assert data["current_stock"] == 90000
        assert data["total_harvested"] == 0
