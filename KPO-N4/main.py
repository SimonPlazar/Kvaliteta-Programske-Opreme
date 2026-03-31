import tkinter as tk
import threading
import queue
import time
import random
import math

# ── colours ──────────────────────────────────────────────────────────────────
COLOR_AGENT   = "#3a7bd5"
COLOR_AGENT_SAFE = "#88cc88"
COLOR_AGENT_DEAD = "#555555"
COLOR_FOOD    = "#2ecc71"
COLOR_BORDER  = "#cccccc"

# ── canvas / agent geometry ───────────────────────────────────────────────────
SIM_WIDTH     = 1200    # širina simulacije (prilagodi po želji)
SIM_HEIGHT    = 420     # višina simulacije
BORDER_W      = 0       # no longer needed for new logic
AGENT_R_BASE  = 4       # base agent radius
FOOD_R        = 3       # food circle radius (px)

# ── simulation ────────────────────────────────────────────────────────────────
QUEUE_MAX          = 100
DEFAULT_N_AGENTS   = "30"
DEFAULT_N_PRED     = "5"
DEFAULT_N_FOOD     = "100"
DEFAULT_E_CAP      = "2000"
DEFAULT_SPEED      = "2.0"
DEFAULT_SIZE       = "1.0"
DEFAULT_SENSE      = "50.0"
DEFAULT_MUT_PROB   = "0.1"

DEFAULT_SIM_SPEED  = "0.01"
SIM_REFRESH_MS     = 30

# ─────────────────────────────────────────────────────────────────────────────
# 1.  MODELS & TERRAIN STUB
# ─────────────────────────────────────────────────────────────────────────────

class Terrain:
    """Stub for the terrain. Will later hold Perlin noise grid and water physics."""
    def __init__(self, width, height):
        self.width = width
        self.height = height
        # TODO: generate 2D grid
        # Trenutno statična voda za testiranje
        self.water_bodies = [
            (300, 200, 50), # x, y, r
            (800, 100, 80),
        ]
    
    def is_water(self, x, y):
        # Stub: check against static water circles
        for wx, wy, wr in self.water_bodies:
            if math.hypot(x - wx, y - wy) < wr:
                return True
        return False

class Agent:
    """Base class for all living entities."""
    def __init__(self, x: float, y: float, speed: float, size: float, sense: float):
        self.x = x
        self.y = y
        self.speed = speed
        self.size = size
        self.sense = sense
        
        self.age = 0
        self.max_age = 1500 + random.randint(-200, 200)
        self.hunger = 0
        self.thirst = 0
        self.reproductive_urge = 0
        
        self.alive = True
        self.color = COLOR_AGENT
        self.sex = random.choice(['M', 'F'])

    @property
    def radius(self):
        return AGENT_R_BASE + int(self.size - 1.0)

    def update_needs(self):
        """Update hunger, thirst, age based on size and speed."""
        if not self.alive: return
        self.age += 1
        
        # Ce bitje stoji (detelja) ne porablja hunger/thirst od hitrosti na enak nacin
        speed_factor = self.speed if self.speed > 0 else 0.1
        
        # Velikost vpliva na hitrost večanja lakote
        self.hunger += 0.05 * self.size
        # Hitrost vpliva na hitrost večanja žeje
        self.thirst += 0.05 * speed_factor
        
        # Če zmanjka hrane (lakota pride do 100), se ne umre direktno,
        # temveč se drastično poveča potreba po vodi (žeja nastopi hitreje).
        if self.hunger > 100:
            self.hunger = 100
            self.thirst += 0.1 * speed_factor

        self.reproductive_urge += 0.02
        
        # Bitje umre, ko mu zmanjka vode (preveč žejno) ali zaradi starosti
        if self.thirst > 100 or self.age > self.max_age:
            self.alive = False

    def get_priority(self):
        """Vrača trenutno najvišjo prioriteto bitja."""
        if self.reproductive_urge > 80:
            return "reproduction"
        # Žeja postane prioriteta tudi, če je zmanjkalo hrane (lakota = 100)
        elif self.thirst > 50 or self.hunger >= 100:
            return "thirst"
        elif self.hunger > 50:
            return "hunger"
        return "wander"
        
    def breed(self, partner):
        """Placeholder za razmnozevanje in dedovanje."""
        pass
        
    def mutate(self):
        """Placeholder za mutacijo podedovanih lastnosti."""
        pass

    def act(self, terrain: Terrain, entities: list):
        """Must be implemented by subclasses to decide movement and actions."""
        pass

    def move_towards(self, tx, ty, speed_limit):
        dist = math.hypot(tx - self.x, ty - self.y)
        if dist > 0:
            step = min(dist, speed_limit)
            self.x += ((tx - self.x) / dist) * step
            self.y += ((ty - self.y) / dist) * step
            self.x = max(0, min(SIM_WIDTH, self.x))
            self.y = max(0, min(SIM_HEIGHT, self.y))

