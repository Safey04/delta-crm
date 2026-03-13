"""Tests for base allocation strategy."""

from datetime import datetime

import pytest

from app.services.harvest.domain import (
    Farm,
    House,
    DailyForecast,
    HarvestInterval,
    IntervalType,
)
from app.services.harvest.optimizers import HouseCandidate
from app.services.harvest.strategies import (
    BaseStrategy,
    HarvestAllocation,
    StrategyFactory,
)
from app.services.harvest.domain.enums import OptimizerStrategy


class TestHarvestAllocation:
    """Test suite for HarvestAllocation class."""

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

    def test_create_allocation(
        self, sample_house: House, sample_farm: Farm
    ) -> None:
        """Test basic allocation creation."""
        allocation = HarvestAllocation(
            house=sample_house,
            farm=sample_farm,
            date=datetime(2025, 9, 15),
            quantity=10000,
            weight=2.0,
            fcr=1.25,
        )

        assert allocation.quantity == 10000
        assert allocation.weight == 2.0
        assert allocation.fcr == 1.25
        assert allocation.was_relaxed is False

    def test_allocation_with_relaxation(
        self, sample_house: House, sample_farm: Farm
    ) -> None:
        """Test allocation with constraint relaxation."""
        allocation = HarvestAllocation(
            house=sample_house,
            farm=sample_farm,
            date=datetime(2025, 9, 15),
            quantity=10000,
            weight=2.0,
            fcr=1.25,
            constraint_relaxation="weight expanded: 1.8-2.2 -> 1.7-2.3",
            original_min_weight=1.8,
            original_max_weight=2.2,
            relaxed_min_weight=1.7,
            relaxed_max_weight=2.3,
        )

        assert allocation.was_relaxed is True
        assert "weight expanded" in allocation.constraint_relaxation

    def test_total_weight(
        self, sample_house: House, sample_farm: Farm
    ) -> None:
        """Test total weight calculation."""
        allocation = HarvestAllocation(
            house=sample_house,
            farm=sample_farm,
            date=datetime(2025, 9, 15),
            quantity=10000,
            weight=2.0,
            fcr=1.25,
        )

        assert allocation.total_weight == 20000.0

    def test_to_harvest_entry(
        self, sample_house: House, sample_farm: Farm
    ) -> None:
        """Test conversion to harvest entry."""
        allocation = HarvestAllocation(
            house=sample_house,
            farm=sample_farm,
            date=datetime(2025, 9, 15),
            quantity=10000,
            weight=2.0,
            fcr=1.25,
            priority=5,
            score=20000.0,
        )

        entry = allocation.to_harvest_entry(reason="Test allocation")

        assert entry.farm_id == "W03"
        assert entry.house_id == "H01"
        assert entry.quantity == 10000
        assert entry.priority == 5

    def test_from_candidate(
        self, sample_house: House, sample_farm: Farm
    ) -> None:
        """Test creating allocation from candidate."""
        candidate = HouseCandidate(
            house=sample_house,
            farm=sample_farm,
            date=datetime(2025, 9, 15),
            available_quantity=10000,
            weight=2.0,
            fcr=1.25,
            score=20000.0,
            priority=3,
        )

        allocation = HarvestAllocation.from_candidate(
            candidate=candidate,
            quantity=5000,
            constraint_relaxation="test relaxation",
        )

        assert allocation.quantity == 5000
        assert allocation.weight == 2.0
        assert allocation.priority == 3
        assert allocation.constraint_relaxation == "test relaxation"


