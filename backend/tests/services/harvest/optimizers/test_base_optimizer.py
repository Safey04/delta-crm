"""Tests for base optimizer and HouseCandidate."""

from datetime import datetime

import pytest

from app.services.harvest.domain import (
    Cycle,
    Farm,
    House,
    DailyForecast,
    HarvestInterval,
    HarvestEntry,
    IntervalType,
)
from app.services.harvest.optimizers import HouseCandidate
from app.services.harvest.optimizers.net_meat_optimizer import NetMeatOptimizer


class TestHouseCandidate:
    """Test suite for HouseCandidate class."""

    @pytest.fixture
    def sample_house(self) -> House:
        """Create a sample house."""
        forecasts = [
            DailyForecast(
                date=datetime(2025, 9, 15),
                weight=2.0,
                fcr=1.25,
                mortality=50,
                projected_stock=30000,
                feed_consumed=45000.0,
                price=60.0,
                total_profit=1500000.0,
                profit_per_bird=50.0,
                profit_loss=5000.0,
                priority=10,
                net_meat=60000.0,
            )
        ]
        return House(
            house_id="H01",
            farm_id="W03",
            initial_stock=30000,
            current_stock=30000,
            placement_date=datetime(2025, 8, 17),
            daily_forecasts=forecasts,
        )

    @pytest.fixture
    def sample_farm(self, sample_house: House) -> Farm:
        """Create a sample farm."""
        return Farm(
            farm_id="W03",
            name="Farm W03",
            houses=[sample_house],
        )

    @pytest.fixture
    def sample_candidate(
        self, sample_house: House, sample_farm: Farm
    ) -> HouseCandidate:
        """Create a sample candidate."""
        return HouseCandidate(
            house=sample_house,
            farm=sample_farm,
            date=datetime(2025, 9, 15),
            available_quantity=10000,
            weight=2.0,
            fcr=1.25,
            score=20000.0,
            priority=1,
            total_profit=1500000.0,
            profit_loss=5000.0,
            net_meat=60000.0,
        )

    def test_create_candidate(self, sample_candidate: HouseCandidate) -> None:
        """Test basic candidate creation."""
        assert sample_candidate.available_quantity == 10000
        assert sample_candidate.weight == 2.0
        assert sample_candidate.fcr == 1.25
        assert sample_candidate.score == 20000.0
        assert sample_candidate.priority == 1

    def test_farm_id_property(self, sample_candidate: HouseCandidate) -> None:
        """Test farm_id property."""
        assert sample_candidate.farm_id == "W03"

    def test_house_id_property(self, sample_candidate: HouseCandidate) -> None:
        """Test house_id property."""
        assert sample_candidate.house_id == "H01"

    def test_to_harvest_entry(self, sample_candidate: HouseCandidate) -> None:
        """Test converting candidate to harvest entry."""
        entry = sample_candidate.to_harvest_entry(
            quantity=5000,
            reason="Test selection",
        )

        assert isinstance(entry, HarvestEntry)
        assert entry.farm_id == "W03"
        assert entry.house_id == "H01"
        assert entry.quantity == 5000
        assert entry.weight == 2.0
        assert entry.fcr == 1.25
        assert entry.selection_score == 20000.0
        assert entry.selection_reason == "Test selection"
        assert entry.priority == 1

    def test_to_harvest_entry_partial_quantity(
        self, sample_candidate: HouseCandidate
    ) -> None:
        """Test entry with quantity less than available."""
        entry = sample_candidate.to_harvest_entry(quantity=3000)

        assert entry.quantity == 3000
        # Should still use candidate's metrics
        assert entry.weight == 2.0


