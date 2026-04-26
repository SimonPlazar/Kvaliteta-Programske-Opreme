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
    # Per-terrain modifiers used by movement and survival systems.
    TERRAIN_PROPS = {
        0: {"walkable": False, "speed_mod": 0.0, "thirst_mod": 1.0, "hunger_mod": 1.0, "color": "#2196f3", "name": "Water"},
        1: {"walkable": True,  "speed_mod": 0.8, "thirst_mod": 1.5, "hunger_mod": 1.0, "color": "#f4d03f", "name": "Sand"},
        2: {"walkable": True,  "speed_mod": 1.0, "thirst_mod": 1.0, "hunger_mod": 1.0, "color": "#2ecc71", "name": "Grass"},
        3: {"walkable": True,  "speed_mod": 0.7, "thirst_mod": 0.8, "hunger_mod": 0.8, "color": "#1b5e20", "name": "Forest"},
        4: {"walkable": True,  "speed_mod": 0.5, "thirst_mod": 1.2, "hunger_mod": 1.2, "color": "#795548", "name": "Mountain"},
        5: {"walkable": False, "speed_mod": 0.0, "thirst_mod": 1.0, "hunger_mod": 1.0, "color": "#fdfefe", "name": "Peak"}
    }

    def __init__(self, width, height, cell_size=CELL_SIZE, terrain_file=None):
        self.width = width
        self.height = height
        self.cell_size = cell_size
        self.cols = width // cell_size
        self.rows = height // cell_size
        
        if terrain_file and terrain_file != "Random Generate":
            with open(terrain_file, "r") as f:
                data = json.load(f)
                grid_data = data["grid"]
                self.grid = [[cell["t"] for cell in row] for row in grid_data]

        elif not terrain_file or terrain_file == "Random Generate":
            seed = random.randint(0, 999999)
            raw_grid = generate_terrain_grid(
                width, height, cell_size, seed, scale=50, octaves=4,
                t_water=0.40, t_sand=0.425, t_grass=0.775, t_forest=0.925, t_mount=0.975
            )
            self.grid = [[cell["t"] for cell in row] for row in raw_grid]
        
        self._compute_water_distance()

    def _compute_water_distance(self):
        """Precompute nearest water location for each cell with BFS."""
        self.water_dist = [[float('inf') for _ in range(self.cols)] for _ in range(self.rows)]
        self.nearest_water = [[None for _ in range(self.cols)] for _ in range(self.rows)]
        q = deque()

        for y in range(self.rows):
            for x in range(self.cols):
                if self.grid[y][x] == 0:
                    self.water_dist[y][x] = 0
                    self.nearest_water[y][x] = (x * self.cell_size + self.cell_size / 2, y * self.cell_size + self.cell_size / 2)
                    q.append((x, y))
                    
        dirs = [ (1,0), (-1,0), (0,1), (0,-1) ]
        while q:
            x, y = q.popleft()
            d = self.water_dist[y][x]
            n_water = self.nearest_water[y][x]
            
            for dx, dy in dirs:
                nx, ny = x + dx, y + dy
                if 0 <= nx < self.cols and 0 <= ny < self.rows:
                    if self.water_dist[ny][nx] > d + 1:
                        self.water_dist[ny][nx] = d + 1
                        self.nearest_water[ny][nx] = n_water
                        q.append((nx, ny))

    def get_cell_coords(self, x, y):
        cx = int(x / self.cell_size)
        cy = int(y / self.cell_size)
        return max(0, min(self.cols - 1, cx)), max(0, min(self.rows - 1, cy))

    def get_type_at(self, x, y):
        cx, cy = self.get_cell_coords(x, y)
        return self.grid[cy][cx]

    def get_terrain_props_at(self, x, y):
        return self.TERRAIN_PROPS[self.get_type_at(x, y)]

    def get_water_distance_at(self, x, y):
        cx, cy = self.get_cell_coords(x, y)
        return self.water_dist[cy][cx] * self.cell_size


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

    # ──────────────────────────────────────────────────────────

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
        self.sex = random.choice(['M', 'F'])

        self.wander_angle = random.uniform(0, 2 * math.pi)
        self.current_action = Action.WANDER

    @property
    def radius(self):
        return AGENT_R_BASE + int(self.size - 1.0)

    def update_needs(self, terrain):
        if not self.alive: return
        self.age += 1

        props = terrain.get_terrain_props_at(self.x, self.y)

        self.thirst += (self.BASE_THIRST_RATE + (self.speed * self.SPEED_THIRST_FACTOR)) * props["thirst_mod"]
        self.hunger += (self.BASE_HUNGER_RATE * (self.size * self.SIZE_HUNGER_FACTOR)) * props["hunger_mod"]

        if self.hunger >= 100:
            self.hunger = 100
            self.thirst += self.BASE_THIRST_RATE * 2

        # Better health increases reproductive growth speed.
        health_factor = max(0, 1.0 - (self.hunger + self.thirst) / 200.0)
        self.reproductive_urge += self.BASE_REPRO_RATE * (0.5 + health_factor)

        if self.thirst >= 100 or self.age > self.max_age:
            self.alive = False

    def mix_genes(self, partner, mutation_probability, mutation_strength):
        speed = (self.speed + partner.speed) / 2.0
        size = (self.size + partner.size) / 2.0
        sense = (self.sense + partner.sense) / 2.0

        speed *= random.uniform(0.9, 1.1)
        size *= random.uniform(0.9, 1.1)
        sense *= random.uniform(0.9, 1.1)

        if random.random() < mutation_probability: speed *= random.choice([1.0 - mutation_strength, 1.0 + mutation_strength])
        if random.random() < mutation_probability: size *= random.choice([1.0 - mutation_strength, 1.0 + mutation_strength])
        if random.random() < mutation_probability: sense *= random.choice([1.0 - mutation_strength, 1.0 + mutation_strength])

        return type(self)(self.x, self.y, max(0.5, speed), max(0.2, size), max(20.0, sense))

    def get_priority(self):
        if self.thirst > 75:
            return Priority.THIRST
        elif self.hunger > 75:
            return Priority.HUNGER

        if self.reproductive_urge >= 100 and self.hunger < 40 and self.thirst < 40:
            return Priority.REPRODUCTION

        if self.thirst > 40:
            return Priority.THIRST
        elif self.hunger > 40:
            return Priority.HUNGER
        return Priority.WANDER

    def _clamp_bounds(self):
        """Keep the agent inside simulation bounds."""
        hit_wall = False
        if self.x < self.radius:
            self.x = self.radius
            hit_wall = True
        elif self.x > SIM_WIDTH - self.radius:
            self.x = SIM_WIDTH - self.radius
            hit_wall = True

        if self.y < self.radius:
            self.y = self.radius
            hit_wall = True
        elif self.y > SIM_HEIGHT - self.radius:
            self.y = SIM_HEIGHT - self.radius
            hit_wall = True

        return hit_wall

    def move_step(self, dx, dy, terrain):
        """Safe movement that stops before unwalkable terrain."""
        props = terrain.get_terrain_props_at(self.x, self.y)
        speed_modifier = props["speed_mod"]

        new_x = self.x + dx * speed_modifier
        new_y = self.y + dy * speed_modifier

        new_props = terrain.get_terrain_props_at(new_x, new_y)
        if not new_props["walkable"]:
            if not self.is_plant:
                self.wander_angle += math.pi
            return False

        self.x = new_x
        self.y = new_y
        if self._clamp_bounds():
            if not self.is_plant:
                self.wander_angle += math.pi
        return True

    def move_towards(self, tx, ty, speed_limit, terrain):
        dist_sq = (tx - self.x) ** 2 + (ty - self.y) ** 2
        if dist_sq > 0:
            dist = math.sqrt(dist_sq)
            step = min(dist, speed_limit)
            dx = ((tx - self.x) / dist) * step
            dy = ((ty - self.y) / dist) * step
            self.move_step(dx, dy, terrain)
            self.wander_angle = math.atan2(ty - self.y, tx - self.x)

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

        if not water_target or distance_to_water > sense_range:
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
        min_distance_sq = float('inf')
        best_score = -float('inf')

        for entity in entities:
            if not filter_func(entity):
                continue
            distance_sq = (entity.x - self.x) ** 2 + (entity.y - self.y) ** 2
            if distance_sq >= sense_sq:
                continue

            if score_func:
                score = score_func(entity, distance_sq)
                if score > best_score:
                    best_score = score
                    best_target = entity
                    min_distance_sq = distance_sq
            else:
                if distance_sq < min_distance_sq:
                    min_distance_sq = distance_sq
                    best_target = entity

        return best_target, min_distance_sq

    def _handle_thirst(self, terrain):
        self.current_action = Action.THIRST
        water_handled, did_drink = self.try_drink_from_nearest_water(terrain, self.sense)
        if did_drink:
            self.current_action = Action.DRINK
            return
        if not water_handled:
            self.wander(terrain)

    def _handle_reproduction(self, entities, sense_sq, new_agents, terrain, mutation_probability, mutation_strength):
        self.current_action = Action.MATE
        best_partner, min_dist_sq = self.get_closest_target(
            entities, sense_sq,
            lambda e: e.entity_type == self.entity_type and e.alive and e != self and getattr(e, 'sex', None) != self.sex and e.get_priority() is Priority.REPRODUCTION
        )

        if not best_partner:
            self.wander(terrain)
            return

        can_reproduce_now = self.is_in_interaction_range(best_partner, min_dist_sq, REPRODUCTION_DISTANCE_PADDING)
        if can_reproduce_now:
            self.hunger += self.REPRO_COST_HUNGER
            self.thirst += self.REPRO_COST_THIRST
            self.reproductive_urge = self.REPRO_COOLDOWN

            best_partner.hunger += best_partner.REPRO_COST_HUNGER
            best_partner.thirst += best_partner.REPRO_COST_THIRST
            best_partner.reproductive_urge = best_partner.REPRO_COOLDOWN

            self._spawn_offspring(best_partner, new_agents, mutation_probability, mutation_strength)
            return

        self.move_towards(best_partner.x, best_partner.y, self.speed, terrain)

    def _spawn_offspring(self, partner, new_agents, mutation_probability, mutation_strength):
        new_agents.append(self.mix_genes(partner, mutation_probability, mutation_strength))

    def act(self, terrain, spatial_grid, new_agents, mutation_probability, mutation_strength):
        if not self.alive: return

        entities = spatial_grid.get_nearby(self.x, self.y, self.sense)
        sense_sq = self.sense * self.sense

        if self._special_interrupt(entities, sense_sq, terrain):
            return

        priority = self.get_priority()
        if priority is Priority.REPRODUCTION:
            self._handle_reproduction(entities, sense_sq, new_agents, terrain, mutation_probability, mutation_strength)
            return

        if priority is Priority.THIRST:
            self._handle_thirst(terrain)
            return

        if priority is Priority.HUNGER:
            self._handle_hunger(entities, sense_sq, terrain)
            return

        self.current_action = Action.WANDER
        self.wander(terrain)

    def _special_interrupt(self, entities, sense_sq, terrain):
        return False

    def _handle_hunger(self, entities, sense_sq, terrain):
        pass

