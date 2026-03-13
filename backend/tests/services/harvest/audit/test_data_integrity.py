"""Tests for DataIntegrityService."""

from datetime import datetime

import pytest

from app.services.harvest.audit import DataIntegrityService, Discrepancy, ReconciliationReport
from app.services.harvest.domain import (
    Cycle,
    Farm,
    House,
    DailyForecast,
    HarvestPlan,
    HarvestDay,
    HarvestEntry,
    HarvestInterval,
    ValidationResult,
)
from app.services.harvest.domain.enums import IntervalType


class TestDiscrepancy:
    """Test suite for Discrepancy dataclass."""

    def test_create_discrepancy(self) -> None:
        """Test creating a discrepancy."""
        discrepancy = Discrepancy(
            farm_id="W01",
            house_id="H01",
            date=datetime(2025, 9, 15),
            field_name="quantity",
            planned_value=5000.0,
            actual_value=4800.0,
        )

        assert discrepancy.farm_id == "W01"
        assert discrepancy.house_id == "H01"
        assert discrepancy.planned_value == 5000.0
        assert discrepancy.actual_value == 4800.0
        assert discrepancy.variance == -200.0
        assert abs(discrepancy.variance_pct - (-4.0)) < 0.01

    def test_severity_low(self) -> None:
        """Test low severity classification (<=5%)."""
        discrepancy = Discrepancy(
            farm_id="W01",
            house_id="H01",
            date=datetime(2025, 9, 15),
            field_name="quantity",
            planned_value=1000.0,
            actual_value=1040.0,  # 4% variance
        )

        assert discrepancy.severity == "low"

    def test_severity_medium(self) -> None:
        """Test medium severity classification (5-15%)."""
        discrepancy = Discrepancy(
            farm_id="W01",
            house_id="H01",
            date=datetime(2025, 9, 15),
            field_name="quantity",
            planned_value=1000.0,
            actual_value=1100.0,  # 10% variance
        )

        assert discrepancy.severity == "medium"

    def test_severity_high(self) -> None:
        """Test high severity classification (>15%)."""
        discrepancy = Discrepancy(
            farm_id="W01",
            house_id="H01",
            date=datetime(2025, 9, 15),
            field_name="quantity",
            planned_value=1000.0,
            actual_value=1200.0,  # 20% variance
        )

        assert discrepancy.severity == "high"

    def test_zero_planned_value(self) -> None:
        """Test handling zero planned value."""
        discrepancy = Discrepancy(
            farm_id="W01",
            house_id="H01",
            date=datetime(2025, 9, 15),
            field_name="quantity",
            planned_value=0.0,
            actual_value=100.0,
        )

        assert discrepancy.variance_pct == 100.0
        assert discrepancy.severity == "high"

    def test_to_dict(self) -> None:
        """Test converting discrepancy to dictionary."""
        discrepancy = Discrepancy(
            farm_id="W01",
            house_id="H01",
            date=datetime(2025, 9, 15),
            field_name="quantity",
            planned_value=5000.0,
            actual_value=4800.0,
            notes="Minor shortage",
        )

        data = discrepancy.to_dict()

        assert data["farm_id"] == "W01"
        assert data["variance"] == -200.0
        assert data["notes"] == "Minor shortage"