class TestBaseOptimizer:
    """Test suite for BaseHarvestOptimizer functionality."""

    @pytest.fixture
    def simple_cycle(self) -> Cycle:
        """Create a simple cycle for testing."""
        forecasts = [
            DailyForecast(
                date=datetime(2025, 9, 15 + i),
                weight=1.8 + (i * 0.05),
                fcr=1.2 + (i * 0.02),
                mortality=50,
                projected_stock=30000 - (i * 100),
                feed_consumed=45000.0 + (i * 1000),
                price=60.0,
                total_profit=1500000.0 + (i * 50000),
                profit_per_bird=50.0 + i,
                profit_loss=5000.0 + (i * 1000),
                priority=10 - i,
                net_meat=54000.0 + (i * 1000),
            )
            for i in range(10)
        ]

        houses = [
            House(
                house_id=f"H{j:02d}",
                farm_id="W01",
                initial_stock=30000,
                current_stock=30000,
                placement_date=datetime(2025, 8, 17),
                daily_forecasts=forecasts.copy(),
            )
            for j in range(1, 4)  # 3 houses
        ]

        farm = Farm(farm_id="W01", name="Farm W01", houses=houses)

        return Cycle(
            cycle_number=1,
            year=2025,
            farms=[farm],
            start_date=datetime(2025, 9, 15),
            end_date=datetime(2025, 9, 24),
        )

    @pytest.fixture
    def simple_interval(self) -> HarvestInterval:
        """Create a simple interval for testing."""
        return HarvestInterval(
            name="Test Interval",
            interval_type=IntervalType.SLAUGHTERHOUSE,
            daily_capacity=30000,
            min_weight=1.5,
            max_weight=3.0,
            max_pct_per_house=0.5,
            start_date=datetime(2025, 9, 15),
            end_date=datetime(2025, 9, 20),
            excluded_weekdays=[],  # Don't exclude any days
        )

    @pytest.fixture
    def optimizer(self) -> NetMeatOptimizer:
        """Create an optimizer for testing."""
        return NetMeatOptimizer()

    def test_get_candidates(
        self,
        optimizer: NetMeatOptimizer,
        simple_cycle: Cycle,
        simple_interval: HarvestInterval,
    ) -> None:
        """Test candidate generation."""
        candidates = optimizer._get_candidates(
            simple_cycle,
            simple_interval,
            datetime(2025, 9, 15),
        )

        assert len(candidates) == 3  # 3 houses
        for candidate in candidates:
            assert candidate.available_quantity > 0
            assert candidate.weight >= simple_interval.min_weight
            assert candidate.weight <= simple_interval.max_weight

    def test_get_candidates_respects_weight_constraint(
        self,
        optimizer: NetMeatOptimizer,
        simple_cycle: Cycle,
    ) -> None:
        """Test that weight constraints are respected."""
        # Interval with narrow weight range
        interval = HarvestInterval(
            name="Narrow",
            interval_type=IntervalType.SLAUGHTERHOUSE,
            min_weight=1.8,
            max_weight=1.85,
            start_date=datetime(2025, 9, 15),
            end_date=datetime(2025, 9, 20),
        )

        candidates = optimizer._get_candidates(
            simple_cycle,
            interval,
            datetime(2025, 9, 15),
        )

        # Only houses with weight 1.8 should qualify
        for candidate in candidates:
            assert 1.8 <= candidate.weight <= 1.85

    def test_get_candidates_respects_max_pct(
        self,
        optimizer: NetMeatOptimizer,
        simple_cycle: Cycle,
        simple_interval: HarvestInterval,
    ) -> None:
        """Test that max_pct_per_house is respected."""
        candidates = optimizer._get_candidates(
            simple_cycle,
            simple_interval,
            datetime(2025, 9, 15),
        )

        # With max_pct_per_house=0.5, max available should be 15000
        for candidate in candidates:
            assert candidate.available_quantity <= 15000

    def test_select_by_priority(
        self,
        optimizer: NetMeatOptimizer,
        simple_cycle: Cycle,
        simple_interval: HarvestInterval,
    ) -> None:
        """Test selection by priority."""
        candidates = optimizer._get_candidates(
            simple_cycle,
            simple_interval,
            datetime(2025, 9, 15),
        )
        candidates = optimizer.assign_priorities(candidates)

        # Select with limited capacity
        selections = optimizer._select_by_priority(candidates, 20000)

        total_selected = sum(qty for _, qty in selections)
        assert total_selected == 20000

    def test_select_by_priority_fills_capacity(
        self,
        optimizer: NetMeatOptimizer,
        simple_cycle: Cycle,
        simple_interval: HarvestInterval,
    ) -> None:
        """Test that selection fills capacity completely."""
        candidates = optimizer._get_candidates(
            simple_cycle,
            simple_interval,
            datetime(2025, 9, 15),
        )
        candidates = optimizer.assign_priorities(candidates)

        # Large capacity - should select all available
        total_available = sum(c.available_quantity for c in candidates)
        selections = optimizer._select_by_priority(candidates, 100000)

        total_selected = sum(qty for _, qty in selections)
        assert total_selected == total_available

    def test_create_harvest_day(
        self,
        optimizer: NetMeatOptimizer,
        simple_cycle: Cycle,
        simple_interval: HarvestInterval,
    ) -> None:
        """Test harvest day creation."""
        candidates = optimizer._get_candidates(
            simple_cycle,
            simple_interval,
            datetime(2025, 9, 15),
        )
        candidates = optimizer.assign_priorities(candidates)
        selections = optimizer._select_by_priority(candidates, 20000)

        day = optimizer._create_harvest_day(
            date=datetime(2025, 9, 15),
            selections=selections,
            capacity_limit=30000,
            reason="Test",
        )

        assert day.date == datetime(2025, 9, 15)
        assert day.daily_capacity_used == 20000
        assert day.capacity_limit == 30000
        assert len(day.entries) > 0
