from importlib import import_module, util

import pytest


def module():
    name = "tests.smoke.restart_backend_smoke"
    assert util.find_spec(name) is not None, "Нет restart helper"
    return import_module(name)


def test_restart_waits_for_new_process_before_accepting_health():
    mod = module()
    states = iter([("old", "healthy"), ("new", "starting"), ("new", "healthy")])
    slept = []
    assert (
        mod.wait_for_restart(
            "old", lambda: next(states), sleep=lambda: slept.append(True), attempts=3
        )
        == "new"
    )
    assert len(slept) == 2


def test_old_health_or_unhealthy_restart_times_out():
    mod = module()
    for state in [("old", "healthy"), ("new", "unhealthy")]:
        with pytest.raises(RuntimeError, match="restart"):
            mod.wait_for_restart("old", lambda: state, sleep=lambda: None, attempts=2)
