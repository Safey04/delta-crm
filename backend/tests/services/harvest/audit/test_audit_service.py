"""Tests for AuditService."""

from datetime import datetime

import pytest

from app.services.harvest.audit import AuditService, AuditEntry
from app.services.harvest.domain.enums import (
    AuditAction,
    IntervalType,
    ExportFormat,
)
from app.services.harvest.domain import (
    OptimizationConfig,
    HarvestInterval,
    HarvestPlan,
    HarvestDay,
    HarvestEntry,
    Cycle,
    Farm,
    House,
    DailyForecast,
)


class TestAuditEntry:
    """Test suite for AuditEntry dataclass."""

    def test_create_entry(self) -> None:
        """Test creating an audit entry."""
        entry = AuditEntry(
            action=AuditAction.OPTIMIZATION_STARTED,
            optimization_id="opt-123",
            user_id="user-1",
            cycle_id="2025-1",
        )

        assert entry.action == AuditAction.OPTIMIZATION_STARTED
        assert entry.optimization_id == "opt-123"
        assert entry.user_id == "user-1"
        assert entry.cycle_id == "2025-1"
        assert entry.entry_id is not None
        assert entry.timestamp is not None

    def test_entry_to_dict(self) -> None:
        """Test converting entry to dictionary."""
        entry = AuditEntry(
            action=AuditAction.HOUSE_SELECTED,
            optimization_id="opt-123",
            farm_id="W01",
            house_id="H01",
            date=datetime(2025, 9, 15),
            parameters={"quantity": 5000, "score": 95.5},
            reason="High score candidate",
        )

        data = entry.to_dict()

        assert data["action"] == "house_selected"
        assert data["optimization_id"] == "opt-123"
        assert data["farm_id"] == "W01"
        assert data["house_id"] == "H01"
        assert data["parameters"]["quantity"] == 5000
        assert data["reason"] == "High score candidate"

    def test_entry_to_json(self) -> None:
        """Test converting entry to JSON."""
        entry = AuditEntry(
            action=AuditAction.CONSTRAINT_RELAXED,
            optimization_id="opt-123",
            before_state={"min_weight": 2.0},
            after_state={"min_weight": 1.9},
        )

        json_str = entry.to_json()

        assert "constraint_relaxed" in json_str
        assert "before_state" in json_str
        assert "after_state" in json_str

    def test_entry_from_dict(self) -> None:
        """Test creating entry from dictionary."""
        data = {
            "entry_id": "entry-123",
            "timestamp": "2025-09-15T10:30:00",
            "action": "optimization_started",
            "optimization_id": "opt-456",
            "user_id": "user-1",
            "cycle_id": "2025-2",
            "parameters": {"mode": "net_meat"},
        }

        entry = AuditEntry.from_dict(data)

        assert entry.entry_id == "entry-123"
        assert entry.action == AuditAction.OPTIMIZATION_STARTED
        assert entry.optimization_id == "opt-456"
        assert entry.parameters["mode"] == "net_meat"


