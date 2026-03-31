import tkinter as tk
import threading
import queue
import time
import random
import math

# ── colours ──────────────────────────────────────────────────────────────────
COLOR_AGENT = "#3a7bd5"
COLOR_AGENT_SAFE = "#88cc88"
COLOR_AGENT_DEAD = "#555555"
COLOR_FOOD = "#2ecc71"
COLOR_BORDER = "#cccccc"

# ── canvas / agent geometry ───────────────────────────────────────────────────
SIM_WIDTH = 1200
SIM_HEIGHT = 420
AGENT_R_BASE = 4
FOOD_R = 3

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
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.water_bodies = [
            (300, 200, 60),
            (850, 150, 70),
            (600, 380, 50),
        ]


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

    # ──────────────────────────────────────────────────────────

    def __init__(self, x: float, y: float, speed: float, size: float, sense: float):
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

    def update_needs(self):
        if not self.alive: return
        self.age += 1

        # LOGIKA IN PORABA AGENTOV:
        # poraba_vode = base_thirst + (speed * faktor)
        self.thirst += self.BASE_THIRST_RATE + (self.speed * self.SPEED_THIRST_FACTOR)

        # vpliv velikosti na lakoto: poraba_hrane = base_hunger * size
        self.hunger += self.BASE_HUNGER_RATE * (self.size * self.SIZE_HUNGER_FACTOR)

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

    def _clamp_pos(self, terrain):
        """Zadrži agenta na mapi in upravlja trke z vodo."""
        hit_wall = False
        if self.x < self.radius:
            self.x = self.radius;
            hit_wall = True
        elif self.x > SIM_WIDTH - self.radius:
            self.x = SIM_WIDTH - self.radius;
            hit_wall = True

        if self.y < self.radius:
            self.y = self.radius;
            hit_wall = True
        elif self.y > SIM_HEIGHT - self.radius:
            self.y = SIM_HEIGHT - self.radius;
            hit_wall = True

        if hit_wall:
            self.wander_angle += math.pi

        # Trk z vodo (Agent ne more plavati, detelja ne more rasti na vodi)
        # Type check izboljšan
        for wx, wy, wr in terrain.water_bodies:
            dx = self.x - wx
            dy = self.y - wy
            dist_sq = dx * dx + dy * dy
            min_dist = wr + self.radius

            if dist_sq < min_dist * min_dist:
                dist = math.sqrt(dist_sq)
                if dist == 0: dist = 0.1
                overlap = min_dist - dist
                self.x += (dx / dist) * overlap
                self.y += (dy / dist) * overlap
                # Detelja ne tava, jo samo odrine na obalo. Prepreči pojavljanje v vodi.
                if not isinstance(self, Clover):
                    self.wander_angle += math.pi

    def move_towards(self, tx, ty, speed_limit, terrain):
        dist_sq = (tx - self.x) ** 2 + (ty - self.y) ** 2
        if dist_sq > 0:
            dist = math.sqrt(dist_sq)
            step = min(dist, speed_limit)
            self.x += ((tx - self.x) / dist) * step
            self.y += ((ty - self.y) / dist) * step
            self.wander_angle = math.atan2(ty - self.y, tx - self.x)
            self._clamp_pos(terrain)

    def wander(self, terrain):
        self.wander_angle += random.uniform(-0.3, 0.3)
        # Hitrejše premikanje pri tavanju
        self.x += math.cos(self.wander_angle) * self.speed
        self.y += math.sin(self.wander_angle) * self.speed
        self._clamp_pos(terrain)


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

    # ──────────────────────────────────────────────────────────

    def __init__(self, x, y, speed, size, sense):
        super().__init__(x, y, speed, size, sense)
        self.color = COLOR_AGENT_SAFE
        self.max_age = random.randint(5000, 8000)  # Daljši lifespan rojstev

    def act(self, terrain, spatial_grid, new_agents, mut_prob, mut_str):
        if not self.alive: return

        entities = spatial_grid.get_nearby(self.x, self.y, self.sense)

        # 1. BEG PRED PLENILCI
        flee_dx, flee_dy = 0.0, 0.0
        fleeing = False
        sense_sq = self.sense * self.sense

        for e in entities:
            if isinstance(e, Predator) and e.alive:
                # Fast AABB check
                if abs(e.x - self.x) > self.sense or abs(e.y - self.y) > self.sense:
                    continue

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
                # Beži z maksimalno hitrostjo
                self.x += (flee_dx / mag) * (self.speed * 1.2)
                self.y += (flee_dy / mag) * (self.speed * 1.2)
                self.wander_angle = math.atan2(flee_dy, flee_dx)
                self._clamp_pos(terrain)
            return

        # 2. REŠEVANJE POTREB
        pri = self.get_priority()

        if pri == "Reproduction":
            self.current_action = "Mate"
            best_partner = None
            min_dist_sq = float('inf')

            for e in entities:
                if type(e) == type(self) and e.alive and e != self and e.sex != self.sex:
                    if e.get_priority() == "Reproduction":
                        d_sq = (e.x - self.x) ** 2 + (e.y - self.y) ** 2
                        if d_sq < self.sense ** 2 and d_sq < min_dist_sq:
                            min_dist_sq = d_sq
                            best_partner = e

            if best_partner:
                dist = math.sqrt(min_dist_sq)
                if dist < self.radius + best_partner.radius + 5:
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
            best_w = None
            min_dist_edge = float('inf')

            for wx, wy, wr in terrain.water_bodies:
                d = math.hypot(wx - self.x, wy - self.y) - wr
                if d < min_dist_edge:
                    min_dist_edge = d
                    best_w = (wx, wy)

            if best_w:
                # Pije lahko, če je zelo blizu roba vode
                if min_dist_edge < self.radius + 15:
                    self.thirst = max(0, self.thirst - 50)
                    self.current_action = "Drink"
                else:
                    self.move_towards(best_w[0], best_w[1], self.speed, terrain)
            else:
                self.wander(terrain)

        elif pri == "Hunger":
            self.current_action = "Hunger"
            best_food = None
            min_dist_sq = sense_sq

            for e in entities:
                if isinstance(e, Clover) and e.alive:
                    dx, dy = e.x - self.x, e.y - self.y
                    if abs(dx) > self.sense or abs(dy) > self.sense: continue

                    d_sq = dx * dx + dy * dy
                    if d_sq < min_dist_sq:
                        min_dist_sq = d_sq
                        best_food = e

            if best_food:
                dist = math.sqrt(min_dist_sq)
                if dist < self.radius + best_food.radius + 10:
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

    # ──────────────────────────────────────────────────────────

    def __init__(self, x, y, speed, size, sense):
        super().__init__(x, y, speed, size, sense)
        self.color = "#e03131"
        self.max_age = random.randint(15000, 25000)  # Zelo dolg lifespan plenilca

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

        if pri == "Reproduction":
            self.current_action = "Mate"
            best_partner = None
            min_dist_sq = float('inf')

            for e in entities:
                if type(e) == type(self) and e.alive and e != self and e.sex != self.sex:
                    if e.get_priority() == "Reproduction":
                        d_sq = (e.x - self.x) ** 2 + (e.y - self.y) ** 2
                        if d_sq < self.sense ** 2 and d_sq < min_dist_sq:
                            min_dist_sq = d_sq
                            best_partner = e

            if best_partner:
                dist = math.sqrt(min_dist_sq)
                if dist < self.radius + best_partner.radius + 5:
                    self.hunger += self.REPRO_COST_HUNGER
                    self.thirst += self.REPRO_COST_THIRST
                    self.reproductive_urge = self.REPRO_COOLDOWN

                    best_partner.hunger += best_partner.REPRO_COST_HUNGER
                    best_partner.thirst += best_partner.REPRO_COST_THIRST
                    best_partner.reproductive_urge = best_partner.REPRO_COOLDOWN

                    # Plenilci imajo samo enega močnega mladiča hkrati
                    new_agents.append(self.mix_genes(best_partner, mut_prob, mut_str))
                else:
                    self.move_towards(best_partner.x, best_partner.y, self.speed, terrain)
            else:
                self.wander(terrain)

        elif pri == "Thirst":
            self.current_action = "Thirst"
            best_w = None
            min_dist_edge = float('inf')
            for wx, wy, wr in terrain.water_bodies:
                d = math.hypot(wx - self.x, wy - self.y) - wr
                if d < min_dist_edge:
                    min_dist_edge = d
                    best_w = (wx, wy)

            if best_w:
                if min_dist_edge < self.radius + 15:
                    self.thirst = max(0, self.thirst - 50)
                    self.current_action = "Drink"
                else:
                    self.move_towards(best_w[0], best_w[1], self.speed, terrain)
            else:
                self.wander(terrain)

        elif pri == "Hunger":
            self.current_action = "Hunt"
            best_prey = None
            best_score = -float('inf')
            min_dist_sq = float('inf')
            sense_sq = self.sense * self.sense

            for e in entities:
                if isinstance(e, Prey) and e.alive:
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
                dist = math.sqrt(min_dist_sq)
                if dist < self.radius + best_prey.radius + 10:
                    best_prey.alive = False
                    self.hunger = 0  # En ulov povsem napolni želodec
                    self.current_action = "Consume"
                else:
                    # Predator dobi pospešek, ko vidi tarčo
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

    # ──────────────────────────────────────────────────────────

    def __init__(self, x: float, y: float, terrain):
        # Detelja ima večji smisel / korenine (npr. 150), da doseže vodo daleč stran
        super().__init__(x, y, speed=0.0, size=0.1, sense=150.0)
        self.color = COLOR_FOOD
        self.max_age = random.randint(800, 1500)  # Krajši lifespan za deteljo
        self.current_action = "Grow"

        # Randomizicija začetnega urge-a, da se ne razmnožijo na isti tick
        self.reproductive_urge = random.uniform(0, 50)

        # Base vodni potencial izračunan enkrat (koliko vlage načeloma doseže rastlino)
        self.base_water_potential = 0.0
        for wx, wy, wr in terrain.water_bodies:
            d = math.hypot(wx - self.x, wy - self.y) - wr
            if d < self.sense:
                # Koliko vlage dobi - bližje kot je robu = več vlage
                supply = (self.sense - max(0, d)) / self.sense * 1.5
                if supply > self.base_water_potential:
                    self.base_water_potential = supply

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
            if isinstance(e, Clover) and e.alive and e != self:
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

                # Aseksualno širjenje beži stran od gneče
                angle = random.uniform(0, 2 * math.pi)
                dist = random.uniform(20, 50)
                nx = max(0, min(SIM_WIDTH, self.x + math.cos(angle) * dist))
                ny = max(0, min(SIM_HEIGHT, self.y + math.sin(angle) * dist))

                new_clover = Clover(nx, ny, terrain)
                new_clover._clamp_pos(terrain)
                new_agents.append(new_clover)
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

    def _spawn_clover(self):
        """Spawna deteljo. 80% možnosti da bo blizu vode."""
        if random.random() < 0.8 and self.terrain.water_bodies:
            wx, wy, wr = random.choice(self.terrain.water_bodies)
            angle = random.uniform(0, 2 * math.pi)
            dist = wr + random.uniform(5, 60)  # Blizu roba
            x = wx + math.cos(angle) * dist
            y = wy + math.sin(angle) * dist
        else:
            x = random.uniform(10, SIM_WIDTH - 10)
            y = random.uniform(10, SIM_HEIGHT - 10)

        new_clover = Clover(max(0, min(SIM_WIDTH, x)), max(0, min(SIM_HEIGHT, y)), self.terrain)
        new_clover._clamp_pos(self.terrain)  # Prepreči spawn v vodo ali izven mape
        return new_clover

    def _spawn(self):
        self.agents = []
        for _ in range(self.n_food):
            self.agents.append(self._spawn_clover())

        for _ in range(self.n_prey):
            s_speed = self.init_params['speed'] * random.uniform(0.9, 1.1)
            s_size = self.init_params['size'] * random.uniform(0.9, 1.1)
            s_sense = self.init_params['sense'] * random.uniform(0.9, 1.1)
            self.agents.append(
                Prey(random.uniform(10, SIM_WIDTH - 10), random.uniform(10, SIM_HEIGHT - 10), s_speed, s_size, s_sense))

        for _ in range(self.n_pred):
            # Plenilec potrebuje biti hitrejši, da bolje lovi in regulira zajce 
            s_speed = (self.init_params['speed'] * 1.5) * random.uniform(0.9, 1.1)
            s_size = (self.init_params['size'] * 1.2) * random.uniform(0.9, 1.1)
            # Predator ima izrazito večji vid (baseline 1.7x), da lahko zalezuje plen
            s_sense = (self.init_params['sense'] * 1.7) * random.uniform(0.9, 1.1)
            self.agents.append(
                Predator(random.uniform(10, SIM_WIDTH - 10), random.uniform(10, SIM_HEIGHT - 10), s_speed, s_size,
                         s_sense))

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
                    ag.update_needs()
                    ag.act(self.terrain, self.spatial_grid, new_agents, self.init_params.get('mut_prob', 0.1),
                           self.init_params.get('mut_str', 0.2))

        self.agents.extend(new_agents)
        self.agents = [a for a in self.agents if a.alive]

        # Naključni "Spore" Spawn: Zelo majhna verjetnost za kolonizacijo naključne suhe lokacije
        if random.random() < 0.005:  # pribl. 1 na 200 tickov
            spore = Clover(random.uniform(10, SIM_WIDTH - 10), random.uniform(10, SIM_HEIGHT - 10), self.terrain)
            spore._clamp_pos(self.terrain)  # Prepreči spawn v vodo ali izven mape
            self.agents.append(spore)

    def _send_payload(self):
        payload = {
            'ticks': self.ticks,
            'terrain_water': self.terrain.water_bodies,
            'agents': [(
                ag.x, ag.y, ag.radius, ag.color, ag.alive, ag.sense, ag.sex, ag.current_action,
                ag.hunger, ag.thirst, getattr(ag, 'max_age', 100), getattr(ag, 'age', 0),
                type(ag).__name__
            ) for ag in self.agents],
            'active_cnt': len(self.agents),
            'prey_cnt': sum(1 for a in self.agents if isinstance(a, Prey)),
            'pred_cnt': sum(1 for a in self.agents if isinstance(a, Predator)),
            'clover_cnt': sum(1 for a in self.agents if isinstance(a, Clover))
        }
        if self.q.qsize() < QUEUE_MAX:
            self.q.put(payload)


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
        self.lbl_info.config(text="Ticks: 0 | Skupaj: 0 | Plen: 0 | Plenilci: 0 | Detelja: 0")
        self._set_ui_running(False)

    def _poll_queue(self):
        if self._restarted: return

        latest = None
        try:
            while True: latest = self.q.get_nowait()
        except queue.Empty:
            pass

        if latest is not None:
            self._last_payload = latest
            self._draw_sim(latest)
            self._update_info(latest)

        self.after(SIM_REFRESH_MS, self._poll_queue)

    def _draw_sim(self, payload: dict):
        self.sim_canvas.delete("all")
        px, py = self.pan_x, self.pan_y

        for wx, wy, wr in payload.get('terrain_water', []):
            self.sim_canvas.create_oval(wx + px - wr, wy + py - wr, wx + px + wr, wy + py + wr,
                                        fill="#2980b9", outline="#3498db", width=3, tags="terrain")

        debug = self.var_debug.get()

        for (ax, ay, ar, col, alive, sense, sex, action,
             hunger, thirst, max_age, age, cls_name) in payload['agents']:
            cx, cy = ax + px, ay + py

            if alive:
                if debug and cls_name != "Clover":
                    # Krog vida
                    self.sim_canvas.create_oval(cx - sense, cy - sense, cx + sense, cy + sense,
                                                outline="#444444", width=1, dash=(2, 4), tags="debug")

                    # Vrstica lakote (Rdeča)
                    bar_w = 16
                    hp = min(1.0, hunger / 100.0)
                    self.sim_canvas.create_rectangle(cx - bar_w / 2, cy - ar - 14, cx + bar_w / 2, cy - ar - 11,
                                                     fill="#333", outline="", tags="debug")
                    self.sim_canvas.create_rectangle(cx - bar_w / 2, cy - ar - 14, cx - bar_w / 2 + bar_w * hp,
                                                     cy - ar - 11, fill="#e74c3c", outline="", tags="debug")

                    # Vrstica žeje (Modra)
                    tp = min(1.0, thirst / 100.0)
                    self.sim_canvas.create_rectangle(cx - bar_w / 2, cy - ar - 10, cx + bar_w / 2, cy - ar - 7,
                                                     fill="#333", outline="", tags="debug")
                    self.sim_canvas.create_rectangle(cx - bar_w / 2, cy - ar - 10, cx - bar_w / 2 + bar_w * tp,
                                                     cy - ar - 7, fill="#3498db", outline="", tags="debug")

                    # Akcija in status
                    self.sim_canvas.create_text(cx, cy - ar - 22, text=f"{action}",
                                                fill="#f1c40f", font=("Arial", 8, "bold"), tags="debug")

                self.sim_canvas.create_oval(cx - ar, cy - ar, cx + ar, cy + ar,
                                            fill=col, outline="black", width=1, tags="agents")

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
