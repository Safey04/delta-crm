"""Tests for House domain model."""

from datetime import datetime

import pytest

from app.services.harvest.domain import (
    House,
    DailyForecast,
    HarvestEvent,
    ForecastNotFoundError,
)


class TestHouse:
    """Test suite for House class."""

    def test_create_house(self, sample_house: House) -> None:
        """Test basic house creation."""
        assert sample_house.house_id == "H01"
        assert sample_house.farm_id == "W03"
        assert sample_house.initial_stock == 30000
        assert sample_house.current_stock == 30000
        assert len(sample_house.daily_forecasts) == 10

    def test_get_weight_on_date(self, sample_house: House) -> None:
        """Test getting weight for a specific date."""
        weight = sample_house.get_weight_on_date(datetime(2025, 9, 15))
        assert weight == 1.8

        weight = sample_house.get_weight_on_date(datetime(2025, 9, 16))
        assert weight == 1.85

    def test_get_fcr_on_date(self, sample_house: House) -> None:
        """Test getting FCR for a specific date."""
        fcr = sample_house.get_fcr_on_date(datetime(2025, 9, 15))
        assert fcr == 1.25

    def test_get_profit_on_date(self, sample_house: House) -> None:
        """Test getting profit for a specific date."""
        profit = sample_house.get_profit_on_date(datetime(2025, 9, 15))
        assert profit == 1500000.0

    def test_get_profit_loss_on_date(self, sample_house: House) -> None:
        """Test getting profit loss for a specific date."""
        profit_loss = sample_house.get_profit_loss_on_date(datetime(2025, 9, 15))
        assert profit_loss == 5000.0

    def test_get_priority_on_date(self, sample_house: House) -> None:
        """Test getting priority for a specific date."""
        priority = sample_house.get_priority_on_date(datetime(2025, 9, 15))
        assert priority == 10

    def test_forecast_not_found(self, sample_house: House) -> None:
        """Test that ForecastNotFoundError is raised for invalid date."""
        with pytest.raises(ForecastNotFoundError):
            sample_house.get_weight_on_date(datetime(2025, 1, 1))

    def test_apply_harvest(self, sample_house: House) -> None:
        """Test applying a harvest to a house."""
        event = sample_house.apply_harvest(
            quantity=5000,
            date=datetime(2025, 9, 15),
        )

        assert event.quantity == 5000
        assert event.house_id == "H01"
        assert event.farm_id == "W03"
        assert event.weight_at_harvest == 1.8
        assert sample_house.current_stock == 25000
        assert len(sample_house.harvest_history) == 1

    def test_apply_harvest_exceeds_stock(self, sample_house: House) -> None:
        """Test that harvesting more than available raises error."""
        with pytest.raises(ValueError, match="Cannot harvest"):
            sample_house.apply_harvest(
                quantity=40000,
                date=datetime(2025, 9, 15),
            )

    def test_cumulative_harvested(self, sample_house: House) -> None:
        """Test cumulative harvest tracking."""
        assert sample_house.get_cumulative_harvested() == 0

        sample_house.apply_harvest(quantity=5000, date=datetime(2025, 9, 15))
        assert sample_house.get_cumulative_harvested() == 5000

        sample_house.apply_harvest(quantity=3000, date=datetime(2025, 9, 16))
        assert sample_house.get_cumulative_harvested() == 8000

    def test_remaining_capacity(self, sample_house: House) -> None:
        """Test remaining capacity calculation."""
        # At 45% max, can harvest 13500 birds
        assert sample_house.get_remaining_capacity(0.45) == 13500

        # Harvest some birds
        sample_house.apply_harvest(quantity=5000, date=datetime(2025, 9, 15))

        # Now can only harvest 8500 more
        assert sample_house.get_remaining_capacity(0.45) == 8500

    def test_stock_balance_invariant(self, sample_house: House) -> None:
        """Test that initial = current + harvested."""
        sample_house.apply_harvest(quantity=5000, date=datetime(2025, 9, 15))
        sample_house.apply_harvest(quantity=3000, date=datetime(2025, 9, 16))

        assert (
            sample_house.initial_stock
            == sample_house.current_stock + sample_house.get_cumulative_harvested()
        )

    def test_to_dict(self, sample_house: House) -> None:
        """Test dictionary conversion."""
        data = sample_house.to_dict()

        assert data["house_id"] == "H01"
        assert data["farm_id"] == "W03"
        assert data["initial_stock"] == 30000
        assert data["current_stock"] == 30000
        assert data["cumulative_harvested"] == 0
        assert data["forecast_count"] == 10

    def test_get_available_stock(self, sample_house: House) -> None:
        """Test available stock calculation with prior harvests."""
        # Initial available stock
        available = sample_house.get_available_stock(datetime(2025, 9, 15))
        assert available == 30000

        # After harvest
        sample_house.apply_harvest(quantity=5000, date=datetime(2025, 9, 15))
        available = sample_house.get_available_stock(datetime(2025, 9, 16))
        # projected_stock on 9/16 is 29900, minus 5000 harvested = 24900
        assert available == 29900 - 5000

    def test_has_forecast_for_date(self, sample_house: House) -> None:
        """Test forecast existence check."""
        assert sample_house.has_forecast_for_date(datetime(2025, 9, 15)) is True
        assert sample_house.has_forecast_for_date(datetime(2025, 1, 1)) is False

    def test_get_date_range(self, sample_house: House) -> None:
        """Test getting forecast date range."""
        date_range = sample_house.get_date_range()
        assert date_range is not None
        start, end = date_range
        assert start == datetime(2025, 9, 15)
        assert end == datetime(2025, 9, 24)