class Prey(Agent):
    """E.g. Rabbit. Runs from predators, goes to food/water."""
    def __init__(self, x, y, speed, size, sense):
        super().__init__(x, y, speed, size, sense)
        self.color = COLOR_AGENT_SAFE # e.g. green/blueish

    def act(self, terrain, entities):
        if not self.alive: return
        
        # 1. Ali bezimo?
        flee_dx, flee_dy = 0.0, 0.0
        fleeing = False
        
        for e in entities:
            if isinstance(e, Predator) and e.alive:
                d = math.hypot(e.x - self.x, e.y - self.y)
                if d < self.sense:
                    fleeing = True
                    # Vektor stran od plenilca, utezen (blizji kot je, bolj vpliva)
                    if d > 0:
                        weight = 1.0 / (d * d) # Uporabimo obrnjeni kvadrat razdalje za močnejši beg bližje reke
                        flee_dx += (self.x - e.x) * weight
                        flee_dy += (self.y - e.y) * weight
                        
        # Beg pred plenilcem vedno prepelje operacijo
        if fleeing:
            mag = math.hypot(flee_dx, flee_dy)
            if mag > 0:
                self.move_towards(self.x + (flee_dx/mag)*100, self.y + (flee_dy/mag)*100, self.speed)
            return

        # 2. Resevanje potreb glede na prioriteto
        pri = self.get_priority()
        
        if pri == "reproduction":
            self.move_towards(self.x + random.uniform(-10,10), self.y + random.uniform(-10,10), self.speed * 0.5)
        elif pri == "thirst":
            # Najdi najbližjo vodo
            best_w = None
            min_dist = float('inf')
            for wx, wy, wr in terrain.water_bodies:
                d = math.hypot(wx - self.x, wy - self.y) - wr
                if d < min_dist:
                    min_dist = d
                    best_w = (wx, wy, wr)
            
            if best_w:
                if min_dist < self.radius + 2:
                    self.thirst = max(0, self.thirst - 80) # Napijemo se
                else:
                    self.move_towards(best_w[0], best_w[1], self.speed)
            else:
                self.move_towards(self.x + random.uniform(-10,10), self.y + random.uniform(-10,10), self.speed * 0.5)
        elif pri == "hunger":
            nearest_food = None
            min_dist_food = self.sense
            for e in entities:
                if isinstance(e, Clover) and e.alive:
                    d = math.hypot(e.x - self.x, e.y - self.y)
                    if d < min_dist_food:
                        min_dist_food = d
                        nearest_food = e
                    
            if nearest_food:
                if min_dist_food < self.radius + nearest_food.radius:
                    nearest_food.alive = False
                    self.hunger = max(0, self.hunger - 60) # Najemo se
                else:
                    self.move_towards(nearest_food.x, nearest_food.y, self.speed)
            else:
                self.move_towards(self.x + random.uniform(-10,10), self.y + random.uniform(-10,10), self.speed * 0.5)
        else:
            # wander
            self.move_towards(self.x + random.uniform(-10,10), self.y + random.uniform(-10,10), self.speed * 0.5)

class Predator(Agent):
    """E.g. Fox. Hunts Prey."""
    def __init__(self, x, y, speed, size, sense):
        super().__init__(x, y, speed, size, sense)
        self.color = "#e03131" # Red

    def act(self, terrain, entities):
        if not self.alive: return
        
        pri = self.get_priority()
        
        if pri == "reproduction":
            self.move_towards(self.x + random.uniform(-10,10), self.y + random.uniform(-10,10), self.speed * 0.5)
        elif pri == "thirst":
            best_w = None
            min_dist = float('inf')
            for wx, wy, wr in terrain.water_bodies:
                d = math.hypot(wx - self.x, wy - self.y) - wr
                if d < min_dist:
                    min_dist = d
                    best_w = (wx, wy, wr)
            
            if best_w:
                if min_dist < self.radius + 2:
                    self.thirst = max(0, self.thirst - 80) # Napije se
                else:
                    self.move_towards(best_w[0], best_w[1], self.speed)
            else:
                self.move_towards(self.x + random.uniform(-10,10), self.y + random.uniform(-10,10), self.speed * 0.5)
        elif pri == "hunger":
            best_prey = None
            best_score = -999999
            min_dist_prey = float('inf')
            
            for e in entities:
                if isinstance(e, Prey) and e.alive:
                    d = math.hypot(e.x - self.x, e.y - self.y)
                    if d < self.sense:
                        # Ocenjevanje plena (blizji, pocasnejsi, vecji = boljsi)
                        score = (e.size * 10) - (e.speed * 5) - d
                        if score > best_score:
                            best_score = score
                            best_prey = e
                            min_dist_prey = d
                        
            if best_prey:
                if min_dist_prey < self.radius + best_prey.radius:
                    best_prey.alive = False
                    self.hunger = max(0, self.hunger - 60) # Naje se
                else:
                    self.move_towards(best_prey.x, best_prey.y, self.speed)
            else:
                self.move_towards(self.x + random.uniform(-10,10), self.y + random.uniform(-10,10), self.speed * 0.5)
        else:
            self.move_towards(self.x + random.uniform(-10,10), self.y + random.uniform(-10,10), self.speed * 0.5)

