import tkinter as tk
import threading
import queue
from collections import deque
import time
import random
import math
from terrain_builder import generate_terrain_grid

# ── colours ──────────────────────────────────────────────────────────────────
COLOR_AGENT = "#3a7bd5"
COLOR_AGENT_DEAD = "#555555"
COLOR_AGENT_PRED = "#e03131"
COLOR_AGENT_PREY = "#88cc88"
COLOR_AGENT_FOOD = "#2ecc71"
COLOR_BORDER = "#cccccc"

# ── canvas / agent geometry ───────────────────────────────────────────────────
SIM_WIDTH = 1200
SIM_HEIGHT = 420
AGENT_R_BASE = 4
FOOD_R = 3
CELL_SIZE = 10  # Velikost mrežne celice za teren

# ── simulation ────────────────────────────────────────────────────────────────
QUEUE_MAX = 100
DEFAULT_N_AGENTS = "30"
DEFAULT_N_PRED = "5"
DEFAULT_N_FOOD = "80"
DEFAULT_SPEED = "2.0"
DEFAULT_SIZE = "1.0"
DEFAULT_SENSE = "80.0"
DEFAULT_MUT_PROB = "0.1"
DEFAULT_MUT_STR = "0.2"

DEFAULT_SIM_SPEED = "0.01"
SIM_REFRESH_MS = 30


# ─────────────────────────────────────────────────────────────────────────────
# 1.  MODELS & TERRAIN
# ─────────────────────────────────────────────────────────────────────────────

