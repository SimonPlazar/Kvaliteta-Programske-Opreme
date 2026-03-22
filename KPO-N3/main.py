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
SIM_SIZE      = 450     # simulation canvas width & height (px)
BORDER_W      = 25      # spawn/return zone thickness (px)
AGENT_R_BASE  = 4       # base agent radius
FOOD_R        = 5       # food circle radius (px)

# ── simulation ────────────────────────────────────────────────────────────────
QUEUE_MAX          = 100
DEFAULT_N_AGENTS   = "30"
DEFAULT_N_FOOD     = "40"
DEFAULT_E_CAP      = "2000"
DEFAULT_SPEED      = "2.0"
DEFAULT_SIZE       = "1.0"
DEFAULT_SENSE      = "50.0"

DEFAULT_SIM_SPEED  = "0.01"
DEFAULT_CHART_RATE = "0.5"
SIM_REFRESH_MS     = 30
CHART_REFRESH_MIN_MS      = 50
CHART_REFRESH_FALLBACK_MS = 500
MAX_HISTORY        = 500

# ── generation phases ─────────────────────────────────────────────────────────
PHASE_SPAWN    = 0
PHASE_DAY      = 1
PHASE_END      = 2

PHASE_NAMES = {
    PHASE_SPAWN:    "Spawn",
    PHASE_DAY:      "Day (Survival)",
    PHASE_END:      "End of generation",
}

# ── chart ─────────────────────────────────────────────────────────────────────
CHART_OX       = 50
CHART_OY       = 400
CHART_W        = 350
CHART_H        = 350
CHART_X_END    = 410
CHART_Y_END    = 40
HOVER_FPS_MS   = 16
HOVER_DOT_R    = 4
HOVER_LINE_DY  = 13
MAX_CHART_PTS  = 400

# ── ui ────────────────────────────────────────────────────────────────────────
CHART_SIZE = 450


# ─────────────────────────────────────────────────────────────────────────────
# 1.  MODELS
# ─────────────────────────────────────────────────────────────────────────────

class Agent:
    """Evolutionary agent with Energy, Size, Speed, Sense."""

    def __init__(self, x: float, y: float, speed: float, size: float, sense: float, energy_cap: float):
        self.x = x
        self.y = y
        
        # Traits (Genome)
        self.speed_trait = max(0.5, speed)
        self.size_trait = max(0.5, size)
        self.sense_trait = max(10.0, sense)
        self.energy_cap = energy_cap

        # State
        self.energy = energy_cap
        self.food_eaten = 0
        self.alive = True
        self.safe = False  # True if returned to border
        self.color = COLOR_AGENT

    @property
    def radius(self):
        # Base size + 1px per integer step of size_trait
        return AGENT_R_BASE + int(self.size_trait - 1.0)

    def mutate(self, mut_prob=0.3):
        """Return a new agent with slightly mutated traits."""
        # Mutation factor: +/- 10%
        def mutate_val(v):
            if random.random() < mut_prob: 
                return v * random.uniform(0.9, 1.1)
            return v
            
        new_speed = mutate_val(self.speed_trait)
        new_size = mutate_val(self.size_trait)
        new_sense = mutate_val(self.sense_trait)
        
        return Agent(self.x, self.y, new_speed, new_size, new_sense, self.energy_cap)

    def consume_energy(self):
        # Formula: size^3 * speed^2 + sense
        # Scaled down to be reasonable per tick
        cost = (pow(self.size_trait, 3) * pow(self.speed_trait, 2) + self.sense_trait) * 0.05
        self.energy -= cost
        if self.energy <= 0:
            self.alive = False
            self.energy = 0

    def move(self, dx, dy, speed_limit):
        if not self.alive or self.safe:
            return
            
        dist = math.hypot(dx, dy)
        if dist > 0:
            step = min(dist, speed_limit)
            self.x += (dx / dist) * step
            self.y += (dy / dist) * step
            
            # Clamp to world
            self.x = max(0, min(SIM_SIZE, self.x))
            self.y = max(0, min(SIM_SIZE, self.y))

    def check_border(self, border_w, sim_size):
        """Check if inside the safe border zone."""
        if (self.x < border_w or self.x > sim_size - border_w or
            self.y < border_w or self.y > sim_size - border_w):
            return True
        return False


class Food:
    """Simple food bit."""
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y


# ─────────────────────────────────────────────────────────────────────────────
# 3.  SIMULATION ENGINE
# ─────────────────────────────────────────────────────────────────────────────