class Clover(Agent):
    """Plant/Clover. Static agent that drinks if water in range, breeds slowly."""
    def __init__(self, x: float, y: float):
        # speed=0, size=0.5, large sense range to find water
        super().__init__(x, y, speed=0.0, size=0.5, sense=100.0)
        self.color = COLOR_FOOD
        self.max_age = random.randint(800, 1200)

    @property
    def radius(self):
        return 3 # fixed visual size for food

    def act(self, terrain, entities):
        if not self.alive: return
        
        pri = self.get_priority()
        
        if pri == "thirst":
            # Detelja ne ugasne zeje ce nima vode v svojem rangu. Njen movement je 0.
            for wx, wy, wr in terrain.water_bodies:
                if math.hypot(wx - self.x, wy - self.y) - wr < self.sense:
                    self.thirst = max(0, self.thirst - 50)
                    break 
                    
        elif pri == "reproduction":
            pass # Stub: later we can spawn new Clover nearby

# ─────────────────────────────────────────────────────────────────────────────
# 3.  SIMULATION ENGINE
# ─────────────────────────────────────────────────────────────────────────────

class SimThread(threading.Thread):
    def __init__(self, data_queue: queue.Queue, n_prey: int, n_pred: int, n_food: int, init_params: dict, speed_entry: tk.Entry):
        super().__init__(daemon=True)
        self.q = data_queue
        self.n_prey = n_prey
        self.n_pred = n_pred
        self.n_food = n_food
        self.init_params = init_params
        self._speed_entry = speed_entry

        self._running = True
        self._paused  = threading.Event()
        self._paused.set()

        self.terrain = Terrain(SIM_WIDTH, SIM_HEIGHT)
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
        except: pass
        return float(DEFAULT_SIM_SPEED)

    def _spawn(self):
        self.agents = []
        for _ in range(self.n_food):
            self.agents.append(Clover(random.uniform(10, SIM_WIDTH-10), random.uniform(10, SIM_HEIGHT-10)))
        for _ in range(self.n_prey):
            self.agents.append(Prey(random.uniform(0, SIM_WIDTH), random.uniform(0, SIM_HEIGHT), 
                                    self.init_params['speed'], self.init_params['size'], self.init_params['sense']))
        for _ in range(self.n_pred):
            self.agents.append(Predator(random.uniform(0, SIM_WIDTH), random.uniform(0, SIM_HEIGHT), 
                                        self.init_params['speed']*1.1, self.init_params['size']*1.2, self.init_params['sense']*1.2))

    def _step(self):
        self.ticks += 1
        for ag in self.agents:
            if ag.alive:
                ag.update_needs()
                ag.act(self.terrain, self.agents)
        
        # Clean up dead
        self.agents = [a for a in self.agents if a.alive]
        
        # Grow some food over time (spontaneous generation placeholder)
        food_count = sum(1 for a in self.agents if isinstance(a, Clover))
        if self.ticks % 20 == 0 and food_count < self.n_food:
            self.agents.append(Clover(random.uniform(10, SIM_WIDTH-10), random.uniform(10, SIM_HEIGHT-10)))

    def _send_payload(self):
        payload = {
            'ticks': self.ticks,
            'terrain_water': self.terrain.water_bodies,
            'agents': [(
                ag.x, ag.y, ag.radius, ag.color, ag.alive, ag.sense, ag.sex, ag.get_priority(),
                ag.hunger, ag.thirst, getattr(ag, 'max_age', 100), getattr(ag, 'age', 0),
                type(ag).__name__
            ) for ag in self.agents],
            'active_cnt': len(self.agents)
        }
        if self.q.qsize() < QUEUE_MAX:
            self.q.put(payload)
