import tkinter as tk
import threading
import queue
import time
import random
import math

# ── colours ──────────────────────────────────────────────────────────────────
COLOR_M       = "#3a7bd5"   # peaceful agent fill
COLOR_M_OUT   = "#1a4a8a"
COLOR_A       = "#e03131"   # aggressive agent fill
COLOR_A_OUT   = "#8b0000"
COLOR_FOOD    = "#2ecc71"
COLOR_BORDER  = "#cccccc"

# ── canvas / agent geometry ───────────────────────────────────────────────────
SIM_SIZE      = 450     # simulation canvas width & height (px)
BORDER_W      = 20      # spawn/return zone thickness (px)
AGENT_R       = 5       # agent circle radius (px)
AGENT_SPEED   = 6.0     # px per animation step
AGENT_OFFSET  = 8       # horizontal separation for two agents at same food
FOOD_R        = 6       # food circle radius (px)

# ── simulation ────────────────────────────────────────────────────────────────
QUEUE_MAX          = 100
DEFAULT_N0_M       = "20"
DEFAULT_N0_A       = "20"
DEFAULT_N_FOOD     = "25"
DEFAULT_SIM_SPEED  = "0.05"
DEFAULT_CHART_RATE = "0.5"
SIM_REFRESH_MS     = 30
CHART_REFRESH_MIN_MS      = 50
CHART_REFRESH_FALLBACK_MS = 500
MAX_HISTORY        = 500

# ── generation phases ─────────────────────────────────────────────────────────
PHASE_SPAWN    = 0
PHASE_MOVE_TO  = 1
PHASE_EVAL     = 2
PHASE_MOVE_OFF = 3
PHASE_END      = 4

