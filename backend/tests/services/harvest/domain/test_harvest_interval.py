"""Tests for HarvestInterval and OptimizationConfig domain models."""

from datetime import datetime, timedelta

import pytest

from app.services.harvest.domain import (
    HarvestInterval,
    OptimizationConfig,
    Cycle,
    Farm,
    House,
    DailyForecast,
    IntervalType,
    OptimizerStrategy,
)


class TestHarvestInterval:
    """Test suite for HarvestInterval class."""

    @pytest.fixture
    def basic_interval(self) -> HarvestInterval:
        """Create a basic harvest interval."""
        return HarvestInterval(
            name="Slaughterhouse 1",
            interval_type=IntervalType.SLAUGHTERHOUSE,
            daily_capacity=30000,
            min_weight=1.8,
            max_weight=2.5,
            start_date=datetime(2025, 9, 15),
            end_date=datetime(2025, 9, 30),
        )

    @pytest.fixture
    def simple_cycle(self) -> Cycle:
        """Create a simple cycle for testing date generation."""
        forecasts = [
            DailyForecast(
                date=datetime(2025, 9, 15) + timedelta(days=i),
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
            for i in range(20)
        ]

        house = House(
            house_id="H01",
            farm_id="W01",
            initial_stock=30000,
            current_stock=30000,
            placement_date=datetime(2025, 8, 17),
            daily_forecasts=forecasts,
        )

        farm = Farm(farm_id="W01", name="Farm W01", houses=[house])

        return Cycle(
            cycle_number=1,
            year=2025,
            farms=[farm],
            start_date=datetime(2025, 9, 15),
            end_date=datetime(2025, 10, 4),
        )

    def test_create_interval(self, basic_interval: HarvestInterval) -> None:
        """Test basic interval creation."""
        assert basic_interval.name == "Slaughterhouse 1"
        assert basic_interval.interval_type == IntervalType.SLAUGHTERHOUSE
        assert basic_interval.daily_capacity == 30000

    def test_default_values(self) -> None:
        """Test default values are applied correctly."""
        interval = HarvestInterval(
            name="Test",
            interval_type=IntervalType.SLAUGHTERHOUSE,
        )

        assert interval.daily_capacity == 30000
        assert interval.min_weight == 1.8
        assert interval.max_weight == 2.5
        assert interval.weight_step == 0.05
        assert interval.starting_pct == 0.30
        assert interval.max_pct == 1.00
        assert interval.max_pct_per_house == 0.45
        assert interval.excluded_weekdays == [3]  # Thursday
        assert interval.optimizer_strategy == OptimizerStrategy.BASE

    def test_get_valid_dates_basic(
        self, basic_interval: HarvestInterval, simple_cycle: Cycle
    ) -> None:
        """Test getting valid dates from interval."""
        valid_dates = basic_interval.get_valid_dates(simple_cycle)

        assert len(valid_dates) > 0
        # All dates should be within range
        for date in valid_dates:
            assert date >= basic_interval.start_date
            assert date <= basic_interval.end_date

    def test_get_valid_dates_excludes_thursdays(
        self, simple_cycle: Cycle
    ) -> None:
        """Test that Thursdays are excluded by default."""
        interval = HarvestInterval(
            name="Test",
            interval_type=IntervalType.SLAUGHTERHOUSE,
            start_date=datetime(2025, 9, 15),
            end_date=datetime(2025, 9, 30),
            excluded_weekdays=[3],  # Thursday
        )

        valid_dates = interval.get_valid_dates(simple_cycle)

        # No Thursdays should be in the list
        for date in valid_dates:
            assert date.weekday() != 3, f"Thursday {date} should be excluded"

    def test_get_valid_dates_excludes_specific_days(
        self, simple_cycle: Cycle
    ) -> None:
        """Test that specific dates can be excluded."""
        excluded = [datetime(2025, 9, 20), datetime(2025, 9, 22)]

        interval = HarvestInterval(
            name="Test",
            interval_type=IntervalType.SLAUGHTERHOUSE,
            start_date=datetime(2025, 9, 15),
            end_date=datetime(2025, 9, 30),
            excluded_days=excluded,
            excluded_weekdays=[],  # Don't exclude any weekdays
        )

        valid_dates = interval.get_valid_dates(simple_cycle)

        # Excluded dates should not be in the list
        excluded_strs = [d.strftime("%Y-%m-%d") for d in excluded]
        for date in valid_dates:
            assert date.strftime("%Y-%m-%d") not in excluded_strs

    def test_get_valid_dates_uses_cycle_dates_when_none(
        self, simple_cycle: Cycle
    ) -> None:
        """Test that cycle dates are used when interval dates are None."""
        interval = HarvestInterval(
            name="Test",
            interval_type=IntervalType.SLAUGHTERHOUSE,
            start_date=None,
            end_date=None,
            excluded_weekdays=[],
        )

        valid_dates = interval.get_valid_dates(simple_cycle)

        assert len(valid_dates) > 0
        assert valid_dates[0] == simple_cycle.start_date
        assert valid_dates[-1] == simple_cycle.end_date

    def test_get_valid_dates_empty_when_no_dates(self) -> None:
        """Test that empty list is returned when no dates are set."""
        interval = HarvestInterval(
            name="Test",
            interval_type=IntervalType.SLAUGHTERHOUSE,
        )

        # Cycle with no dates
        cycle = Cycle(cycle_number=1, year=2025, farms=[])

        valid_dates = interval.get_valid_dates(cycle)
        assert valid_dates == []

    def test_is_valid_date_within_range(self, basic_interval: HarvestInterval) -> None:
        """Test date validation for dates within range."""
        # Monday (weekday=0)
        assert basic_interval.is_valid_date(datetime(2025, 9, 15)) is True

    def test_is_valid_date_thursday_excluded(
        self, basic_interval: HarvestInterval
    ) -> None:
        """Test that Thursdays are invalid by default."""
        # September 18, 2025 is a Thursday
        assert basic_interval.is_valid_date(datetime(2025, 9, 18)) is False

    def test_is_valid_date_before_start(self, basic_interval: HarvestInterval) -> None:
        """Test date before start is invalid."""
        assert basic_interval.is_valid_date(datetime(2025, 9, 1)) is False

    def test_is_valid_date_after_end(self, basic_interval: HarvestInterval) -> None:
        """Test date after end is invalid."""
        assert basic_interval.is_valid_date(datetime(2025, 10, 15)) is False

    def test_is_weight_in_range(self, basic_interval: HarvestInterval) -> None:
        """Test weight range validation."""
        assert basic_interval.is_weight_in_range(2.0) is True
        assert basic_interval.is_weight_in_range(1.8) is True  # Boundary
        assert basic_interval.is_weight_in_range(2.5) is True  # Boundary
        assert basic_interval.is_weight_in_range(1.5) is False  # Below
        assert basic_interval.is_weight_in_range(3.0) is False  # Above

    def test_validate_constraints_valid(self, basic_interval: HarvestInterval) -> None:
        """Test validation of a valid interval."""
        result = basic_interval.validate_constraints()
        assert result.is_valid is True
        assert len(result.errors) == 0

    def test_validate_constraints_negative_weight(self) -> None:
        """Test validation catches negative weights."""
        interval = HarvestInterval(
            name="Test",
            interval_type=IntervalType.SLAUGHTERHOUSE,
            min_weight=-1.0,
        )

        result = interval.validate_constraints()
        assert result.is_valid is False
        assert any("min_weight" in e and "negative" in e for e in result.errors)

    def test_validate_constraints_min_greater_than_max_weight(self) -> None:
        """Test validation catches min > max weight."""
        interval = HarvestInterval(
            name="Test",
            interval_type=IntervalType.SLAUGHTERHOUSE,
            min_weight=3.0,
            max_weight=2.0,
        )

        result = interval.validate_constraints()
        assert result.is_valid is False
        assert any("min_weight" in e and "max_weight" in e for e in result.errors)

    def test_validate_constraints_invalid_percentage(self) -> None:
        """Test validation catches invalid percentages."""
        interval = HarvestInterval(
            name="Test",
            interval_type=IntervalType.SLAUGHTERHOUSE,
            starting_pct=1.5,  # > 1.0
        )

        result = interval.validate_constraints()
        assert result.is_valid is False
        assert any("starting_pct" in e for e in result.errors)

    def test_validate_constraints_starting_pct_greater_than_max(self) -> None:
        """Test validation catches starting_pct > max_pct."""
        interval = HarvestInterval(
            name="Test",
            interval_type=IntervalType.SLAUGHTERHOUSE,
            starting_pct=0.8,
            max_pct=0.5,
        )

        result = interval.validate_constraints()
        assert result.is_valid is False
        assert any("starting_pct" in e and "max_pct" in e for e in result.errors)

    def test_validate_constraints_zero_capacity(self) -> None:
        """Test validation catches zero capacity."""
        interval = HarvestInterval(
            name="Test",
            interval_type=IntervalType.SLAUGHTERHOUSE,
            daily_capacity=0,
        )

        result = interval.validate_constraints()
        assert result.is_valid is False
        assert any("daily_capacity" in e for e in result.errors)

    def test_validate_constraints_start_after_end(self) -> None:
        """Test validation catches start > end date."""
        interval = HarvestInterval(
            name="Test",
            interval_type=IntervalType.SLAUGHTERHOUSE,
            start_date=datetime(2025, 10, 1),
            end_date=datetime(2025, 9, 1),
        )

        result = interval.validate_constraints()
        assert result.is_valid is False
        assert any("start_date" in e and "end_date" in e for e in result.errors)

    def test_validate_constraints_many_excluded_weekdays_warning(self) -> None:
        """Test warning for many excluded weekdays."""
        interval = HarvestInterval(
            name="Test",
            interval_type=IntervalType.SLAUGHTERHOUSE,
            excluded_weekdays=[0, 1, 2, 3, 4],  # 5 days excluded
        )

        result = interval.validate_constraints()
        assert len(result.warnings) > 0
        assert any("weekdays excluded" in w for w in result.warnings)

    def test_to_dict(self, basic_interval: HarvestInterval) -> None:
        """Test dictionary conversion."""
        data = basic_interval.to_dict()

        assert data["name"] == "Slaughterhouse 1"
        assert data["interval_type"] == "slaughterhouse"
        assert data["daily_capacity"] == 30000
        assert data["min_weight"] == 1.8
        assert data["max_weight"] == 2.5
        assert "start_date" in data
        assert "end_date" in data

    def test_market_interval_type(self) -> None:
        """Test creating a market interval."""
        interval = HarvestInterval(
            name="Market 1",
            interval_type=IntervalType.MARKET,
        )

        assert interval.interval_type == IntervalType.MARKET
        assert interval.to_dict()["interval_type"] == "market"

    def test_different_optimizer_strategies(self) -> None:
        """Test different optimizer strategies."""
        for strategy in OptimizerStrategy:
            interval = HarvestInterval(
                name="Test",
                interval_type=IntervalType.SLAUGHTERHOUSE,
                optimizer_strategy=strategy,
            )
            assert interval.optimizer_strategy == strategy
            assert interval.to_dict()["optimizer_strategy"] == strategy.value


class TestOptimizationConfig:
    """Test suite for OptimizationConfig class."""

    @pytest.fixture
    def basic_interval(self) -> HarvestInterval:
        """Create a basic interval for config tests."""
        return HarvestInterval(
            name="Test Interval",
            interval_type=IntervalType.SLAUGHTERHOUSE,
        )

    def test_create_config(self, basic_interval: HarvestInterval) -> None:
        """Test basic config creation."""
        config = OptimizationConfig(
            optimization_mode="profit_priority",
            intervals=[basic_interval],
        )

        assert config.optimization_mode == "profit_priority"
        assert len(config.intervals) == 1

    def test_default_values(self) -> None:
        """Test default values."""
        config = OptimizationConfig(optimization_mode="net_meat")

        assert config.target_fcr is None
        assert config.profit_weight == 0.5
        assert config.profit_loss_weight == 0.5
        assert config.intervals == []
        assert config.additional_params == {}

    def test_validate_valid_config(self, basic_interval: HarvestInterval) -> None:
        """Test validation of a valid config."""
        config = OptimizationConfig(
            optimization_mode="net_meat",
            intervals=[basic_interval],
        )

        result = config.validate()
        assert result.is_valid is True

    def test_validate_invalid_mode(self) -> None:
        """Test validation catches invalid mode."""
        config = OptimizationConfig(
            optimization_mode="invalid_mode",
        )

        result = config.validate()
        assert result.is_valid is False
        assert any("Invalid optimization_mode" in e for e in result.errors)

    def test_validate_target_fcr_required(self) -> None:
        """Test validation requires target_fcr for target_fcr mode."""
        config = OptimizationConfig(
            optimization_mode="target_fcr",
            target_fcr=None,
        )

        result = config.validate()
        assert result.is_valid is False
        assert any("target_fcr is required" in e for e in result.errors)

    def test_validate_target_fcr_provided(self) -> None:
        """Test validation passes when target_fcr is provided."""
        config = OptimizationConfig(
            optimization_mode="target_fcr",
            target_fcr=1.25,
        )

        result = config.validate()
        # May have warning about no intervals, but should be valid
        assert not any("target_fcr is required" in e for e in result.errors)

    def test_validate_no_intervals_warning(self) -> None:
        """Test warning when no intervals configured."""
        config = OptimizationConfig(
            optimization_mode="net_meat",
            intervals=[],
        )

        result = config.validate()
        assert any("No intervals configured" in w for w in result.warnings)

    def test_validate_interval_errors_propagate(self) -> None:
        """Test that interval validation errors are included."""
        invalid_interval = HarvestInterval(
            name="Invalid",
            interval_type=IntervalType.SLAUGHTERHOUSE,
            min_weight=-1.0,  # Invalid
        )

        config = OptimizationConfig(
            optimization_mode="net_meat",
            intervals=[invalid_interval],
        )

        result = config.validate()
        assert result.is_valid is False
        assert any("min_weight" in e for e in result.errors)

    def test_validate_profit_priority_weights_warning(self) -> None:
        """Test warning when profit weights don't sum to 1.0."""
        config = OptimizationConfig(
            optimization_mode="profit_priority",
            profit_weight=0.3,
            profit_loss_weight=0.3,  # Sum = 0.6 != 1.0
        )

        result = config.validate()
        assert any("profit_weight + profit_loss_weight" in w for w in result.warnings)

    def test_validate_profit_priority_weights_valid(self) -> None:
        """Test no warning when profit weights sum to 1.0."""
        config = OptimizationConfig(
            optimization_mode="profit_priority",
            profit_weight=0.6,
            profit_loss_weight=0.4,
        )

        result = config.validate()
        assert not any("profit_weight + profit_loss_weight" in w for w in result.warnings)

    def test_all_valid_modes(self) -> None:
        """Test all valid optimization modes are accepted."""
        valid_modes = [
            "net_meat",
            "min_fcr",
            "target_fcr",
            "profit_priority",
            "legacy_profit",
            "legacy_slaughterhouse",
        ]

        for mode in valid_modes:
            config = OptimizationConfig(
                optimization_mode=mode,
                target_fcr=1.25 if mode == "target_fcr" else None,
            )
            result = config.validate()
            assert not any("Invalid optimization_mode" in e for e in result.errors), (
                f"Mode {mode} should be valid"
            )

    def test_to_dict(self, basic_interval: HarvestInterval) -> None:
        """Test dictionary conversion."""
        config = OptimizationConfig(
            optimization_mode="target_fcr",
            intervals=[basic_interval],
            target_fcr=1.3,
            profit_weight=0.6,
            profit_loss_weight=0.4,
            additional_params={"custom_key": "value"},
        )

        data = config.to_dict()

        assert data["optimization_mode"] == "target_fcr"
        assert data["target_fcr"] == 1.3
        assert data["profit_weight"] == 0.6
        assert data["profit_loss_weight"] == 0.4
        assert len(data["intervals"]) == 1
        assert data["additional_params"] == {"custom_key": "value"}

    def test_additional_params(self) -> None:
        """Test additional params are preserved."""
        config = OptimizationConfig(
            optimization_mode="net_meat",
            additional_params={
                "custom_setting": True,
                "threshold": 0.95,
            },
        )

        assert config.additional_params["custom_setting"] is True
        assert config.additional_params["threshold"] == 0.95
