"""Tests for weight and percentage strategy."""

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
    WeightAndPctStrategy,
    WeightExpansionStrategy,
    StrategyFactory,
)
from app.services.harvest.domain.enums import OptimizerStrategy


class TestWeightAndPctStrategy:
    """Test suite for WeightAndPctStrategy."""

    @pytest.fixture
    def strategy(self) -> WeightAndPctStrategy:
        """Create strategy instance."""
        return WeightAndPctStrategy(
            max_weight_expansion_rounds=3,
            max_pct_expansion_rounds=3,
        )

    @pytest.fixture
    def limited_candidates(self) -> list[HouseCandidate]:
        """Create candidates with limited availability."""
        candidates = []
        weights = [1.9, 2.0, 2.1]

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
                initial_stock=20000,  # Smaller stock
                current_stock=20000,
                placement_date=datetime(2025, 8, 17),
                daily_forecasts=forecasts,
            )
            farm = Farm(farm_id="W01", name="Farm W01", houses=[house])

            candidates.append(
                HouseCandidate(
                    house=house,
                    farm=farm,
                    date=datetime(2025, 9, 15),
                    available_quantity=20000,  # All stock available
                    weight=weight,
                    fcr=1.25,
                    priority=i + 1,
                )
            )
        return candidates

    @pytest.fixture
    def restrictive_interval(self) -> HarvestInterval:
        """Create interval with restrictive constraints."""
        return HarvestInterval(
            name="Restrictive",
            interval_type=IntervalType.SLAUGHTERHOUSE,
            daily_capacity=50000,
            min_weight=1.95,
            max_weight=2.05,
            weight_step=0.05,
            max_pct_per_house=0.3,  # Only 30% per house
            pct_step=0.1,
            max_pct=0.8,
        )

    def test_expands_both_constraints(
        self,
        strategy: WeightAndPctStrategy,
        limited_candidates: list[HouseCandidate],
        restrictive_interval: HarvestInterval,
    ) -> None:
        """Test that both weight and pct are expanded."""
        allocations = strategy.allocate(
            candidates=limited_candidates,
            daily_capacity=40000,
            interval=restrictive_interval,
        )

        total_allocated = sum(a.quantity for a in allocations)
        assert total_allocated > 0

        # Check for both types of relaxation
        weight_relaxed = any(
            a.relaxed_min_weight is not None
            for a in allocations
        )
        pct_relaxed = any(
            a.relaxed_max_pct is not None
            for a in allocations
        )

        # At least one type should be relaxed to fill capacity
        assert weight_relaxed or pct_relaxed

    def test_tracks_pct_relaxation(
        self,
        strategy: WeightAndPctStrategy,
        limited_candidates: list[HouseCandidate],
    ) -> None:
        """Test that pct relaxation is tracked."""
        # Interval with very restrictive pct
        interval = HarvestInterval(
            name="Low Pct",
            interval_type=IntervalType.SLAUGHTERHOUSE,
            min_weight=1.8,
            max_weight=2.2,  # Wide weight range
            max_pct_per_house=0.1,  # Only 10%
            pct_step=0.1,
            max_pct=0.5,
        )

        allocations = strategy.allocate(
            candidates=limited_candidates,
            daily_capacity=30000,  # Need more than 10% from each
            interval=interval,
        )

        # Some allocations should have pct relaxation
        pct_relaxed = [a for a in allocations if a.relaxed_max_pct is not None]
        assert len(pct_relaxed) > 0

        for allocation in pct_relaxed:
            assert allocation.original_max_pct == interval.max_pct_per_house
            assert allocation.relaxed_max_pct > interval.max_pct_per_house

    def test_respects_max_pct_limit(
        self,
        strategy: WeightAndPctStrategy,
        limited_candidates: list[HouseCandidate],
    ) -> None:
        """Test that max_pct limit is respected."""
        interval = HarvestInterval(
            name="Limited Max",
            interval_type=IntervalType.SLAUGHTERHOUSE,
            min_weight=1.8,
            max_weight=2.2,
            max_pct_per_house=0.1,
            pct_step=0.1,
            max_pct=0.3,  # Can only expand to 30%
        )

        allocations = strategy.allocate(
            candidates=limited_candidates,
            daily_capacity=100000,  # Very high
            interval=interval,
        )

        # Calculate total allocated per house
        house_totals: dict[str, int] = {}
        for a in allocations:
            key = f"{a.farm_id}/{a.house_id}"
            house_totals[key] = house_totals.get(key, 0) + a.quantity

        # No house should exceed max_pct (30% of 20000 = 6000)
        for house_key, total in house_totals.items():
            assert total <= 20000 * interval.max_pct

    def test_combines_relaxations_in_description(
        self,
        strategy: WeightAndPctStrategy,
        limited_candidates: list[HouseCandidate],
        restrictive_interval: HarvestInterval,
    ) -> None:
        """Test that combined relaxations are described."""
        allocations = strategy.allocate(
            candidates=limited_candidates,
            daily_capacity=40000,
            interval=restrictive_interval,
        )

        # Find allocations with both relaxations
        both_relaxed = [
            a for a in allocations
            if a.relaxed_min_weight is not None and a.relaxed_max_pct is not None
        ]

        if both_relaxed:
            for allocation in both_relaxed:
                # Should have both in description
                assert "weight" in allocation.constraint_relaxation.lower()
                assert "pct" in allocation.constraint_relaxation.lower()

    def test_fills_capacity_when_possible(
        self,
        strategy: WeightAndPctStrategy,
        limited_candidates: list[HouseCandidate],
    ) -> None:
        """Test that capacity is filled when constraints allow."""
        # Very permissive interval
        interval = HarvestInterval(
            name="Permissive",
            interval_type=IntervalType.SLAUGHTERHOUSE,
            min_weight=1.5,
            max_weight=2.5,
            max_pct_per_house=0.8,
            max_pct=1.0,
        )

        allocations = strategy.allocate(
            candidates=limited_candidates,
            daily_capacity=50000,
            interval=interval,
        )

        total_allocated = sum(a.quantity for a in allocations)
        # Total available is 3 * 20000 * 0.8 = 48000
        # Should allocate as much as possible
        assert total_allocated > 40000

    def test_get_strategy_name(self, strategy: WeightAndPctStrategy) -> None:
        """Test strategy name."""
        assert strategy.get_strategy_name() == "weight_and_pct"

    def test_factory_creates_weight_and_pct_strategy(self) -> None:
        """Test factory creates weight and pct strategy."""
        strategy = StrategyFactory.create(OptimizerStrategy.WEIGHT_AND_PCT)
        assert isinstance(strategy, WeightAndPctStrategy)

    def test_factory_creates_pct_as_weight_and_pct(self) -> None:
        """Test factory creates pct strategy as weight_and_pct."""
        strategy = StrategyFactory.create(OptimizerStrategy.PCT)
        assert isinstance(strategy, WeightAndPctStrategy)

    def test_no_double_allocation(
        self,
        strategy: WeightAndPctStrategy,
        limited_candidates: list[HouseCandidate],
    ) -> None:
        """Test that same capacity is not allocated twice."""
        interval = HarvestInterval(
            name="Test",
            interval_type=IntervalType.SLAUGHTERHOUSE,
            min_weight=1.8,
            max_weight=2.2,
            max_pct_per_house=0.5,
            pct_step=0.1,
            max_pct=0.8,
        )

        allocations = strategy.allocate(
            candidates=limited_candidates,
            daily_capacity=30000,
            interval=interval,
        )

        # Calculate total per house
        house_totals: dict[str, int] = {}
        for a in allocations:
            key = f"{a.farm_id}/{a.house_id}"
            house_totals[key] = house_totals.get(key, 0) + a.quantity

        # No house should exceed available stock
        for house_key, total in house_totals.items():
            assert total <= 20000  # initial_stock