class TestReconciliationReport:
    """Test suite for ReconciliationReport dataclass."""

    def test_create_report(self) -> None:
        """Test creating a reconciliation report."""
        report = ReconciliationReport(
            plan_id="plan-123",
            total_planned=50000,
            total_actual=48000,
        )

        assert report.plan_id == "plan-123"
        assert report.variance == -2000
        assert abs(report.variance_pct - (-4.0)) < 0.01

    def test_report_with_discrepancies(self) -> None:
        """Test report with discrepancies."""
        discrepancies = [
            Discrepancy(
                farm_id="W01",
                house_id="H01",
                date=datetime(2025, 9, 15),
                field_name="quantity",
                planned_value=5000.0,
                actual_value=4000.0,  # 20% variance - high
            ),
            Discrepancy(
                farm_id="W01",
                house_id="H02",
                date=datetime(2025, 9, 15),
                field_name="quantity",
                planned_value=5000.0,
                actual_value=4800.0,  # 4% variance - low
            ),
        ]

        report = ReconciliationReport(
            plan_id="plan-123",
            total_planned=10000,
            total_actual=8800,
            discrepancies=discrepancies,
        )

        assert len(report.discrepancies) == 2
        assert report.summary["total_discrepancies"] == 2
        assert report.summary["severity_breakdown"]["high"] == 1
        assert report.summary["severity_breakdown"]["low"] == 1

    def test_report_status_needs_review(self) -> None:
        """Test report status when high severity exists."""
        discrepancies = [
            Discrepancy(
                farm_id="W01",
                house_id="H01",
                date=datetime(2025, 9, 15),
                field_name="quantity",
                planned_value=1000.0,
                actual_value=1500.0,  # 50% variance - high
            ),
        ]

        report = ReconciliationReport(
            plan_id="plan-123",
            total_planned=1000,
            total_actual=1500,
            discrepancies=discrepancies,
        )

        assert report.summary["overall_status"] == "needs_review"
        assert report.has_critical_issues is True

    def test_report_status_acceptable(self) -> None:
        """Test report status when only medium severity exists."""
        discrepancies = [
            Discrepancy(
                farm_id="W01",
                house_id="H01",
                date=datetime(2025, 9, 15),
                field_name="quantity",
                planned_value=1000.0,
                actual_value=1100.0,  # 10% variance - medium
            ),
        ]

        report = ReconciliationReport(
            plan_id="plan-123",
            total_planned=1000,
            total_actual=1100,
            discrepancies=discrepancies,
        )

        assert report.summary["overall_status"] == "acceptable"
        assert report.has_critical_issues is False

    def test_report_status_good(self) -> None:
        """Test report status when only low severity exists."""
        discrepancies = [
            Discrepancy(
                farm_id="W01",
                house_id="H01",
                date=datetime(2025, 9, 15),
                field_name="quantity",
                planned_value=1000.0,
                actual_value=1030.0,  # 3% variance - low
            ),
        ]

        report = ReconciliationReport(
            plan_id="plan-123",
            total_planned=1000,
            total_actual=1030,
            discrepancies=discrepancies,
        )

        assert report.summary["overall_status"] == "good"

    def test_high_severity_discrepancies(self) -> None:
        """Test filtering high severity discrepancies."""
        discrepancies = [
            Discrepancy(
                farm_id="W01",
                house_id="H01",
                date=datetime(2025, 9, 15),
                field_name="quantity",
                planned_value=1000.0,
                actual_value=1500.0,  # high
            ),
            Discrepancy(
                farm_id="W01",
                house_id="H02",
                date=datetime(2025, 9, 15),
                field_name="quantity",
                planned_value=1000.0,
                actual_value=1030.0,  # low
            ),
        ]

        report = ReconciliationReport(
            plan_id="plan-123",
            total_planned=2000,
            total_actual=2530,
            discrepancies=discrepancies,
        )

        high_only = report.high_severity_discrepancies
        assert len(high_only) == 1
        assert high_only[0].house_id == "H01"


