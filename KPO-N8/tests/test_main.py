import json
import random
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from main import (
    Action,
    Clover,
    EntityType,
    Predator,
    Prey,
    Priority,
    SpatialGrid,
    Terrain,
)


def _write_terrain(tmp_path, grid, cell_size=10):
    rows = len(grid)
    cols = len(grid[0])
    data = {
        "width": cols * cell_size,
        "height": rows * cell_size,
        "cell_size": cell_size,
        "grid": [[{"t": cell} for cell in row] for row in grid],
    }
    path = tmp_path / "terrain.json"
    path.write_text(json.dumps(data))
    return str(path)


def test_terrain_load_and_water_distance(tmp_path):
    terrain_path = _write_terrain(tmp_path, [[0, 2, 2]])
    terrain = Terrain(30, 10, 10, terrain_path)

    assert terrain.get_type_at(25, 5) == 2
    assert terrain.get_water_distance_at(25, 5) == 20

    cell_x, cell_y = terrain.get_cell_coords(25, 5)
    assert terrain.nearest_water[cell_y][cell_x] == (5.0, 5.0)


@pytest.mark.xfail(strict=True, reason="Protitest: wrong water distance expectation")
def test_terrain_load_and_water_distance_protitest(tmp_path):
    terrain_path = _write_terrain(tmp_path, [[0, 2, 2]])
    terrain = Terrain(30, 10, 10, terrain_path)
    assert terrain.get_water_distance_at(25, 5) == 10


def test_spatial_grid_skips_dead_agents(tmp_path):
    terrain_path = _write_terrain(tmp_path, [[2, 2], [2, 2]])
    terrain = Terrain(20, 20, 10, terrain_path)

    prey = Prey(5, 5, 1.0, 1.0, 50.0)
    prey.alive = False

    grid = SpatialGrid(10)
    grid.insert(prey)

    assert grid.get_nearby(5, 5, 10) == []
    assert terrain.get_terrain_props_at(5, 5)["walkable"]


@pytest.mark.xfail(strict=True, reason="Protitest: dead agents should not be returned")
def test_spatial_grid_skips_dead_agents_protitest(tmp_path):
    terrain_path = _write_terrain(tmp_path, [[2, 2], [2, 2]])
    terrain = Terrain(20, 20, 10, terrain_path)
    prey = Prey(5, 5, 1.0, 1.0, 50.0)
    prey.alive = False
    grid = SpatialGrid(10)
    grid.insert(prey)
    assert grid.get_nearby(5, 5, 10) != []


def test_agent_move_step_blocks_nonwalkable(tmp_path):
    terrain_path = _write_terrain(tmp_path, [[2, 0]])
    terrain = Terrain(20, 10, 10, terrain_path)

    prey = Prey(5, 5, 2.0, 1.0, 50.0)
    moved = prey.move_step(10, 0, terrain)

    assert moved is False
    assert prey.x == 5
    assert prey.y == 5


@pytest.mark.xfail(strict=True, reason="Protitest: movement into non-walkable should fail")
def test_agent_move_step_blocks_nonwalkable_protitest(tmp_path):
    terrain_path = _write_terrain(tmp_path, [[2, 0]])
    terrain = Terrain(20, 10, 10, terrain_path)
    prey = Prey(5, 5, 2.0, 1.0, 50.0)
    moved = prey.move_step(10, 0, terrain)
    assert moved is True


def test_agent_priority_rules():
    prey = Prey(0, 0, 1.0, 1.0, 50.0)
    prey.thirst = 80
    prey.hunger = 10
    prey.reproductive_urge = 0

    assert prey.get_priority() is Priority.THIRST

    prey.thirst = 10
    prey.hunger = 80
    assert prey.get_priority() is Priority.HUNGER


@pytest.mark.xfail(strict=True, reason="Protitest: wrong priority ordering")
def test_agent_priority_rules_protitest():
    prey = Prey(0, 0, 1.0, 1.0, 50.0)
    prey.thirst = 80
    prey.hunger = 10
    prey.reproductive_urge = 0
    assert prey.get_priority() is Priority.HUNGER


