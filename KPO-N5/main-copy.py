import tkinter as tk
import threading
import queue
from collections import deque
import time
import random
import math
import glob
import os
import json
from enum import Enum
from terrain_builder import generate_terrain_grid

# ── colours ──────────────────────────────────────────────────────────────────
COLOR_AGENT = "#3a7bd5"
COLOR_AGENT_DEAD = "#555555"
COLOR_AGENT_PRED = "#e03131"
COLOR_AGENT_PREY = "#dcdcdc"
COLOR_AGENT_FOOD = "#2ecc71"
COLOR_BORDER = "#cccccc"

# ── canvas / agent geometry ───────────────────────────────────────────────────
SIM_WIDTH = 1200
SIM_HEIGHT = 420
AGENT_R_BASE = 4
FOOD_R = 3
CELL_SIZE = 10  # Velikost mrežne celice za teren

# -- simulation defaults -------------------------------------------------------
QUEUE_MAX = 100
DEFAULT_PREY_COUNT = "30"
DEFAULT_PREDATOR_COUNT = "5"
DEFAULT_CLOVER_CAPACITY = "80"
DEFAULT_INITIAL_SPEED = "2.0"
DEFAULT_INITIAL_SIZE = "1.0"
DEFAULT_INITIAL_SENSE = "80.0"
DEFAULT_MUTATION_PROBABILITY = "0.1"
DEFAULT_MUTATION_STRENGTH = "0.2"

DEFAULT_SIMULATION_DELAY_SECONDS = "0.01"
DEFAULT_UI_REFRESH_INTERVAL_MS = "60"

REPRODUCTION_DISTANCE_PADDING = 5
INTERACTION_DISTANCE_PADDING = 10
WATER_SHORELINE_PADDING = 10
THIRST_RESTORE_AMOUNT = 50
PREY_FLEE_SPEED_MULTIPLIER = 1.2
PREDATOR_CHASE_SPEED_MULTIPLIER = 1.3


class EntityType(Enum):
    AGENT = "Agent"
    PREY = "Prey"
    PREDATOR = "Predator"
    CLOVER = "Clover"


class Priority(Enum):
    THIRST = "Thirst"
    HUNGER = "Hunger"
    REPRODUCTION = "Reproduction"
    WANDER = "Wander"


class Action(Enum):
    WANDER = "Wander"
    FLEE = "Flee"
    MATE = "Mate"
    THIRST = "Thirst"
    DRINK = "Drink"
    HUNGER = "Hunger"
    EAT = "Eat"
    HUNT = "Hunt"
    CONSUME = "Consume"
    GROW = "Grow"


# ─────────────────────────────────────────────────────────────────────────────
# 1.  MODELS & TERRAIN
# ─────────────────────────────────────────────────────────────────────────────

class Terrain:
    # Terrain modifiers used by movement and survival systems.
    TERRAIN_PROPS = {
        0: {"walkable": False, "speed_mod": 0.0, "thirst_mod": 1.0, "hunger_mod": 1.0, "color": "#2196f3",
            "name": "Water"},
        1: {"walkable": True, "speed_mod": 0.8, "thirst_mod": 1.5, "hunger_mod": 1.0, "color": "#f4d03f",
            "name": "Sand"},
        2: {"walkable": True, "speed_mod": 1.0, "thirst_mod": 1.0, "hunger_mod": 1.0, "color": "#2ecc71",
            "name": "Grass"},
        3: {"walkable": True, "speed_mod": 0.7, "thirst_mod": 0.8, "hunger_mod": 0.8, "color": "#1b5e20",
            "name": "Forest"},
        4: {"walkable": True, "speed_mod": 0.5, "thirst_mod": 1.2, "hunger_mod": 1.2, "color": "#795548",
            "name": "Mountain"},
        5: {"walkable": False, "speed_mod": 0.0, "thirst_mod": 1.0, "hunger_mod": 1.0, "color": "#fdfefe",
            "name": "Peak"},
    }

    def __init__(self, width, height, cell_size=CELL_SIZE, terrain_file=None):
        self.width = width
        self.height = height
        self.cell_size = cell_size
        self.cols = width // cell_size
        self.rows = height // cell_size

        self.grid = self._load_or_generate_grid(terrain_file)
        self._compute_water_distance()

    def _load_or_generate_grid(self, terrain_file):
        if terrain_file and terrain_file != "Random Generate":
            return self._load_grid_from_file(terrain_file)

        return self._generate_random_grid()

    def _load_grid_from_file(self, terrain_file):
        with open(terrain_file, "r") as file:
            data = json.load(file)
            grid_rows = data["grid"]
            return [[cell["t"] for cell in row] for row in grid_rows]

    def _generate_random_grid(self):
        seed = random.randint(0, 999999)
        raw_grid = generate_terrain_grid(
            self.width,
            self.height,
            self.cell_size,
            seed,
            scale=50,
            octaves=4,
            t_water=0.40,
            t_sand=0.425,
            t_grass=0.775,
            t_forest=0.925,
            t_mount=0.975,
        )
        return [[cell["t"] for cell in row] for row in raw_grid]

    def _compute_water_distance(self):
        """Precompute nearest water location for each cell using BFS."""
        self.water_dist = [[float("inf") for _ in range(self.cols)] for _ in range(self.rows)]
        self.nearest_water = [[None for _ in range(self.cols)] for _ in range(self.rows)]

        queue_cells = deque()

        for y in range(self.rows):
            for x in range(self.cols):
                if self.grid[y][x] != 0:
                    continue

                self.water_dist[y][x] = 0
                self.nearest_water[y][x] = (
                    x * self.cell_size + self.cell_size / 2,
                    y * self.cell_size + self.cell_size / 2,
                )
                queue_cells.append((x, y))

        directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]

        while queue_cells:
            x, y = queue_cells.popleft()
            current_distance = self.water_dist[y][x]
            nearest_water_point = self.nearest_water[y][x]

            for dx, dy in directions:
                neighbor_x = x + dx
                neighbor_y = y + dy

                if not (0 <= neighbor_x < self.cols and 0 <= neighbor_y < self.rows):
                    continue

                if self.water_dist[neighbor_y][neighbor_x] <= current_distance + 1:
                    continue

                self.water_dist[neighbor_y][neighbor_x] = current_distance + 1
                self.nearest_water[neighbor_y][neighbor_x] = nearest_water_point
                queue_cells.append((neighbor_x, neighbor_y))

    def get_cell_coords(self, x, y):
        cell_x = int(x / self.cell_size)
        cell_y = int(y / self.cell_size)

        cell_x = max(0, min(self.cols - 1, cell_x))
        cell_y = max(0, min(self.rows - 1, cell_y))

        return cell_x, cell_y

    def get_type_at(self, x, y):
        cell_x, cell_y = self.get_cell_coords(x, y)
        return self.grid[cell_y][cell_x]

    def get_terrain_props_at(self, x, y):
        terrain_type = self.get_type_at(x, y)
        return self.TERRAIN_PROPS[terrain_type]

    def get_water_distance_at(self, x, y):
        cell_x, cell_y = self.get_cell_coords(x, y)
        return self.water_dist[cell_y][cell_x] * self.cell_size