class Terrain:
    # Definicija lastnosti unikatnih vrst terena:
    # walkable: ali lahko agent stopi nanj
    # speed_mod: faktor hitrosti premikanja
    # thirst_mod: faktor hitrosti dehidracije (npr. puščava/pesek hitreje)
    # hunger_mod: faktor hitrosti pojavljanja lakote
    TERRAIN_PROPS = {
        0: {"walkable": False, "speed_mod": 0.0, "thirst_mod": 1.0, "hunger_mod": 1.0, "color": "#2196f3", "name": "Water"},
        1: {"walkable": True,  "speed_mod": 0.8, "thirst_mod": 1.5, "hunger_mod": 1.0, "color": "#f4d03f", "name": "Sand"},
        2: {"walkable": True,  "speed_mod": 1.0, "thirst_mod": 1.0, "hunger_mod": 1.0, "color": "#2ecc71", "name": "Grass"},
        3: {"walkable": True,  "speed_mod": 0.7, "thirst_mod": 0.8, "hunger_mod": 0.8, "color": "#1b5e20", "name": "Forest"},
        4: {"walkable": True,  "speed_mod": 0.5, "thirst_mod": 1.2, "hunger_mod": 1.2, "color": "#795548", "name": "Mountain"},
        5: {"walkable": False, "speed_mod": 0.0, "thirst_mod": 1.0, "hunger_mod": 1.0, "color": "#fdfefe", "name": "Peak"}
    }

    def __init__(self, width, height, cell_size=CELL_SIZE):
        self.width = width
        self.height = height
        self.cell_size = cell_size
        self.cols = width // cell_size
        self.rows = height // cell_size
        
        seed = random.randint(0, 999999)
        raw_grid = generate_terrain_grid(
            width, height, cell_size, seed, scale=50, octaves=4,
            t_water=0.40, t_sand=0.425, t_grass=0.775, t_forest=0.925, t_mount=0.975
        )
        
        self.grid = [[cell["t"] for cell in row] for row in raw_grid]
        
        self._compute_water_distance()

    def _compute_water_distance(self):
        """ BFS algoritem, ki izracuna zračno razdaljo in KOORDINATE najblizje vöde (O(1) lookupi za preživetje in rastline) """
        self.water_dist = [[float('inf') for _ in range(self.cols)] for _ in range(self.rows)]
        self.nearest_water = [[None for _ in range(self.cols)] for _ in range(self.rows)]
        q = deque()  # deque je bistveno hitrejši od queue.Queue za BFS
        
        # Dodaj vse vodne celice v vrsto
        for y in range(self.rows):
            for x in range(self.cols):
                if self.grid[y][x] == 0:
                    self.water_dist[y][x] = 0
                    self.nearest_water[y][x] = (x * self.cell_size + self.cell_size / 2, y * self.cell_size + self.cell_size / 2)
                    q.append((x, y))
                    
        # BFS razsirjanje
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

    def get_props_at(self, x, y):
        return self.TERRAIN_PROPS[self.get_type_at(x, y)]

    def get_water_dist_at(self, x, y):
        cx, cy = self.get_cell_coords(x, y)
        # Pretvorba vdejanskih pikslov nazaj - dist je preštet v celicah
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
    # ── FAKTORJI ZA TWEAKANJE (Base) ──────────────────────────
    BASE_HUNGER_RATE = 0.05
    BASE_THIRST_RATE = 0.05
    SPEED_THIRST_FACTOR = 0.05
    SIZE_HUNGER_FACTOR = 1.0
    BASE_REPRO_RATE = 0.005
    REPRO_COST_HUNGER = 30
    REPRO_COST_THIRST = 30
    REPRO_COOLDOWN = -30

    cls_name = "Agent"
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
        # Življenjska doba je bistveno daljša
        self.max_age = random.randint(3000, 5000)
        self.hunger = 0.0
        self.thirst = 0.0
        self.reproductive_urge = 0.0

        self.alive = True
        self.color = COLOR_AGENT
        self.sex = random.choice(['M', 'F'])

        self.wander_angle = random.uniform(0, 2 * math.pi)
        self.current_action = "Wander"

    @property
    def radius(self):
        return AGENT_R_BASE + int(self.size - 1.0)

    def update_needs(self, terrain):
        if not self.alive: return
        self.age += 1

        props = terrain.get_props_at(self.x, self.y)

        # LOGIKA IN PORABA AGENTOV ob upoštevanju terena (thirst_mod, hunger_mod)
        self.thirst += (self.BASE_THIRST_RATE + (self.speed * self.SPEED_THIRST_FACTOR)) * props["thirst_mod"]
        self.hunger += (self.BASE_HUNGER_RATE * (self.size * self.SIZE_HUNGER_FACTOR)) * props["hunger_mod"]

        if self.hunger >= 100:
            self.hunger = 100
            self.thirst += self.BASE_THIRST_RATE * 2  # Hitrejša dehidracija ob stradanju

        # Adaptiven reproductive urge: Hitrejši, če je agent bolj sit in odžejan
        health_factor = max(0, 1.0 - (self.hunger + self.thirst) / 200.0)
        # health_factor bo blizu 1.0, če je skoraj sit/odžejan in 0, če strada.
        self.reproductive_urge += self.BASE_REPRO_RATE * (0.5 + health_factor)

        if self.thirst >= 100 or self.age > self.max_age:
            self.alive = False

    def mix_genes(self, partner, mut_prob, mut_strength):
        speed = (self.speed + partner.speed) / 2.0
        size = (self.size + partner.size) / 2.0
        sense = (self.sense + partner.sense) / 2.0

        # Osnovna variacija (+/- 10%)
        speed *= random.uniform(0.9, 1.1)
        size *= random.uniform(0.9, 1.1)
        sense *= random.uniform(0.9, 1.1)

        # Mutacija po vnesenih parametrih
        if random.random() < mut_prob: speed *= random.choice([1.0 - mut_strength, 1.0 + mut_strength])
        if random.random() < mut_prob: size *= random.choice([1.0 - mut_strength, 1.0 + mut_strength])
        if random.random() < mut_prob: sense *= random.choice([1.0 - mut_strength, 1.0 + mut_strength])

        return type(self)(self.x, self.y, max(0.5, speed), max(0.2, size), max(20.0, sense))

    def get_priority(self):
        # Preprečevanje "tunnel vision" - nujno preživetje povozijo reprodukcijo
        if self.thirst > 75:
            return "Thirst"
        elif self.hunger > 75:
            return "Hunger"

        if self.reproductive_urge >= 100 and self.hunger < 40 and self.thirst < 40:
            return "Reproduction"

        if self.thirst > 40:
            return "Thirst"
        elif self.hunger > 40:
            return "Hunger"
        return "Wander"

    def _clamp_bounds(self):
        """Prepreči beg izven okvirjev simulacije."""
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
        """Varno premikanje, ki se ustavi pred neprehodnim terenom."""
        props = terrain.get_props_at(self.x, self.y)
        speed_modifier = props["speed_mod"]

        new_x = self.x + dx * speed_modifier
        new_y = self.y + dy * speed_modifier

        # Preveri, če je nova pozicija v neprehodnem območju
        new_props = terrain.get_props_at(new_x, new_y)
        if not new_props["walkable"]:
            if not self.is_plant:
                self.wander_angle += math.pi  # Obrni se
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


