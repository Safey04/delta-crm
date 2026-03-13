"""Pytest configuration and fixtures."""

import sys
from pathlib import Path
from datetime import datetime

import pytest

# Add backend to path for imports
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from app.services.harvest.domain import (
    DailyForecast,
    HarvestEvent,
    HarvestEntry,
    House,
    Farm,
    Cycle,
    HarvestDay,
    HarvestInterval,
    OptimizationConfig,
    HarvestPlan,
    IntervalType,
    OptimizerStrategy,
)


@pytest.fixture
def sample_forecast() -> DailyForecast:
    """Create a sample daily forecast."""
    return DailyForecast(
        date=datetime(2025, 9, 15),
        weight=1.8,
        fcr=1.25,
        mortality=50,
        projected_stock=30000,
        feed_consumed=45000.0,
        price=60.0,
        total_profit=1500000.0,
        profit_per_bird=50.0,
        profit_loss=5000.0,
        priority=10,
        net_meat=54000.0,
    )


@pytest.fixture
def sample_forecasts() -> list[DailyForecast]:
    """Create a list of sample daily forecasts."""
    base_date = datetime(2025, 9, 15)
    forecasts = []

    for i in range(10):
        forecasts.append(
            DailyForecast(
                date=datetime(2025, 9, 15 + i),
                weight=1.8 + (i * 0.05),
                fcr=1.25 + (i * 0.02),
                mortality=50 + i,
                projected_stock=30000 - (i * 100),
                feed_consumed=45000.0 + (i * 1000),
                price=60.0 + (i % 3),
                total_profit=1500000.0 + (i * 50000),
                profit_per_bird=50.0 + i,
                profit_loss=5000.0 + (i * 1000),
                priority=10 - i,
                net_meat=54000.0 + (i * 500),
            )
        )

    return forecasts


@pytest.fixture
def sample_house(sample_forecasts: list[DailyForecast]) -> House:
    """Create a sample house with forecasts."""
    return House(
        house_id="H01",
        farm_id="W03",
        initial_stock=30000,
        current_stock=30000,
        placement_date=datetime(2025, 8, 17),
        daily_forecasts=sample_forecasts,
        harvest_history=[],
    )


@pytest.fixture
def sample_farm() -> Farm:
    """Create a sample farm with multiple houses."""
    houses = []
    for i in range(1, 4):  # 3 houses
        house_id = f"H{i:02d}"
        forecasts = [
            DailyForecast(
                date=datetime(2025, 9, 15 + j),
                weight=1.8 + (j * 0.05),
                fcr=1.25,
                mortality=50,
                projected_stock=30000 - (j * 100),
                feed_consumed=45000.0,
                price=60.0,
                total_profit=1500000.0,
                profit_per_bird=50.0,
                profit_loss=5000.0,
                priority=10,
                net_meat=54000.0,
            )
            for j in range(5)
        ]

        houses.append(
            House(
                house_id=house_id,
                farm_id="W03",
                initial_stock=30000,
                current_stock=30000,
                placement_date=datetime(2025, 8, 17),
                daily_forecasts=forecasts,
                harvest_history=[],
            )
        )

    return Farm(
        farm_id="W03",
        name="Farm W03",
        houses=houses,
        organization_code="default",
    )


@pytest.fixture
def sample_cycle(sample_farm: Farm) -> Cycle:
    """Create a sample cycle with one farm."""
    return Cycle(
        cycle_number=1,
        year=2025,
        farms=[sample_farm],
        start_date=datetime(2025, 8, 17),
        end_date=datetime(2025, 9, 30),
    )


@pytest.fixture
def sample_interval() -> HarvestInterval:
    """Create a sample harvest interval."""
    return HarvestInterval(
        name="Slaughterhouse 1",
        interval_type=IntervalType.SLAUGHTERHOUSE,
        daily_capacity=30000,
        min_weight=1.8,
        max_weight=2.5,
        start_date=datetime(2025, 9, 15),
        end_date=datetime(2025, 9, 30),
    )