PHASE_NAMES = {
    PHASE_SPAWN:    "Spawn",
    PHASE_MOVE_TO:  "Move → food",
    PHASE_EVAL:     "Evaluation",
    PHASE_MOVE_OFF: "Move → border",
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
    """Single creature – peaceful ('M') or aggressive ('A')."""

    def __init__(self, kind: str, x: float, y: float):
        self.kind = kind            # 'M' or 'A'
        self.x = x
        self.y = y
        self.target_x: float | None = None
        self.target_y: float | None = None
        self.alive = True
        self.slot: int = 0          # 0 = left offset, 1 = right offset at food
        self._food_pair: 'FoodPair | None' = None

    # ── properties ───────────────────────────────────────────────────────────

    @property
    def has_target(self) -> bool:
        return self.target_x is not None

    @property
    def has_food(self) -> bool:
        return self._food_pair is not None

    # ── food assignment ───────────────────────────────────────────────────────

    def assign_food(self, pair: 'FoodPair', slot: int):
        """Claim a slot at a food pair and set the offset target."""
        self._food_pair = pair
        self.slot = slot
        offset = AGENT_OFFSET * (slot * 2 - 1)   # slot 0 → left, slot 1 → right
        self.target_x = pair.x + offset
        self.target_y = pair.y

    def release_food(self):
        """Clear food reference and movement target."""
        self._food_pair = None
        self.target_x = None
        self.target_y = None

    def reached_food(self) -> bool:
        """True when the agent is within one step of its target."""
        if self.target_x is None:
            return True
        return math.hypot(self.target_x - self.x, self.target_y - self.y) < AGENT_SPEED

    # ── movement ─────────────────────────────────────────────────────────────

    def set_target(self, x: float, y: float):
        self.target_x = x
        self.target_y = y

    def move_towards_target(self, speed: float) -> bool:
        """Step toward target. Returns True on arrival."""
        if self.target_x is None:
            return True
        dx = self.target_x - self.x
        dy = self.target_y - self.y
        dist = math.hypot(dx, dy)
        if dist <= speed:
            self.x, self.y = self.target_x, self.target_y
            return True
        self.x += (dx / dist) * speed
        self.y += (dy / dist) * speed
        return False

    def move_random(self, speed: float, size: int, border: int):
        """Random walk, clamped to the inner field (used when no food assigned)."""
        angle = random.uniform(0, 2 * math.pi)
        self.x += math.cos(angle) * speed
        self.y += math.sin(angle) * speed
        margin = border + AGENT_R
        self.x = max(margin, min(size - margin, self.x))
        self.y = max(margin, min(size - margin, self.y))


class FoodPair:
    """One food location – accepts at most 2 agents."""

    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y
        self.agents: list[Agent] = []
        self.eaten: bool = False    # set True in evaluation → removed from canvas

    @property
    def full(self) -> bool:
        return len(self.agents) >= 2


# ─────────────────────────────────────────────────────────────────────────────
# 2.  Evolucioja agresije RULES
# ─────────────────────────────────────────────────────────────────────────────

def evaluate_pair(agents: list[Agent]) -> None:
    """
    Apply rules to agents at one food pair (in-place).
    Offspring are appended to the list; the engine collects survivors.

    Rules:
      0 agents   → nothing
      1 agent    → survives + 1 offspring (same type)
      M + M      → both survive, no offspring
      A + A      → both die
      M + A      → A always survives, 50 % chance of offspring
                   M survives with 50 % probability
    """
    n = len(agents)
    if n == 0:
        return

    if n == 1:
        agents[0].alive = True
        clone = Agent(agents[0].kind, agents[0].x, agents[0].y)
        clone.alive = True
        agents.append(clone)
        return

    a, b = agents[0], agents[1]
    kinds = {a.kind, b.kind}

    if kinds == {'M'}:
        a.alive = b.alive = True

    elif kinds == {'A'}:
        a.alive = b.alive = False

    else:
        m  = a if a.kind == 'M' else b
        ag = a if a.kind == 'A' else b
        ag.alive = True
        m.alive  = random.random() < 0.5
        if random.random() < 0.5:
            clone = Agent('A', ag.x, ag.y)
            clone.alive = True
            agents.append(clone)


# ─────────────────────────────────────────────────────────────────────────────
# 2b.  FOOD ASSIGNMENT STRATEGIES
# ─────────────────────────────────────────────────────────────────────────────

def assign_stochastic(agents: list, food: list):
    """
    All slots (2 per pair) shuffled together and assigned randomly.
    A pair can receive 2 agents while another stays empty.
    """
    slots: list[tuple] = []
    for pair in food:
        slots.append((pair, 0))
        slots.append((pair, 1))
    random.shuffle(slots)

    for i, agent in enumerate(agents):
        if i < len(slots):
            pair, slot = slots[i]
            pair.agents.append(agent)
            agent.assign_food(pair, slot)
        else:
            agent.release_food()


def assign_deterministic(agents: list, food: list):
    """
    Two-round assignment: every pair gets one agent first (round 1),
    then second slots are filled (round 2).
    Guarantees no pair receives a second visitor before all pairs have one.
    """
    round1 = list(food)
    round2 = list(food)
    random.shuffle(round1)
    random.shuffle(round2)
    schedule = [(p, 0) for p in round1] + [(p, 1) for p in round2]

    for i, agent in enumerate(agents):
        if i < len(schedule):
            pair, slot = schedule[i]
            pair.agents.append(agent)
            agent.assign_food(pair, slot)
        else:
            agent.release_food()


ASSIGNMENT_MODES = {
    "Stochastic":    assign_stochastic,
    "Deterministic": assign_deterministic,
}


# ─────────────────────────────────────────────────────────────────────────────
# 3.  SIMULATION ENGINE
# ─────────────────────────────────────────────────────────────────────────────

def _random_border_point(size: int, border: int) -> tuple[float, float]:
    """Random point on the inner edge of the border zone."""
    side = random.randint(0, 3)
    if side == 0: return float(random.randint(border, size - border)), float(border)
    if side == 1: return float(random.randint(border, size - border)), float(size - border)
    if side == 2: return float(border), float(random.randint(border, size - border))
    return       float(size - border), float(random.randint(border, size - border))


def _random_inner_point(size: int, border: int) -> tuple[float, float]:
    """Random point strictly inside the field (away from border)."""
    margin = border + FOOD_R + 10
    return (float(random.randint(margin, size - margin)),
            float(random.randint(margin, size - margin)))


class SimThread(threading.Thread):
    """
    Single simulation thread for both agent types.
    Phase loop: SPAWN → MOVE_TO → EVAL → MOVE_OFF → END → repeat.
    Every tick sends one payload dict to the UI queue.
    """

    def __init__(self, data_queue: queue.Queue, n0_m: int, n0_a: int,
                 n_food: int, speed_entry: tk.Entry, assignment: str = "Deterministic"):
        super().__init__(daemon=True)
        self.q        = data_queue
        self.n0_m     = n0_m
        self.n0_a     = n0_a
        self.n_food   = n_food
        self._speed_entry  = speed_entry
        self._assign  = ASSIGNMENT_MODES.get(assignment, assign_deterministic)

        self._running = True
        self._paused  = threading.Event()
        self._paused.set()      # set = running, clear = paused

        self.agents:      list[Agent]    = []
        self.food:        list[FoodPair] = []
        self.phase:       int            = PHASE_SPAWN
        self.generation:  int            = 0
        self.history:     list[tuple[int, int, int]] = []   # (gen, n_M, n_A)

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
            self.phase = PHASE_MOVE_TO

        elif self.phase == PHASE_MOVE_TO:
            if self._phase_move(towards_food=True):
                self.phase = PHASE_EVAL

        elif self.phase == PHASE_EVAL:
            self._phase_eval()
            self.phase = PHASE_MOVE_OFF

        elif self.phase == PHASE_MOVE_OFF:
            if self._phase_move(towards_food=False):
                self.phase = PHASE_END

        elif self.phase == PHASE_END:
            self._phase_end()
            self.phase = PHASE_SPAWN

    # ── phases ────────────────────────────────────────────────────────────────

    def _phase_spawn(self):
        """Place food and agents; assign each agent to a food slot (max 2 per pair)."""
        self.food = [
            FoodPair(*_random_inner_point(SIM_SIZE, BORDER_W))
            for _ in range(self.n_food)
        ]

        if self.generation == 0:
            self.agents = (
                [Agent('M', *_random_border_point(SIM_SIZE, BORDER_W)) for _ in range(self.n0_m)] +
                [Agent('A', *_random_border_point(SIM_SIZE, BORDER_W)) for _ in range(self.n0_a)]
            )
        else:
            # move survivors back to border and reset state
            for ag in self.agents:
                ag.x, ag.y = _random_border_point(SIM_SIZE, BORDER_W)
                ag.release_food()
                ag.alive = True

        random.shuffle(self.agents)
        self._assign(self.agents, self.food)

        # record gen 0 as initial conditions (only once)
        if self.generation == 0:
            n_m = sum(1 for ag in self.agents if ag.kind == 'M')
            n_a = sum(1 for ag in self.agents if ag.kind == 'A')
            self.history.append((0, n_m, n_a))

    def _phase_move(self, towards_food: bool) -> bool:
        """
        Move all agents one step.
        towards_food=True  → agents with food walk to it; foodless agents wander.
        towards_food=False → all agents walk back to the border.
        Returns True when every agent with a target has arrived.
        """
        all_arrived = True
        for ag in self.agents:
            if ag.has_food or (not towards_food and ag.has_target):
                if not ag.move_towards_target(AGENT_SPEED):
                    all_arrived = False
            elif towards_food:
                ag.move_random(AGENT_SPEED, SIM_SIZE, BORDER_W)
        return all_arrived

    def _phase_eval(self):
        """
        Apply Hawk-Dove rules per food pair.
        Agents without food don't survive.
        Food is marked eaten here → disappears from canvas on first MOVE_OFF tick.
        """
        for pair in self.food:
            pair.eaten = True

        survivors: list[Agent] = []
        for pair in self.food:
            if not pair.agents:
                continue
            evaluate_pair(pair.agents)
            for ag in pair.agents:
                if ag.alive:
                    ag.release_food()
                    ag.set_target(*_random_border_point(SIM_SIZE, BORDER_W))
                    survivors.append(ag)

        self.agents = survivors

    def _phase_end(self):
        """Record post-evaluation stats, increment generation, reset if extinct."""
        self.generation += 1
        n_m = sum(1 for ag in self.agents if ag.kind == 'M')
        n_a = sum(1 for ag in self.agents if ag.kind == 'A')
        self.history.append((self.generation, n_m, n_a))
        if len(self.history) > MAX_HISTORY:
            self.history.pop(0)

        if n_m + n_a == 0:
            self.agents = (
                [Agent('M', *_random_border_point(SIM_SIZE, BORDER_W)) for _ in range(self.n0_m)] +
                [Agent('A', *_random_border_point(SIM_SIZE, BORDER_W)) for _ in range(self.n0_a)]
            )

    # ── payload ───────────────────────────────────────────────────────────────

    def _send_payload(self):
        payload = {
            'phase':      self.phase,
            'phase_name': PHASE_NAMES.get(self.phase, ''),
            'generation': self.generation,
            'agents':     [(ag.x, ag.y, ag.kind, ag.has_food) for ag in self.agents],
            'food':       [(f.x, f.y) for f in self.food if not f.eaten],
            'history':    list(self.history),
        }
        if self.q.qsize() < QUEUE_MAX:
            self.q.put(payload)


# ─────────────────────────────────────────────────────────────────────────────
# 4.  UI COMPONENTS
# ─────────────────────────────────────────────────────────────────────────────

class AgentRow(tk.Frame):
    """Settings row for one agent type (M or A). Fixed – no delete button."""

    def __init__(self, parent, kind: str, color: str, default_n0: str):
        super().__init__(parent, bd=1, relief=tk.GROOVE, pady=3)
        self.kind = kind
        self.pack(fill=tk.X, pady=1)

        tk.Label(self, bg=color, width=2).pack(side=tk.LEFT, padx=(3, 5))
        label = "Peaceful (M)" if kind == 'M' else "Aggressive (A)"
        tk.Label(self, text=label, font=("Arial", 8, "bold"), width=14, anchor='w').pack(side=tk.LEFT)
        tk.Label(self, text="N0:", font=("Arial", 8)).pack(side=tk.LEFT, padx=(8, 1))
        self.ent_n0 = tk.Entry(self, width=6, font=("Arial", 8))
        self.ent_n0.insert(0, default_n0)
        self.ent_n0.pack(side=tk.LEFT)

    def get_n0(self) -> int:
        try:
            return max(0, int(self.ent_n0.get()))
        except ValueError:
            return 0

    def set_enabled(self, enabled: bool):
        self.ent_n0.config(state=tk.NORMAL if enabled else tk.DISABLED)


class Chart(tk.Canvas):
    """
    Population chart over generations.
    Two fixed series: Peaceful (blue) and Aggressive (red).
    Supports hover crosshair + tooltip.
    """

    _SERIES = [
        ('M', COLOR_M, "Peaceful"),
        ('A', COLOR_A, "Aggressive"),
    ]

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.ox, self.oy = CHART_OX, CHART_OY
        self.w,  self.h  = CHART_W,  CHART_H
        self._line_refs: dict[str, list] = {'M': [], 'A': []}
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
        self.create_text(self.ox - 20, CHART_Y_END,   text="N",      tags="axis")
        self.create_text(CHART_X_END,  self.oy + 20,  text="t (gen)", tags="axis")
        # legend
        self.delete("legend")
        for i, (_, color, label) in enumerate(self._SERIES):
            lx, ly = CHART_OX + i * 100, 14
            self.create_rectangle(lx, ly - 5, lx + 12, ly + 5, fill=color, outline=color, tags="legend")
            self.create_text(lx + 16, ly, text=label, anchor="w", font=("Arial", 8), tags="legend")

    def reset(self):
        self.delete("all")
        self._line_refs  = {'M': [], 'A': []}
        self._last_hist  = []
        self._last_scale = None
        self._draw_axes()

    def update_chart(self, history: list[tuple[int, int, int]]):
        """Redraw both series from (gen, n_M, n_A) history list."""
        if not history:
            return
        self._last_hist = list(history)

        # duplicate single point so the renderer always has ≥2 coords
        if len(history) == 1:
            history = [history[0], history[0]]

        gens = [p[0] for p in history]
        ns   = [p[1] for p in history] + [p[2] for p in history]
        min_t, max_t = min(gens), max(gens)
        if max_t == min_t:
            max_t = min_t + 1
        max_n = max(ns)
        pad   = max(max_n * 0.05, 1)
        scale = (min_t, max_t, 0.0, max_n + pad)
        self._last_scale = scale

        for idx, (key, color, _) in enumerate(self._SERIES):
            data  = [(p[0], p[idx + 1]) for p in history]
            pts   = self._to_canvas(data, *scale)
            self._draw_series(key, pts, color)

    def _to_canvas(self, data, min_t, max_t, min_y, max_y):
        rt, ry = max_t - min_t, max_y - min_y
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
        gen, n_m, n_a = nearest

        # dots on each series line
        for idx, (_, color, _) in enumerate(self._SERIES):
            val = nearest[idx + 1]
            px  = self.ox + ((gen - min_t) / rt) * self.w
            py  = self.oy - ((val - min_y) / ry) * self.h
            r   = HOVER_DOT_R
            self.create_oval(px - r, py - r, px + r, py + r,
                             fill=color, outline="white", tags="hover")

        # tooltip
        lines = [(COLOR_M, f"Peaceful:   {n_m}"), (COLOR_A, f"Aggressive: {n_a}")]
        tx = mx + 12
        ty = my - 10 - len(lines) * HOVER_LINE_DY
        self.create_text(tx, ty, text=f"gen = {gen}",
                         fill="#333333", anchor="w", font=("Arial", 8, "bold"), tags="hover")
        for j, (col, txt) in enumerate(lines):
            self.create_text(tx, ty + HOVER_LINE_DY * (j + 1), text=txt,
                             fill=col, anchor="w", font=("Arial", 8, "bold"), tags="hover")


# ─────────────────────────────────────────────────────────────────────────────
# 5.  APPLICATION CONTROLLER
# ─────────────────────────────────────────────────────────────────────────────

class App(tk.Tk):

    def __init__(self):
        super().__init__()
        self.title("Evolution of Aggression — Hawk-Dove")

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

        self.lbl_info = tk.Label(root, text="Generation: 0 | M: 0 | A: 0 | Phase: —",
                                 font=("Arial", 9, "bold"))
        self.lbl_info.pack(side=tk.BOTTOM, anchor="e")

    def _draw_border(self):
        s, r = SIM_SIZE, BORDER_W
        self.sim_canvas.create_rectangle(r, r, s - r, s - r,
                                         outline=COLOR_BORDER, dash=(4, 4), tags="border")

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
        outer = tk.Frame(self.ctrl, bd=1, relief=tk.SUNKEN)
        outer.pack(fill=tk.X, pady=6)

        self.row_m = AgentRow(outer, 'M', COLOR_M, DEFAULT_N0_M)
        self.row_a = AgentRow(outer, 'A', COLOR_A, DEFAULT_N0_A)

        # food row
        food_row = tk.Frame(outer, bd=1, relief=tk.GROOVE, pady=3)
        food_row.pack(fill=tk.X, pady=1)
        tk.Label(food_row, bg=COLOR_FOOD, width=2).pack(side=tk.LEFT, padx=(3, 5))
        tk.Label(food_row, text="Food pairs", font=("Arial", 8, "bold"),
                 width=14, anchor='w').pack(side=tk.LEFT)
        tk.Label(food_row, text="N:", font=("Arial", 8)).pack(side=tk.LEFT, padx=(8, 1))
        self.ent_food = tk.Entry(food_row, width=6, font=("Arial", 8))
        self.ent_food.insert(0, DEFAULT_N_FOOD)
        self.ent_food.pack(side=tk.LEFT)

        tk.Label(food_row, text="Assignment:", font=("Arial", 8)).pack(side=tk.LEFT, padx=(15, 2))
        self.var_assignment = tk.StringVar(value="Deterministic")
        self.opt_assignment = tk.OptionMenu(food_row, self.var_assignment, *ASSIGNMENT_MODES.keys())
        self.opt_assignment.config(font=("Arial", 8), width=14)
        self.opt_assignment.pack(side=tk.LEFT)

    # ── simulation control ────────────────────────────────────────────────────

    def _set_ui_running(self, running: bool):
        if running:
            self.btn_start.config(state=tk.DISABLED)
            self.btn_pause.config(state=tk.NORMAL, text="PAUSE")
            self.btn_restart.config(state=tk.NORMAL)
            self.ent_food.config(state=tk.DISABLED)
            self.opt_assignment.config(state=tk.DISABLED)
            self.row_m.set_enabled(False)
            self.row_a.set_enabled(False)
        else:
            self.btn_start.config(state=tk.NORMAL)
            self.btn_pause.config(state=tk.DISABLED, text="PAUSE")
            self.btn_restart.config(state=tk.DISABLED)
            self.ent_food.config(state=tk.NORMAL)
            self.opt_assignment.config(state=tk.NORMAL)
            self.row_m.set_enabled(True)
            self.row_a.set_enabled(True)

    def start(self):
        self._restarted = False
        try:
            n_food = max(1, int(self.ent_food.get()))
        except ValueError:
            return

        self.sim = SimThread(
            data_queue = self.q,
            n0_m       = self.row_m.get_n0(),
            n0_a       = self.row_a.get_n0(),
            n_food     = n_food,
            speed_entry= self.ent_speed,
            assignment = self.var_assignment.get(),
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
        self.lbl_info.config(text="Generation: 0 | M: 0 | A: 0 | Phase: —")
        self._set_ui_running(False)

    # ── render loops ──────────────────────────────────────────────────────────

    def _poll_queue(self):
        """Main animation loop – drains queue, renders latest frame."""
        if self._restarted:
            return

        # keep only the most recent payload
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

        # agents: (x, y, kind, has_food) – thicker outline when carrying food
        for ax, ay, kind, has_food in payload['agents']:
            fill    = COLOR_M     if kind == 'M' else COLOR_A
            outline = COLOR_M_OUT if kind == 'M' else COLOR_A_OUT
            ar      = AGENT_R
            self.sim_canvas.create_oval(ax - ar, ay - ar, ax + ar, ay + ar,
                                        fill=fill, outline=outline,
                                        width=2 if has_food else 1,
                                        tags="agents")

    def _update_info(self, payload: dict):
        n_m  = sum(1 for _, _, k, _ in payload['agents'] if k == 'M')
        n_a  = sum(1 for _, _, k, _ in payload['agents'] if k == 'A')
        gen  = payload['generation']
        phase = payload['phase_name']
        self.lbl_info.config(text=f"Generation: {gen} | M: {n_m} | A: {n_a} | Phase: {phase}")

    def _refresh_chart(self):
        """Slower, separate loop for chart updates."""
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