def _random_border_point(size: int, border: int) -> tuple[float, float]:
    """Random point on the inner edge of the border zone."""
    side = random.randint(0, 3)
    if side == 0: return float(random.randint(0, size)), float(random.randint(0, border))
    if side == 1: return float(random.randint(0, size)), float(random.randint(size - border, size))
    if side == 2: return float(random.randint(0, border)), float(random.randint(0, size))
    return       float(random.randint(size - border, size)), float(random.randint(0, size))

def _random_inner_point(size: int, border: int) -> tuple[float, float]:
    """Random point strictly inside the field (away from border)."""
    margin = border + FOOD_R + 5
    return (float(random.randint(margin, size - margin)),
            float(random.randint(margin, size - margin)))


class SimThread(threading.Thread):
    """
    Simulation loop:
    1. Spawn Food & Reset Agents
    2. Day Loop: Move, Eat, Interact until all safe or dead
    3. Reproduction / Mutation
    """

    def __init__(self, data_queue: queue.Queue, 
                 n_agents: int, n_food: int, 
                 decreasing_food: bool,
                 init_params: dict,
                 speed_entry: tk.Entry):
        super().__init__(daemon=True)
        self.q        = data_queue
        self.n_agents = n_agents
        self.n_food   = n_food
        self.decreasing_food = decreasing_food
        self.init_params = init_params
        self._speed_entry = speed_entry

        self._running = True
        self._paused  = threading.Event()
        self._paused.set()

        self.agents: list[Agent] = []
        self.food:   list[Food]  = []
        self.phase:  int         = PHASE_SPAWN
        self.generation: int     = 0
        # History: gen, avg_speed, avg_size, avg_sense
        self.history: list[tuple[int, float, float, float]] = []

    # ── public interface ──────────────────────────────────────────────────────

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

    # ── main loop ─────────────────────────────────────────────────────────────

    def run(self):
        # Create initial population
        self.agents = []
        base_size = self.init_params['size']
        
        for _ in range(self.n_agents):
            # Randomize initial size: base +/- 0.5
            s_val = max(0.1, base_size + random.uniform(-0.5, 0.5))
            
            ag = Agent(*_random_border_point(SIM_SIZE, BORDER_W),
                    self.init_params['speed'],
                    s_val,
                    self.init_params['sense'],
                    self.init_params['energy'])
            self.agents.append(ag)

        while self._running:
            self._paused.wait()
            if not self._running:
                break
                
            self._step()
            self._send_payload()
            time.sleep(self._get_speed())

    def _get_speed(self) -> float:
        try:
            val = float(self._speed_entry.get())
            if val > 0:
                return val
        except (ValueError, tk.TclError):
            pass
        return float(DEFAULT_SIM_SPEED)

    # ── phase dispatcher ──────────────────────────────────────────────────────

    def _step(self):
        if self.phase == PHASE_SPAWN:
            self._phase_spawn()
            self.phase = PHASE_DAY
        
        elif self.phase == PHASE_DAY:
            if self._phase_day_tick():
                self.phase = PHASE_END
                
        elif self.phase == PHASE_END:
            self._phase_end()
            self.phase = PHASE_SPAWN

    # ── phases ────────────────────────────────────────────────────────────────

    def _phase_spawn(self):
        """Prepare map for the day."""
        # Calculate food count
        current_food = self.n_food
        if self.decreasing_food and self.generation > 0:
             # Decrease by 1 per gen, minimum 10
             current_food = max(10, self.n_food - self.generation)
        
        self.food = [Food(*_random_inner_point(SIM_SIZE, BORDER_W)) for _ in range(current_food)]
        
        # Reset agents to border and energy
        for ag in self.agents:
            ag.x, ag.y = _random_border_point(SIM_SIZE, BORDER_W)
            ag.energy = ag.energy_cap
            ag.food_eaten = 0
            ag.alive = True
            ag.safe = False
            ag.color = COLOR_AGENT

    def _phase_day_tick(self) -> bool:
        """
        One tick of simulation. 
        Returns True if day is over (all agents Dead or Safe).
        """
        active_count = 0
        
        # Shuffle for fairness
        random.shuffle(self.agents)
        
        for ag in self.agents:
            if not ag.alive or ag.safe:
                continue
            
            active_count += 1
            ag.consume_energy()
            
            if not ag.alive:
                ag.color = COLOR_AGENT_DEAD
                continue

            # Logic:
            # 1. Perception
            # 2. Decision: Flee, Forage, or Return
            
            targets = []
            
            # -- Scan surroundings --
            # Find nearest food
            nearest_food = None
            min_dist_food = float('inf')
            for f in self.food:
                d = math.hypot(f.x - ag.x, f.y - ag.y)
                if d <= ag.sense_trait and d < min_dist_food:
                    min_dist_food = d
                    nearest_food = f
            
            # Find nearest predator (larger agent)
            nearest_predator = None
            min_dist_pred = float('inf')
            
            # Find nearest prey (smaller agent)
            nearest_prey = None
            min_dist_prey = float('inf')

            for other in self.agents:
                if other is ag or not other.alive or other.safe:
                    continue
                d = math.hypot(other.x - ag.x, other.y - ag.y)
                if d <= ag.sense_trait:
                    # Predator check: Other is > 20% larger
                    if other.size_trait > ag.size_trait * 1.2:
                        if d < min_dist_pred:
                            min_dist_pred = d
                            nearest_predator = other
                    # Prey check: Other is < 20% smaller (ag is > 1.25 * other)
                    elif ag.size_trait > other.size_trait * 1.2:
                        if d < min_dist_prey:
                            min_dist_prey = d
                            nearest_prey = other

            # -- Decision Making --
            
            dx, dy = 0, 0
            move_speed = ag.speed_trait
            
            # PRIORITY 1: Flee from predator
            if nearest_predator:
                # Run away
                dx = ag.x - nearest_predator.x
                dy = ag.y - nearest_predator.y
            
            # PRIORITY 2: Return to safe zone if satisfied or energy critical
            # Satisfied if 2 food. Or 1 food and energy is getting low (heuristic: < 30%)
            elif ag.food_eaten >= 2 or (ag.food_eaten >= 1 and ag.energy < ag.energy_cap * 0.3):
                # Move to nearest border point
                # Simple logic: move towards closest wall
                d_left, d_right = ag.x, SIM_SIZE - ag.x
                d_top, d_bottom = ag.y, SIM_SIZE - ag.y
                mn = min(d_left, d_right, d_top, d_bottom)
                if mn == d_left:   dx = -1
                elif mn == d_right: dx = 1
                elif mn == d_top:   dy = -1
                else:              dy = 1
            
            # PRIORITY 3: Hunt / Forage
            elif nearest_food:
                dx = nearest_food.x - ag.x
                dy = nearest_food.y - ag.y
            
            elif nearest_prey:
                dx = nearest_prey.x - ag.x
                dy = nearest_prey.y - ag.y
                
            else:
                # Random walk / momentum
                # For simplicity, move towards center slightly + random jitter
                dx = (SIM_SIZE/2 - ag.x) * 0.1 + random.uniform(-20, 20)
                dy = (SIM_SIZE/2 - ag.y) * 0.1 + random.uniform(-20, 20)

            # Check if entering safe zone
            if ag.check_border(BORDER_W, SIM_SIZE):
                # If no food, border doesn't save you yet
                if ag.food_eaten > 0:
                    ag.safe = True
                    ag.color = COLOR_AGENT_SAFE
                    continue

            ag.move(dx, dy, move_speed)
            
            # Interactions
            # Eat food?
            if not ag.safe:
                # Food collision
                for f in self.food[:]:
                    if math.hypot(f.x - ag.x, f.y - ag.y) < (ag.radius + FOOD_R):
                        self.food.remove(f)
                        ag.food_eaten += 1
                        ag.energy += ag.energy_cap * 0.2 # Small refill for eating? (optional, not in prompt, but helpful)
                
                # Eat Prey?
                if nearest_prey and min_dist_prey < (ag.radius + nearest_prey.radius):
                    # Collision
                    nearest_prey.alive = False
                    nearest_prey.color = COLOR_AGENT_DEAD
                    ag.food_eaten += 1
                    ag.energy += ag.energy_cap * 0.4 # Big reward

        return active_count == 0

    def _phase_end(self):
        """Evolution step."""
        survivors = []
        offspring = []
        
        total_speed = 0
        total_size = 0
        total_sense = 0
        count = 0
        
        for ag in self.agents:
            if ag.safe and ag.alive and ag.food_eaten >= 1:
                survivors.append(ag)
                total_speed += ag.speed_trait
                total_size += ag.size_trait
                total_sense += ag.sense_trait
                count += 1
                
                # Reproduce if 2+ food
                if ag.food_eaten >= 2:
                    child = ag.mutate(self.init_params.get('mut_prob', 0.3))
                    child.x, child.y = ag.x, ag.y
                    offspring.append(child)
        
        # Stats
        if count > 0:
            avg_speed = total_speed / count
            avg_size = total_size / count
            avg_sense = total_sense / count
        else:
            avg_speed = avg_size = avg_sense = 0
            
        self.history.append((self.generation, avg_speed, avg_size, avg_sense))
        if len(self.history) > MAX_HISTORY:
            self.history.pop(0)
            
        # Setup next gen
        self.agents = survivors + offspring
        self.generation += 1
        
        # Extinction check
        if len(self.agents) == 0:
            # Restart with defaults? Or just leave empty.
            pass

    # ── payload ───────────────────────────────────────────────────────────────

    def _send_payload(self):
        payload = {
            'phase':      self.phase,
            'phase_name': PHASE_NAMES.get(self.phase, ''),
            'generation': self.generation,
            # Schema: x, y, radius, color, alive, sense, energy, max_energy
            'agents':     [(ag.x, ag.y, ag.radius, ag.color, ag.alive, ag.sense_trait, ag.energy, ag.energy_cap) for ag in self.agents],
            'food':       [(f.x, f.y) for f in self.food],
            'history':    list(self.history),
            'active_cnt': sum(1 for a in self.agents if a.alive and not a.safe)
        }
        if self.q.qsize() < QUEUE_MAX:
            self.q.put(payload)