class SpatialGrid:
    def __init__(self, cell_size):
        self.cell_size = cell_size
        self.cells = {}

    def clear(self):
        self.cells.clear()

    def insert(self, agent):
        if not agent.alive: return
        cx = int(agent.x / self.cell_size)
        cy = int(agent.y / self.cell_size)
        if (cx, cy) not in self.cells:
            self.cells[(cx, cy)] = []
        self.cells[(cx, cy)].append(agent)

    def get_nearby(self, x, y, radius):
        nearby = []
        min_cx = int((x - radius) / self.cell_size)
        max_cx = int((x + radius) / self.cell_size)
        min_cy = int((y - radius) / self.cell_size)
        max_cy = int((y + radius) / self.cell_size)

        for cx in range(min_cx, max_cx + 1):
            for cy in range(min_cy, max_cy + 1):
                if (cx, cy) in self.cells:
                    nearby.extend(self.cells[(cx, cy)])
        return nearby


class Agent:
    # Base survival and reproduction constants.
    BASE_HUNGER_RATE = 0.05
    BASE_THIRST_RATE = 0.05
    SPEED_THIRST_FACTOR = 0.05
    SIZE_HUNGER_FACTOR = 1.0
    BASE_REPRO_RATE = 0.005
    REPRO_COST_HUNGER = 30
    REPRO_COST_THIRST = 30
    REPRO_COOLDOWN = -30

    entity_type = EntityType.AGENT
    is_plant = False

    id_counter = 0

    def __init__(self, x: float, y: float, speed: float, size: float, sense: float):
        Agent.id_counter += 1
        self.id = Agent.id_counter

        self.x = x
        self.y = y
        self.speed = speed
        self.size = size
        self.sense = sense

        self.age = 0
        self.max_age = random.randint(3000, 5000)

        self.hunger = 0.0
        self.thirst = 0.0
        self.reproductive_urge = 0.0

        self.alive = True
        self.color = COLOR_AGENT
        self.sex = random.choice(["M", "F"])

        self.wander_angle = random.uniform(0, 2 * math.pi)
        self.current_action = Action.WANDER

    @property
    def radius(self):
        return AGENT_R_BASE + int(self.size - 1.0)

    def update_needs(self, terrain):
        if not self.alive:
            return

        self.age += 1

        terrain_props = terrain.get_terrain_props_at(self.x, self.y)

        thirst_increase = self.BASE_THIRST_RATE + (self.speed * self.SPEED_THIRST_FACTOR)
        hunger_increase = self.BASE_HUNGER_RATE * (self.size * self.SIZE_HUNGER_FACTOR)

        self.thirst += thirst_increase * terrain_props["thirst_mod"]
        self.hunger += hunger_increase * terrain_props["hunger_mod"]

        if self.hunger >= 100:
            self.hunger = 100
            self.thirst += self.BASE_THIRST_RATE * 2

        health_factor = max(0.0, 1.0 - (self.hunger + self.thirst) / 200.0)
        self.reproductive_urge += self.BASE_REPRO_RATE * (0.5 + health_factor)

        if self.thirst >= 100:
            self.alive = False
            return

        if self.age > self.max_age:
            self.alive = False

    def mix_genes(self, partner, mutation_probability, mutation_strength):
        child_speed = (self.speed + partner.speed) / 2.0
        child_size = (self.size + partner.size) / 2.0
        child_sense = (self.sense + partner.sense) / 2.0

        child_speed *= random.uniform(0.9, 1.1)
        child_size *= random.uniform(0.9, 1.1)
        child_sense *= random.uniform(0.9, 1.1)

        if random.random() < mutation_probability:
            child_speed *= random.choice([1.0 - mutation_strength, 1.0 + mutation_strength])

        if random.random() < mutation_probability:
            child_size *= random.choice([1.0 - mutation_strength, 1.0 + mutation_strength])

        if random.random() < mutation_probability:
            child_sense *= random.choice([1.0 - mutation_strength, 1.0 + mutation_strength])

        return type(self)(
            self.x,
            self.y,
            max(0.5, child_speed),
            max(0.2, child_size),
            max(20.0, child_sense),
        )

    def get_priority(self):
        if self.thirst > 75:
            return Priority.THIRST

        if self.hunger > 75:
            return Priority.HUNGER

        if self.reproductive_urge >= 100 and self.hunger < 40 and self.thirst < 40:
            return Priority.REPRODUCTION

        if self.thirst > 40:
            return Priority.THIRST

        if self.hunger > 40:
            return Priority.HUNGER

        return Priority.WANDER

    def _clamp_bounds(self):
        hit_wall = False

        if self.x < self.radius:
            self.x = self.radius
            hit_wall = True

        if self.x > SIM_WIDTH - self.radius:
            self.x = SIM_WIDTH - self.radius
            hit_wall = True

        if self.y < self.radius:
            self.y = self.radius
            hit_wall = True

        if self.y > SIM_HEIGHT - self.radius:
            self.y = SIM_HEIGHT - self.radius
            hit_wall = True

        return hit_wall

    def move_step(self, dx, dy, terrain):
        terrain_props = terrain.get_terrain_props_at(self.x, self.y)
        speed_modifier = terrain_props["speed_mod"]

        new_x = self.x + dx * speed_modifier
        new_y = self.y + dy * speed_modifier

        new_props = terrain.get_terrain_props_at(new_x, new_y)

        if not new_props["walkable"]:
            if not self.is_plant:
                self.wander_angle += math.pi
            return False

        self.x = new_x
        self.y = new_y

        hit_wall = self._clamp_bounds()

        if hit_wall and not self.is_plant:
            self.wander_angle += math.pi

        return True

    def _can_reproduce_with(self, other):
        if other.entity_type != self.entity_type:
            return False

        if not other.alive:
            return False

        if other == self:
            return False

        if getattr(other, "sex", None) == self.sex:
            return False

        return other.get_priority() is Priority.REPRODUCTION

    def _apply_reproduction_cost(self):
        self.hunger += self.REPRO_COST_HUNGER
        self.thirst += self.REPRO_COST_THIRST
        self.reproductive_urge = self.REPRO_COOLDOWN

    def _apply_reproduction_to_pair(self, partner):
        self._apply_reproduction_cost()
        partner._apply_reproduction_cost()

    def _find_reproduction_partner(self, entities, sense_sq):
        return self.get_closest_target(entities, sense_sq, self._can_reproduce_with)

    def move_towards(self, target_x, target_y, speed_limit, terrain):
        distance_sq = (target_x - self.x) ** 2 + (target_y - self.y) ** 2

        if distance_sq <= 0:
            return

        distance = math.sqrt(distance_sq)
        step = min(distance, speed_limit)

        dx = ((target_x - self.x) / distance) * step
        dy = ((target_y - self.y) / distance) * step

        self.move_step(dx, dy, terrain)
        self.wander_angle = math.atan2(target_y - self.y, target_x - self.x)

    def wander(self, terrain):
        self.wander_angle += random.uniform(-0.3, 0.3)

        dx = math.cos(self.wander_angle) * self.speed
        dy = math.sin(self.wander_angle) * self.speed

        self.move_step(dx, dy, terrain)

    def is_in_interaction_range(self, target, distance_sq, extra_padding=INTERACTION_DISTANCE_PADDING):
        required_distance = self.radius + target.radius + extra_padding
        return distance_sq < required_distance * required_distance

    def try_drink_from_nearest_water(self, terrain, sense_range):
        cell_x, cell_y = terrain.get_cell_coords(self.x, self.y)
        water_target = terrain.nearest_water[cell_y][cell_x]

        distance_to_water = terrain.get_water_distance_at(self.x, self.y)

        if not water_target:
            return False, False

        if distance_to_water > sense_range:
            return False, False

        target_x, target_y = water_target

        distance = math.hypot(target_x - self.x, target_y - self.y)
        shoreline_distance = terrain.cell_size + self.radius + WATER_SHORELINE_PADDING

        if distance < shoreline_distance:
            self.thirst = max(0.0, self.thirst - THIRST_RESTORE_AMOUNT)
            return True, True

        self.move_towards(target_x, target_y, self.speed, terrain)
        return True, False

    def get_closest_target(self, entities, sense_sq, filter_func, score_func=None):
        best_target = None
        min_distance_sq = float("inf")
        best_score = -float("inf")

        for entity in entities:
            if not filter_func(entity):
                continue

            distance_sq = (entity.x - self.x) ** 2 + (entity.y - self.y) ** 2

            if distance_sq >= sense_sq:
                continue

            if score_func:
                score = score_func(entity, distance_sq)
                if score <= best_score:
                    continue

                best_score = score
                best_target = entity
                min_distance_sq = distance_sq
                continue

            if distance_sq >= min_distance_sq:
                continue

            min_distance_sq = distance_sq
            best_target = entity

        return best_target, min_distance_sq

    def _handle_thirst(self, terrain):
        self.current_action = Action.THIRST

        water_handled, did_drink = self.try_drink_from_nearest_water(terrain, self.sense)

        if did_drink:
            self.current_action = Action.DRINK
            return

        if water_handled:
            return

        self.wander(terrain)

    def _handle_reproduction(self, entities, sense_sq, new_agents, terrain, mutation_probability, mutation_strength):
        self.current_action = Action.MATE

        best_partner, min_distance_sq = self._find_reproduction_partner(entities, sense_sq)

        if not best_partner:
            self.wander(terrain)
            return

        can_reproduce_now = self.is_in_interaction_range(
            best_partner,
            min_distance_sq,
            REPRODUCTION_DISTANCE_PADDING,
        )

        if not can_reproduce_now:
            self.move_towards(best_partner.x, best_partner.y, self.speed, terrain)
            return

        self._apply_reproduction_to_pair(best_partner)
        self._spawn_offspring(best_partner, new_agents, mutation_probability, mutation_strength)

    def _spawn_offspring(self, partner, new_agents, mutation_probability, mutation_strength):
        new_agents.append(self.mix_genes(partner, mutation_probability, mutation_strength))

    def act(self, terrain, spatial_grid, new_agents, mutation_probability, mutation_strength):
        if not self.alive:
            return

        nearby_entities = spatial_grid.get_nearby(self.x, self.y, self.sense)
        sense_sq = self.sense * self.sense

        if self._special_interrupt(nearby_entities, sense_sq, terrain):
            return

        priority = self.get_priority()

        if priority is Priority.REPRODUCTION:
            self._handle_reproduction(
                nearby_entities,
                sense_sq,
                new_agents,
                terrain,
                mutation_probability,
                mutation_strength,
            )
            return

        if priority is Priority.THIRST:
            self._handle_thirst(terrain)
            return

        if priority is Priority.HUNGER:
            self._handle_hunger(nearby_entities, sense_sq, terrain)
            return

        self.current_action = Action.WANDER
        self.wander(terrain)

    def _special_interrupt(self, entities, sense_sq, terrain):
        return False

    def _handle_hunger(self, entities, sense_sq, terrain):
        pass