class Prey(Agent):
    # Prey tuning constants.
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
        flee_dx, flee_dy = 0.0, 0.0
        fleeing = False

        for entity in entities:
            if entity.entity_type is EntityType.PREDATOR and entity.alive:
                distance_sq = (entity.x - self.x) ** 2 + (entity.y - self.y) ** 2
                if distance_sq < sense_sq:
                    fleeing = True
                    escape_weight = 1.0 / (distance_sq + 0.1)
                    flee_dx += (self.x - entity.x) * escape_weight
                    flee_dy += (self.y - entity.y) * escape_weight

        if not fleeing:
            return False

        self.current_action = Action.FLEE
        flee_magnitude = math.hypot(flee_dx, flee_dy)
        if flee_magnitude > 0:
            dx = (flee_dx / flee_magnitude) * (self.speed * PREY_FLEE_SPEED_MULTIPLIER)
            dy = (flee_dy / flee_magnitude) * (self.speed * PREY_FLEE_SPEED_MULTIPLIER)
            self.move_step(dx, dy, terrain)
            self.wander_angle = math.atan2(flee_dy, flee_dx)
        return True

    def _handle_hunger(self, entities, sense_sq, terrain):
        self.current_action = Action.HUNGER
        best_food, min_distance_sq = self.get_closest_target(
            entities, sense_sq,
            lambda e: e.is_plant and e.alive
        )

        if not best_food:
            self.wander(terrain)
            return

        can_eat_now = self.is_in_interaction_range(best_food, min_distance_sq, INTERACTION_DISTANCE_PADDING)
        if can_eat_now:
            best_food.alive = False
            self.hunger = 0
            self.current_action = Action.EAT
            return

        self.move_towards(best_food.x, best_food.y, self.speed, terrain)