# ─────────────────────────────────────────────────────────────────────────────
# 4.  UI COMPONENTS
# ─────────────────────────────────────────────────────────────────────────────

class Chart(tk.Canvas):
    """
    Population traits chart.
    Series: Speed (Red), Size (Blue), Sense (Green)
    """

    _SERIES = [
        ('Speed', "#e03131", "Avg Speed"),
        ('Size',  "#3a7bd5", "Avg Size"),
        ('Sense', "#2ecc71", "Avg Sense (/10)"), # Divide sense by 10 to fit scale better?
    ]

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.ox, self.oy = CHART_OX, CHART_OY
        self.w,  self.h  = CHART_W,  CHART_H
        self._line_refs: dict[str, list] = {'Speed': [], 'Size': [], 'Sense': []}
        self._mouse      = (None, None)
        self._last_hist:  list[tuple]  = []
        self._last_scale = None

        self.bind("<Motion>", lambda e: self._on_mouse(e.x, e.y))
        self.bind("<Leave>",  lambda e: self._on_leave())
        self._draw_axes()
        self._hover_loop()

    def _draw_axes(self):
        self.delete("axis")
        self.create_line(self.ox, self.oy, self.ox, CHART_Y_END, arrow=tk.LAST, tags="axis")
        self.create_line(self.ox, self.oy, CHART_X_END, self.oy,  arrow=tk.LAST, tags="axis")
        self.create_text(self.ox - 20, CHART_Y_END,   text="Val",    tags="axis")
        self.create_text(CHART_X_END,  self.oy + 20,  text="Gen", tags="axis")
        # legend
        self.delete("legend")
        for i, (_, color, label) in enumerate(self._SERIES):
            lx, ly = CHART_OX + i * 100, 14
            self.create_rectangle(lx, ly - 5, lx + 12, ly + 5, fill=color, outline=color, tags="legend")
            self.create_text(lx + 16, ly, text=label, anchor="w", font=("Arial", 8), tags="legend")

    def reset(self):
        self.delete("all")
        self._line_refs  = {'Speed': [], 'Size': [], 'Sense': []}
        self._last_hist  = []
        self._last_scale = None
        self._draw_axes()

    def update_chart(self, history: list[tuple[int, float, float, float]]):
        if not history:
            return
        self._last_hist = list(history)

        if len(history) == 1:
            history = [history[0], history[0]]

        gens = [p[0] for p in history]
        # Normalize sense for display (stats are stored raw, but sense is ~50-100 vs speed ~2-5)
        # To make it readable, we display Sense/10.
        
        # Prepare data series
        spd = [p[1] for p in history]
        siz = [p[2] for p in history]
        sen = [p[3]/10.0 for p in history]
        
        all_vals = spd + siz + sen
        min_t, max_t = min(gens), max(gens)
        if max_t == min_t: max_t = min_t + 1
        
        max_y = max(all_vals) if all_vals else 1
        pad   = max(max_y * 0.1, 0.5)
        
        scale = (min_t, max_t, 0.0, max_y + pad)
        self._last_scale = scale

        # Draw Speed
        self._draw_series('Speed', self._to_canvas([(p[0], p[1]) for p in history], *scale), self._SERIES[0][1])
        # Draw Size
        self._draw_series('Size',  self._to_canvas([(p[0], p[2]) for p in history], *scale), self._SERIES[1][1])
        # Draw Sense
        self._draw_series('Sense', self._to_canvas([(p[0], p[3]/10.0) for p in history], *scale), self._SERIES[2][1])

    def _to_canvas(self, data, min_t, max_t, min_y, max_y):
        rt, ry = max_t - min_t, max_y - min_y
        if ry == 0: ry = 1
        if len(data) > MAX_CHART_PTS:
            k    = len(data) / MAX_CHART_PTS
            data = [data[int(j * k)] for j in range(MAX_CHART_PTS)]
        return [(self.ox + ((t - min_t) / rt) * self.w,
                 self.oy - ((n - min_y) / ry) * self.h) for t, n in data]

    def _draw_series(self, key: str, pts: list, color: str):
        lines    = self._line_refs[key]
        segments = len(pts) - 1
        for j in range(segments):
            c = (*pts[j], *pts[j + 1])
            if j < len(lines):
                self.coords(lines[j], *c)
            else:
                lines.append(self.create_line(*c, fill=color, width=2, tags="series"))
        for j in range(segments, len(lines)):
            self.delete(lines[j])
        self._line_refs[key] = lines[:segments]

    # ── hover ─────────────────────────────────────────────────────────────────

    def _on_mouse(self, x, y): self._mouse = (x, y)
    def _on_leave(self):
        self._mouse = (None, None)
        self.delete("hover")

    def _hover_loop(self):
        self._update_hover()
        self.after(HOVER_FPS_MS, self._hover_loop)

    def _update_hover(self):
        self.delete("hover")
        mx, my = self._mouse
        if mx is None or not self._last_scale or not self._last_hist:
            return
        if not (self.ox <= mx <= self.ox + self.w):
            return

        min_t, max_t, min_y, max_y = self._last_scale
        rt, ry = max_t - min_t, max_y - min_y
        t_cursor = min_t + ((mx - self.ox) / self.w) * rt

        self.create_line(mx, self.oy - self.h, mx, self.oy,
                         fill="#aaaaaa", dash=(4, 4), tags="hover")

        nearest = min(self._last_hist, key=lambda p: abs(p[0] - t_cursor))
        gen, s, z, e = nearest # speed, size, sense

        # Draw dots for Speed, Size, Sense with scaling
        vals = [s, z, e/10.0]
        
        for idx, (_, color, _) in enumerate(self._SERIES):
            val = vals[idx]
            px  = self.ox + ((gen - min_t) / rt) * self.w
            py  = self.oy - ((val - min_y) / ry) * self.h
            r   = HOVER_DOT_R
            self.create_oval(px - r, py - r, px + r, py + r,
                             fill=color, outline="white", tags="hover")

        # tooltip
        lines = [
            (self._SERIES[0][1], f"Speed: {s:.2f}"), 
            (self._SERIES[1][1], f"Size:  {z:.2f}"),
            (self._SERIES[2][1], f"Sense: {e:.1f}")
        ]
        tx = mx + 12
        ty = my - 10 - len(lines) * HOVER_LINE_DY
        self.create_text(tx, ty, text=f"Gen {gen}",
                         fill="#333333", anchor="w", font=("Arial", 8, "bold"), tags="hover")
        for j, (col, txt) in enumerate(lines):
            self.create_text(tx, ty + HOVER_LINE_DY * (j + 1), text=txt,
                             fill=col, anchor="w", font=("Arial", 8, "bold"), tags="hover")