def test_reproduction_costs_are_applied():
    random.seed(0)
    a = Prey(0, 0, 1.0, 1.0, 50.0)
    b = Prey(1, 1, 1.0, 1.0, 50.0)
    a.sex = "M"
    b.sex = "F"

    a.reproductive_urge = 120
    b.reproductive_urge = 120

    assert a._can_reproduce_with(b) is True

    a._apply_reproduction_to_pair(b)

    assert a.hunger == a.REPRO_COST_HUNGER
    assert b.thirst == b.REPRO_COST_THIRST
    assert a.reproductive_urge == a.REPRO_COOLDOWN
    assert b.reproductive_urge == b.REPRO_COOLDOWN


@pytest.mark.xfail(strict=True, reason="Protitest: reproduction costs must be applied")
def test_reproduction_costs_are_applied_protitest():
    a = Prey(0, 0, 1.0, 1.0, 50.0)
    b = Prey(1, 1, 1.0, 1.0, 50.0)
    a.sex = "M"
    b.sex = "F"
    a.reproductive_urge = 120
    b.reproductive_urge = 120
    a._apply_reproduction_to_pair(b)
    assert a.hunger == 0


def test_prey_flee_interrupts_for_predator(tmp_path):
    terrain_path = _write_terrain(tmp_path, [[2, 2, 2]])
    terrain = Terrain(30, 10, 10, terrain_path)

    prey = Prey(15, 5, 2.0, 1.0, 100.0)
    predator = Predator(25, 5, 2.0, 1.0, 100.0)

    did_interrupt = prey._special_interrupt([predator], prey.sense * prey.sense, terrain)

    assert did_interrupt is True
    assert prey.current_action is Action.FLEE
    assert prey.x < 15


@pytest.mark.xfail(strict=True, reason="Protitest: prey should flee from predator")
def test_prey_flee_interrupts_for_predator_protitest(tmp_path):
    terrain_path = _write_terrain(tmp_path, [[2, 2, 2]])
    terrain = Terrain(30, 10, 10, terrain_path)
    prey = Prey(15, 5, 2.0, 1.0, 100.0)
    predator = Predator(25, 5, 2.0, 1.0, 100.0)
    did_interrupt = prey._special_interrupt([predator], prey.sense * prey.sense, terrain)
    assert did_interrupt is False


def test_predator_consumes_close_prey(tmp_path):
    terrain_path = _write_terrain(tmp_path, [[2, 2, 2]])
    terrain = Terrain(30, 10, 10, terrain_path)

    predator = Predator(10, 5, 2.0, 1.0, 100.0)
    prey = Prey(10, 5, 1.0, 1.0, 80.0)

    predator._handle_hunger([prey], predator.sense * predator.sense, terrain)

    assert predator.current_action is Action.CONSUME
    assert predator.hunger == 0
    assert prey.alive is False


@pytest.mark.xfail(strict=True, reason="Protitest: predator should consume prey at close range")
def test_predator_consumes_close_prey_protitest(tmp_path):
    terrain_path = _write_terrain(tmp_path, [[2, 2, 2]])
    terrain = Terrain(30, 10, 10, terrain_path)
    predator = Predator(10, 5, 2.0, 1.0, 100.0)
    prey = Prey(10, 5, 1.0, 1.0, 80.0)
    predator._handle_hunger([prey], predator.sense * predator.sense, terrain)
    assert prey.alive is True


def test_clover_spawns_when_ready(monkeypatch, tmp_path):
    terrain_path = _write_terrain(tmp_path, [[2, 2, 2], [2, 0, 2], [2, 2, 2]])
    terrain = Terrain(30, 30, 10, terrain_path)

    clover = Clover(10, 10, terrain)
    clover.reproductive_urge = 150
    clover.thirst = 0

    grid = SpatialGrid(10)
    grid.insert(clover)

    calls = iter([0.0, 20.0])

    def _fixed_uniform(a, b):
        try:
            return next(calls)
        except StopIteration:
            return 0.0

    monkeypatch.setattr(random, "uniform", _fixed_uniform)

    new_agents = []
    clover.act(terrain, grid, new_agents, max_food_capacity=80)

    assert len(new_agents) == 1
    assert new_agents[0].entity_type is EntityType.CLOVER
    assert clover.thirst >= 40