class Predator(Agent):
    # Predator tuning constants.
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
        elif self.hunger > 85:
            return Priority.HUNGER

        if self.reproductive_urge >= 100 and self.hunger < 50 and self.thirst < 50:
            return Priority.REPRODUCTION

        if self.hunger > 30:
            return Priority.HUNGER
        elif self.thirst > 50:
            return Priority.THIRST
        return Priority.WANDER

    def _handle_hunger(self, entities, sense_sq, terrain):
        self.current_action = Action.HUNT

        def score_func(entity, distance_sq):
            distance = math.sqrt(distance_sq)
            return (entity.size * 10) - distance

        best_prey, min_distance_sq = self.get_closest_target(
            entities, sense_sq,
            lambda e: e.entity_type is EntityType.PREY and e.alive,
            score_func
        )

        if not best_prey:
            self.current_action = Action.HUNGER
            self.wander(terrain)
            return

        can_consume_now = self.is_in_interaction_range(best_prey, min_distance_sq, INTERACTION_DISTANCE_PADDING)
        if can_consume_now:
            best_prey.alive = False
            self.hunger = 0
            self.current_action = Action.CONSUME
            return

        self.move_towards(best_prey.x, best_prey.y, self.speed * PREDATOR_CHASE_SPEED_MULTIPLIER, terrain)