# ─────────────────────────────────────────────────────────────────────────────
# 4.  UI COMPONENTS
# ─────────────────────────────────────────────────────────────────────────────

class ParamEntry(tk.Frame):
    """Helper for a labelled entry."""
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
        self.title("EcoSim MVP - Lisica, Zajec, Detelja")

        self.sim = None
        self.q = queue.Queue()
        self._restarted = False
        self._last_payload = None
        
        # Panning
        self.pan_x = 0
        self.pan_y = 0
        self._drag_start_x = 0
        self._drag_start_y = 0

        self._build_ui()

    # ── UI construction ───────────────────────────────────────────────────────
    def _build_ui(self):
        root = tk.Frame(self, padx=10, pady=10)
        root.pack(fill=tk.BOTH, expand=True)

        top = tk.Frame(root)
        top.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # simulation canvas - increased target area
        self.sim_canvas = tk.Canvas(top, width=SIM_WIDTH, height=SIM_HEIGHT,
                                    bg="#1a1a2e", relief=tk.SUNKEN, bd=1)
        self.sim_canvas.pack(side=tk.LEFT, padx=5, fill=tk.BOTH, expand=True)

        self.sim_canvas.bind("<ButtonPress-1>", self._on_drag_start)
        self.sim_canvas.bind("<B1-Motion>", self._on_drag_motion)

        # control panel
        self.ctrl = tk.LabelFrame(root, text=" Simulation control ", padx=10, pady=8)
        self.ctrl.pack(side=tk.BOTTOM, fill=tk.X, pady=8)

        self._build_buttons()
        self._build_settings()

        self.lbl_info = tk.Label(root, text="Ticks: 0 | Plen: 0 | Plenilci: 0",
                                 font=("Arial", 9, "bold"))
        self.lbl_info.pack(side=tk.BOTTOM, anchor="e")

    def _build_buttons(self):
        bar = tk.Frame(self.ctrl)
        bar.pack(fill=tk.X)

        self.btn_start = tk.Button(bar, text="START", bg="#ccffcc", width=12, command=self.start)
        self.btn_start.pack(side=tk.LEFT, padx=2)

        self.btn_pause = tk.Button(bar, text="PAUSE", state=tk.DISABLED, width=12, command=self.toggle_pause)
        self.btn_pause.pack(side=tk.LEFT, padx=2)

        self.btn_restart = tk.Button(bar, text="RESTART", bg="#ffcccc", state=tk.DISABLED, width=12, command=self.restart)
        self.btn_restart.pack(side=tk.LEFT, padx=2)

        tk.Label(bar, text="Hitrost (s):").pack(side=tk.LEFT, padx=(20, 2))
        self.ent_speed = tk.Entry(bar, width=6)
        self.ent_speed.insert(0, DEFAULT_SIM_SPEED)
        self.ent_speed.pack(side=tk.LEFT)

    def _build_settings(self):
        outer = tk.Frame(self.ctrl, bd=1, relief=tk.SUNKEN, pady=5)
        outer.pack(fill=tk.X, pady=6)

        row0 = tk.Frame(outer)
        row0.pack(fill=tk.X, pady=2)
        
        tk.Label(row0, text="Teren:").pack(side=tk.LEFT, padx=5)
        from tkinter import ttk
        self.cb_terrain = ttk.Combobox(row0, values=["Reka", "Jezero", "Več jezer", "Otočje", "Naključen (Perlin)"])
        self.cb_terrain.current(0)
        self.cb_terrain.pack(side=tk.LEFT, padx=5)
        
        self.var_debug = tk.BooleanVar(value=False)
        tk.Checkbutton(row0, text="Prikaži Debug", variable=self.var_debug).pack(side=tk.LEFT, padx=15)

        row1 = tk.Frame(outer)
        row1.pack(fill=tk.X, pady=2)

        self.p_nprey   = ParamEntry(row1, "Št. Zajcev", DEFAULT_N_AGENTS)
        self.p_npred   = ParamEntry(row1, "Št. Lisic", DEFAULT_N_PRED)
        self.p_nfood   = ParamEntry(row1, "Hrana", DEFAULT_N_FOOD)

        row2 = tk.Frame(outer)
        row2.pack(fill=tk.X, pady=2)

        self.p_speed  = ParamEntry(row2, "Začetna hitrost", DEFAULT_SPEED)
        self.p_size   = ParamEntry(row2, "Začetna velikost", DEFAULT_SIZE)
        self.p_sense  = ParamEntry(row2, "Začetni vid", DEFAULT_SENSE)
        self.p_mut    = ParamEntry(row2, "Možnost mutacije (0-1)", DEFAULT_MUT_PROB)

    # ── Map Panning  ──────────────────────────────────────────────────────────
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

    # ── simulation control ────────────────────────────────────────────────────

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

        for p in [self.p_nprey, self.p_npred, self.p_nfood, self.p_speed, self.p_size, self.p_sense]:
            p.set_state(state)

    def start(self):
        self._restarted = False
        try:
            n_prey = int(self.p_nprey.get())
            n_pred = int(self.p_npred.get())
            n_food = int(self.p_nfood.get())

            init_params = {
                'speed': float(self.p_speed.get()),
                'size':  float(self.p_size.get()),
                'sense': float(self.p_sense.get()),
                'mut_prob': float(self.p_mut.get())
            }
        except ValueError:
            print("Neveljavni podatki!")
            return

        self.sim = SimThread(
            data_queue = self.q,
            n_prey     = n_prey,
            n_pred     = n_pred,
            n_food     = n_food,
            init_params = init_params,
            speed_entry = self.ent_speed
        )
        self.sim.start()
        self._set_ui_running(True)
        self._poll_queue()

    def toggle_pause(self):
        if self.sim is None:
            return
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
            try: self.q.get_nowait()
            except queue.Empty: break

        self._last_payload = None
        self.sim_canvas.delete("all")
        self.lbl_info.config(text="Ticks: 0 | Plen: 0 | Plenilci: 0")
        self._set_ui_running(False)

    # ── render loops ──────────────────────────────────────────────────────────

    def _poll_queue(self):
        if self._restarted: return

        latest = None
        try:
            while True: latest = self.q.get_nowait()
        except queue.Empty: pass

        if latest is not None:
            self._last_payload = latest
            self._draw_sim(latest)
            self._update_info(latest)

        self.after(SIM_REFRESH_MS, self._poll_queue)

    def _draw_sim(self, payload: dict):
        self.sim_canvas.delete("all")
        
        px, py = self.pan_x, self.pan_y

        # Narisi vodo
        for wx, wy, wr in payload.get('terrain_water', []):
            self.sim_canvas.create_oval(wx + px - wr, wy + py - wr, wx + px + wr, wy + py + wr,
                                        fill="#3498db", outline="#2980b9", tags="terrain")

        debug = self.var_debug.get()

        for (ax, ay, ar, col, alive, sense, sex, prio, 
             hunger, thirst, max_age, age, cls_name) in payload['agents']:
            cx, cy = ax + px, ay + py
            
            if alive:
                if debug:
                    if cls_name != "Clover":
                        # Risanje vidnega polja zgolj za premikajoca ziva bitja,
                        # sicer bo od detelj pregosto
                        self.sim_canvas.create_oval(cx - sense, cy - sense, cx + sense, cy + sense,
                                                    outline="#444444", width=1, dash=(2, 4), tags="debug")

                        # Hunger bar (red)
                        hw = 12
                        hp = min(1.0, hunger / 100.0)
                        self.sim_canvas.create_rectangle(cx - hw/2, cy - ar - 10, cx + hw/2, cy - ar - 8, fill="#555", outline="", tags="debug")
                        self.sim_canvas.create_rectangle(cx - hw/2, cy - ar - 10, cx - hw/2 + hw*hp, cy - ar - 8, fill="red", outline="", tags="debug")
                        
                        # Thirst bar (blue)
                        tp = min(1.0, thirst / 100.0)
                        self.sim_canvas.create_rectangle(cx - hw/2, cy - ar - 7, cx + hw/2, cy - ar - 5, fill="#555", outline="", tags="debug")
                        self.sim_canvas.create_rectangle(cx - hw/2, cy - ar - 7, cx - hw/2 + hw*tp, cy - ar - 5, fill="cyan", outline="", tags="debug")

                        # Text
                        self.sim_canvas.create_text(cx, cy - ar - 16, text=f"[{sex}] {prio}", 
                                                    fill="white", font=("Arial", 7), tags="debug")
                                                
                self.sim_canvas.create_oval(cx - ar, cy - ar, cx + ar, cy + ar,
                                            fill=col, outline="black", width=1, tags="agents")

    def _update_info(self, payload: dict):
        active_cnt = payload.get('active_cnt', 0)
        ticks = payload.get('ticks', 0)
        self.lbl_info.config(text=f"Tiki: {ticks} | Preživetih agentov: {active_cnt}")


if __name__ == "__main__":
    app = App()
    app.mainloop()