class Prey(Agent):
    BASE_HUNGER_RATE = 0.04
    BASE_THIRST_RATE = 0.05
    SPEED_THIRST_FACTOR = 0.04
    SIZE_HUNGER_FACTOR = 1.0
    BASE_REPRO_RATE = 0.22
    REPRO_COST_HUNGER = 25
    REPRO_COST_THIRST = 25
    REPRO_COOLDOWN = -60

    entity_type = EntityType.PREY

    def __init__(self, x, y, speed, size, sense):
        super().__init__(x, y, speed, size, sense)
        self.color = COLOR_AGENT_PREY
        self.max_age = random.randint(3000, 5000)

    def _spawn_offspring(self, partner, new_agents, mutation_probability, mutation_strength):
        litter_size = random.choice([1, 1, 2, 2, 2, 3])

        for _ in range(litter_size):
            new_agents.append(self.mix_genes(partner, mutation_probability, mutation_strength))

    def _special_interrupt(self, entities, sense_sq, terrain):
        flee_dx = 0.0
        flee_dy = 0.0
        is_fleeing = False

        for entity in entities:
            if entity.entity_type is not EntityType.PREDATOR:
                continue

            if not entity.alive:
                continue

            distance_sq = (entity.x - self.x) ** 2 + (entity.y - self.y) ** 2

            if distance_sq >= sense_sq:
                continue

            is_fleeing = True
            weight = 1.0 / (distance_sq + 0.1)

            flee_dx += (self.x - entity.x) * weight
            flee_dy += (self.y - entity.y) * weight

        if not is_fleeing:
            return False

        self.current_action = Action.FLEE

        magnitude = math.hypot(flee_dx, flee_dy)

        if magnitude <= 0:
            return True

        dx = (flee_dx / magnitude) * (self.speed * PREY_FLEE_SPEED_MULTIPLIER)
        dy = (flee_dy / magnitude) * (self.speed * PREY_FLEE_SPEED_MULTIPLIER)

        self.move_step(dx, dy, terrain)
        self.wander_angle = math.atan2(flee_dy, flee_dx)

        return True

    def _handle_hunger(self, entities, sense_sq, terrain):
        self.current_action = Action.HUNGER

        best_food, distance_sq = self.get_closest_target(
            entities,
            sense_sq,
            lambda e: e.is_plant and e.alive,
        )

        if not best_food:
            self.wander(terrain)
            return

        if self.is_in_interaction_range(best_food, distance_sq, INTERACTION_DISTANCE_PADDING):
            best_food.alive = False
            self.hunger = 0
            self.current_action = Action.EAT
            return

        self.move_towards(best_food.x, best_food.y, self.speed, terrain)