class Prey(Agent):
    # ── FAKTORJI PLENA: "Vezan na oazo" ───────────────────────
    BASE_HUNGER_RATE = 0.04
    BASE_THIRST_RATE = 0.05     
    SPEED_THIRST_FACTOR = 0.04  
    SIZE_HUNGER_FACTOR = 1.0
    BASE_REPRO_RATE = 0.22      # <-- Sredina med 0.15 (izumrtje) in 0.3 (eksplozija)
    REPRO_COST_HUNGER = 25      # <-- Sredina med 35 in 20
    REPRO_COST_THIRST = 25      # <-- Sredina med 35 in 20
    REPRO_COOLDOWN = -60        # <-- Sredina med -80 in -40

    cls_name = "Prey"

    # ──────────────────────────────────────────────────────────

    def __init__(self, x, y, speed, size, sense):
        super().__init__(x, y, speed, size, sense)
        self.color = COLOR_AGENT_PREY
        self.max_age = random.randint(3000, 5000)  # Daljši lifespan rojstev

    def act(self, terrain, spatial_grid, new_agents, mut_prob, mut_str):
        if not self.alive: return

        entities = spatial_grid.get_nearby(self.x, self.y, self.sense)
        sense_sq = self.sense * self.sense

        # Single pass preko vseh entitet za zbiranje
        predators = []
        potential_mates = []
        food = []

        for e in entities:
            # Hitri filter
            if abs(e.x - self.x) > self.sense or abs(e.y - self.y) > self.sense: continue
            
            if e.cls_name == "Predator" and e.alive:
                predators.append(e)
            elif e.cls_name == "Prey" and e.alive and e != self and e.sex != self.sex:
                potential_mates.append(e)
            elif e.is_plant and e.alive:
                food.append(e)

        # 1. BEG PRED PLENILCI
        flee_dx, flee_dy = 0.0, 0.0
        fleeing = False

        for e in predators:
            dist_sq = (e.x - self.x) ** 2 + (e.y - self.y) ** 2
            if dist_sq < sense_sq:
                fleeing = True
                weight = 1.0 / (dist_sq + 0.1)
                flee_dx += (self.x - e.x) * weight
                flee_dy += (self.y - e.y) * weight

        if fleeing:
            self.current_action = "Flee"
            mag = math.hypot(flee_dx, flee_dy)
            if mag > 0:
                dx = (flee_dx / mag) * (self.speed * 1.2)
                dy = (flee_dy / mag) * (self.speed * 1.2)
                self.move_step(dx, dy, terrain)
                self.wander_angle = math.atan2(flee_dy, flee_dx)
            return

        # 2. REŠEVANJE POTREB
        pri = self.get_priority()

        if pri == "Reproduction":
            self.current_action = "Mate"
            best_partner = None
            min_dist_sq = float('inf')

            for e in potential_mates:
                if e.get_priority() == "Reproduction":
                    d_sq = (e.x - self.x) ** 2 + (e.y - self.y) ** 2
                    if d_sq < sense_sq and d_sq < min_dist_sq:
                        min_dist_sq = d_sq
                        best_partner = e

            if best_partner:
                dist_sq = min_dist_sq
                req_dist = self.radius + best_partner.radius + 5
                if dist_sq < req_dist * req_dist:
                    self.hunger += self.REPRO_COST_HUNGER
                    self.thirst += self.REPRO_COST_THIRST
                    self.reproductive_urge = self.REPRO_COOLDOWN

                    best_partner.hunger += best_partner.REPRO_COST_HUNGER
                    best_partner.thirst += best_partner.REPRO_COST_THIRST
                    best_partner.reproductive_urge = best_partner.REPRO_COOLDOWN

                    # Uravnoteženo leglo: zlata sredina (največkrat 2 mladiča, včasih 1 ali 3)
                    litter_size = random.choice([1, 1, 2, 2, 2, 3])  
                    for _ in range(litter_size):
                        new_agents.append(self.mix_genes(best_partner, mut_prob, mut_str))
                else:
                    self.move_towards(best_partner.x, best_partner.y, self.speed, terrain)
            else:
                self.wander(terrain)

        elif pri == "Thirst":
            self.current_action = "Thirst"
            # Uporabimo optimizirano O(1) pridobivanje vode namesto zamudnega O(N^2) skeniranja!
            c_x, c_y = terrain.get_cell_coords(self.x, self.y)
            n_target = terrain.nearest_water[c_y][c_x]
            dist_to_water = terrain.get_water_dist_at(self.x, self.y)

            # Preverimo, če je najbližja voda dovolj blizu in vidna agentu
            if n_target and dist_to_water <= self.sense:
                best_wx, best_wy = n_target
                d_sq = (best_wx - self.x)**2 + (best_wy - self.y)**2
                dist = math.sqrt(d_sq)
                # Ob obali vode (ko razdalja pade pod celico), agenta reši žeja
                if dist < terrain.cell_size + self.radius + 10:
                    self.thirst = max(0, self.thirst - 50)
                    self.current_action = "Drink"
                else:
                    self.move_towards(best_wx, best_wy, self.speed, terrain)
            else:
                self.wander(terrain)

        elif pri == "Hunger":
            self.current_action = "Hunger"
            best_food = None
            min_dist_sq = sense_sq

            for e in food:
                d_sq = (e.x - self.x)**2 + (e.y - self.y)**2
                if d_sq < min_dist_sq:
                    min_dist_sq = d_sq
                    best_food = e

            if best_food:
                req_dist = self.radius + best_food.radius + 10
                if min_dist_sq < req_dist * req_dist:
                    best_food.alive = False
                    self.hunger = 0
                    self.current_action = "Eat"
                else:
                    self.move_towards(best_food.x, best_food.y, self.speed, terrain)
            else:
                self.wander(terrain)
        else:
            self.current_action = "Wander"
            self.wander(terrain)

