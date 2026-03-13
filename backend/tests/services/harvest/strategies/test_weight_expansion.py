"""Tests for weight expansion strategy."""

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
    WeightExpansionStrategy,
    StrategyFactory,
)
from app.services.harvest.domain.enums import OptimizerStrategy


class TestWeightExpansionStrategy:
    """Test suite for WeightExpansionStrategy."""

    @pytest.fixture
    def strategy(self) -> WeightExpansionStrategy:
        """Create strategy instance."""
        return WeightExpansionStrategy(max_expansion_rounds=5)

    @pytest.fixture
    def candidates_varied_weights(self) -> list[HouseCandidate]:
        """Create candidates with varied weights."""
        candidates = []
        weights = [1.5, 1.7, 1.9, 2.0, 2.1, 2.3, 2.5]  # Various weights

        for i, weight in enumerate(weights):
            forecasts = [
                DailyForecast(
                    date=datetime(2025, 9, 15),
                    weight=weight,
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
                    weight=weight,
                    fcr=1.25,
                    priority=i + 1,
                )
            )
        return candidates

    @pytest.fixture
    def narrow_interval(self) -> HarvestInterval:
        """Create interval with narrow weight range."""
        return HarvestInterval(
            name="Narrow",
            interval_type=IntervalType.SLAUGHTERHOUSE,
            daily_capacity=50000,
            min_weight=1.95,
            max_weight=2.05,
            weight_step=0.1,
        )

    def test_expands_weight_range(
        self,
        strategy: WeightExpansionStrategy,
        candidates_varied_weights: list[HouseCandidate],
        narrow_interval: HarvestInterval,
    ) -> None:
        """Test that weight range is expanded to fill capacity."""
        allocations = strategy.allocate(
            candidates=candidates_varied_weights,
            daily_capacity=30000,
            interval=narrow_interval,
        )

        total_allocated = sum(a.quantity for a in allocations)
        assert total_allocated == 30000

        # Should have allocated from candidates outside original range
        weights_used = {a.weight for a in allocations}
        # Should include weights outside 1.95-2.05
        assert len(weights_used) > 1

    def test_tracks_weight_relaxation(
        self,
        strategy: WeightExpansionStrategy,
        candidates_varied_weights: list[HouseCandidate],
        narrow_interval: HarvestInterval,
    ) -> None:
        """Test that weight relaxation is tracked."""
        allocations = strategy.allocate(
            candidates=candidates_varied_weights,
            daily_capacity=30000,
            interval=narrow_interval,
        )

        # Some allocations should have relaxation
        relaxed = [a for a in allocations if a.was_relaxed]
        assert len(relaxed) > 0

        # Check relaxation details
        for allocation in relaxed:
            assert "weight_expanded" in allocation.constraint_relaxation
            assert allocation.original_min_weight == narrow_interval.min_weight
            assert allocation.original_max_weight == narrow_interval.max_weight

    def test_no_relaxation_when_not_needed(
        self,
        strategy: WeightExpansionStrategy,
        candidates_varied_weights: list[HouseCandidate],
    ) -> None:
        """Test no relaxation when strict constraints are sufficient."""
        # Wide interval that includes all candidates
        wide_interval = HarvestInterval(
            name="Wide",
            interval_type=IntervalType.SLAUGHTERHOUSE,
            min_weight=1.0,
            max_weight=3.0,
        )

        allocations = strategy.allocate(
            candidates=candidates_varied_weights,
            daily_capacity=20000,
            interval=wide_interval,
        )

        # No relaxation should be needed
        for allocation in allocations:
            assert allocation.was_relaxed is False

    def test_stops_at_max_expansion(
        self,
        candidates_varied_weights: list[HouseCandidate],
    ) -> None:
        """Test that expansion stops at max rounds."""
        # Strategy with limited expansion
        strategy = WeightExpansionStrategy(max_expansion_rounds=1)

        # Very narrow interval
        narrow_interval = HarvestInterval(
            name="Very Narrow",
            interval_type=IntervalType.SLAUGHTERHOUSE,
            min_weight=2.0,
            max_weight=2.0,  # Exact match only
            weight_step=0.05,
        )

        allocations = strategy.allocate(
            candidates=candidates_varied_weights,
            daily_capacity=100000,  # More than available
            interval=narrow_interval,
        )

        # Should have limited allocation due to expansion limit
        # With max_rounds=1, can only expand to 1.95-2.05
        weights_used = {a.weight for a in allocations}
        # Should not include 1.5, 1.7, 2.3, 2.5 (too far from original)
        for w in weights_used:
            assert 1.9 <= w <= 2.15  # 2 rounds: 2.0 +/- 2*0.05

    def test_symmetric_expansion(
        self,
        strategy: WeightExpansionStrategy,
        candidates_varied_weights: list[HouseCandidate],
    ) -> None:
        """Test that expansion is symmetric around original range."""
        interval = HarvestInterval(
            name="Test",
            interval_type=IntervalType.SLAUGHTERHOUSE,
            min_weight=2.0,
            max_weight=2.0,
            weight_step=0.1,
        )

        allocations = strategy.allocate(
            candidates=candidates_varied_weights,
            daily_capacity=50000,
            interval=interval,
        )

        # Check that expansion was symmetric
        for allocation in allocations:
            if allocation.relaxed_min_weight is not None:
                original_range = interval.max_weight - interval.min_weight
                relaxed_range = allocation.relaxed_max_weight - allocation.relaxed_min_weight
                # Relaxed range should be larger
                assert relaxed_range >= original_range

    def test_get_strategy_name(self, strategy: WeightExpansionStrategy) -> None:
        """Test strategy name."""
        assert strategy.get_strategy_name() == "weight_expansion"

    def test_factory_creates_weight_strategy(self) -> None:
        """Test factory creates weight expansion strategy."""
        strategy = StrategyFactory.create(OptimizerStrategy.WEIGHT)
        assert isinstance(strategy, WeightExpansionStrategy)
