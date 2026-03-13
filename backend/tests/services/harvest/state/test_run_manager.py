import uuid

from app.services.harvest.state.run_manager import ActiveRun


def test_active_run_starts_unpaused():
    run = ActiveRun(
        run_id=uuid.uuid4(),
        owner_id=uuid.uuid4(),
        config={"optimization_mode": "net_meat"},
    )
    assert run.status == "pending"
    assert run.pause_event.is_set()


def test_active_run_pause_resume():
    run = ActiveRun(
        run_id=uuid.uuid4(),
        owner_id=uuid.uuid4(),
        config={},
    )
    run.pause_event.clear()
    assert not run.pause_event.is_set()
    run.pause_event.set()
    assert run.pause_event.is_set()


def test_active_run_cancel_flag():
    run = ActiveRun(
        run_id=uuid.uuid4(),
        owner_id=uuid.uuid4(),
        config={},
    )
    assert not run.cancel_flag
    run.cancel_flag = True
    assert run.cancel_flag