class Predator(Agent):
    # ── FAKTORJI PLENILCA: "Potrpežljivi lovec" ───────────────
    BASE_HUNGER_RATE = 0.15  # Hitro postane lačen, sili v lov
    BASE_THIRST_RATE = 0.005  # Zelo počasna poraba vode (nomad)
    SPEED_THIRST_FACTOR = 0.02
    SIZE_HUNGER_FACTOR = 1.5
    BASE_REPRO_RATE = 0.05  # Počasna in draga reprodukcija
    REPRO_COST_HUNGER = 80  # <-- Še bolj utrujajoče parjenje, zahteva napolnjen trebuh
    REPRO_COST_THIRST = 40
    REPRO_COOLDOWN = -150   # <-- Večji cooldown, da lisice ne prerastejo zajcev v drugi generaciji

    cls_name = "Predator"

    # ──────────────────────────────────────────────────────────

    def __init__(self, x, y, speed, size, sense):
        super().__init__(x, y, speed, size, sense)
        self.color = COLOR_AGENT_PRED
        self.max_age = random.randint(8000, 10000)  # Zelo dolg lifespan plenilca

    def get_priority(self):
        # Prilagojene prioritete plenilca
        if self.thirst > 85:
            return "Thirst"
        elif self.hunger > 85:
            return "Hunger"

        if self.reproductive_urge >= 100 and self.hunger < 50 and self.thirst < 50:
            return "Reproduction"

        if self.hunger > 30:  # Zelo hitro začne iskati hrano
            return "Hunger"
        elif self.thirst > 50:  # Voda mu ni tako pomembna
            return "Thirst"
        return "Wander"

    def act(self, terrain, spatial_grid, new_agents, mut_prob, mut_str):
        if not self.alive: return
        pri = self.get_priority()

        entities = spatial_grid.get_nearby(self.x, self.y, self.sense)
        sense_sq = self.sense * self.sense

        if pri == "Reproduction":
            self.current_action = "Mate"
            best_partner = None
            min_dist_sq = float('inf')

            for e in entities:
                if e.cls_name == "Predator" and e.alive and e != self and e.sex != self.sex:
                    if abs(e.x - self.x) > self.sense or abs(e.y - self.y) > self.sense: continue
                    if e.get_priority() == "Reproduction":
                        d_sq = (e.x - self.x) ** 2 + (e.y - self.y) ** 2
                        if d_sq < sense_sq and d_sq < min_dist_sq:
                            min_dist_sq = d_sq
                            best_partner = e

            if best_partner:
                req_dist = self.radius + best_partner.radius + 5
                if min_dist_sq < req_dist * req_dist:
                    self.hunger += self.REPRO_COST_HUNGER
                    self.thirst += self.REPRO_COST_THIRST
                    self.reproductive_urge = self.REPRO_COOLDOWN

                    best_partner.hunger += best_partner.REPRO_COST_HUNGER
                    best_partner.thirst += best_partner.REPRO_COST_THIRST
                    best_partner.reproductive_urge = best_partner.REPRO_COOLDOWN

                    new_agents.append(self.mix_genes(best_partner, mut_prob, mut_str))
                else:
                    self.move_towards(best_partner.x, best_partner.y, self.speed, terrain)
            else:
                self.wander(terrain)

        elif pri == "Thirst":
            self.current_action = "Thirst"
            # O(1) pridobivanje vode v delčku milisekunde namesto O(N^2)
            c_x, c_y = terrain.get_cell_coords(self.x, self.y)
            n_target = terrain.nearest_water[c_y][c_x]
            dist_to_water = terrain.get_water_dist_at(self.x, self.y)

            if n_target and dist_to_water <= self.sense:
                best_wx, best_wy = n_target
                # Realna razdalja do znane lokacije kroga celice
                d_sq = (best_wx - self.x)**2 + (best_wy - self.y)**2
                dist = math.sqrt(d_sq)
                if dist < terrain.cell_size + self.radius + 10:
                    self.thirst = max(0, self.thirst - 50)
                    self.current_action = "Drink"
                else:
                    self.move_towards(best_wx, best_wy, self.speed, terrain)
            else:
                self.wander(terrain)

        elif pri == "Hunger":
            self.current_action = "Hunt"
            best_prey = None
            best_score = -float('inf')
            min_dist_sq = float('inf')

            for e in entities:
                if e.cls_name == "Prey" and e.alive:
                    dx, dy = e.x - self.x, e.y - self.y
                    if abs(dx) > self.sense or abs(dy) > self.sense: continue

                    d_sq = dx * dx + dy * dy
                    if d_sq < sense_sq:
                        d = math.sqrt(d_sq)
                        score = (e.size * 10) - d
                        if score > best_score:
                            best_score = score
                            best_prey = e
                            min_dist_sq = d_sq

            if best_prey:
                req_dist = self.radius + best_prey.radius + 10
                if min_dist_sq < req_dist * req_dist:
                    best_prey.alive = False
                    self.hunger = 0
                    self.current_action = "Consume"
                else:
                    self.move_towards(best_prey.x, best_prey.y, self.speed * 1.3, terrain)
            else:
                self.current_action = "Hunger"
                self.wander(terrain)
        else:
            self.current_action = "Wander"
            self.wander(terrain)