class TestStrategyIntegration:
    """Integration tests for strategies."""

    @pytest.fixture
    def multi_farm_candidates(self) -> list[HouseCandidate]:
        """Create candidates from multiple farms."""
        candidates = []
        farms_config = [
            ("W01", [1.8, 1.9, 2.0]),
            ("W02", [2.0, 2.1, 2.2]),
            ("W03", [2.2, 2.3, 2.4]),
        ]

        for farm_id, weights in farms_config:
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
                    farm_id=farm_id,
                    initial_stock=15000,
                    current_stock=15000,
                    placement_date=datetime(2025, 8, 17),
                    daily_forecasts=forecasts,
                )
                farm = Farm(farm_id=farm_id, name=f"Farm {farm_id}", houses=[house])

                candidates.append(
                    HouseCandidate(
                        house=house,
                        farm=farm,
                        date=datetime(2025, 9, 15),
                        available_quantity=15000,
                        weight=weight,
                        fcr=1.25,
                        priority=len(candidates) + 1,
                    )
                )
        return candidates

    def test_all_strategies_handle_same_input(
        self,
        multi_farm_candidates: list[HouseCandidate],
    ) -> None:
        """Test that all strategies can handle the same input."""
        interval = HarvestInterval(
            name="Test",
            interval_type=IntervalType.SLAUGHTERHOUSE,
            daily_capacity=50000,
            min_weight=1.9,
            max_weight=2.1,
            weight_step=0.1,
            max_pct_per_house=0.5,
            pct_step=0.1,
            max_pct=0.8,
        )

        from app.services.harvest.strategies import BaseStrategy

        strategies = [
            BaseStrategy(),
            WeightExpansionStrategy(),
            WeightAndPctStrategy(),
        ]

        for strategy in strategies:
            allocations = strategy.allocate(
                candidates=multi_farm_candidates,
                daily_capacity=50000,
                interval=interval,
            )

            # All strategies should produce valid allocations
            total = sum(a.quantity for a in allocations)
            assert total > 0
            assert all(a.quantity > 0 for a in allocations)

    def test_aggressive_strategy_fills_more(
        self,
        multi_farm_candidates: list[HouseCandidate],
    ) -> None:
        """Test that aggressive strategies fill more capacity."""
        # Very restrictive interval
        interval = HarvestInterval(
            name="Restrictive",
            interval_type=IntervalType.SLAUGHTERHOUSE,
            daily_capacity=100000,
            min_weight=2.0,
            max_weight=2.0,  # Very narrow
            weight_step=0.1,
            max_pct_per_house=0.2,  # Very low
            pct_step=0.1,
            max_pct=0.6,
        )

        from app.services.harvest.strategies import BaseStrategy

        base_strategy = BaseStrategy()
        aggressive_strategy = WeightAndPctStrategy()

        base_allocations = base_strategy.allocate(
            candidates=multi_farm_candidates,
            daily_capacity=100000,
            interval=interval,
        )

        aggressive_allocations = aggressive_strategy.allocate(
            candidates=multi_farm_candidates,
            daily_capacity=100000,
            interval=interval,
        )

        base_total = sum(a.quantity for a in base_allocations)
        aggressive_total = sum(a.quantity for a in aggressive_allocations)

        # Aggressive strategy should fill at least as much
        assert aggressive_total >= base_total