class Clover(Agent):
    # Plant tuning constants.
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

        dist_to_water = terrain.get_water_distance_at(self.x, self.y)
        self.base_water_potential = 0.0
        if dist_to_water < self.sense:
            self.base_water_potential = (self.sense - max(0, dist_to_water)) / self.sense * 1.5

        self.moisture_supply = self.base_water_potential

    @property
    def radius(self):
        return FOOD_R

    def update_needs(self):
        pass

    def _update_plant_needs(self, local_crowding_factor):
        if not self.alive: return
        self.age += 1

        self.moisture_supply = self.base_water_potential / max(1.0, local_crowding_factor)

        net_thirst = self.BASE_THIRST_RATE - self.moisture_supply
        self.thirst = max(0.0, min(150.0, self.thirst + net_thirst))

        if self.thirst >= 100 or self.age > self.max_age:
            self.alive = False
            return

        if self.thirst < 5.0 and self.moisture_supply > self.BASE_THIRST_RATE:
            health_factor = max(0.0, 1.0 - (self.thirst / 100.0))
            surplus = self.moisture_supply - self.BASE_THIRST_RATE
            self.reproductive_urge += self.BASE_REPRO_RATE * (0.5 + 2.0 * health_factor + surplus)

    def _count_neighbors(self, spatial_grid):
        nearby_entities = spatial_grid.get_nearby(self.x, self.y, 30)
        sosedi_count = 0
        for e in nearby_entities:
            if e.is_plant and e.alive and e != self:
                if (e.x - self.x) ** 2 + (e.y - self.y) ** 2 < 900:
                    sosedi_count += 1
        return sosedi_count

    def _attempt_spawn(self, terrain, new_agents):
        for _ in range(5):
            angle = random.uniform(0, 2 * math.pi)
            dist = random.uniform(20, 50)
            nx = self.x + math.cos(angle) * dist
            ny = self.y + math.sin(angle) * dist

            if 0 < nx < SIM_WIDTH and 0 < ny < SIM_HEIGHT:
                if terrain.get_terrain_props_at(nx, ny)["walkable"]:
                    new_clover = Clover(nx, ny, terrain)
                    new_agents.append(new_clover)
                    break

    def act(self, terrain, spatial_grid, new_agents, max_food_capacity):
        if not self.alive: return

        sosedi_count = self._count_neighbors(spatial_grid)
        fertility_modifier = 80.0 / max(1.0, float(max_food_capacity))

        crowding_penalty = (sosedi_count * 0.15) * fertility_modifier
        self._update_plant_needs(1.0 + crowding_penalty)

        if not self.alive: return

        if self.reproductive_urge >= 100:
            if self.thirst < 5.0 and sosedi_count < 8:
                self.reproductive_urge = 0
                self.thirst += 40
                self._attempt_spawn(terrain, new_agents)
            if self.thirst >= 5.0 or sosedi_count >= 8:
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
        return AgentClass(SIM_WIDTH/2, SIM_HEIGHT/2, *args, **kwargs)

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

        self.spatial_grid.clear()
        for ag in self.agents:
            self.spatial_grid.insert(ag)

        new_agents = []
        for ag in self.agents:
            if ag.alive:
                if isinstance(ag, Clover):
                    ag.act(self.terrain, self.spatial_grid, new_agents, self.n_food)
                    continue
                ag.update_needs(self.terrain)
                ag.act(self.terrain, self.spatial_grid, new_agents, self.init_params.get('mutation_probability', 0.1),
                       self.init_params.get('mutation_strength', 0.2))

        self.agents.extend(new_agents)
        self.agents = [a for a in self.agents if a.alive]

        if random.random() < 0.005:
            self.agents.append(self._spawn_clover())

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
        self.title("EcoSim MVP - Optimized")

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

        top = tk.Frame(root)
        top.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.sim_canvas = tk.Canvas(top, width=SIM_WIDTH, height=SIM_HEIGHT,
                                    bg="#1a1a2e", relief=tk.SUNKEN, bd=1)
        self.sim_canvas.pack(expand=True)

        self.sim_canvas.bind("<ButtonPress-1>", self._on_drag_start)
        self.sim_canvas.bind("<B1-Motion>", self._on_drag_motion)

        self.ctrl = tk.LabelFrame(root, text=" Simulation Controls ", padx=10, pady=8)
        self.ctrl.pack(side=tk.BOTTOM, fill=tk.X, pady=8)

        self._build_buttons()
        self._build_settings()

        self.lbl_info = tk.Label(
            root,
            text="Ticks: 0 | Total: 0 | Prey: 0 | Predators: 0 | Clover: 0 | Dropped: 0",
            font=("Arial", 9, "bold"),
        )
        self.lbl_info.pack(side=tk.BOTTOM, anchor="e")

    def _build_buttons(self):
        bar = tk.Frame(self.ctrl)
        bar.pack(fill=tk.X)

        self.btn_start = tk.Button(bar, text="START", bg="#ccffcc", width=12, command=self.start)
        self.btn_start.pack(side=tk.LEFT, padx=2)

        self.btn_pause = tk.Button(bar, text="PAUSE", state=tk.DISABLED, width=12, command=self.toggle_pause)
        self.btn_pause.pack(side=tk.LEFT, padx=2)

        self.btn_restart = tk.Button(bar, text="RESTART", bg="#ffcccc", state=tk.DISABLED, width=12,
                                     command=self.restart)
        self.btn_restart.pack(side=tk.LEFT, padx=2)

        tk.Label(bar, text="Speed (s):").pack(side=tk.LEFT, padx=(20, 2))
        self.entry_simulation_delay = tk.Entry(bar, width=6)
        self.entry_simulation_delay.insert(0, DEFAULT_SIMULATION_DELAY_SECONDS)
        self.entry_simulation_delay.pack(side=tk.LEFT)

        tk.Label(bar, text="UI Refresh (ms):").pack(side=tk.LEFT, padx=(20, 2))
        self.entry_ui_refresh_ms = tk.Entry(bar, width=6)
        self.entry_ui_refresh_ms.insert(0, DEFAULT_UI_REFRESH_INTERVAL_MS)
        self.entry_ui_refresh_ms.pack(side=tk.LEFT)

        self.show_debug_overlay = tk.BooleanVar(value=True)
        tk.Checkbutton(
            bar,
            text="Show Debug (Sight, Hunger, Thirst)",
            variable=self.show_debug_overlay
        ).pack(side=tk.RIGHT, padx=5)

    def _build_settings(self):
        outer = tk.Frame(self.ctrl, bd=1, relief=tk.SUNKEN, pady=5)
        outer.pack(fill=tk.X, pady=6)

        row1 = tk.Frame(outer)
        row1.pack(fill=tk.X, pady=2)

        self.input_prey_count = ParameterEntry(row1, "Prey Count", DEFAULT_PREY_COUNT)
        self.input_predator_count = ParameterEntry(row1, "Predator Count", DEFAULT_PREDATOR_COUNT)
        self.input_clover_capacity = ParameterEntry(row1, "Food Capacity", DEFAULT_CLOVER_CAPACITY)

        self.input_initial_speed = ParameterEntry(row1, "Initial Speed", DEFAULT_INITIAL_SPEED)
        self.input_initial_size = ParameterEntry(row1, "Initial Size", DEFAULT_INITIAL_SIZE)
        self.input_initial_sense = ParameterEntry(row1, "Initial Sight", DEFAULT_INITIAL_SENSE)

        self.input_mutation_probability = ParameterEntry(row1, "Mutation Prob.\n(e.g. 0.1)", DEFAULT_MUTATION_PROBABILITY, width=6)
        self.input_mutation_strength = ParameterEntry(row1, "Mutation Strength\n(e.g. 0.2)", DEFAULT_MUTATION_STRENGTH, width=6)

        row2 = tk.Frame(outer)
        row2.pack(fill=tk.X, pady=5)
        
        tk.Label(row2, text="Terrain Selection:").pack(side=tk.LEFT, padx=(5, 10))

        terrain_files = glob.glob(os.path.join("terrains", "*.json"))
        terrain_opts = ["Random Generate"] + terrain_files
        
        self.selected_terrain_name = tk.StringVar(value="Random Generate")
        self.terrain_option_menu = tk.OptionMenu(row2, self.selected_terrain_name, *terrain_opts)
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

    def _set_ui_running(self, running: bool):
        state = tk.DISABLED if running else tk.NORMAL
        if running:
            self.btn_start.config(state=tk.DISABLED)
            self.btn_pause.config(state=tk.NORMAL, text="PAUSE")
            self.btn_restart.config(state=tk.NORMAL)

        elif not running:
            self.btn_start.config(state=tk.NORMAL)
            self.btn_pause.config(state=tk.DISABLED, text="PAUSE")
            self.btn_restart.config(state=tk.DISABLED)

        for p in [self.input_prey_count, self.input_predator_count, self.input_clover_capacity, self.input_initial_speed,
                  self.input_initial_size, self.input_initial_sense, self.input_mutation_probability,
                  self.input_mutation_strength]:
            p.set_state(state)

    def start(self):
        self._restarted = False
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
            print("Invalid input values!")
            return

        terrain_file = getattr(self, 'selected_terrain_name', None)
        selected_terrain = terrain_file.get() if terrain_file else "Random Generate"

        try:
            sim_delay = float(self.entry_simulation_delay.get())
        except ValueError:
            sim_delay = float(DEFAULT_SIMULATION_DELAY_SECONDS)

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
        if self.sim:
            self.sim.stop()
            self.sim = None

        while not self.data_queue.empty():
            try:
                self.data_queue.get_nowait()
            except queue.Empty:
                break

        self._last_payload = None
        self.sim_canvas.delete("all")
        self._agent_canvas_items.clear()
        self._is_terrain_drawn = False
        self.lbl_info.config(text="Ticks: 0 | Total: 0 | Prey: 0 | Predators: 0 | Clover: 0 | Dropped: 0")
        self._set_ui_running(False)

    def _poll_queue(self):
        if self._restarted: return

        latest = None
        try:
            while True:
                latest = self.data_queue.get_nowait()
        except queue.Empty:
            pass

        if latest is not None:
            self._last_payload = latest
            self._draw_sim(latest)
            self._update_info(latest)

        try:
            refresh_ms = int(self.entry_ui_refresh_ms.get())
            if refresh_ms < 10: refresh_ms = 10
        except ValueError:
            refresh_ms = int(DEFAULT_UI_REFRESH_INTERVAL_MS)

        try:
            raw_delay = self.entry_simulation_delay.get().strip()
            sim_delay = float(raw_delay) if raw_delay else float(DEFAULT_SIMULATION_DELAY_SECONDS)
            if sim_delay <= 0:
                sim_delay = float(DEFAULT_SIMULATION_DELAY_SECONDS)
        except ValueError:
            sim_delay = float(DEFAULT_SIMULATION_DELAY_SECONDS)

        if self.sim is not None:
            self.sim.simulation_delay = sim_delay

        self.after(refresh_ms, self._poll_queue)

    def _draw_sim(self, payload: dict):
        px, py = self.pan_x, self.pan_y

        if not getattr(self, '_is_terrain_drawn', False):
            self.sim_canvas.delete("terrain")
            terrain = self.sim.terrain if self.sim else None
            if terrain:
                for y in range(terrain.rows):
                    start_x = 0
                    current_ctype = terrain.grid[y][0]
                    for x in range(1, terrain.cols):
                        if terrain.grid[y][x] != current_ctype:
                            col = terrain.TERRAIN_PROPS[current_ctype]["color"]
                            wx1 = start_x * terrain.cell_size
                            wy1 = y * terrain.cell_size
                            wx2 = x * terrain.cell_size
                            wy2 = (y + 1) * terrain.cell_size
                            self.sim_canvas.create_rectangle(wx1, wy1, wx2, wy2, fill=col, outline="", tags="terrain")

                            start_x = x
                            current_ctype = terrain.grid[y][x]

                    col = terrain.TERRAIN_PROPS[current_ctype]["color"]
                    wx1 = start_x * terrain.cell_size
                    wy1 = y * terrain.cell_size
                    wx2 = terrain.cols * terrain.cell_size
                    wy2 = (y + 1) * terrain.cell_size
                    self.sim_canvas.create_rectangle(wx1, wy1, wx2, wy2, fill=col, outline="", tags="terrain")

            self._is_terrain_drawn = True

        # Panning the entire canvas
        self.sim_canvas.scan_mark(0, 0)
        self.sim_canvas.scan_dragto(px, py, gain=1)

        debug = self.show_debug_overlay.get()
        current_ids = set()

        for (ag_id, ax, ay, ar, col, alive, sense, action,
             hunger, thirst, entity_type_name) in payload['agents']:
            if not alive: continue

            current_ids.add(ag_id)
            cx, cy = ax, ay

            if ag_id not in self._agent_canvas_items:
                g = {}
                g['sight'] = self.sim_canvas.create_oval(0, 0, 0, 0, outline="#444444", width=1, dash=(2, 4), state=tk.HIDDEN)
                g['hp_bg'] = self.sim_canvas.create_rectangle(0, 0, 0, 0, fill="#333", outline="", state=tk.HIDDEN)
                g['hp_fg'] = self.sim_canvas.create_rectangle(0, 0, 0, 0, fill="#e74c3c", outline="", state=tk.HIDDEN)
                g['tp_bg'] = self.sim_canvas.create_rectangle(0, 0, 0, 0, fill="#333", outline="", state=tk.HIDDEN)
                g['tp_fg'] = self.sim_canvas.create_rectangle(0, 0, 0, 0, fill="#3498db", outline="", state=tk.HIDDEN)
                g['text'] = self.sim_canvas.create_text(0, 0, text="", fill="#f1c40f", font=("Arial", 8, "bold"), state=tk.HIDDEN)
                g['body'] = self.sim_canvas.create_oval(0, 0, 0, 0, fill=col, outline="black", width=1)
                g['debug_visible'] = False
                self._agent_canvas_items[ag_id] = g

            g = self._agent_canvas_items[ag_id]

            self.sim_canvas.coords(g['body'], cx - ar, cy - ar, cx + ar, cy + ar)

            if debug and entity_type_name != EntityType.CLOVER.value:
                if not g['debug_visible']:
                    self.sim_canvas.itemconfig(g['sight'], state=tk.NORMAL)
                    self.sim_canvas.itemconfig(g['hp_bg'], state=tk.NORMAL)
                    self.sim_canvas.itemconfig(g['hp_fg'], state=tk.NORMAL)
                    self.sim_canvas.itemconfig(g['tp_bg'], state=tk.NORMAL)
                    self.sim_canvas.itemconfig(g['tp_fg'], state=tk.NORMAL)
                    self.sim_canvas.itemconfig(g['text'], state=tk.NORMAL)
                    g['debug_visible'] = True

                self.sim_canvas.coords(g['sight'], cx - sense, cy - sense, cx + sense, cy + sense)

                bar_w = 16
                hp = min(1.0, hunger / 100.0)
                self.sim_canvas.coords(g['hp_bg'], cx - bar_w / 2, cy - ar - 14, cx + bar_w / 2, cy - ar - 11)
                self.sim_canvas.coords(g['hp_fg'], cx - bar_w / 2, cy - ar - 14, cx - bar_w / 2 + bar_w * hp, cy - ar - 11)

                tp = min(1.0, thirst / 100.0)
                self.sim_canvas.coords(g['tp_bg'], cx - bar_w / 2, cy - ar - 10, cx + bar_w / 2, cy - ar - 7)
                self.sim_canvas.coords(g['tp_fg'], cx - bar_w / 2, cy - ar - 10, cx - bar_w / 2 + bar_w * tp, cy - ar - 7)

                self.sim_canvas.itemconfig(g['text'], text=action)
                self.sim_canvas.coords(g['text'], cx, cy - ar - 22)
                continue

            if g['debug_visible']:
                self.sim_canvas.itemconfig(g['sight'], state=tk.HIDDEN)
                self.sim_canvas.itemconfig(g['hp_bg'], state=tk.HIDDEN)
                self.sim_canvas.itemconfig(g['hp_fg'], state=tk.HIDDEN)
                self.sim_canvas.itemconfig(g['tp_bg'], state=tk.HIDDEN)
                self.sim_canvas.itemconfig(g['tp_fg'], state=tk.HIDDEN)
                self.sim_canvas.itemconfig(g['text'], state=tk.HIDDEN)
                g['debug_visible'] = False

        dead_ids = []
        for ag_id, g in self._agent_canvas_items.items():
            if ag_id not in current_ids:
                for key, item in g.items():
                    if key != 'debug_visible':
                        self.sim_canvas.delete(item)
                dead_ids.append(ag_id)

        for dead in dead_ids:
            del self._agent_canvas_items[dead]


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