class Clover(Agent):
    # ── FAKTORJI DETELJE: "Temelj ekosistema" ─────────────────
    BASE_THIRST_RATE = 0.8
    SPEED_THIRST_FACTOR = 0.0
    SIZE_HUNGER_FACTOR = 0.0
    BASE_REPRO_RATE = 0.4

    cls_name = "Clover"
    is_plant = True

    # ──────────────────────────────────────────────────────────

    def __init__(self, x: float, y: float, terrain):
        # Detelja ima večji smisel / korenine (npr. 150), da doseže vodo daleč stran
        super().__init__(x, y, speed=0.0, size=0.1, sense=150.0)
        self.color = COLOR_AGENT_FOOD
        self.max_age = random.randint(800, 1500)  # Krajši lifespan za deteljo
        self.current_action = "Grow"

        # Randomizicija začetnega urge-a, da se ne razmnožijo na isti tick
        self.reproductive_urge = random.uniform(0, 50)

        # Base vodni potencial izračunan takoj, s preprostim pridobivanjem O(1)
        dist_to_water = terrain.get_water_dist_at(self.x, self.y)
        if dist_to_water < self.sense:
            self.base_water_potential = (self.sense - max(0, dist_to_water)) / self.sense * 1.5
        else:
            self.base_water_potential = 0.0

        # Dinamični potencial, ki se posodablja
        self.moisture_supply = self.base_water_potential

    @property
    def radius(self):
        return FOOD_R

    def update_needs(self):  # Zdaj zahteva argument, ampak ga bomo predelali v act() za optimizacijo
        pass

    def _update_plant_needs(self, local_crowding_factor):
        if not self.alive: return
        self.age += 1

        # Izračun končne vlage: Base zmanjšan za lokalno tekmovanje (crowding)
        self.moisture_supply = self.base_water_potential / max(1.0, local_crowding_factor)

        # Detelja dehidrira, če nima dovolj vode, in se polni, če jo ima viška.
        net_thirst = self.BASE_THIRST_RATE - self.moisture_supply
        self.thirst = max(0.0, min(150.0, self.thirst + net_thirst))

        if self.thirst >= 100 or self.age > self.max_age:
            self.alive = False
            return

        # Adaptiven urge: Uspešno raste, če ima dovolj vlage.
        # Razmnožuje se le, če je resnično odžejana (thirst < 5)
        if self.thirst < 5.0 and self.moisture_supply > self.BASE_THIRST_RATE:
            health_factor = max(0.0, 1.0 - (self.thirst / 100.0))
            # Višek vlage pomaga pri rasti reprodukcije
            surplus = self.moisture_supply - self.BASE_THIRST_RATE
            self.reproductive_urge += self.BASE_REPRO_RATE * (0.5 + 2.0 * health_factor + surplus)

    def act(self, terrain, spatial_grid, new_agents, max_food_capacity):
        if not self.alive: return

        # 1. Zaznavanje sosedov in "Dušenje" (Resource Competition)
        # Manjši radij iskanja za tekmovanje sosedov (~30 pikslov)
        nearby_entities = spatial_grid.get_nearby(self.x, self.y, 30)

        sosedi_count = 0
        for e in nearby_entities:
            if e.is_plant and e.alive and e != self:
                # Točen izračun razdalje znotraj zamejene celice
                if (e.x - self.x) ** 2 + (e.y - self.y) ** 2 < 900:  # 30^2 = 900
                    sosedi_count += 1

        # Globalna rodovitnost zmanjša tekmovanje (višji max_food = lažje rastjo skupaj)
        # Npr. capacity okoli 80 da normalni pritisk. 
        fertility_modifier = 80.0 / max(1.0, float(max_food_capacity))

        # Lokalni pritisk: 1 sosed je skoraj neopazen, 5 je precej, 20 je huda suša
        # Koeficient dušenja je dinamičen
        crowding_penalty = (sosedi_count * 0.15) * fertility_modifier

        self._update_plant_needs(1.0 + crowding_penalty)

        if not self.alive: return

        # 2. Razmnoževanje
        if self.reproductive_urge >= 100:
            # Strog pogoj: Je polna vode, in ima prostor (npr. manj kot 8 sosedov)
            if self.thirst < 5.0 and sosedi_count < 8:
                self.reproductive_urge = 0  # reset
                self.thirst += 40  # Ceni jo vode

                for _ in range(5):  # Več poskusov za iskanje varne suhe lokacije
                    angle = random.uniform(0, 2 * math.pi)
                    dist = random.uniform(20, 50)
                    nx = self.x + math.cos(angle) * dist
                    ny = self.y + math.sin(angle) * dist
                    
                    if 0 < nx < SIM_WIDTH and 0 < ny < SIM_HEIGHT:
                        if terrain.get_props_at(nx, ny)["walkable"]:
                            new_clover = Clover(nx, ny, terrain)
                            new_agents.append(new_clover)
                            break
            else:
                self.reproductive_urge = 100  # Čaka na priložnost