class TestBaseStrategy:
    """Test suite for BaseStrategy."""

    @pytest.fixture
    def strategy(self) -> BaseStrategy:
        """Create strategy instance."""
        return BaseStrategy()

    @pytest.fixture
    def sample_candidates(self) -> list[HouseCandidate]:
        """Create sample candidates."""
        candidates = []
        for i in range(3):
            forecasts = [
                DailyForecast(
                    date=datetime(2025, 9, 15),
                    weight=1.9 + (i * 0.1),  # 1.9, 2.0, 2.1
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
            house = House(
                house_id=f"H{i+1:02d}",
                farm_id="W01",
                initial_stock=30000,
                current_stock=30000,
                placement_date=datetime(2025, 8, 17),
                daily_forecasts=forecasts,
            )
            farm = Farm(farm_id="W01", name="Farm W01", houses=[house])

            candidates.append(
                HouseCandidate(
                    house=house,
                    farm=farm,
                    date=datetime(2025, 9, 15),
                    available_quantity=10000,
                    weight=1.9 + (i * 0.1),
                    fcr=1.25,
                    priority=i + 1,
                )
            )
        return candidates

    @pytest.fixture
    def interval(self) -> HarvestInterval:
        """Create a test interval."""
        return HarvestInterval(
            name="Test",
            interval_type=IntervalType.SLAUGHTERHOUSE,
            daily_capacity=30000,
            min_weight=1.8,
            max_weight=2.2,
        )

    def test_allocate_fills_capacity(
        self,
        strategy: BaseStrategy,
        sample_candidates: list[HouseCandidate],
        interval: HarvestInterval,
    ) -> None:
        """Test that allocation fills capacity."""
        allocations = strategy.allocate(
            candidates=sample_candidates,
            daily_capacity=25000,
            interval=interval,
        )

        total_allocated = sum(a.quantity for a in allocations)
        assert total_allocated == 25000

    def test_allocate_respects_weight_constraints(
        self,
        strategy: BaseStrategy,
        sample_candidates: list[HouseCandidate],
    ) -> None:
        """Test that allocation respects weight constraints."""
        # Narrow interval that excludes some candidates
        narrow_interval = HarvestInterval(
            name="Narrow",
            interval_type=IntervalType.SLAUGHTERHOUSE,
            min_weight=1.95,
            max_weight=2.05,
        )

        allocations = strategy.allocate(
            candidates=sample_candidates,
            daily_capacity=30000,
            interval=narrow_interval,
        )

        # Only candidate with weight 2.0 should be selected
        assert len(allocations) == 1
        assert allocations[0].weight == 2.0

    def test_allocate_no_relaxation(
        self,
        strategy: BaseStrategy,
        sample_candidates: list[HouseCandidate],
        interval: HarvestInterval,
    ) -> None:
        """Test that base strategy does not relax constraints."""
        allocations = strategy.allocate(
            candidates=sample_candidates,
            daily_capacity=25000,
            interval=interval,
        )

        for allocation in allocations:
            assert allocation.was_relaxed is False
            assert allocation.constraint_relaxation is None

    def test_allocate_respects_priority_order(
        self,
        strategy: BaseStrategy,
        sample_candidates: list[HouseCandidate],
        interval: HarvestInterval,
    ) -> None:
        """Test that allocation follows priority order."""
        # Request less than one candidate can provide
        allocations = strategy.allocate(
            candidates=sample_candidates,
            daily_capacity=5000,
            interval=interval,
        )

        # Should select from highest priority (lowest number) first
        assert len(allocations) == 1
        assert allocations[0].priority == 1

    def test_get_strategy_name(self, strategy: BaseStrategy) -> None:
        """Test strategy name."""
        assert strategy.get_strategy_name() == "base"


class TestStrategyFactory:
    """Test suite for StrategyFactory."""

    def test_create_base_strategy(self) -> None:
        """Test creating base strategy."""
        strategy = StrategyFactory.create(OptimizerStrategy.BASE)
        assert isinstance(strategy, BaseStrategy)

    def test_create_by_name(self) -> None:
        """Test creating strategy by name."""
        strategy = StrategyFactory.create_by_name("base")
        assert isinstance(strategy, BaseStrategy)

    def test_create_unknown_raises(self) -> None:
        """Test that unknown strategy name raises error."""
        with pytest.raises(ValueError, match="Unknown strategy"):
            StrategyFactory.create_by_name("unknown")

    def test_get_available_strategies(self) -> None:
        """Test getting available strategies."""
        strategies = StrategyFactory.get_available_strategies()
        assert "base" in strategies
        assert "weight" in strategies
        assert "weight_and_pct" in strategies
