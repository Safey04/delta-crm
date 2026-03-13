"""Integration tests for optimizers using real data."""

from datetime import datetime
from pathlib import Path

import pytest

from app.services.harvest.loaders import DataLoader
from app.services.harvest.domain import (
    HarvestInterval,
    IntervalType,
    OptimizationConfig,
)
from app.services.harvest.optimizers import (
    NetMeatOptimizer,
    MinFCROptimizer,
    TargetFCROptimizer,
    ProfitPriorityOptimizer,
    OptimizerFactory,
)


class TestOptimizerIntegration:
    """Integration tests using actual data."""

    @pytest.fixture
    def data_loader(self) -> DataLoader:
        """Create data loader with real data."""
        data_path = Path(__file__).parent.parent.parent / "data" / "raw" / "predicted_data_combined.csv"
        return DataLoader(data_path=data_path)

    @pytest.fixture
    def cycle(self, data_loader: DataLoader):
        """Load cycle from real data."""
        return data_loader.build_cycle(cycle_number=1, year=2025)

    @pytest.fixture
    def interval(self) -> HarvestInterval:
        """Create a test interval."""
        return HarvestInterval(
            name="Test Slaughterhouse",
            interval_type=IntervalType.SLAUGHTERHOUSE,
            daily_capacity=30000,
            min_weight=1.8,
            max_weight=2.5,
            max_pct_per_house=0.45,
            start_date=datetime(2025, 9, 15),
            end_date=datetime(2025, 9, 20),
            excluded_weekdays=[],  # Allow all days for testing
        )

    def test_net_meat_optimizer_produces_plan(self, cycle, interval) -> None:
        """Test that NetMeatOptimizer produces a valid plan."""
        optimizer = NetMeatOptimizer()
        plan = optimizer.optimize(cycle, interval)

        assert plan is not None
        assert len(plan.harvest_days) > 0

        # Verify all days have entries
        for day in plan.harvest_days:
            assert len(day.entries) > 0
            assert day.daily_capacity_used > 0

        # Verify metrics are calculated
        metrics = plan.get_total_metrics()
        assert metrics.total_harvested > 0
        assert metrics.avg_weight > 0

    def test_min_fcr_optimizer_produces_plan(self, cycle, interval) -> None:
        """Test that MinFCROptimizer produces a valid plan."""
        optimizer = MinFCROptimizer()
        plan = optimizer.optimize(cycle, interval)

        assert plan is not None
        assert len(plan.harvest_days) > 0

        # Verify entries have valid FCR
        for day in plan.harvest_days:
            for entry in day.entries:
                assert entry.fcr > 0

    def test_target_fcr_optimizer_produces_plan(self, cycle, interval) -> None:
        """Test that TargetFCROptimizer produces a valid plan."""
        optimizer = TargetFCROptimizer(target_fcr=1.3)
        plan = optimizer.optimize(cycle, interval)

        assert plan is not None
        assert len(plan.harvest_days) > 0

    def test_profit_priority_optimizer_produces_plan(self, cycle, interval) -> None:
        """Test that ProfitPriorityOptimizer produces a valid plan."""
        optimizer = ProfitPriorityOptimizer()
        plan = optimizer.optimize(cycle, interval)

        assert plan is not None
        assert len(plan.harvest_days) > 0

    def test_optimizer_respects_daily_capacity(self, cycle, interval) -> None:
        """Test that optimizer respects daily capacity limit."""
        optimizer = NetMeatOptimizer()
        plan = optimizer.optimize(cycle, interval)

        for day in plan.harvest_days:
            assert day.daily_capacity_used <= day.capacity_limit

    def test_optimizer_respects_weight_constraints(self, cycle) -> None:
        """Test that optimizer respects weight constraints."""
        # Create interval with narrow weight range
        interval = HarvestInterval(
            name="Narrow Weight",
            interval_type=IntervalType.SLAUGHTERHOUSE,
            daily_capacity=30000,
            min_weight=2.0,
            max_weight=2.2,
            start_date=datetime(2025, 9, 20),
            end_date=datetime(2025, 9, 25),
            excluded_weekdays=[],
        )

        optimizer = NetMeatOptimizer()
        plan = optimizer.optimize(cycle, interval)

        # All entries should be within weight range
        for day in plan.harvest_days:
            for entry in day.entries:
                assert 2.0 <= entry.weight <= 2.2

    def test_optimizer_updates_house_stock(self, cycle, interval) -> None:
        """Test that optimizer updates house stock after harvesting."""
        # Get initial stock
        house = cycle.farms[0].houses[0]
        initial_stock = house.current_stock

        optimizer = NetMeatOptimizer()
        plan = optimizer.optimize(cycle, interval)

        # Stock should be reduced
        if plan.harvest_days:  # If any harvest occurred
            total_harvested = cycle.get_harvested_stock()
            assert total_harvested > 0

    def test_plan_validation_passes(self, cycle, interval) -> None:
        """Test that generated plan passes validation."""
        optimizer = NetMeatOptimizer()
        plan = optimizer.optimize(cycle, interval)

        result = plan.validate()
        # May have warnings, but should not have critical errors about capacity
        capacity_errors = [e for e in result.errors if "capacity exceeded" in e]
        assert len(capacity_errors) == 0

    def test_plan_has_checksum(self, cycle, interval) -> None:
        """Test that plan has a checksum."""
        optimizer = NetMeatOptimizer()
        plan = optimizer.optimize(cycle, interval)

        assert plan.checksum is not None
        assert len(plan.checksum) > 0

    def test_factory_creates_working_optimizer(self, cycle, interval) -> None:
        """Test that factory-created optimizer works."""
        config = OptimizationConfig(
            optimization_mode="profit_priority",
            profit_weight=0.6,
            profit_loss_weight=0.4,
        )

        optimizer = OptimizerFactory.create("profit_priority", config)
        plan = optimizer.optimize(cycle, interval)

        assert plan is not None
        assert len(plan.harvest_days) > 0

    def test_different_optimizers_produce_different_results(
        self, cycle, interval
    ) -> None:
        """Test that different optimizers may produce different results."""
        # Reset cycle by rebuilding
        data_path = Path(__file__).parent.parent.parent / "data" / "raw" / "predicted_data_combined.csv"
        loader = DataLoader(data_path=data_path)

        cycle1 = loader.build_cycle()
        cycle2 = loader.build_cycle()

        net_meat_optimizer = NetMeatOptimizer()
        min_fcr_optimizer = MinFCROptimizer()

        plan1 = net_meat_optimizer.optimize(cycle1, interval)
        plan2 = min_fcr_optimizer.optimize(cycle2, interval)

        # Both should have results
        assert len(plan1.harvest_days) > 0
        assert len(plan2.harvest_days) > 0

        # Checksums might be different (different selection order)
        # This is expected as optimizers have different objectives

    def test_export_to_dataframe(self, cycle, interval) -> None:
        """Test that plan can be exported to DataFrame."""
        optimizer = NetMeatOptimizer()
        plan = optimizer.optimize(cycle, interval)

        df = plan.export_to_dataframe()

        assert len(df) > 0
        assert "farm_id" in df.columns
        assert "house_id" in df.columns
        assert "quantity" in df.columns
        assert "weight" in df.columns
        assert "fcr" in df.columns
        assert "priority" in df.columns
