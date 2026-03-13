"""Tests for DataLoader."""

from datetime import datetime
from pathlib import Path

import pytest

from app.services.harvest.loaders import DataLoader


class TestDataLoader:
    """Test suite for DataLoader class."""

    @pytest.fixture
    def data_loader(self) -> DataLoader:
        """Create a DataLoader pointing to the test data."""
        # Use the actual data file
        data_path = Path(__file__).parent.parent.parent / "data" / "raw" / "predicted_data_combined.csv"
        return DataLoader(data_path=data_path)

    def test_load_data(self, data_loader: DataLoader) -> None:
        """Test loading the CSV data."""
        df = data_loader.load()

        assert df is not None
        assert len(df) > 0
        assert "farm" in df.columns
        assert "house" in df.columns
        assert "date" in df.columns

    def test_load_caches_data(self, data_loader: DataLoader) -> None:
        """Test that data is cached after first load."""
        df1 = data_loader.load()
        df2 = data_loader.load()

        # Should be the same object (cached)
        assert df1 is df2

    def test_get_raw_dataframe(self, data_loader: DataLoader) -> None:
        """Test getting a copy of the raw DataFrame."""
        df = data_loader.get_raw_dataframe()

        assert df is not None
        # Should be a copy, not the cached version
        assert df is not data_loader._df

    def test_build_cycle(self, data_loader: DataLoader) -> None:
        """Test building a complete Cycle from data."""
        cycle = data_loader.build_cycle(cycle_number=1, year=2025)

        assert cycle is not None
        assert cycle.cycle_number == 1
        assert cycle.year == 2025
        assert len(cycle.farms) > 0

    def test_build_cycle_has_farms(self, data_loader: DataLoader) -> None:
        """Test that built cycle contains farms."""
        cycle = data_loader.build_cycle()

        farm_ids = [f.farm_id for f in cycle.farms]
        assert len(farm_ids) > 0
        # Check that W03 is in the data (from our sample)
        assert "W03" in farm_ids

    def test_build_cycle_farms_have_houses(self, data_loader: DataLoader) -> None:
        """Test that farms have houses."""
        cycle = data_loader.build_cycle()

        for farm in cycle.farms:
            assert len(farm.houses) > 0

    def test_build_cycle_houses_have_forecasts(self, data_loader: DataLoader) -> None:
        """Test that houses have daily forecasts."""
        cycle = data_loader.build_cycle()

        for farm in cycle.farms:
            for house in farm.houses:
                assert len(house.daily_forecasts) > 0

                # Check forecast fields
                forecast = house.daily_forecasts[0]
                assert forecast.date is not None
                assert forecast.weight > 0
                assert forecast.fcr > 0
                assert forecast.projected_stock > 0

    def test_forecast_has_all_fields(self, data_loader: DataLoader) -> None:
        """Test that forecasts have all expected fields from CSV."""
        cycle = data_loader.build_cycle()

        house = cycle.farms[0].houses[0]
        forecast = house.daily_forecasts[0]

        # Check all fields are populated
        assert hasattr(forecast, 'date')
        assert hasattr(forecast, 'weight')
        assert hasattr(forecast, 'fcr')
        assert hasattr(forecast, 'mortality')
        assert hasattr(forecast, 'projected_stock')
        assert hasattr(forecast, 'feed_consumed')
        assert hasattr(forecast, 'price')
        assert hasattr(forecast, 'total_profit')
        assert hasattr(forecast, 'profit_per_bird')
        assert hasattr(forecast, 'profit_loss')
        assert hasattr(forecast, 'priority')
        assert hasattr(forecast, 'net_meat')

    def test_get_farm_ids(self, data_loader: DataLoader) -> None:
        """Test getting list of farm IDs."""
        farm_ids = data_loader.get_farm_ids()

        assert len(farm_ids) > 0
        assert all(isinstance(fid, str) for fid in farm_ids)
        # Should be sorted
        assert farm_ids == sorted(farm_ids)

    def test_get_house_ids(self, data_loader: DataLoader) -> None:
        """Test getting list of house IDs."""
        house_ids = data_loader.get_house_ids()

        assert len(house_ids) > 0
        assert all(isinstance(hid, str) for hid in house_ids)

    def test_get_house_ids_for_farm(self, data_loader: DataLoader) -> None:
        """Test getting house IDs for a specific farm."""
        farm_ids = data_loader.get_farm_ids()
        if not farm_ids:
            pytest.skip("No farms in data")

        house_ids = data_loader.get_house_ids(farm_id=farm_ids[0])

        assert len(house_ids) > 0

    def test_get_date_range(self, data_loader: DataLoader) -> None:
        """Test getting the date range of the data."""
        start, end = data_loader.get_date_range()

        assert start is not None
        assert end is not None
        assert start <= end

    def test_get_farm_house_data(self, data_loader: DataLoader) -> None:
        """Test getting data for a specific farm/house."""
        farm_ids = data_loader.get_farm_ids()
        if not farm_ids:
            pytest.skip("No farms in data")

        house_ids = data_loader.get_house_ids(farm_id=farm_ids[0])
        if not house_ids:
            pytest.skip("No houses in farm")

        df = data_loader.get_farm_house_data(farm_ids[0], house_ids[0])

        assert len(df) > 0
        assert all(df["farm"] == farm_ids[0])
        assert all(df["house"] == house_ids[0])

    def test_get_data_summary(self, data_loader: DataLoader) -> None:
        """Test getting a summary of the data."""
        summary = data_loader.get_data_summary()

        assert "total_rows" in summary
        assert "farm_count" in summary
        assert "house_count" in summary
        assert "date_range" in summary
        assert "farms" in summary

        assert summary["total_rows"] > 0
        assert summary["farm_count"] > 0

    def test_house_can_lookup_forecasts(self, data_loader: DataLoader) -> None:
        """Test that houses can look up forecasts by date."""
        cycle = data_loader.build_cycle()

        house = cycle.farms[0].houses[0]
        forecast_date = house.daily_forecasts[0].date

        # Should be able to look up by date
        weight = house.get_weight_on_date(forecast_date)
        fcr = house.get_fcr_on_date(forecast_date)
        profit = house.get_profit_on_date(forecast_date)
        priority = house.get_priority_on_date(forecast_date)

        assert weight > 0
        assert fcr > 0
        assert priority >= 0

    def test_file_not_found(self) -> None:
        """Test that FileNotFoundError is raised for missing file."""
        loader = DataLoader(data_path="/nonexistent/path.csv")

        with pytest.raises(FileNotFoundError):
            loader.load()

    def test_stock_balance_integrity(self, data_loader: DataLoader) -> None:
        """Test that initial stock matches first day's expected stock."""
        cycle = data_loader.build_cycle()

        for farm in cycle.farms:
            for house in farm.houses:
                # Initial stock should match first forecast's projected stock
                first_forecast = house.daily_forecasts[0]
                assert house.initial_stock == first_forecast.projected_stock
