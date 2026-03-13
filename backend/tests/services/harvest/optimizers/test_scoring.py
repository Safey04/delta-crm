"""Tests for optimizer scoring logic."""

from datetime import datetime

import pytest

from app.services.harvest.domain import (
    Cycle,
    Farm,
    House,
    DailyForecast,
    HarvestInterval,
    HarvestPlan,
    OptimizationConfig,
    IntervalType,
)
from app.services.harvest.optimizers import (
    HouseCandidate,
    NetMeatOptimizer,
    MinFCROptimizer,
    TargetFCROptimizer,
    ProfitPriorityOptimizer,
    OptimizerFactory,
)


class TestNetMeatOptimizer:
    """Test suite for NetMeatOptimizer."""

    @pytest.fixture
    def optimizer(self) -> NetMeatOptimizer:
        """Create optimizer instance."""
        return NetMeatOptimizer()

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
            farm_id="W01",
            initial_stock=30000,
            current_stock=30000,
            placement_date=datetime(2025, 8, 17),
            daily_forecasts=forecasts,
        )

    def test_score_candidate(
        self, optimizer: NetMeatOptimizer, sample_house: House
    ) -> None:
        """Test scoring based on net meat."""
        score = optimizer.score_candidate(
            house=sample_house,
            date=datetime(2025, 9, 15),
            quantity=10000,
        )

        # Score = quantity * weight = 10000 * 2.0 = 20000
        assert score == 20000.0

    def test_assign_priorities_by_score(
        self, optimizer: NetMeatOptimizer
    ) -> None:
        """Test priority assignment based on net meat score."""
        farm = Farm(farm_id="W01", name="Farm", houses=[])

        # Create candidates with different scores
        candidates = [
            HouseCandidate(
                house=None,  # Not needed for priority test
                farm=farm,
                date=datetime(2025, 9, 15),
                available_quantity=10000,
                weight=1.5,  # Lower weight
                fcr=1.25,
                score=15000,  # 10000 * 1.5
            ),
            HouseCandidate(
                house=None,
                farm=farm,
                date=datetime(2025, 9, 15),
                available_quantity=10000,
                weight=2.5,  # Higher weight
                fcr=1.25,
                score=25000,  # 10000 * 2.5
            ),
            HouseCandidate(
                house=None,
                farm=farm,
                date=datetime(2025, 9, 15),
                available_quantity=10000,
                weight=2.0,  # Medium weight
                fcr=1.25,
                score=20000,  # 10000 * 2.0
            ),
        ]

        result = optimizer.assign_priorities(candidates)

        # Highest score (25000) should have priority 1
        assert result[0].score == 25000
        assert result[0].priority == 1

        # Medium score (20000) should have priority 2
        assert result[1].score == 20000
        assert result[1].priority == 2

        # Lowest score (15000) should have priority 3
        assert result[2].score == 15000
        assert result[2].priority == 3

    def test_optimization_mode(self, optimizer: NetMeatOptimizer) -> None:
        """Test optimization mode name."""
        assert optimizer.get_optimization_mode() == "net_meat"