class TestAuditService:
    """Test suite for AuditService."""

    @pytest.fixture
    def service(self) -> AuditService:
        """Create audit service instance."""
        return AuditService()

    @pytest.fixture
    def config(self) -> OptimizationConfig:
        """Create optimization config."""
        interval = HarvestInterval(
            name="Main",
            interval_type=IntervalType.SLAUGHTERHOUSE,
            daily_capacity=30000,
            min_weight=1.8,
            max_weight=2.2,
        )
        return OptimizationConfig(
            optimization_mode="net_meat",
            intervals=[interval],
        )

    @pytest.fixture
    def sample_plan(self) -> HarvestPlan:
        """Create a sample harvest plan for testing."""
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

        return HarvestPlan(
            plan_id="plan-123",
            cycle=cycle,
            intervals=[interval],
            harvest_days=[harvest_day],
        )

    def test_log_optimization_start(
        self,
        service: AuditService,
        config: OptimizationConfig,
    ) -> None:
        """Test logging optimization start."""
        opt_id = service.log_optimization_start(
            config=config,
            user_id="user-1",
            cycle_id="2025-1",
        )

        assert opt_id is not None

        entries = service.get_audit_trail(opt_id)
        assert len(entries) == 1
        assert entries[0].action == AuditAction.OPTIMIZATION_STARTED
        assert entries[0].user_id == "user-1"

    def test_log_house_selection(self, service: AuditService) -> None:
        """Test logging house selection."""
        opt_id = "opt-123"

        service.log_house_selection(
            optimization_id=opt_id,
            house_id="H01",
            farm_id="W01",
            date=datetime(2025, 9, 15),
            quantity=5000,
            score=95.5,
            reason="Highest net meat score",
            weight=2.0,
            fcr=1.25,
            priority=1,
        )

        entries = service.get_audit_trail(opt_id)
        assert len(entries) == 1
        assert entries[0].action == AuditAction.HOUSE_SELECTED
        assert entries[0].parameters["quantity"] == 5000
        assert entries[0].parameters["score"] == 95.5

    def test_log_constraint_relaxed(self, service: AuditService) -> None:
        """Test logging constraint relaxation."""
        opt_id = "opt-123"

        service.log_constraint_relaxed(
            optimization_id=opt_id,
            constraint_name="min_weight",
            old_value=2.0,
            new_value=1.9,
            reason="Insufficient candidates within weight range",
            interval_name="Main",
        )

        entries = service.get_audit_trail(opt_id)
        assert len(entries) == 1
        assert entries[0].action == AuditAction.CONSTRAINT_RELAXED
        assert entries[0].before_state["value"] == 2.0
        assert entries[0].after_state["value"] == 1.9

    def test_log_optimization_complete(
        self,
        service: AuditService,
        sample_plan: HarvestPlan,
    ) -> None:
        """Test logging optimization completion."""
        opt_id = "opt-123"

        service.log_optimization_complete(
            optimization_id=opt_id,
            plan=sample_plan,
            metrics={"custom_metric": 123},
        )

        entries = service.get_audit_trail(opt_id)
        assert len(entries) == 1
        assert entries[0].action == AuditAction.OPTIMIZATION_COMPLETE
        assert entries[0].parameters["plan_id"] == "plan-123"
        assert entries[0].after_state["custom_metric"] == 123

    def test_full_optimization_flow(
        self,
        service: AuditService,
        config: OptimizationConfig,
        sample_plan: HarvestPlan,
    ) -> None:
        """Test full optimization audit flow."""
        # Start optimization
        opt_id = service.log_optimization_start(
            config=config,
            user_id="user-1",
            cycle_id="2025-1",
        )

        # Log house selection
        service.log_house_selection(
            optimization_id=opt_id,
            house_id="H01",
            farm_id="W01",
            date=datetime(2025, 9, 15),
            quantity=5000,
            score=95.5,
            reason="Best candidate",
        )

        # Log constraint relaxation
        service.log_constraint_relaxed(
            optimization_id=opt_id,
            constraint_name="max_pct",
            old_value=0.5,
            new_value=0.6,
            reason="Need more capacity",
        )

        # Complete optimization
        service.log_optimization_complete(
            optimization_id=opt_id,
            plan=sample_plan,
        )

        # Verify trail
        entries = service.get_audit_trail(opt_id)
        assert len(entries) == 4
        assert entries[0].action == AuditAction.OPTIMIZATION_STARTED
        assert entries[1].action == AuditAction.HOUSE_SELECTED
        assert entries[2].action == AuditAction.CONSTRAINT_RELAXED
        assert entries[3].action == AuditAction.OPTIMIZATION_COMPLETE

    def test_get_entries_by_action(self, service: AuditService) -> None:
        """Test filtering entries by action type."""
        opt_id = "opt-123"

        # Log multiple entries
        service.log_house_selection(
            optimization_id=opt_id,
            house_id="H01",
            farm_id="W01",
            date=datetime(2025, 9, 15),
            quantity=5000,
            score=95.5,
            reason="First selection",
        )
        service.log_house_selection(
            optimization_id=opt_id,
            house_id="H02",
            farm_id="W01",
            date=datetime(2025, 9, 15),
            quantity=4000,
            score=92.0,
            reason="Second selection",
        )
        service.log_constraint_relaxed(
            optimization_id=opt_id,
            constraint_name="min_weight",
            old_value=2.0,
            new_value=1.9,
            reason="Expand range",
        )

        # Filter by action
        selections = service.get_entries_by_action(opt_id, AuditAction.HOUSE_SELECTED)
        assert len(selections) == 2

        relaxations = service.get_entries_by_action(opt_id, AuditAction.CONSTRAINT_RELAXED)
        assert len(relaxations) == 1

    def test_get_entries_for_house(self, service: AuditService) -> None:
        """Test filtering entries for a specific house."""
        opt_id = "opt-123"

        # Log entries for different houses
        service.log_house_selection(
            optimization_id=opt_id,
            house_id="H01",
            farm_id="W01",
            date=datetime(2025, 9, 15),
            quantity=5000,
            score=95.5,
            reason="Selection 1",
        )
        service.log_house_selection(
            optimization_id=opt_id,
            house_id="H02",
            farm_id="W01",
            date=datetime(2025, 9, 15),
            quantity=4000,
            score=92.0,
            reason="Selection 2",
        )
        service.log_house_selection(
            optimization_id=opt_id,
            house_id="H01",
            farm_id="W01",
            date=datetime(2025, 9, 16),
            quantity=3000,
            score=88.0,
            reason="Selection 3",
        )

        # Filter for H01
        h01_entries = service.get_entries_for_house(opt_id, "W01", "H01")
        assert len(h01_entries) == 2

        h02_entries = service.get_entries_for_house(opt_id, "W01", "H02")
        assert len(h02_entries) == 1

    def test_export_audit_trail_json(self, service: AuditService) -> None:
        """Test exporting audit trail as JSON."""
        opt_id = "opt-123"

        service.log_house_selection(
            optimization_id=opt_id,
            house_id="H01",
            farm_id="W01",
            date=datetime(2025, 9, 15),
            quantity=5000,
            score=95.5,
            reason="Test selection",
        )

        json_export = service.export_audit_trail(opt_id, ExportFormat.JSON)

        assert "house_selected" in json_export
        assert "H01" in json_export
        assert "W01" in json_export

    def test_export_audit_trail_csv(self, service: AuditService) -> None:
        """Test exporting audit trail as CSV."""
        opt_id = "opt-123"

        service.log_house_selection(
            optimization_id=opt_id,
            house_id="H01",
            farm_id="W01",
            date=datetime(2025, 9, 15),
            quantity=5000,
            score=95.5,
            reason="Test selection",
        )

        csv_export = service.export_audit_trail(opt_id, ExportFormat.CSV)

        lines = csv_export.split("\n")
        assert len(lines) == 2  # Header + 1 entry
        assert "entry_id" in lines[0]
        assert "house_selected" in lines[1]

    def test_get_optimization_summary(
        self,
        service: AuditService,
        config: OptimizationConfig,
        sample_plan: HarvestPlan,
    ) -> None:
        """Test getting optimization summary."""
        opt_id = service.log_optimization_start(
            config=config,
            user_id="user-1",
            cycle_id="2025-1",
        )

        service.log_house_selection(
            optimization_id=opt_id,
            house_id="H01",
            farm_id="W01",
            date=datetime(2025, 9, 15),
            quantity=5000,
            score=95.5,
            reason="Selection",
        )

        service.log_optimization_complete(
            optimization_id=opt_id,
            plan=sample_plan,
        )

        summary = service.get_optimization_summary(opt_id)

        assert summary["optimization_id"] == opt_id
        assert summary["total_entries"] == 3
        assert summary["houses_selected"] == 1
        assert summary["started_at"] is not None
        assert summary["completed_at"] is not None

    def test_clear_audit_trail(self, service: AuditService) -> None:
        """Test clearing audit trail."""
        opt_id = "opt-123"

        service.log_house_selection(
            optimization_id=opt_id,
            house_id="H01",
            farm_id="W01",
            date=datetime(2025, 9, 15),
            quantity=5000,
            score=95.5,
            reason="Test",
        )

        assert len(service.get_audit_trail(opt_id)) == 1

        service.clear_audit_trail(opt_id)

        assert len(service.get_audit_trail(opt_id)) == 0

    def test_empty_trail_returns_empty_list(self, service: AuditService) -> None:
        """Test that non-existent optimization returns empty list."""
        entries = service.get_audit_trail("non-existent")
        assert entries == []

    def test_log_custom_event(self, service: AuditService) -> None:
        """Test logging custom events."""
        opt_id = "opt-123"

        service.log_custom_event(
            optimization_id=opt_id,
            action=AuditAction.HOUSE_SELECTED,
            parameters={"custom_param": "value"},
            reason="Custom reason",
            farm_id="W01",
            house_id="H01",
        )

        entries = service.get_audit_trail(opt_id)
        assert len(entries) == 1
        assert entries[0].parameters["custom_param"] == "value"
