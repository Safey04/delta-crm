"""Tests for HarvestPlanningServiceV2."""

from datetime import datetime
import tempfile
import shutil

import pytest

from app.services.harvest.services import HarvestPlanningServiceV2
from app.services.harvest.domain import (
    Cycle,
    Farm,
    House,
    DailyForecast,
    HarvestPlan,
    HarvestDay,
    HarvestEntry,
    HarvestInterval,
    OptimizationConfig,
)
from app.services.harvest.domain.enums import IntervalType, ExportFormat
from app.services.harvest.audit import AuditService, DataIntegrityService
from app.services.harvest.storage import StorageService
from app.services.harvest.storage.storage_service import LocalStorageBackend


class TestHarvestPlanningServiceV2:
    """Test suite for HarvestPlanningServiceV2."""

    @pytest.fixture
    def temp_dir(self) -> str:
        """Create a temporary directory for testing."""
        path = tempfile.mkdtemp()
        yield path
        shutil.rmtree(path)

    @pytest.fixture
    def service(self, temp_dir: str) -> HarvestPlanningServiceV2:
        """Create a service instance with test configuration."""
        backend = LocalStorageBackend(base_path=temp_dir)
        storage = StorageService(backend=backend)
        
        return HarvestPlanningServiceV2(
            storage_service=storage,
        )

    @pytest.fixture
    def sample_cycle(self) -> Cycle:
        """Create a sample cycle for testing."""
        forecasts = []
        for day in range(15, 25):
            forecasts.append(
                DailyForecast(
                    date=datetime(2025, 9, day),
                    weight=1.8 + (day - 15) * 0.05,
                    fcr=1.20 + (day - 15) * 0.01,
                    mortality=50,
                    projected_stock=30000 - (day - 15) * 100,
                    feed_consumed=40000.0 + (day - 15) * 1000,
                    price=60.0,
                    total_profit=1500000.0 - (day - 15) * 10000,
                    profit_per_bird=50.0 - (day - 15),
                    profit_loss=5000.0 + (day - 15) * 500,
                    priority=day - 14,
                    net_meat=55000.0 + (day - 15) * 1000,
                )
            )
        
        house1 = House(
            house_id="H01",
            farm_id="W01",
            initial_stock=30000,
            current_stock=30000,
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
        """Create a sample harvest plan."""
        entries = [
            HarvestEntry(
                entry_id="e1",
                farm_id="W01",
                house_id="H01",
                date=datetime(2025, 9, 15),
                quantity=5000,
                weight=2.0,
                fcr=1.25,
            ),
            HarvestEntry(
                entry_id="e2",
                farm_id="W01",
                house_id="H02",
                date=datetime(2025, 9, 15),
                quantity=6000,
                weight=2.1,
                fcr=1.24,
            ),
        ]
        harvest_day = HarvestDay(
            date=datetime(2025, 9, 15),
            entries=entries,
            capacity_limit=30000,
        )
        interval = HarvestInterval(
            name="Main",
            interval_type=IntervalType.SLAUGHTERHOUSE,
        )
        config = OptimizationConfig(
            optimization_mode="net_meat",
            intervals=[interval],
        )

        return HarvestPlan(
            plan_id="plan-test-123",
            cycle=sample_cycle,
            intervals=[interval],
            harvest_days=[harvest_day],
            config=config,
        )

    def test_service_initialization(self, service: HarvestPlanningServiceV2) -> None:
        """Test service initializes with all components."""
        assert service.data_loader is not None
        assert service.audit_service is not None
        assert service.integrity_service is not None
        assert service.storage_service is not None

    def test_validate_plan(
        self,
        service: HarvestPlanningServiceV2,
        sample_plan: HarvestPlan,
    ) -> None:
        """Test plan validation."""
        result = service.validate_plan(sample_plan)

        assert result is not None
        # Should be valid (no errors)
        assert result.is_valid is True

    def test_save_plan(
        self,
        service: HarvestPlanningServiceV2,
        sample_plan: HarvestPlan,
    ) -> None:
        """Test saving a plan."""
        plan_id = service.save_plan(sample_plan, user_id="user-1")

        assert plan_id == sample_plan.plan_id

        # Verify saved
        saved = service.get_plan(plan_id)
        assert saved is not None
        assert saved["plan_id"] == plan_id
        assert saved["created_by"] == "user-1"

    def test_save_plan_sets_checksum(
        self,
        service: HarvestPlanningServiceV2,
        sample_plan: HarvestPlan,
    ) -> None:
        """Test that saving a plan sets the checksum."""
        service.save_plan(sample_plan)

        assert sample_plan.checksum is not None
        assert len(sample_plan.checksum) == 64  # SHA-256

    def test_get_plan_not_found(self, service: HarvestPlanningServiceV2) -> None:
        """Test getting a non-existent plan."""
        result = service.get_plan("nonexistent")
        assert result is None

    def test_list_plans(
        self,
        service: HarvestPlanningServiceV2,
        sample_plan: HarvestPlan,
    ) -> None:
        """Test listing saved plans."""
        # Save a few plans
        service.save_plan(sample_plan, user_id="user-1")
        
        # Create another plan with different ID - reset checksum so it can be recalculated
        sample_plan.plan_id = "plan-test-456"
        sample_plan.checksum = None  # Reset so save_plan recalculates
        service.save_plan(sample_plan, user_id="user-2")

        # List all
        plans = service.list_plans()
        assert len(plans) == 2

    def test_list_plans_filter_by_user(
        self,
        service: HarvestPlanningServiceV2,
        sample_plan: HarvestPlan,
    ) -> None:
        """Test filtering plans by user."""
        service.save_plan(sample_plan, user_id="user-1")
        
        sample_plan.plan_id = "plan-test-789"
        sample_plan.checksum = None  # Reset so save_plan recalculates
        service.save_plan(sample_plan, user_id="user-2")

        # Filter by user
        user1_plans = service.list_plans(user_id="user-1")
        assert len(user1_plans) == 1
        assert user1_plans[0]["created_by"] == "user-1"

    def test_export_plan_csv(
        self,
        service: HarvestPlanningServiceV2,
        sample_plan: HarvestPlan,
    ) -> None:
        """Test exporting a plan to CSV."""
        url = service.export_plan(sample_plan, format=ExportFormat.CSV)

        assert url is not None
        # Local storage returns file:// URL
        assert "csv" in url.lower() or "file://" in url

    def test_export_plan_json(
        self,
        service: HarvestPlanningServiceV2,
        sample_plan: HarvestPlan,
    ) -> None:
        """Test exporting a plan to JSON."""
        url = service.export_plan(sample_plan, format=ExportFormat.JSON)

        assert url is not None

    def test_get_optimization_summary(
        self,
        service: HarvestPlanningServiceV2,
    ) -> None:
        """Test getting optimization summary for non-existent run."""
        summary = service.get_optimization_summary("nonexistent")

        assert "error" in summary

    def test_reconcile_plan(
        self,
        service: HarvestPlanningServiceV2,
        sample_plan: HarvestPlan,
    ) -> None:
        """Test reconciling a plan against actuals."""
        actuals = [
            {
                "farm_id": "W01",
                "house_id": "H01",
                "date": datetime(2025, 9, 15),
                "quantity": 5000,  # Exact match
                "weight": 2.0,
                "fcr": 1.25,
            },
            {
                "farm_id": "W01",
                "house_id": "H02",
                "date": datetime(2025, 9, 15),
                "quantity": 5500,  # 500 less
                "weight": 2.1,
                "fcr": 1.24,
            },
        ]

        report = service.reconcile_plan(sample_plan, actuals)

        assert report is not None
        assert "total_planned" in report
        assert "total_actual" in report
        assert "discrepancies" in report

    def test_delete_plan(
        self,
        service: HarvestPlanningServiceV2,
        sample_plan: HarvestPlan,
    ) -> None:
        """Test deleting a plan."""
        service.save_plan(sample_plan)

        # Verify saved
        assert service.get_plan(sample_plan.plan_id) is not None

        # Delete
        result = service.delete_plan(sample_plan.plan_id)
        assert result is True

        # Verify deleted
        assert service.get_plan(sample_plan.plan_id) is None

    def test_delete_plan_not_found(
        self,
        service: HarvestPlanningServiceV2,
    ) -> None:
        """Test deleting a non-existent plan."""
        result = service.delete_plan("nonexistent")
        assert result is False

    def test_export_audit_trail(
        self,
        service: HarvestPlanningServiceV2,
    ) -> None:
        """Test exporting an audit trail."""
        # First log something to audit
        opt_id = service.audit_service.log_optimization_start(
            config=OptimizationConfig(
                optimization_mode="net_meat",
                intervals=[],
            ),
            user_id="user-1",
            cycle_id="2025-1",
        )

        # Export
        url = service.export_audit_trail(
            optimization_id=opt_id,
            cycle_id="2025-1",
        )

        assert url is not None
        assert "audits" in url


class TestHarvestPlanningServiceV2Integration:
    """Integration tests for HarvestPlanningServiceV2."""

    @pytest.fixture
    def temp_dir(self) -> str:
        """Create a temporary directory for testing."""
        path = tempfile.mkdtemp()
        yield path
        shutil.rmtree(path)

    @pytest.fixture
    def service(self, temp_dir: str) -> HarvestPlanningServiceV2:
        """Create a service instance."""
        backend = LocalStorageBackend(base_path=temp_dir)
        storage = StorageService(backend=backend)
        
        return HarvestPlanningServiceV2(
            storage_service=storage,
        )

    def test_full_workflow(
        self,
        service: HarvestPlanningServiceV2,
    ) -> None:
        """Test a full workflow: save, list, export, reconcile, delete."""
        # Create a sample plan manually
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
            current_stock=25000,
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
        entry = HarvestEntry(
            entry_id="e1",
            farm_id="W01",
            house_id="H01",
            date=datetime(2025, 9, 15),
            quantity=5000,
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
        config = OptimizationConfig(
            optimization_mode="net_meat",
            intervals=[interval],
        )
        plan = HarvestPlan(
            plan_id="workflow-test",
            cycle=cycle,
            intervals=[interval],
            harvest_days=[harvest_day],
            config=config,
        )

        # 1. Validate
        validation = service.validate_plan(plan)
        assert validation.is_valid

        # 2. Save
        plan_id = service.save_plan(plan, user_id="workflow-user")
        assert plan_id is not None

        # 3. List
        plans = service.list_plans(user_id="workflow-user")
        assert len(plans) == 1

        # 4. Export
        url = service.export_plan(plan, format=ExportFormat.CSV)
        assert url is not None

        # 5. Reconcile
        actuals = [
            {
                "farm_id": "W01",
                "house_id": "H01",
                "date": datetime(2025, 9, 15),
                "quantity": 5000,
            }
        ]
        report = service.reconcile_plan(plan, actuals)
        assert report["variance"] == 0

        # 6. Delete
        deleted = service.delete_plan(plan_id)
        assert deleted is True

        # Verify deleted
        assert service.get_plan(plan_id) is None