class TestMinFCROptimizer:
    """Test suite for MinFCROptimizer."""

    @pytest.fixture
    def optimizer(self) -> MinFCROptimizer:
        """Create optimizer instance."""
        return MinFCROptimizer()

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
            farm_id="W01",
            initial_stock=30000,
            current_stock=30000,
            placement_date=datetime(2025, 8, 17),
            daily_forecasts=forecasts,
        )

    def test_score_candidate(
        self, optimizer: MinFCROptimizer, sample_house: House
    ) -> None:
        """Test scoring based on FCR (inverted)."""
        score = optimizer.score_candidate(
            house=sample_house,
            date=datetime(2025, 9, 15),
            quantity=10000,
        )

        # Score = -FCR = -1.25
        assert score == -1.25

    def test_assign_priorities_by_fcr(
        self, optimizer: MinFCROptimizer
    ) -> None:
        """Test priority assignment based on FCR (lower = better)."""
        farm = Farm(farm_id="W01", name="Farm", houses=[])

        candidates = [
            HouseCandidate(
                house=None,
                farm=farm,
                date=datetime(2025, 9, 15),
                available_quantity=10000,
                weight=2.0,
                fcr=1.4,  # Worst FCR
            ),
            HouseCandidate(
                house=None,
                farm=farm,
                date=datetime(2025, 9, 15),
                available_quantity=10000,
                weight=2.0,
                fcr=1.1,  # Best FCR
            ),
            HouseCandidate(
                house=None,
                farm=farm,
                date=datetime(2025, 9, 15),
                available_quantity=10000,
                weight=2.0,
                fcr=1.25,  # Medium FCR
            ),
        ]

        result = optimizer.assign_priorities(candidates)

        # Lowest FCR (1.1) should have priority 1
        assert result[0].fcr == 1.1
        assert result[0].priority == 1

        # Medium FCR (1.25) should have priority 2
        assert result[1].fcr == 1.25
        assert result[1].priority == 2

        # Highest FCR (1.4) should have priority 3
        assert result[2].fcr == 1.4
        assert result[2].priority == 3

    def test_optimization_mode(self, optimizer: MinFCROptimizer) -> None:
        """Test optimization mode name."""
        assert optimizer.get_optimization_mode() == "min_fcr"