# ─────────────────────────────────────────────────────────────────────────────
# 5.  APPLICATION CONTROLLER
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
        self.title("Evolution Sim - Traits")

        self.sim:           SimThread | None = None
        self.q:             queue.Queue      = queue.Queue()
        self._restarted     = False
        self._last_payload: dict | None      = None

        self._build_ui()

    # ── UI construction ───────────────────────────────────────────────────────
    def _build_ui(self):
        root = tk.Frame(self, padx=10, pady=10)
        root.pack(fill=tk.BOTH, expand=True)

        top = tk.Frame(root)
        top.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # simulation canvas
        self.sim_canvas = tk.Canvas(top, width=SIM_SIZE, height=SIM_SIZE,
                                    bg="#1a1a2e", relief=tk.SUNKEN, bd=1)
        self.sim_canvas.pack(side=tk.LEFT, padx=5)
        self._draw_border()

        # chart
        self.chart = Chart(top, width=CHART_SIZE, height=CHART_SIZE,
                           bg="#fdfdfd", relief=tk.SUNKEN, bd=1)
        self.chart.pack(side=tk.RIGHT, padx=5)

        # control panel
        self.ctrl = tk.LabelFrame(root, text=" Simulation control ", padx=10, pady=8)
        self.ctrl.pack(side=tk.BOTTOM, fill=tk.X, pady=8)

        self._build_buttons()
        self._build_settings()

        self.lbl_info = tk.Label(root, text="Gen: 0 | Agents: 0 | Phase: —",
                                 font=("Arial", 9, "bold"))
        self.lbl_info.pack(side=tk.BOTTOM, anchor="e")

    def _draw_border(self):
        s, r = SIM_SIZE, BORDER_W
        self.sim_canvas.create_rectangle(r, r, s - r, s - r,
                                         outline=COLOR_BORDER, dash=(4, 4), tags="border")
        # Visual hint for safe zone
        self.sim_canvas.create_text(s/2, r/2, text="SAFE ZONE", fill="#555555", font=("Arial", 8))

    def _build_buttons(self):
        bar = tk.Frame(self.ctrl)
        bar.pack(fill=tk.X)

        self.btn_start = tk.Button(bar, text="START", bg="#ccffcc", width=12,
                                   command=self.start)
        self.btn_start.pack(side=tk.LEFT, padx=2)

        self.btn_pause = tk.Button(bar, text="PAUSE", state=tk.DISABLED, width=12,
                                   command=self.toggle_pause)
        self.btn_pause.pack(side=tk.LEFT, padx=2)

        self.btn_restart = tk.Button(bar, text="RESTART", bg="#ffcccc", state=tk.DISABLED, width=12,
                                     command=self.restart)
        self.btn_restart.pack(side=tk.LEFT, padx=2)

        tk.Label(bar, text="Sim speed (s):").pack(side=tk.LEFT, padx=(20, 2))
        self.ent_speed = tk.Entry(bar, width=6)
        self.ent_speed.insert(0, DEFAULT_SIM_SPEED)
        self.ent_speed.pack(side=tk.LEFT)

        tk.Label(bar, text="Chart refresh (s):").pack(side=tk.LEFT, padx=(15, 2))
        self.ent_chart_rate = tk.Entry(bar, width=6)
        self.ent_chart_rate.insert(0, DEFAULT_CHART_RATE)
        self.ent_chart_rate.pack(side=tk.LEFT)

    def _build_settings(self):
        outer = tk.Frame(self.ctrl, bd=1, relief=tk.SUNKEN, pady=5)
        outer.pack(fill=tk.X, pady=6)
        
        # Row 1: Population & Food
        row1 = tk.Frame(outer)
        row1.pack(fill=tk.X, pady=2)
        
        self.p_nagents = ParamEntry(row1, "Initial Agents", DEFAULT_N_AGENTS)
        self.p_nfood   = ParamEntry(row1, "Food / Gen", DEFAULT_N_FOOD)
        
        self.var_decreasing = tk.BooleanVar(value=False)
        cb = tk.Checkbutton(row1, text="Decrease Food (-1/gen)", variable=self.var_decreasing)
        cb.pack(side=tk.LEFT, padx=20, pady=10)

        self.var_debug = tk.BooleanVar(value=False)
        cb_debug = tk.Checkbutton(row1, text="Debug View", variable=self.var_debug)
        cb_debug.pack(side=tk.LEFT, padx=10, pady=10)

        # Row 2: Traits
        row2 = tk.Frame(outer)
        row2.pack(fill=tk.X, pady=2)
        
        self.p_speed  = ParamEntry(row2, "Base Speed", DEFAULT_SPEED)
        self.p_size   = ParamEntry(row2, "Base Size", DEFAULT_SIZE)
        self.p_sense  = ParamEntry(row2, "Base Sense", DEFAULT_SENSE)
        self.p_energy = ParamEntry(row2, "Base Energy", DEFAULT_E_CAP)
        self.p_mut_prob = ParamEntry(row2, "Mut. Chance", "0.3")

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
            
        for p in [self.p_nagents, self.p_nfood, self.p_speed, 
                  self.p_size, self.p_sense, self.p_energy, self.p_mut_prob]:
             p.set_state(state)

    def start(self):
        self._restarted = False
        try:
            n_ag = int(self.p_nagents.get())
            n_fd = int(self.p_nfood.get())
            
            init_params = {
                'speed': float(self.p_speed.get()),
                'size':  float(self.p_size.get()),
                'sense': float(self.p_sense.get()),
                'energy': float(self.p_energy.get()),
                'mut_prob': float(self.p_mut_prob.get())
            }
        except ValueError:
            print("Invalid input")
            return

        self.sim = SimThread(
            data_queue = self.q,
            n_agents   = n_ag,
            n_food     = n_fd,
            decreasing_food = self.var_decreasing.get(),
            init_params = init_params,
            speed_entry = self.ent_speed
        )
        self.sim.start()
        self._set_ui_running(True)
        self._poll_queue()
        self._refresh_chart()
    
    def toggle_pause(self):
        if self.sim is None:
            return
        if self.sim.is_paused:
            self.sim.resume()
            self.btn_pause.config(text="PAUSE")
        else:
            self.sim.pause()
            self.btn_pause.config(text="RESUME")
    
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
        self._draw_border()
        self.chart.reset()
        self.lbl_info.config(text="Gen: 0 | Agents: 0 | Phase: —")
        self._set_ui_running(False)

    # ── render loops ──────────────────────────────────────────────────────────

    def _poll_queue(self):
        """Main animation loop – drains queue, renders latest frame."""
        if self._restarted:
            return

        latest = None
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
        self.sim_canvas.delete("agents")
        self.sim_canvas.delete("food")

        r = FOOD_R
        for fx, fy in payload['food']:
            self.sim_canvas.create_oval(fx - r, fy - r, fx + r, fy + r,
                                        fill=COLOR_FOOD, outline="#1a8a4a",
                                        width=1, tags="food")

        # Agents: x, y, radius, color, alive, sense, energy, max_energy
        # Only draw living or recently dead?
        # Draw dead as grey, alive as colored
        debug_mode = self.var_debug.get()
        self.sim_canvas.delete("debug") # clear old debug items if any

        for ax, ay, ar, col, alive, sense, energy, max_e in payload['agents']:
            # Visual Z-order: larger on top or bottom? Smaller on top is better to see them.
            # But usually sorting by size helps.
            # Just draw simply.
            if debug_mode and alive:
                # Sense range
                self.sim_canvas.create_oval(ax - sense, ay - sense, ax + sense, ay + sense,
                                            outline="#444444", width=1, dash=(2, 4), tags="debug")
                
                # Energy bar
                bar_w = 20
                bar_h = 3
                pct = max(0, min(1, energy / max_e))
                # color from green to red based on pct
                r = int(255 * (1 - pct))
                g = int(255 * pct)
                ecol = f'#{r:02x}{g:02x}00'
                
                bx = ax - bar_w / 2
                by = ay - ar - 8
                self.sim_canvas.create_rectangle(bx, by, bx + bar_w * pct, by + bar_h,
                                                 fill=ecol, outline="", tags="debug")

            self.sim_canvas.create_oval(ax - ar, ay - ar, ax + ar, ay + ar,
                                        fill=col, outline="black",
                                        width=1,
                                        tags="agents")

    def _update_info(self, payload: dict):
        active_cnt = payload.get('active_cnt', 0)
        total = len(payload['agents'])
        gen  = payload['generation']
        phase = payload['phase_name']
        self.lbl_info.config(text=f"Gen: {gen} | Pop: {total} (Active: {active_cnt}) | Phase: {phase}")

    def _refresh_chart(self):
        if self._restarted:
            return
        if self._last_payload and self._last_payload['history']:
            self.chart.update_chart(self._last_payload['history'])
        try:
            ms = max(CHART_REFRESH_MIN_MS, int(float(self.ent_chart_rate.get()) * 1000))
        except (ValueError, tk.TclError):
            ms = CHART_REFRESH_FALLBACK_MS
        self.after(ms, self._refresh_chart)


if __name__ == "__main__":
    app = App()
    app.mainloop()