class Predator(Agent):
    BASE_HUNGER_RATE = 0.15
    BASE_THIRST_RATE = 0.005
    SPEED_THIRST_FACTOR = 0.02
    SIZE_HUNGER_FACTOR = 1.5
    BASE_REPRO_RATE = 0.05
    REPRO_COST_HUNGER = 80
    REPRO_COST_THIRST = 40
    REPRO_COOLDOWN = -150

    entity_type = EntityType.PREDATOR

    def __init__(self, x, y, speed, size, sense):
        super().__init__(x, y, speed, size, sense)
        self.color = COLOR_AGENT_PRED
        self.max_age = random.randint(8000, 10000)

    def get_priority(self):
        if self.thirst > 85:
            return Priority.THIRST

        if self.hunger > 85:
            return Priority.HUNGER

        if self.reproductive_urge >= 100 and self.hunger < 50 and self.thirst < 50:
            return Priority.REPRODUCTION

        if self.hunger > 30:
            return Priority.HUNGER

        if self.thirst > 50:
            return Priority.THIRST

        return Priority.WANDER

    def _handle_hunger(self, entities, sense_sq, terrain):
        self.current_action = Action.HUNT

        def score(entity, distance_sq):
            distance = math.sqrt(distance_sq)
            return (entity.size * 10) - distance

        best_prey, distance_sq = self.get_closest_target(
            entities,
            sense_sq,
            lambda e: e.entity_type is EntityType.PREY and e.alive,
            score,
        )

        if not best_prey:
            self.current_action = Action.HUNGER
            self.wander(terrain)
            return

        if self.is_in_interaction_range(best_prey, distance_sq, INTERACTION_DISTANCE_PADDING):
            best_prey.alive = False
            self.hunger = 0
            self.current_action = Action.CONSUME
            return

        self.move_towards(
            best_prey.x,
            best_prey.y,
            self.speed * PREDATOR_CHASE_SPEED_MULTIPLIER,
            terrain,
        )


class Clover(Agent):
    BASE_THIRST_RATE = 0.8
    SPEED_THIRST_FACTOR = 0.0
    SIZE_HUNGER_FACTOR = 0.0
    BASE_REPRO_RATE = 0.4

    entity_type = EntityType.CLOVER
    is_plant = True

    def __init__(self, x: float, y: float, terrain):
        super().__init__(x, y, speed=0.0, size=0.1, sense=150.0)

        self.color = COLOR_AGENT_FOOD
        self.max_age = random.randint(1000, 2000)
        self.current_action = Action.GROW

        self.reproductive_urge = random.uniform(0, 50)

        distance_to_water = terrain.get_water_distance_at(self.x, self.y)

        self.base_water_potential = 0.0
        if distance_to_water < self.sense:
            self.base_water_potential = (
                    (self.sense - max(0, distance_to_water)) / self.sense * 1.5
            )

        self.moisture_supply = self.base_water_potential

    @property
    def radius(self):
        return FOOD_R

    def update_needs(self):
        pass

    def _update_plant_needs(self, crowding_factor):
        if not self.alive:
            return

        self.age += 1

        self.moisture_supply = self.base_water_potential / max(1.0, crowding_factor)

        net_thirst = self.BASE_THIRST_RATE - self.moisture_supply
        self.thirst = max(0.0, min(150.0, self.thirst + net_thirst))

        if self.thirst >= 100:
            self.alive = False
            return

        if self.age > self.max_age:
            self.alive = False
            return

        if self.thirst >= 5.0:
            return

        if self.moisture_supply <= self.BASE_THIRST_RATE:
            return

        health_factor = max(0.0, 1.0 - (self.thirst / 100.0))
        surplus = self.moisture_supply - self.BASE_THIRST_RATE

        self.reproductive_urge += self.BASE_REPRO_RATE * (0.5 + 2.0 * health_factor + surplus)

    def _count_neighbors(self, spatial_grid):
        nearby_entities = spatial_grid.get_nearby(self.x, self.y, 30)

        neighbor_count = 0

        for entity in nearby_entities:
            if not entity.is_plant:
                continue

            if not entity.alive:
                continue

            if entity == self:
                continue

            if (entity.x - self.x) ** 2 + (entity.y - self.y) ** 2 >= 900:
                continue

            neighbor_count += 1

        return neighbor_count

    def _attempt_spawn(self, terrain, new_agents):
        for _ in range(5):
            angle = random.uniform(0, 2 * math.pi)
            distance = random.uniform(20, 50)

            new_x = self.x + math.cos(angle) * distance
            new_y = self.y + math.sin(angle) * distance

            if not (0 < new_x < SIM_WIDTH and 0 < new_y < SIM_HEIGHT):
                continue

            if not terrain.get_terrain_props_at(new_x, new_y)["walkable"]:
                continue

            new_agents.append(Clover(new_x, new_y, terrain))
            return

    def act(self, terrain, spatial_grid, new_agents, max_food_capacity):
        if not self.alive:
            return

        neighbor_count = self._count_neighbors(spatial_grid)

        fertility_modifier = 80.0 / max(1.0, float(max_food_capacity))
        crowding_penalty = (neighbor_count * 0.15) * fertility_modifier

        self._update_plant_needs(1.0 + crowding_penalty)

        if not self.alive:
            return

        if self.reproductive_urge < 100:
            return

        if self.thirst < 5.0 and neighbor_count < 8:
            self.reproductive_urge = 0
            self.thirst += 40
            self._attempt_spawn(terrain, new_agents)
            return

        self.reproductive_urge = 100