class TestTargetFCROptimizer:
    """Test suite for TargetFCROptimizer."""

    @pytest.fixture
    def optimizer(self) -> TargetFCROptimizer:
        """Create optimizer with target FCR of 1.25."""
        return TargetFCROptimizer(target_fcr=1.25)

    @pytest.fixture
    def sample_house(self) -> House:
        """Create a sample house."""
        forecasts = [
            DailyForecast(
                date=datetime(2025, 9, 15),
                weight=2.0,
                fcr=1.30,  # 0.05 from target
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
            farm_id="W01",
            initial_stock=30000,
            current_stock=30000,
            placement_date=datetime(2025, 8, 17),
            daily_forecasts=forecasts,
        )

    def test_score_candidate(
        self, optimizer: TargetFCROptimizer, sample_house: House
    ) -> None:
        """Test scoring based on distance from target FCR."""
        score = optimizer.score_candidate(
            house=sample_house,
            date=datetime(2025, 9, 15),
            quantity=10000,
        )

        # Score = -|FCR - target| = -|1.30 - 1.25| = -0.05
        assert score == pytest.approx(-0.05)

    def test_assign_priorities_by_distance_from_target(
        self, optimizer: TargetFCROptimizer
    ) -> None:
        """Test priority assignment based on distance from target."""
        farm = Farm(farm_id="W01", name="Farm", houses=[])

        # Target is 1.25
        candidates = [
            HouseCandidate(
                house=None,
                farm=farm,
                date=datetime(2025, 9, 15),
                available_quantity=10000,
                weight=2.0,
                fcr=1.4,  # Distance = 0.15
            ),
            HouseCandidate(
                house=None,
                farm=farm,
                date=datetime(2025, 9, 15),
                available_quantity=10000,
                weight=2.0,
                fcr=1.25,  # Distance = 0 (exact match)
            ),
            HouseCandidate(
                house=None,
                farm=farm,
                date=datetime(2025, 9, 15),
                available_quantity=10000,
                weight=2.0,
                fcr=1.2,  # Distance = 0.05
            ),
        ]

        result = optimizer.assign_priorities(candidates)

        # Exact match (1.25) should have priority 1
        assert result[0].fcr == 1.25
        assert result[0].priority == 1

        # Close (1.2, distance=0.05) should have priority 2
        assert result[1].fcr == 1.2
        assert result[1].priority == 2

        # Far (1.4, distance=0.15) should have priority 3
        assert result[2].fcr == 1.4
        assert result[2].priority == 3

    def test_optimization_mode(self, optimizer: TargetFCROptimizer) -> None:
        """Test optimization mode name."""
        assert optimizer.get_optimization_mode() == "target_fcr"


class TestProfitPriorityOptimizer:
    """Test suite for ProfitPriorityOptimizer."""

    @pytest.fixture
    def optimizer(self) -> ProfitPriorityOptimizer:
        """Create optimizer with equal weights."""
        return ProfitPriorityOptimizer(
            profit_weight=0.5,
            profit_loss_weight=0.5,
        )

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
            farm_id="W01",
            initial_stock=30000,
            current_stock=30000,
            placement_date=datetime(2025, 8, 17),
            daily_forecasts=forecasts,
        )

    def test_score_candidate(
        self, optimizer: ProfitPriorityOptimizer, sample_house: House
    ) -> None:
        """Test scoring based on weighted profit metrics."""
        score = optimizer.score_candidate(
            house=sample_house,
            date=datetime(2025, 9, 15),
            quantity=10000,
        )

        # Score = 0.5 * profit + 0.5 * profit_loss
        # = 0.5 * 1500000 + 0.5 * 5000 = 752500
        assert score == pytest.approx(752500.0)

    def test_assign_priorities_combined_ranking(
        self, optimizer: ProfitPriorityOptimizer
    ) -> None:
        """Test priority assignment using combined profit/profit_loss ranking."""
        farm = Farm(farm_id="W01", name="Farm", houses=[])

        candidates = [
            HouseCandidate(
                house=None,
                farm=farm,
                date=datetime(2025, 9, 15),
                available_quantity=10000,
                weight=2.0,
                fcr=1.25,
                total_profit=1000000,  # Rank 3 in profit
                profit_loss=10000,     # Rank 1 in profit_loss (highest)
            ),
            HouseCandidate(
                house=None,
                farm=farm,
                date=datetime(2025, 9, 15),
                available_quantity=10000,
                weight=2.0,
                fcr=1.25,
                total_profit=2000000,  # Rank 1 in profit (highest)
                profit_loss=3000,      # Rank 3 in profit_loss
            ),
            HouseCandidate(
                house=None,
                farm=farm,
                date=datetime(2025, 9, 15),
                available_quantity=10000,
                weight=2.0,
                fcr=1.25,
                total_profit=1500000,  # Rank 2 in profit
                profit_loss=5000,      # Rank 2 in profit_loss
            ),
        ]

        result = optimizer.assign_priorities(candidates)

        # With equal weights (0.5, 0.5):
        # Candidate 0: 0.5*3 + 0.5*1 = 2.0
        # Candidate 1: 0.5*1 + 0.5*3 = 2.0
        # Candidate 2: 0.5*2 + 0.5*2 = 2.0
        # All have the same combined score, so order may vary
        # But priorities should be assigned 1, 2, 3

        priorities = [c.priority for c in result]
        assert sorted(priorities) == [1, 2, 3]

    def test_assign_priorities_profit_dominated(self) -> None:
        """Test with profit_weight=1.0 (pure profit optimization)."""
        optimizer = ProfitPriorityOptimizer(
            profit_weight=1.0,
            profit_loss_weight=0.0,
        )
        farm = Farm(farm_id="W01", name="Farm", houses=[])

        candidates = [
            HouseCandidate(
                house=None,
                farm=farm,
                date=datetime(2025, 9, 15),
                available_quantity=10000,
                weight=2.0,
                fcr=1.25,
                total_profit=1000000,
                profit_loss=10000,
            ),
            HouseCandidate(
                house=None,
                farm=farm,
                date=datetime(2025, 9, 15),
                available_quantity=10000,
                weight=2.0,
                fcr=1.25,
                total_profit=2000000,
                profit_loss=1000,
            ),
        ]

        result = optimizer.assign_priorities(candidates)

        # Higher profit should be priority 1
        assert result[0].total_profit == 2000000
        assert result[0].priority == 1

    def test_assign_priorities_profit_loss_dominated(self) -> None:
        """Test with profit_loss_weight=1.0 (harvest urgent houses first)."""
        optimizer = ProfitPriorityOptimizer(
            profit_weight=0.0,
            profit_loss_weight=1.0,
        )
        farm = Farm(farm_id="W01", name="Farm", houses=[])

        candidates = [
            HouseCandidate(
                house=None,
                farm=farm,
                date=datetime(2025, 9, 15),
                available_quantity=10000,
                weight=2.0,
                fcr=1.25,
                total_profit=2000000,
                profit_loss=1000,  # Low loss
            ),
            HouseCandidate(
                house=None,
                farm=farm,
                date=datetime(2025, 9, 15),
                available_quantity=10000,
                weight=2.0,
                fcr=1.25,
                total_profit=1000000,
                profit_loss=10000,  # High loss - should harvest first
            ),
        ]

        result = optimizer.assign_priorities(candidates)

        # Higher profit_loss should be priority 1
        assert result[0].profit_loss == 10000
        assert result[0].priority == 1

    def test_optimization_mode(self, optimizer: ProfitPriorityOptimizer) -> None:
        """Test optimization mode name."""
        assert optimizer.get_optimization_mode() == "profit_priority"