# ─────────────────────────────────────────────────────────────────────────────
# 3.  SIMULATION ENGINE
# ─────────────────────────────────────────────────────────────────────────────

class SimThread(threading.Thread):
    def __init__(self, data_queue: queue.Queue, n_prey: int, n_pred: int, n_food: int, init_params: dict,
                 speed_entry: tk.Entry):
        super().__init__(daemon=True)
        self.q = data_queue
        self.n_prey = n_prey
        self.n_pred = n_pred
        self.n_food = n_food
        self.init_params = init_params
        self._speed_entry = speed_entry

        self._running = True
        self._paused = threading.Event()
        self._paused.set()

        self.terrain = Terrain(SIM_WIDTH, SIM_HEIGHT)
        self.spatial_grid = SpatialGrid(100)
        self.agents: list[Agent] = []
        self.ticks = 0

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
        try:
            val = float(self._speed_entry.get())
            if val > 0: return val
        except:
            pass
        return float(DEFAULT_SIM_SPEED)

    def _spawn_agent_safe(self, AgentClass, *args, **kwargs):
        """Varno spawna agenta na lokaciji, ki je WALKABLE (omejeno število poizkusov)"""
        for _ in range(20):
            x = random.uniform(20, SIM_WIDTH - 20)
            y = random.uniform(20, SIM_HEIGHT - 20)
            if self.terrain.get_props_at(x, y)["walkable"]:
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
                else:
                    ag.update_needs(self.terrain)
                    ag.act(self.terrain, self.spatial_grid, new_agents, self.init_params.get('mut_prob', 0.1),
                           self.init_params.get('mut_str', 0.2))

        self.agents.extend(new_agents)
        self.agents = [a for a in self.agents if a.alive]

        # Naključni "Spore" Spawn: kolonizacija na safe zemlji
        if random.random() < 0.005:  
            self.agents.append(self._spawn_clover())

    def _send_payload(self):
        payload = {
            'ticks': self.ticks,
            # Terrena ne pošiljamo več, ker ga app izkicli iz generatorja v draw root
            'agents': [(
                ag.id, ag.x, ag.y, ag.radius, ag.color, ag.alive, ag.sense, ag.current_action,
                ag.hunger, ag.thirst, ag.cls_name
            ) for ag in self.agents],
            'active_cnt': len(self.agents),
            'prey_cnt': sum(1 for a in self.agents if a.cls_name == "Prey"),
            'pred_cnt': sum(1 for a in self.agents if a.cls_name == "Predator"),
            'clover_cnt': sum(1 for a in self.agents if a.is_plant)
        }
        if self.q.qsize() < QUEUE_MAX:
            self.q.put(payload)
        else:
            # Drop older frames to keep the queue small and UI responsive
            try:
                self.q.get_nowait()
                self.q.put(payload)
            except queue.Empty:
                pass


# ─────────────────────────────────────────────────────────────────────────────
# 4.  UI COMPONENTS
# ─────────────────────────────────────────────────────────────────────────────