# ─────────────────────────────────────────────────────────────────────────────
# 3.  SIMULATION ENGINE
# ─────────────────────────────────────────────────────────────────────────────

class SimThread(threading.Thread):
    def __init__(self, data_queue: queue.Queue, n_prey: int, n_pred: int, n_food: int, init_params: dict,
                 simulation_delay: float, terrain_file: str = None):
        super().__init__(daemon=True)
        self.q = data_queue
        self.n_prey = n_prey
        self.n_pred = n_pred
        self.n_food = n_food
        self.init_params = init_params
        self.simulation_delay = simulation_delay

        self._running = True
        self._paused = threading.Event()
        self._paused.set()

        self.terrain = Terrain(SIM_WIDTH, SIM_HEIGHT, CELL_SIZE, terrain_file)
        self.spatial_grid = SpatialGrid(100)
        self.agents: list[Agent] = []
        self.ticks = 0
        self.dropped_frames = 0

    def stop(self):
        self._running = False
        self._paused.set()

    def pause(self):
        self._paused.clear()

    def resume(self):
        self._paused.set()

    @property
    def is_paused(self) -> bool:
        return not self._paused.is_set()

    def run(self):
        self._spawn()
        while self._running:
            self._paused.wait()
            if not self._running: break
            self._step()
            self._send_payload()
            time.sleep(self._get_speed())

    def _get_speed(self) -> float:
        if self.simulation_delay > 0:
            return self.simulation_delay
        return float(DEFAULT_SIMULATION_DELAY_SECONDS)

    def _spawn_agent_safe(self, AgentClass, *args, **kwargs):
        """Varno spawna agenta na lokaciji, ki je WALKABLE (omejeno število poizkusov)"""
        for _ in range(20):
            x = random.uniform(20, SIM_WIDTH - 20)
            y = random.uniform(20, SIM_HEIGHT - 20)
            if self.terrain.get_terrain_props_at(x, y)["walkable"]:
                return AgentClass(x, y, *args, **kwargs)
        # Fallback (zelo redko bi odpovedalo celih 20 seedov v Perlinu)
        return AgentClass(SIM_WIDTH / 2, SIM_HEIGHT / 2, *args, **kwargs)

    def _spawn_clover(self):
        """Spawna deteljo na naključni sprejemljivi podlagi."""
        return self._spawn_agent_safe(Clover, self.terrain)

    def _spawn(self):
        self.agents = []
        for _ in range(self.n_food):
            self.agents.append(self._spawn_clover())

        for _ in range(self.n_prey):
            s_speed = self.init_params['speed'] * random.uniform(0.9, 1.1)
            s_size = self.init_params['size'] * random.uniform(0.9, 1.1)
            s_sense = self.init_params['sense'] * random.uniform(0.9, 1.1)
            self.agents.append(self._spawn_agent_safe(Prey, s_speed, s_size, s_sense))

        for _ in range(self.n_pred):
            s_speed = (self.init_params['speed'] * 1.5) * random.uniform(0.9, 1.1)
            s_size = (self.init_params['size'] * 1.2) * random.uniform(0.9, 1.1)
            s_sense = (self.init_params['sense'] * 1.7) * random.uniform(0.9, 1.1)
            self.agents.append(self._spawn_agent_safe(Predator, s_speed, s_size, s_sense))

    def _step(self):
        self.ticks += 1

        self._rebuild_spatial_grid()
        new_agents = self._process_agents_for_tick()

        self.agents.extend(new_agents)
        self.agents = [a for a in self.agents if a.alive]

        if random.random() < 0.005:
            self.agents.append(self._spawn_clover())

    def _rebuild_spatial_grid(self):
        self.spatial_grid.clear()
        for ag in self.agents:
            self.spatial_grid.insert(ag)

    def _process_agents_for_tick(self):
        new_agents = []
        for ag in self.agents:
            self._process_single_agent(ag, new_agents)
        return new_agents

    def _process_single_agent(self, ag, new_agents):
        if not ag.alive:
            return

        if isinstance(ag, Clover):
            ag.act(self.terrain, self.spatial_grid, new_agents, self.n_food)
            return

        ag.update_needs(self.terrain)
        ag.act(
            self.terrain,
            self.spatial_grid,
            new_agents,
            self.init_params.get('mutation_probability', 0.1),
            self.init_params.get('mutation_strength', 0.2),
        )

    def _send_payload(self):
        payload = {
            'ticks': self.ticks,
            'dropped_frames': self.dropped_frames,
            'agents': [(
                ag.id, ag.x, ag.y, ag.radius, ag.color, ag.alive, ag.sense, ag.current_action.value,
                ag.hunger, ag.thirst, ag.entity_type.value
            ) for ag in self.agents],
            'active_cnt': len(self.agents),
            'prey_cnt': sum(1 for a in self.agents if a.entity_type is EntityType.PREY),
            'pred_cnt': sum(1 for a in self.agents if a.entity_type is EntityType.PREDATOR),
            'clover_cnt': sum(1 for a in self.agents if a.is_plant)
        }

        try:
            self.q.put_nowait(payload)
        except queue.Full:
            self.dropped_frames += 1