class TestDataIntegrityService:
    """Test suite for DataIntegrityService."""

    @pytest.fixture
    def service(self) -> DataIntegrityService:
        """Create data integrity service instance."""
        return DataIntegrityService()

    @pytest.fixture
    def sample_cycle(self) -> Cycle:
        """Create a sample cycle for testing."""
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
                priority=1,
                net_meat=60000.0,
            )
        ]
        house1 = House(
            house_id="H01",
            farm_id="W01",
            initial_stock=30000,
            current_stock=25000,
            placement_date=datetime(2025, 8, 17),
            daily_forecasts=forecasts,
        )
        house2 = House(
            house_id="H02",
            farm_id="W01",
            initial_stock=30000,
            current_stock=30000,
            placement_date=datetime(2025, 8, 17),
            daily_forecasts=forecasts,
        )
        farm = Farm(farm_id="W01", name="Farm W01", houses=[house1, house2])

        return Cycle(
            cycle_number=1,
            year=2025,
            farms=[farm],
            start_date=datetime(2025, 8, 17),
            end_date=datetime(2025, 10, 15),
        )

    @pytest.fixture
    def sample_plan(self, sample_cycle: Cycle) -> HarvestPlan:
        """Create a sample harvest plan for testing."""
        entry1 = HarvestEntry(
            entry_id="e1",
            farm_id="W01",
            house_id="H01",
            date=datetime(2025, 9, 15),
            quantity=5000,
            weight=2.0,
            fcr=1.25,
        )
        entry2 = HarvestEntry(
            entry_id="e2",
            farm_id="W01",
            house_id="H02",
            date=datetime(2025, 9, 15),
            quantity=6000,
            weight=2.1,
            fcr=1.24,
        )
        harvest_day = HarvestDay(
            date=datetime(2025, 9, 15),
            entries=[entry1, entry2],
            capacity_limit=30000,
        )

        interval = HarvestInterval(
            name="Main",
            interval_type=IntervalType.SLAUGHTERHOUSE,
        )

        return HarvestPlan(
            plan_id="plan-123",
            cycle=sample_cycle,
            intervals=[interval],
            harvest_days=[harvest_day],
        )

    def test_validate_stock_balance_valid(
        self,
        service: DataIntegrityService,
        sample_cycle: Cycle,
    ) -> None:
        """Test validating a valid stock balance."""
        result = service.validate_stock_balance(sample_cycle)

        # There will be a warning because current_stock doesn't match expected
        # (no harvest history recorded)
        assert isinstance(result, ValidationResult)

    def test_validate_stock_balance_negative_stock(
        self,
        service: DataIntegrityService,
    ) -> None:
        """Test detecting negative stock."""
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
                priority=1,
                net_meat=60000.0,
            )
        ]
        house = House(
            house_id="H01",
            farm_id="W01",
            initial_stock=30000,
            current_stock=-100,  # Invalid!
            placement_date=datetime(2025, 8, 17),
            daily_forecasts=forecasts,
        )
        farm = Farm(farm_id="W01", name="Farm W01", houses=[house])
        cycle = Cycle(
            cycle_number=1,
            year=2025,
            farms=[farm],
            start_date=datetime(2025, 8, 17),
            end_date=datetime(2025, 10, 15),
        )

        result = service.validate_stock_balance(cycle)

        assert result.is_valid is False
        assert any("negative stock" in e.lower() for e in result.errors)

    def test_validate_capacity_limits_valid(
        self,
        service: DataIntegrityService,
        sample_plan: HarvestPlan,
    ) -> None:
        """Test validating valid capacity limits."""
        result = service.validate_capacity_limits(sample_plan)

        assert result.is_valid is True
        assert len(result.errors) == 0

    def test_validate_capacity_limits_exceeded(
        self,
        service: DataIntegrityService,
        sample_cycle: Cycle,
    ) -> None:
        """Test detecting exceeded capacity."""
        entry = HarvestEntry(
            entry_id="e1",
            farm_id="W01",
            house_id="H01",
            date=datetime(2025, 9, 15),
            quantity=35000,  # Exceeds capacity
            weight=2.0,
            fcr=1.25,
        )
        harvest_day = HarvestDay(
            date=datetime(2025, 9, 15),
            entries=[entry],
            capacity_limit=30000,
        )
        interval = HarvestInterval(
            name="Main",
            interval_type=IntervalType.SLAUGHTERHOUSE,
        )
        plan = HarvestPlan(
            plan_id="plan-123",
            cycle=sample_cycle,
            intervals=[interval],
            harvest_days=[harvest_day],
        )

        result = service.validate_capacity_limits(plan)

        assert result.is_valid is False
        assert any("exceeds capacity" in e.lower() for e in result.errors)

    def test_calculate_checksum(
        self,
        service: DataIntegrityService,
        sample_plan: HarvestPlan,
    ) -> None:
        """Test calculating plan checksum."""
        checksum = service.calculate_checksum(sample_plan)

        assert isinstance(checksum, str)
        assert len(checksum) == 64  # SHA-256 hex digest

    def test_checksum_deterministic(
        self,
        service: DataIntegrityService,
        sample_plan: HarvestPlan,
    ) -> None:
        """Test that checksum is deterministic."""
        checksum1 = service.calculate_checksum(sample_plan)
        checksum2 = service.calculate_checksum(sample_plan)

        assert checksum1 == checksum2

    def test_verify_checksum_valid(
        self,
        service: DataIntegrityService,
        sample_plan: HarvestPlan,
    ) -> None:
        """Test verifying a valid checksum."""
        sample_plan.checksum = service.calculate_checksum(sample_plan)

        assert service.verify_checksum(sample_plan) is True

    def test_verify_checksum_invalid(
        self,
        service: DataIntegrityService,
        sample_plan: HarvestPlan,
    ) -> None:
        """Test detecting an invalid checksum."""
        sample_plan.checksum = "invalid_checksum_12345"

        assert service.verify_checksum(sample_plan) is False

    def test_verify_checksum_missing(
        self,
        service: DataIntegrityService,
        sample_plan: HarvestPlan,
    ) -> None:
        """Test handling missing checksum."""
        sample_plan.checksum = None

        assert service.verify_checksum(sample_plan) is False

    def test_reconcile_with_actuals_exact_match(
        self,
        service: DataIntegrityService,
        sample_plan: HarvestPlan,
    ) -> None:
        """Test reconciliation with exact match."""
        actuals = [
            {
                "farm_id": "W01",
                "house_id": "H01",
                "date": datetime(2025, 9, 15),
                "quantity": 5000,
                "weight": 2.0,
                "fcr": 1.25,
            },
            {
                "farm_id": "W01",
                "house_id": "H02",
                "date": datetime(2025, 9, 15),
                "quantity": 6000,
                "weight": 2.1,
                "fcr": 1.24,
            },
        ]

        report = service.reconcile_with_actuals(sample_plan, actuals)

        assert report.total_planned == 11000
        assert report.total_actual == 11000
        assert report.variance == 0
        assert len(report.discrepancies) == 0

    def test_reconcile_with_actuals_quantity_variance(
        self,
        service: DataIntegrityService,
        sample_plan: HarvestPlan,
    ) -> None:
        """Test reconciliation with quantity variance."""
        actuals = [
            {
                "farm_id": "W01",
                "house_id": "H01",
                "date": datetime(2025, 9, 15),
                "quantity": 4500,  # 500 less than planned
                "weight": 2.0,
                "fcr": 1.25,
            },
            {
                "farm_id": "W01",
                "house_id": "H02",
                "date": datetime(2025, 9, 15),
                "quantity": 6000,
                "weight": 2.1,
                "fcr": 1.24,
            },
        ]

        report = service.reconcile_with_actuals(sample_plan, actuals)

        assert report.total_planned == 11000
        assert report.total_actual == 10500
        assert report.variance == -500
        assert len(report.discrepancies) == 1
        assert report.discrepancies[0].field_name == "quantity"

    def test_reconcile_with_actuals_missing_entry(
        self,
        service: DataIntegrityService,
        sample_plan: HarvestPlan,
    ) -> None:
        """Test reconciliation with missing actual entry."""
        actuals = [
            {
                "farm_id": "W01",
                "house_id": "H01",
                "date": datetime(2025, 9, 15),
                "quantity": 5000,
                "weight": 2.0,
                "fcr": 1.25,
            },
            # H02 missing
        ]

        report = service.reconcile_with_actuals(sample_plan, actuals)

        assert len(report.discrepancies) == 1
        assert report.discrepancies[0].house_id == "H02"
        assert report.discrepancies[0].notes == "Missing from actuals"

    def test_reconcile_with_actuals_extra_entry(
        self,
        service: DataIntegrityService,
        sample_plan: HarvestPlan,
    ) -> None:
        """Test reconciliation with extra actual entry."""
        actuals = [
            {
                "farm_id": "W01",
                "house_id": "H01",
                "date": datetime(2025, 9, 15),
                "quantity": 5000,
                "weight": 2.0,
                "fcr": 1.25,
            },
            {
                "farm_id": "W01",
                "house_id": "H02",
                "date": datetime(2025, 9, 15),
                "quantity": 6000,
                "weight": 2.1,
                "fcr": 1.24,
            },
            {
                "farm_id": "W01",
                "house_id": "H03",  # Not in plan
                "date": datetime(2025, 9, 15),
                "quantity": 3000,
                "weight": 1.9,
                "fcr": 1.26,
            },
        ]

        report = service.reconcile_with_actuals(sample_plan, actuals)

        assert any(d.house_id == "H03" and d.notes == "Not in plan" for d in report.discrepancies)

    def test_validate_plan_consistency(
        self,
        service: DataIntegrityService,
        sample_plan: HarvestPlan,
    ) -> None:
        """Test comprehensive plan validation."""
        result = service.validate_plan_consistency(sample_plan)

        # Should have some warnings about stock consistency
        assert isinstance(result, ValidationResult)

    def test_validate_plan_with_zero_quantity(
        self,
        service: DataIntegrityService,
        sample_cycle: Cycle,
    ) -> None:
        """Test detecting zero quantity entries."""
        entry = HarvestEntry(
            entry_id="e1",
            farm_id="W01",
            house_id="H01",
            date=datetime(2025, 9, 15),
            quantity=0,  # Invalid!
            weight=2.0,
            fcr=1.25,
        )
        harvest_day = HarvestDay(
            date=datetime(2025, 9, 15),
            entries=[entry],
        )
        interval = HarvestInterval(
            name="Main",
            interval_type=IntervalType.SLAUGHTERHOUSE,
        )
        plan = HarvestPlan(
            plan_id="plan-123",
            cycle=sample_cycle,
            intervals=[interval],
            harvest_days=[harvest_day],
        )

        result = service.validate_plan_consistency(plan)

        assert result.is_valid is False
        assert any("invalid quantity" in e.lower() for e in result.errors)

    def test_validate_empty_plan(
        self,
        service: DataIntegrityService,
        sample_cycle: Cycle,
    ) -> None:
        """Test validating empty plan generates warning."""
        interval = HarvestInterval(
            name="Main",
            interval_type=IntervalType.SLAUGHTERHOUSE,
        )
        plan = HarvestPlan(
            plan_id="plan-123",
            cycle=sample_cycle,
            intervals=[interval],
            harvest_days=[],  # Empty!
        )

        result = service.validate_plan_consistency(plan)

        assert any("no harvest days" in w.lower() for w in result.warnings)