class TestOptimizerFactory:
    """Test suite for OptimizerFactory."""

    def test_create_net_meat(self) -> None:
        """Test creating net_meat optimizer."""
        optimizer = OptimizerFactory.create("net_meat")
        assert isinstance(optimizer, NetMeatOptimizer)

    def test_create_min_fcr(self) -> None:
        """Test creating min_fcr optimizer."""
        optimizer = OptimizerFactory.create("min_fcr")
        assert isinstance(optimizer, MinFCROptimizer)

    def test_create_target_fcr(self) -> None:
        """Test creating target_fcr optimizer with config."""
        config = OptimizationConfig(
            optimization_mode="target_fcr",
            target_fcr=1.25,
        )
        optimizer = OptimizerFactory.create("target_fcr", config)

        assert isinstance(optimizer, TargetFCROptimizer)
        assert optimizer.target_fcr == 1.25

    def test_create_target_fcr_without_config_raises(self) -> None:
        """Test that target_fcr requires config."""
        with pytest.raises(ValueError, match="target_fcr"):
            OptimizerFactory.create("target_fcr")

    def test_create_profit_priority(self) -> None:
        """Test creating profit_priority optimizer."""
        config = OptimizationConfig(
            optimization_mode="profit_priority",
            profit_weight=0.7,
            profit_loss_weight=0.3,
        )
        optimizer = OptimizerFactory.create("profit_priority", config)

        assert isinstance(optimizer, ProfitPriorityOptimizer)
        assert optimizer.profit_weight == 0.7
        assert optimizer.profit_loss_weight == 0.3

    def test_create_profit_priority_default_weights(self) -> None:
        """Test profit_priority with default weights."""
        optimizer = OptimizerFactory.create("profit_priority")

        assert isinstance(optimizer, ProfitPriorityOptimizer)
        assert optimizer.profit_weight == 0.5
        assert optimizer.profit_loss_weight == 0.5

    def test_create_unknown_mode_raises(self) -> None:
        """Test that unknown mode raises ValueError."""
        with pytest.raises(ValueError, match="Unknown optimization mode"):
            OptimizerFactory.create("unknown_mode")

    def test_get_available_modes(self) -> None:
        """Test getting available modes."""
        modes = OptimizerFactory.get_available_modes()

        assert "net_meat" in modes
        assert "min_fcr" in modes
        assert "target_fcr" in modes
        assert "profit_priority" in modes

    def test_is_registered(self) -> None:
        """Test mode registration check."""
        assert OptimizerFactory.is_registered("net_meat") is True
        assert OptimizerFactory.is_registered("unknown") is False