# ─────────────────────────────────────────────────────────────────────────────
# 4.  UI COMPONENTS
# ─────────────────────────────────────────────────────────────────────────────

class ParameterEntry(tk.Frame):
    def __init__(self, parent, label, default, width=6):
        super().__init__(parent)
        self.pack(side=tk.LEFT, padx=5)
        tk.Label(self, text=label, font=("Arial", 7)).pack(anchor="w")
        self.ent = tk.Entry(self, width=width, font=("Arial", 9))
        self.ent.insert(0, str(default))
        self.ent.pack()

    def get(self):
        return self.ent.get()

    def set_state(self, state):
        self.ent.config(state=state)


class App(tk.Tk):

    def __init__(self):
        super().__init__()
        self.title("EcoSim MVP")

        self.sim = None
        self.data_queue = queue.Queue(maxsize=2)
        self._restarted = False
        self._last_payload = None

        self.pan_x = 0
        self.pan_y = 0
        self._drag_start_x = 0
        self._drag_start_y = 0

        self._agent_canvas_items = {}
        self._is_terrain_drawn = False

        self._build_ui()

    def _build_ui(self):
        root = tk.Frame(self, padx=10, pady=10)
        root.pack(fill=tk.BOTH, expand=True)

        self._create_canvas_area(root)
        self._create_control_panel(root)
        self._create_info_label(root)

    def _create_canvas_area(self, parent):
        top = tk.Frame(parent)
        top.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.sim_canvas = tk.Canvas(top, width=SIM_WIDTH, height=SIM_HEIGHT,
                                    bg="#1a1a2e", relief=tk.SUNKEN, bd=1)
        self.sim_canvas.pack(expand=True)

        self.sim_canvas.bind("<ButtonPress-1>", self._on_drag_start)
        self.sim_canvas.bind("<B1-Motion>", self._on_drag_motion)

    def _create_control_panel(self, parent):
        self.ctrl = tk.LabelFrame(parent, text=" Simulation Controls ", padx=10, pady=8)
        self.ctrl.pack(side=tk.BOTTOM, fill=tk.X, pady=8)

        self._build_buttons()
        self._build_settings()

    def _create_info_label(self, parent):
        self.lbl_info = tk.Label(
            parent,
            text="Ticks: 0 | Total: 0 | Prey: 0 | Predators: 0 | Clover: 0 | Dropped: 0",
            font=("Arial", 9, "bold"),
        )
        self.lbl_info.pack(side=tk.BOTTOM, anchor="e")

    def _build_buttons(self):
        bar = tk.Frame(self.ctrl)
        bar.pack(fill=tk.X)

        self._add_simulation_action_buttons(bar)
        self._add_speed_control_inputs(bar)
        self._add_debug_toggle(bar)

    def _add_simulation_action_buttons(self, parent):
        self.btn_start = tk.Button(parent, text="START", bg="#ccffcc", width=12, command=self.start)
        self.btn_start.pack(side=tk.LEFT, padx=2)

        self.btn_pause = tk.Button(parent, text="PAUSE", state=tk.DISABLED, width=12, command=self.toggle_pause)
        self.btn_pause.pack(side=tk.LEFT, padx=2)

        self.btn_restart = tk.Button(parent, text="RESTART", bg="#ffcccc", state=tk.DISABLED, width=12,
                                     command=self.restart)
        self.btn_restart.pack(side=tk.LEFT, padx=2)

    def _add_speed_control_inputs(self, parent):
        tk.Label(parent, text="Speed (s):").pack(side=tk.LEFT, padx=(20, 2))
        self.entry_simulation_delay = tk.Entry(parent, width=6)
        self.entry_simulation_delay.insert(0, DEFAULT_SIMULATION_DELAY_SECONDS)
        self.entry_simulation_delay.pack(side=tk.LEFT)

        tk.Label(parent, text="UI Refresh (ms):").pack(side=tk.LEFT, padx=(20, 2))
        self.entry_ui_refresh_ms = tk.Entry(parent, width=6)
        self.entry_ui_refresh_ms.insert(0, DEFAULT_UI_REFRESH_INTERVAL_MS)
        self.entry_ui_refresh_ms.pack(side=tk.LEFT)

    def _add_debug_toggle(self, parent):
        self.show_debug_overlay = tk.BooleanVar(value=True)
        tk.Checkbutton(
            parent,
            text="Show Debug (Sight, Hunger, Thirst)",
            variable=self.show_debug_overlay
        ).pack(side=tk.RIGHT, padx=5)

    def _build_settings(self):
        outer = tk.Frame(self.ctrl, bd=1, relief=tk.SUNKEN, pady=5)
        outer.pack(fill=tk.X, pady=6)

        self._add_agent_settings_row(outer)
        self._add_terrain_settings_row(outer)

    def _add_agent_settings_row(self, parent):
        row = tk.Frame(parent)
        row.pack(fill=tk.X, pady=2)

        self.input_prey_count = ParameterEntry(row, "Prey Count", DEFAULT_PREY_COUNT)
        self.input_predator_count = ParameterEntry(row, "Predator Count", DEFAULT_PREDATOR_COUNT)
        self.input_clover_capacity = ParameterEntry(row, "Food Capacity", DEFAULT_CLOVER_CAPACITY)

        self.input_initial_speed = ParameterEntry(row, "Initial Speed", DEFAULT_INITIAL_SPEED)
        self.input_initial_size = ParameterEntry(row, "Initial Size", DEFAULT_INITIAL_SIZE)
        self.input_initial_sense = ParameterEntry(row, "Initial Sight", DEFAULT_INITIAL_SENSE)

        self.input_mutation_probability = ParameterEntry(row, "Mutation Prob.\n(e.g. 0.1)",
                                                         DEFAULT_MUTATION_PROBABILITY, width=6)
        self.input_mutation_strength = ParameterEntry(row, "Mutation Strength\n(e.g. 0.2)", DEFAULT_MUTATION_STRENGTH,
                                                      width=6)

    def _add_terrain_settings_row(self, parent):
        row = tk.Frame(parent)
        row.pack(fill=tk.X, pady=5)

        tk.Label(row, text="Terrain Selection:").pack(side=tk.LEFT, padx=(5, 10))

        terrain_files = glob.glob(os.path.join("terrains", "*.json"))
        terrain_opts = ["Random Generate"] + terrain_files

        self.selected_terrain_name = tk.StringVar(value="Random Generate")
        self.terrain_option_menu = tk.OptionMenu(row, self.selected_terrain_name, *terrain_opts)
        self.terrain_option_menu.pack(side=tk.LEFT)

    def _on_drag_start(self, event):
        self._drag_start_x = event.x
        self._drag_start_y = event.y

    def _on_drag_motion(self, event):
        dx = event.x - self._drag_start_x
        dy = event.y - self._drag_start_y
        self.pan_x += dx
        self.pan_y += dy
        self._drag_start_x = event.x
        self._drag_start_y = event.y

    def _set_ui_state(self, is_running):
        self._update_button_states(is_running)
        self._update_parameter_entry_states(is_running)

    def _update_button_states(self, is_running):
        if is_running:
            self.btn_start.config(state=tk.DISABLED)
            self.btn_pause.config(state=tk.NORMAL, text="PAUSE")
            self.btn_restart.config(state=tk.NORMAL)
            return

        self.btn_start.config(state=tk.NORMAL)
        self.btn_pause.config(state=tk.DISABLED, text="PAUSE")
        self.btn_restart.config(state=tk.DISABLED)

    def _update_parameter_entry_states(self, is_running):
        state = tk.DISABLED if is_running else tk.NORMAL
        entries = [
            self.input_prey_count, self.input_predator_count, self.input_clover_capacity,
            self.input_initial_speed, self.input_initial_size, self.input_initial_sense,
            self.input_mutation_probability, self.input_mutation_strength
        ]
        for p in entries:
            p.set_state(state)

    def _set_ui_running(self, running: bool):
        self._set_ui_state(running)

    def start(self):
        self._restarted = False
        parsed = self._parse_start_inputs()
        if parsed is None:
            print("Invalid input values!")
            return

        n_prey, n_pred, n_food, init_params = parsed
        selected_terrain = self._get_selected_terrain()
        sim_delay = self._read_simulation_delay()

        self.sim = SimThread(
            data_queue=self.data_queue,
            n_prey=n_prey,
            n_pred=n_pred,
            n_food=n_food,
            init_params=init_params,
            simulation_delay=sim_delay,
            terrain_file=selected_terrain
        )
        self.sim.start()
        self._set_ui_running(True)
        self._poll_queue()

    def _parse_start_inputs(self):
        try:
            n_prey = int(self.input_prey_count.get())
            n_pred = int(self.input_predator_count.get())
            n_food = int(self.input_clover_capacity.get())

            init_params = {
                'speed': float(self.input_initial_speed.get()),
                'size': float(self.input_initial_size.get()),
                'sense': float(self.input_initial_sense.get()),
                'mutation_probability': float(self.input_mutation_probability.get()),
                'mutation_strength': float(self.input_mutation_strength.get()),
            }
        except ValueError:
            return None
        return n_prey, n_pred, n_food, init_params

    def _get_selected_terrain(self):
        terrain_file = getattr(self, 'selected_terrain_name', None)
        return terrain_file.get() if terrain_file else "Random Generate"

    def _read_simulation_delay(self):
        try:
            return float(self.entry_simulation_delay.get())
        except ValueError:
            return float(DEFAULT_SIMULATION_DELAY_SECONDS)

    def toggle_pause(self):
        if self.sim is None: return
        if self.sim.is_paused:
            self.sim.resume()
            self.btn_pause.config(text="PAUSE")
            return

        self.sim.pause()
        self.btn_pause.config(text="RESUME")

    def restart(self):
        self._restarted = True
        self._stop_simulation()
        self._clear_queue()
        self._reset_ui_simulation_view()
        self._set_ui_running(False)

    def _stop_simulation(self):
        if not self.sim:
            return
        self.sim.stop()
        self.sim = None

    def _clear_queue(self):
        while not self.data_queue.empty():
            try:
                self.data_queue.get_nowait()
            except queue.Empty:
                break

    def _reset_ui_simulation_view(self):
        self._last_payload = None
        self.sim_canvas.delete("all")
        self._agent_canvas_items.clear()
        self._is_terrain_drawn = False
        self.lbl_info.config(text="Ticks: 0 | Total: 0 | Prey: 0 | Predators: 0 | Clover: 0 | Dropped: 0")

    def _poll_queue(self):
        if self._restarted:
            return

        latest = self._drain_queue_latest()
        if latest is not None:
            self._process_payload(latest)

        refresh_ms = self._read_refresh_interval_ms()
        self._update_sim_runtime_speed()
        self.after(refresh_ms, self._poll_queue)

    def _drain_queue_latest(self):
        latest = None
        while not self.data_queue.empty():
            latest = self._try_get_queue_item(latest)
        return latest

    def _try_get_queue_item(self, fallback):
        try:
            return self.data_queue.get_nowait()
        except queue.Empty:
            return fallback

    def _read_refresh_interval_ms(self):
        try:
            return int(self.entry_ui_refresh_ms.get())
        except ValueError:
            return int(DEFAULT_UI_REFRESH_INTERVAL_MS)

    def _read_runtime_simulation_delay(self):
        try:
            return float(self.entry_simulation_delay.get())
        except ValueError:
            return float(DEFAULT_SIMULATION_DELAY_SECONDS)

    def _process_payload(self, payload):
        self._last_payload = payload
        self._draw_sim(payload)
        self._update_info(payload)

    def _update_sim_runtime_speed(self):
        if self.sim is None:
            return
        self.sim.simulation_delay = self._read_runtime_simulation_delay()

    def _draw_sim(self, payload: dict):
        self._draw_terrain_if_needed()
        self._update_canvas_panning()

        current_ids = self._draw_agents(payload['agents'])
        self._cleanup_dead_agents(current_ids)

    def _draw_terrain_if_needed(self):
        if self._is_terrain_drawn:
            return

        terrain = self.sim.terrain if self.sim else None
        if not terrain:
            return

        self.sim_canvas.delete("terrain")
        for y in range(terrain.rows):
            self._draw_terrain_row(terrain, y)

        self._is_terrain_drawn = True

    def _draw_terrain_row(self, terrain, y):
        start_x = 0
        current_ctype = terrain.grid[y][0]

        for x in range(1, terrain.cols):
            if terrain.grid[y][x] == current_ctype:
                continue

            self._create_terrain_rect(terrain, y, start_x, x, current_ctype)
            start_x = x
            current_ctype = terrain.grid[y][x]

        self._create_terrain_rect(terrain, y, start_x, terrain.cols, current_ctype)

    def _create_terrain_rect(self, terrain, y, x1, x2, ctype):
        col = terrain.TERRAIN_PROPS[ctype]["color"]
        wx1 = x1 * terrain.cell_size
        wy1 = y * terrain.cell_size
        wx2 = x2 * terrain.cell_size
        wy2 = (y + 1) * terrain.cell_size
        self.sim_canvas.create_rectangle(wx1, wy1, wx2, wy2, fill=col, outline="", tags="terrain")

    def _update_canvas_panning(self):
        self.sim_canvas.scan_mark(0, 0)
        self.sim_canvas.scan_dragto(self.pan_x, self.pan_y, gain=1)

    def _draw_agents(self, agents_data):
        debug = self.show_debug_overlay.get()
        current_ids = set()

        for ag_data in agents_data:
            ag_id = ag_data[0]
            if not ag_data[5]:  # not alive
                continue

            current_ids.add(ag_id)
            self._update_agent_graphic(ag_data, debug)

        return current_ids

    def _update_agent_graphic(self, ag_data, debug):
        (ag_id, ax, ay, ar, col, _, sense, action_val, hunger, thirst, type_name) = ag_data

        if ag_id not in self._agent_canvas_items:
            self._agent_canvas_items[ag_id] = self._create_agent_graphics_item(col)

        g = self._agent_canvas_items[ag_id]
        self.sim_canvas.coords(g['body'], ax - ar, ay - ar, ax + ar, ay + ar)

        is_plant = (type_name == EntityType.CLOVER.value)
        if debug and not is_plant:
            self._show_agent_debug(g, ax, ay, ar, sense, action_val, hunger, thirst)
            return

        self._hide_agent_debug(g)

    def _create_agent_graphics_item(self, col):
        g = {}
        g['sight'] = self.sim_canvas.create_oval(0, 0, 0, 0, outline="#444444", width=1, dash=(2, 4), state=tk.HIDDEN)
        g['hp_bg'] = self.sim_canvas.create_rectangle(0, 0, 0, 0, fill="#333", outline="", state=tk.HIDDEN)
        g['hp_fg'] = self.sim_canvas.create_rectangle(0, 0, 0, 0, fill="#e74c3c", outline="", state=tk.HIDDEN)
        g['tp_bg'] = self.sim_canvas.create_rectangle(0, 0, 0, 0, fill="#333", outline="", state=tk.HIDDEN)
        g['tp_fg'] = self.sim_canvas.create_rectangle(0, 0, 0, 0, fill="#3498db", outline="", state=tk.HIDDEN)
        g['text'] = self.sim_canvas.create_text(0, 0, text="", fill="#f1c40f", font=("Arial", 8, "bold"),
                                                state=tk.HIDDEN)
        g['body'] = self.sim_canvas.create_oval(0, 0, 0, 0, fill=col, outline="black", width=1)
        g['debug_visible'] = False
        return g

    def _show_agent_debug(self, g, cx, cy, ar, sense, action, hunger, thirst):
        if not g['debug_visible']:
            self._set_debug_visibility(g, tk.NORMAL)
            g['debug_visible'] = True

        self.sim_canvas.coords(g['sight'], cx - sense, cy - sense, cx + sense, cy + sense)

        bar_w = 16
        self._update_status_bar(g['hp_bg'], g['hp_fg'], cx, cy, ar, bar_w, hunger, -14, -11)
        self._update_status_bar(g['tp_bg'], g['tp_fg'], cx, cy, ar, bar_w, thirst, -10, -7)

        self.sim_canvas.itemconfig(g['text'], text=action)
        self.sim_canvas.coords(g['text'], cx, cy - ar - 22)

    def _hide_agent_debug(self, g):
        if not g['debug_visible']:
            return
        self._set_debug_visibility(g, tk.HIDDEN)
        g['debug_visible'] = False

    def _set_debug_visibility(self, g, state):
        for key in ['sight', 'hp_bg', 'hp_fg', 'tp_bg', 'tp_fg', 'text']:
            self.sim_canvas.itemconfig(g[key], state=state)

    def _update_status_bar(self, bg_item, fg_item, cx, cy, ar, width, value, offset_y1, offset_y2):
        level = min(1.0, value / 100.0)
        x1 = cx - width / 2
        x2 = cx + width / 2
        y1 = cy - ar + offset_y1
        y2 = cy - ar + offset_y2

        self.sim_canvas.coords(bg_item, x1, y1, x2, y2)
        self.sim_canvas.coords(fg_item, x1, y1, x1 + width * level, y2)

    def _cleanup_dead_agents(self, current_ids):
        dead_ids = [ag_id for ag_id in self._agent_canvas_items if ag_id not in current_ids]
        for dead_id in dead_ids:
            self._remove_agent_graphics(dead_id)

    def _remove_agent_graphics(self, ag_id):
        g = self._agent_canvas_items.pop(ag_id)
        for key, item in g.items():
            if key != 'debug_visible':
                self.sim_canvas.delete(item)

    def _update_info(self, payload: dict):
        active_cnt = payload.get('active_cnt', 0)
        prey_cnt = payload.get('prey_cnt', 0)
        pred_cnt = payload.get('pred_cnt', 0)
        clover_cnt = payload.get('clover_cnt', 0)
        ticks = payload.get('ticks', 0)
        dropped = payload.get('dropped_frames', 0)
        self.lbl_info.config(
            text=f"Ticks: {ticks} | Total: {active_cnt} | Prey: {prey_cnt} | Predators: {pred_cnt} | Clover: {clover_cnt} | Dropped: {dropped}")


if __name__ == "__main__":
    app = App()
    app.mainloop()