class ParamEntry(tk.Frame):
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
        self.title("EcoSim MVP - Optimizirano")

        self.sim = None
        self.q = queue.Queue()
        self._restarted = False
        self._last_payload = None

        self.pan_x = 0
        self.pan_y = 0
        self._drag_start_x = 0
        self._drag_start_y = 0

        self._agent_graphics = {}  # Shranjevanje canvas ID-jev za vsakega agenta

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

        self.ctrl = tk.LabelFrame(root, text=" Kontrola simulacije ", padx=10, pady=8)
        self.ctrl.pack(side=tk.BOTTOM, fill=tk.X, pady=8)

        self._build_buttons()
        self._build_settings()

        self.lbl_info = tk.Label(root, text="Ticks: 0 | Skupaj: 0 | Plen: 0 | Plenilci: 0 | Detelja: 0",
                                 font=("Arial", 9, "bold"))
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

        tk.Label(bar, text="Hitrost (s):").pack(side=tk.LEFT, padx=(20, 2))
        self.ent_speed = tk.Entry(bar, width=6)
        self.ent_speed.insert(0, DEFAULT_SIM_SPEED)
        self.ent_speed.pack(side=tk.LEFT)

        self.var_debug = tk.BooleanVar(value=True)
        tk.Checkbutton(
            bar,
            text="Prikaži Debug (Vid, Lakota, Žeja)",
            variable=self.var_debug
        ).pack(side=tk.RIGHT, padx=5)

    def _build_settings(self):
        outer = tk.Frame(self.ctrl, bd=1, relief=tk.SUNKEN, pady=5)
        outer.pack(fill=tk.X, pady=6)

        row1 = tk.Frame(outer)
        row1.pack(fill=tk.X, pady=2)

        self.p_nprey = ParamEntry(row1, "Št. Zajcev", DEFAULT_N_AGENTS)
        self.p_npred = ParamEntry(row1, "Št. Lisic", DEFAULT_N_PRED)
        self.p_nfood = ParamEntry(row1, "Hrana (Max)", DEFAULT_N_FOOD)

        self.p_speed = ParamEntry(row1, "Začetna hitrost", DEFAULT_SPEED)
        self.p_size = ParamEntry(row1, "Začetna velikost", DEFAULT_SIZE)
        self.p_sense = ParamEntry(row1, "Začetni vid", DEFAULT_SENSE)

        self.p_mut_prob = ParamEntry(row1, "Verjetnost mut.\n(npr. 0.1)", DEFAULT_MUT_PROB, width=6)
        self.p_mut_str = ParamEntry(row1, "Moč mutacije\n(npr. 0.2)", DEFAULT_MUT_STR, width=6)

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
        else:
            self.btn_start.config(state=tk.NORMAL)
            self.btn_pause.config(state=tk.DISABLED, text="PAUSE")
            self.btn_restart.config(state=tk.DISABLED)

        for p in [self.p_nprey, self.p_npred, self.p_nfood, self.p_speed, self.p_size, self.p_sense, self.p_mut_prob,
                  self.p_mut_str]:
            p.set_state(state)

    def start(self):
        self._restarted = False
        try:
            n_prey = int(self.p_nprey.get())
            n_pred = int(self.p_npred.get())
            n_food = int(self.p_nfood.get())

            init_params = {
                'speed': float(self.p_speed.get()),
                'size': float(self.p_size.get()),
                'sense': float(self.p_sense.get()),
                'mut_prob': float(self.p_mut_prob.get()),
                'mut_str': float(self.p_mut_str.get()),
            }
        except ValueError:
            print("Neveljavni podatki!")
            return

        self.sim = SimThread(
            data_queue=self.q,
            n_prey=n_prey,
            n_pred=n_pred,
            n_food=n_food,
            init_params=init_params,
            speed_entry=self.ent_speed
        )
        self.sim.start()
        self._set_ui_running(True)
        self._poll_queue()

    def toggle_pause(self):
        if self.sim is None: return
        if self.sim.is_paused:
            self.sim.resume()
            self.btn_pause.config(text="PAUSE")
        else:
            self.sim.pause()
            self.btn_pause.config(text="NADALJUJ")

    def restart(self):
        self._restarted = True
        if self.sim:
            self.sim.stop()
            self.sim = None

        while not self.q.empty():
            try:
                self.q.get_nowait()
            except queue.Empty:
                break

        self._last_payload = None
        self.sim_canvas.delete("all")
        self._agent_graphics.clear()
        self._terrain_drawn = False # Reset za ponoven izris terena
        self.lbl_info.config(text="Ticks: 0 | Skupaj: 0 | Plen: 0 | Plenilci: 0 | Detelja: 0")
        self._set_ui_running(False)

    def _poll_queue(self):
        if self._restarted: return

        latest = None
        # Poberi VSE kar je trenutno v vrsti, prikaži samo ZADNJE stanje
        # To zmanjša lag, ker preskoči stare izrise, če simulacija teče hitreje kot zaslon
        try:
            while True: 
                latest = self.q.get_nowait()
        except queue.Empty:
            pass

        if latest is not None:
            self._last_payload = latest
            self._draw_sim(latest)
            self._update_info(latest)

        self.after(SIM_REFRESH_MS, self._poll_queue)

    def _draw_sim(self, payload: dict):
        px, py = self.pan_x, self.pan_y

        # Inicializacija ali premikanje terena ob "pan" premiku
        if not getattr(self, '_terrain_drawn', False):
            self.sim_canvas.delete("terrain")
            # Nariši Terrain Grid na začetku iz simulacije - Z Run-Length Encodingom da drastično zmanjšamo število elementov
            terrain = self.sim.terrain if self.sim else None
            if terrain:
                for y in range(terrain.rows):
                    start_x = 0
                    current_ctype = terrain.grid[y][0]
                    for x in range(1, terrain.cols):
                        if terrain.grid[y][x] != current_ctype:
                            # Nariši vrsto združenih pravokotnikov naenkrat
                            col = terrain.TERRAIN_PROPS[current_ctype]["color"]
                            wx1 = start_x * terrain.cell_size
                            wy1 = y * terrain.cell_size
                            wx2 = x * terrain.cell_size
                            wy2 = (y + 1) * terrain.cell_size
                            self.sim_canvas.create_rectangle(wx1, wy1, wx2, wy2, fill=col, outline="", tags="terrain")
                            
                            start_x = x
                            current_ctype = terrain.grid[y][x]
                            
                    # Nariši preostanek še ob koncu zanke
                    col = terrain.TERRAIN_PROPS[current_ctype]["color"]
                    wx1 = start_x * terrain.cell_size
                    wy1 = y * terrain.cell_size
                    wx2 = terrain.cols * terrain.cell_size
                    wy2 = (y + 1) * terrain.cell_size
                    self.sim_canvas.create_rectangle(wx1, wy1, wx2, wy2, fill=col, outline="", tags="terrain")
                                                         
            self._terrain_drawn = True
        
        # Panning the entire canvas
        self.sim_canvas.scan_mark(0, 0)
        self.sim_canvas.scan_dragto(px, py, gain=1)

        debug = self.var_debug.get()
        current_ids = set()

        for (ag_id, ax, ay, ar, col, alive, sense, action,
             hunger, thirst, cls_name) in payload['agents']:
            if not alive: continue
            
            current_ids.add(ag_id)
            cx, cy = ax, ay

            # Če agenta še ni na zaslonu, ga ustvarimo
            if ag_id not in self._agent_graphics:
                g = {}
                g['sight'] = self.sim_canvas.create_oval(0, 0, 0, 0, outline="#444444", width=1, dash=(2, 4), state=tk.HIDDEN)
                g['hp_bg'] = self.sim_canvas.create_rectangle(0, 0, 0, 0, fill="#333", outline="", state=tk.HIDDEN)
                g['hp_fg'] = self.sim_canvas.create_rectangle(0, 0, 0, 0, fill="#e74c3c", outline="", state=tk.HIDDEN)
                g['tp_bg'] = self.sim_canvas.create_rectangle(0, 0, 0, 0, fill="#333", outline="", state=tk.HIDDEN)
                g['tp_fg'] = self.sim_canvas.create_rectangle(0, 0, 0, 0, fill="#3498db", outline="", state=tk.HIDDEN)
                g['text'] = self.sim_canvas.create_text(0, 0, text="", fill="#f1c40f", font=("Arial", 8, "bold"), state=tk.HIDDEN)
                # Telo naj bo vedno na vrhu (narisano nazadnje v zanki kreacije)
                g['body'] = self.sim_canvas.create_oval(0, 0, 0, 0, fill=col, outline="black", width=1)
                self._agent_graphics[ag_id] = g

            g = self._agent_graphics[ag_id]

            # Posodobi pozicijo telesa
            self.sim_canvas.coords(g['body'], cx - ar, cy - ar, cx + ar, cy + ar)

            # Upravljanje vidnosti in animacije Debug elementov
            if debug and cls_name != "Clover":
                self.sim_canvas.itemconfig(g['sight'], state=tk.NORMAL)
                self.sim_canvas.coords(g['sight'], cx - sense, cy - sense, cx + sense, cy + sense)
                
                bar_w = 16
                hp = min(1.0, hunger / 100.0)
                self.sim_canvas.itemconfig(g['hp_bg'], state=tk.NORMAL)
                self.sim_canvas.coords(g['hp_bg'], cx - bar_w / 2, cy - ar - 14, cx + bar_w / 2, cy - ar - 11)
                self.sim_canvas.itemconfig(g['hp_fg'], state=tk.NORMAL)
                self.sim_canvas.coords(g['hp_fg'], cx - bar_w / 2, cy - ar - 14, cx - bar_w / 2 + bar_w * hp, cy - ar - 11)

                tp = min(1.0, thirst / 100.0)
                self.sim_canvas.itemconfig(g['tp_bg'], state=tk.NORMAL)
                self.sim_canvas.coords(g['tp_bg'], cx - bar_w / 2, cy - ar - 10, cx + bar_w / 2, cy - ar - 7)
                self.sim_canvas.itemconfig(g['tp_fg'], state=tk.NORMAL)
                self.sim_canvas.coords(g['tp_fg'], cx - bar_w / 2, cy - ar - 10, cx - bar_w / 2 + bar_w * tp, cy - ar - 7)

                self.sim_canvas.itemconfig(g['text'], state=tk.NORMAL, text=f"{action}")
                self.sim_canvas.coords(g['text'], cx, cy - ar - 22)
            else:
                self.sim_canvas.itemconfig(g['sight'], state=tk.HIDDEN)
                self.sim_canvas.itemconfig(g['hp_bg'], state=tk.HIDDEN)
                self.sim_canvas.itemconfig(g['hp_fg'], state=tk.HIDDEN)
                self.sim_canvas.itemconfig(g['tp_bg'], state=tk.HIDDEN)
                self.sim_canvas.itemconfig(g['tp_fg'], state=tk.HIDDEN)
                self.sim_canvas.itemconfig(g['text'], state=tk.HIDDEN)

        # Odstrani in počisti narisane komponente za mrtve agente
        dead_ids = []
        for ag_id, g in self._agent_graphics.items():
            if ag_id not in current_ids:
                for item in g.values():
                    self.sim_canvas.delete(item)
                dead_ids.append(ag_id)
        
        for dead in dead_ids:
            del self._agent_graphics[dead]


    def _update_info(self, payload: dict):
        active_cnt = payload.get('active_cnt', 0)
        prey_cnt = payload.get('prey_cnt', 0)
        pred_cnt = payload.get('pred_cnt', 0)
        clover_cnt = payload.get('clover_cnt', 0)
        ticks = payload.get('ticks', 0)
        self.lbl_info.config(
            text=f"Tiki: {ticks} | Skupaj: {active_cnt} | Zajci: {prey_cnt} | Lisice: {pred_cnt} | Detelja: {clover_cnt}")


if __name__ == "__main__":
    app = App()
    app.mainloop()