@pytest.mark.xfail(strict=True, reason="Protitest: clover should spawn when ready")
def test_clover_spawns_when_ready_protitest(monkeypatch, tmp_path):
    terrain_path = _write_terrain(tmp_path, [[2, 2, 2], [2, 0, 2], [2, 2, 2]])
    terrain = Terrain(30, 30, 10, terrain_path)
    clover = Clover(10, 10, terrain)
    clover.reproductive_urge = 150
    clover.thirst = 0
    grid = SpatialGrid(10)
    grid.insert(clover)
    calls = iter([0.0, 20.0])

    def _fixed_uniform(a, b):
        try:
            return next(calls)
        except StopIteration:
            return 0.0

    monkeypatch.setattr(random, "uniform", _fixed_uniform)
    new_agents = []
    clover.act(terrain, grid, new_agents, max_food_capacity=80)
    assert len(new_agents) == 0


def test_terrain_clamps_cell_coords(tmp_path):
    terrain_path = _write_terrain(tmp_path, [[2, 2], [2, 2]])
    terrain = Terrain(20, 20, 10, terrain_path)

    assert terrain.get_cell_coords(-5, -5) == (0, 0)
    assert terrain.get_cell_coords(999, 999) == (1, 1)


@pytest.mark.xfail(strict=True, reason="Protitest: coords should clamp to grid")
def test_terrain_clamps_cell_coords_protitest(tmp_path):
    terrain_path = _write_terrain(tmp_path, [[2, 2], [2, 2]])
    terrain = Terrain(20, 20, 10, terrain_path)
    assert terrain.get_cell_coords(-5, -5) == (1, 1)


def test_agent_drinks_at_shoreline(tmp_path):
    terrain_path = _write_terrain(tmp_path, [[0, 2]])
    terrain = Terrain(20, 10, 10, terrain_path)

    prey = Prey(10, 5, 1.0, 1.0, 80.0)
    prey.thirst = 80

    handled, drank = prey.try_drink_from_nearest_water(terrain, prey.sense)

    assert handled is True
    assert drank is True
    assert prey.thirst < 80


@pytest.mark.xfail(strict=True, reason="Protitest: drinking should reduce thirst")
def test_agent_drinks_at_shoreline_protitest(tmp_path):
    terrain_path = _write_terrain(tmp_path, [[0, 2]])
    terrain = Terrain(20, 10, 10, terrain_path)
    prey = Prey(10, 5, 1.0, 1.0, 80.0)
    prey.thirst = 80
    _, _ = prey.try_drink_from_nearest_water(terrain, prey.sense)
    assert prey.thirst >= 80


def test_predator_priority_prefers_hunger_over_thirst():
    predator = Predator(0, 0, 1.0, 1.0, 50.0)
    predator.hunger = 90
    predator.thirst = 80

    assert predator.get_priority() is Priority.HUNGER


@pytest.mark.xfail(strict=True, reason="Protitest: hunger should win over thirst")
def test_predator_priority_prefers_hunger_over_thirst_protitest():
    predator = Predator(0, 0, 1.0, 1.0, 50.0)
    predator.hunger = 90
    predator.thirst = 80
    assert predator.get_priority() is Priority.THIRST


def test_reproduction_partner_requires_opposite_sex():
    a = Prey(0, 0, 1.0, 1.0, 50.0)
    b = Prey(1, 1, 1.0, 1.0, 50.0)
    a.sex = "M"
    b.sex = "M"

    a.reproductive_urge = 120
    b.reproductive_urge = 120

    assert a._can_reproduce_with(b) is False


@pytest.mark.xfail(strict=True, reason="Protitest: same-sex should not reproduce")
def test_reproduction_partner_requires_opposite_sex_protitest():
    a = Prey(0, 0, 1.0, 1.0, 50.0)
    b = Prey(1, 1, 1.0, 1.0, 50.0)
    a.sex = "M"
    b.sex = "M"
    a.reproductive_urge = 120
    b.reproductive_urge = 120
    assert a._can_reproduce_with(b) is True

