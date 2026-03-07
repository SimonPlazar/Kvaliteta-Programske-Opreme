import tkinter as tk
from tkinter import ttk
import threading
import queue
import time
import random

# --- KONFIGURACIJA IN KONSTANTE ---
BARVE = ["blue", "red", "green", "orange", "purple", "brown", "teal", "magenta", "navy", "olive"]
BARVE_ORIS = ["darkblue", "darkred", "darkgreen", "darkorange", "indigo", "saddlebrown", "darkcyan", "darkmagenta",
              "midnightblue", "darkolivegreen"]

# Agent / simulacija
AGENT_PREMIK = 10               # Največji korak premika agenta na korak
AGENT_SPAWN_MIN = 20            # Minimalna koordinata pri ustvarjanju agentov
AGENT_SPAWN_MAX = 430           # Maksimalna koordinata pri ustvarjanju agentov
PLATNO_SIM_VELIKOST = 450       # Širina/višina simulacijskega platna (px)
PLATNO_SIM_MEJA = 10            # Rob, znotraj katerega ostanejo agenti
QUEUE_MAX = 50                  # Največje število sporočil v vrsti
POZICIJ_MAX = 1000              # Koliko pozicij agentov pošljemo UI-ju na korak

# Graf
GRAF_OX = 50                    # X izhodišče grafa
GRAF_OY = 400                   # Y izhodišče grafa
GRAF_W = 350                    # Širina grafa (px)
GRAF_H = 350                    # Višina grafa (px)
GRAF_OS_X_KONEC = 410           # Konec x osi grafa
GRAF_OS_Y_KONEC = 40            # Konec y osi grafa (vrh)
GRAF_LEGENDA_X0 = 55            # X začetek prve legende
GRAF_LEGENDA_DX = 78            # Razmik med legendami
GRAF_LEGENDA_Y0 = 14            # Y pozicija prve vrstice legend
GRAF_LEGENDA_DY = 16            # Razmik med vrsticama legend
GRAF_LEGENDA_STOLPCI = 5        # Koliko legend na vrstico
HOVER_FPS_MS = 16               # Interval hover zanke (~60fps)
HOVER_PIKA_R = 4                # Polmer pike pri hoverju
HOVER_TOOLTIP_DY = 13           # Razmik vrstic v tooltippu
MAX_ZGODOVINA = 200             # Največje število točk v zgodovini na agenta
MAX_TOCKE_GRAFA = 400           # Največje število točk izrisanih na grafu

# UI
PLATNO_GRAF_VELIKOST = 450      # Širina/višina grafičnega platna (px)
SEZNAM_AGENTOV_VISINA = 120     # Višina scrollable področja agentov (px)
PRIVZETA_HITROST_SIM = "0.1"    # Privzeta hitrost simulacije (s)
PRIVZETA_HITROST_GRAF = "0.5"   # Privzeto osveževanje grafa (s)
GRAF_OSVEZI_MIN_MS = 50         # Minimalni interval osveževanja grafa (ms)
GRAF_OSVEZI_FALLBACK_MS = 500   # Fallback interval osveževanja grafa (ms)
SIM_OSVEZI_MS = 30              # Interval posodabljanja sim platna (ms)

# Privzete vrednosti parametrov agenta
PRIVZETI_N0 = "50"
PRIVZETI_R = "0.1"
PRIVZETI_S = "0.05"
PRIVZETI_K = "0.0005"


# --- 1. DOMENSKI MODELI (MODEL) ---

class Agent:
    """Predstavlja posamezno bitje v simulaciji."""

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.move = AGENT_PREMIK

    def premakni(self, meja_w, meja_h):
        """Naključno premikanje znotraj meja platna."""
        self.x += random.uniform(-self.move, self.move)
        self.y += random.uniform(-self.move, self.move)
        self.x = max(PLATNO_SIM_MEJA, min(meja_w - PLATNO_SIM_MEJA, self.x))
        self.y = max(PLATNO_SIM_MEJA, min(meja_h - PLATNO_SIM_MEJA, self.y))


# --- 2. SIMULACIJSKI ENGINE (LOGIKA) ---

class SimulacijaNit(threading.Thread):
    """Niti za izvajanje matematičnega dela simulacije za določeno populacijo."""

    def __init__(self, data_queue, parametri, agent_id, speed_entry):
        super().__init__()
        self.data_queue = data_queue
        self.params = parametri
        self.agent_id = agent_id
        self.running = True
        self.paused = False
        self.daemon = True
        self._speed_entry = speed_entry

        self.agenti = [Agent(random.randint(AGENT_SPAWN_MIN, AGENT_SPAWN_MAX),
                             random.randint(AGENT_SPAWN_MIN, AGENT_SPAWN_MAX))
                       for _ in range(int(self.params['st']))]

    def _get_speed(self):
        try:
            val = float(self._speed_entry.get())
            if val > 0:
                return val
        except (ValueError, tk.TclError):
            pass
        return self.params['speed']

    def run(self):
        casovni_korak = 0
        while self.running:
            if not self.paused:
                self._evolucija()
                self._poslji_podatke(casovni_korak)
                casovni_korak += 1
            time.sleep(self._get_speed())

    def _evolucija(self):
        """Izvede en korak rasti populacije (deterministično ali stohastično)."""
        r, s, k = self.params['r'], self.params['s'], self.params['k']
        n = len(self.agenti)
        nacin = self.params.get('nacin', 'stohastični')

        if nacin == 'deterministični':
            delta = int(round((r - s - k * n) * n))
            for agent in self.agenti:
                agent.premakni(PLATNO_SIM_VELIKOST, PLATNO_SIM_VELIKOST)

            if delta > 0:
                for _ in range(delta):
                    self.agenti.append(Agent(random.randint(AGENT_SPAWN_MIN, AGENT_SPAWN_MAX),
                                             random.randint(AGENT_SPAWN_MIN, AGENT_SPAWN_MAX)))
            elif delta < 0:
                for _ in range(min(abs(delta), len(self.agenti))):
                    if self.agenti: self.agenti.pop(random.randrange(len(self.agenti)))
        else:
            nova_populacija = []
            verjetnost_smrti = s + (k * n)
            for agent in self.agenti:
                agent.premakni(PLATNO_SIM_VELIKOST, PLATNO_SIM_VELIKOST)
                if random.random() >= verjetnost_smrti:
                    nova_populacija.append(agent)
                if random.random() < r:
                    nova_populacija.append(Agent(random.randint(AGENT_SPAWN_MIN, AGENT_SPAWN_MAX),
                                                 random.randint(AGENT_SPAWN_MIN, AGENT_SPAWN_MAX)))
            self.agenti = nova_populacija

    def _poslji_podatke(self, korak):
        """Pripravi podatke za glavno UI nit."""
        podatki = {
            'agent_id': self.agent_id,
            'n': len(self.agenti),
            'cas': korak,
            'pozicije': [(a.x, a.y) for a in self.agenti[:POZICIJ_MAX]]
        }
        if self.data_queue.qsize() < QUEUE_MAX:
            self.data_queue.put(podatki)

    def stop(self):
        self.running = False


# --- 3. UI KOMPONENTE (VIEW) ---

class AgentVrstica(tk.Frame):
    """UI komponenta za vnos parametrov posameznega tipa agenta."""

    def __init__(self, parent, agent_id, barva, on_delete_cb, is_first=False):
        super().__init__(parent, bd=1, relief=tk.GROOVE, pady=2)
        self.agent_id = agent_id  # Fiksni ID (1–10), vezan na barvo
        self.pack(fill=tk.X, pady=1)

        # Vizualni indikator barve — shranjen kot instanca za posodobitev
        self.lbl_barva = tk.Label(self, bg=barva, width=2)
        self.lbl_barva.pack(side=tk.LEFT, padx=(3, 5))
        self.lbl_ime = tk.Label(self, text=f"Agent {agent_id}:", font=("Arial", 8, "bold"))
        self.lbl_ime.pack(side=tk.LEFT)

        self.ent_st = self._ustvari_entry("N0:", PRIVZETI_N0)
        self.ent_r = self._ustvari_entry("R:", PRIVZETI_R)
        self.ent_s = self._ustvari_entry("S:", PRIVZETI_S)
        self.ent_k = self._ustvari_entry("K:", PRIVZETI_K)

        self.btn_delete = None
        if not is_first:
            self.btn_delete = tk.Button(self, text="✕", fg="red", command=on_delete_cb,
                                        relief=tk.FLAT, font=("Arial", 9, "bold"))
            self.btn_delete.pack(side=tk.RIGHT, padx=3)

    def update_display(self, display_idx, barva):
        """Ni več potrebno — ID in barva sta fiksna."""
        pass

    def _ustvari_entry(self, label, default):
        tk.Label(self, text=label, font=("Arial", 8)).pack(side=tk.LEFT, padx=(4, 1))
        e = tk.Entry(self, width=6, font=("Arial", 8))
        e.insert(0, default)
        e.pack(side=tk.LEFT)
        return e

    def pridobi_parametre(self, speed):
        return {
            'st': int(self.ent_st.get()),
            'r': float(self.ent_r.get()),
            's': float(self.ent_s.get()),
            'k': float(self.ent_k.get()),
            'speed': speed
        }

    def nastavi_stanje_brisanja(self, omogoceno):
        if self.btn_delete:
            self.btn_delete.config(state=tk.NORMAL if omogoceno else tk.DISABLED)


class Grafikon(tk.Canvas):
    """Specializirano platno za izris grafov in interakcijo (hover)."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.ox, self.oy = GRAF_OX, GRAF_OY
        self.w, self.h = GRAF_W, GRAF_H
        self.linije_refs = {}
        self.zadnja_miska = (None, None)
        self._zadnje_zgodovine = {}
        self._zadnje_skale = None
        self._zadnji_aktivni_ids = []
        self.bind("<Motion>", self._na_premik_miske)
        self.bind("<Leave>", self._na_izhod_miske)
        self._narisi_osi()
        self._hover_loop()

    def _narisi_osi(self):
        self.delete("os")
        self.create_line(self.ox, self.oy, self.ox, GRAF_OS_Y_KONEC, arrow=tk.LAST, tags="os")
        self.create_line(self.ox, self.oy, GRAF_OS_X_KONEC, self.oy, arrow=tk.LAST, tags="os")
        self.create_text(self.ox - 20, GRAF_OS_Y_KONEC, text="N", tags="os")
        self.create_text(GRAF_OS_X_KONEC, self.oy + 20, text="t", tags="os")

    def posodobi(self, zgodovine, aktivni_ids):
        """Glavna metoda za ponovni izris linij in legende."""
        skale = self._izracunaj_skale(zgodovine)
        if not skale: return
        min_t, max_t, min_y, max_y = skale

        self._zadnje_zgodovine = {k: list(v) for k, v in zgodovine.items()}
        self._zadnje_skale = skale
        self._zadnji_aktivni_ids = list(aktivni_ids)

        self.delete("legenda")
        for aid in list(self.linije_refs.keys()):
            if aid not in aktivni_ids:
                for lid in self.linije_refs[aid]: self.delete(lid)
                del self.linije_refs[aid]

        for i, aid in enumerate(aktivni_ids):
            data = zgodovine.get(aid, [])
            if len(data) < 2: continue
            barva = BARVE[aid]
            tocke = self._pretvori_v_koordinate(data, min_t, max_t, min_y, max_y)
            self._izrisi_pot(aid, tocke, barva)
            self._narisi_legendo(i, aid, barva)

    def _izracunaj_skale(self, zgodovine):
        vsi_t, vsi_n = [], []
        for h in zgodovine.values():
            if len(h) < 2: continue
            vsi_t.extend([h[0][0], h[-1][0]])
            vsi_n.extend([p[1] for p in h])

        if not vsi_t or max(vsi_t) == min(vsi_t): return None

        max_n = max(vsi_n)
        pad = (max_n - min(vsi_n)) * 0.1
        return min(vsi_t), max(vsi_t), max(0, min(vsi_n) - pad), max_n + pad

    def _pretvori_v_koordinate(self, data, min_t, max_t, min_y, max_y):
        razpon_t = max_t - min_t
        razpon_y = max_y - min_y

        if len(data) > MAX_TOCKE_GRAFA:
            korak = len(data) / MAX_TOCKE_GRAFA
            data = [data[int(j * korak)] for j in range(MAX_TOCKE_GRAFA)]

        return [(self.ox + ((t - min_t) / razpon_t) * self.w,
                 self.oy - ((n - min_y) / razpon_y) * self.h) for t, n in data]

    def _izrisi_pot(self, aid, tocke, barva):
        if aid not in self.linije_refs: self.linije_refs[aid] = []
        linije = self.linije_refs[aid]

        potrebno = len(tocke) - 1
        for j in range(potrebno):
            c = (*tocke[j], *tocke[j + 1])
            if j < len(linije):
                self.coords(linije[j], *c)
            else:
                lid = self.create_line(*c, fill=barva, width=2, tags="pot")
                linije.append(lid)

        for j in range(potrebno, len(linije)): self.delete(linije[j])
        self.linije_refs[aid] = linije[:potrebno]

    def _narisi_legendo(self, i, aid, barva):
        col = i % GRAF_LEGENDA_STOLPCI
        row = i // GRAF_LEGENDA_STOLPCI
        lx = GRAF_LEGENDA_X0 + col * GRAF_LEGENDA_DX
        ly = GRAF_LEGENDA_Y0 + row * GRAF_LEGENDA_DY
        self.create_rectangle(lx, ly - 5, lx + 12, ly + 5, fill=barva, outline=barva, tags="legenda")
        self.create_text(lx + 16, ly, text=f"A{aid}", anchor="w", font=("Arial", 7), tags="legenda")

    def _na_premik_miske(self, event):
        self.zadnja_miska = (event.x, event.y)

    def _na_izhod_miske(self, event):
        self.zadnja_miska = (None, None)
        self.delete("hover")

    def _hover_loop(self):
        """Fast independent hover refresh loop (~60fps)."""
        self._osvezi_hover()
        self.after(HOVER_FPS_MS, self._hover_loop)

    def _osvezi_hover(self):
        self.delete("hover")
        mx, my = self.zadnja_miska
        if mx is None or not self._zadnje_skale: return
        if not (self.ox <= mx <= self.ox + self.w): return

        zgodovine = self._zadnje_zgodovine
        skale = self._zadnje_skale
        aktivni_ids = self._zadnji_aktivni_ids

        min_t, max_t, min_y, max_y = skale
        razpon_t = max_t - min_t
        razpon_y = max_y - min_y
        t_miska = min_t + ((mx - self.ox) / self.w) * razpon_t

        self.create_line(mx, self.oy - self.h, mx, self.oy,
                         fill="#aaaaaa", dash=(4, 4), tags="hover")

        besedilo_podatki = []
        for i, aid in enumerate(aktivni_ids):
            zgodovina = zgodovine.get(aid, [])
            if len(zgodovina) < 2: continue

            najblizja = min(zgodovina, key=lambda p: abs(p[0] - t_miska))
            px = self.ox + ((najblizja[0] - min_t) / razpon_t) * self.w
            py = self.oy - ((najblizja[1] - min_y) / razpon_y) * self.h

            barva = BARVE[aid]
            r = HOVER_PIKA_R
            self.create_oval(px - r, py - r, px + r, py + r,
                             fill=barva, outline="white", tags="hover")
            besedilo_podatki.append((barva, f"A{aid}: N={int(najblizja[1])}"))

        if besedilo_podatki:
            t_label = f"t = {int(t_miska)}"
            tip_x = mx + 12
            tip_y = my - 10 - len(besedilo_podatki) * HOVER_TOOLTIP_DY

            self.create_text(tip_x, tip_y, text=t_label,
                             fill="#333333", anchor="w",
                             font=("Arial", 8, "bold"), tags="hover")

            for j, (col, txt) in enumerate(besedilo_podatki):
                self.create_text(tip_x, tip_y + HOVER_TOOLTIP_DY + j * HOVER_TOOLTIP_DY, text=txt,
                                 fill=col, anchor="w",
                                 font=("Arial", 8, "bold"), tags="hover")


# --- 4. GLAVNA APLIKACIJA (CONTROLLER) ---

class EvolucijskaSimulacija(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Evolucijska Simulacija")

        self.niti = {}
        self.zgodovine = {}
        self.vrstice_ui = []
        self.data_queue = queue.Queue()
        self._prosti_ids = list(range(len(BARVE)))
        self._resetiran = False
        self.nacin_sim = tk.StringVar(value="stohastični")

        self._ustvari_vmesnik()
        self._dodaj_vrstico()  # Prvi agent

    def _ustvari_vmesnik(self):
        root_fm = tk.Frame(self, padx=10, pady=10)
        root_fm.pack(fill=tk.BOTH, expand=True)

        top_fm = tk.Frame(root_fm)
        top_fm.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.platno_sim = tk.Canvas(top_fm, width=PLATNO_SIM_VELIKOST, height=PLATNO_SIM_VELIKOST,
                                    bg="white", relief=tk.SUNKEN, bd=1)
        self.platno_sim.pack(side=tk.LEFT, padx=5)

        self.platno_graf = Grafikon(top_fm, width=PLATNO_GRAF_VELIKOST, height=PLATNO_GRAF_VELIKOST,
                                    bg="#fdfdfd", relief=tk.SUNKEN, bd=1)
        self.platno_graf.pack(side=tk.RIGHT, padx=5)

        self.ctrl_fm = tk.LabelFrame(root_fm, text=" Nadzor simulacije ", padx=10, pady=10)
        self.ctrl_fm.pack(side=tk.BOTTOM, fill=tk.X, pady=10)

        self._zgradi_gumbe()
        self._zgradi_seznam_agentov()

        self.lbl_info = tk.Label(root_fm, text="Skupna populacija: 0", font=("Arial", 10, "bold"))
        self.lbl_info.pack(side=tk.BOTTOM, anchor="e")

    def _zgradi_gumbe(self):
        btn_box = tk.Frame(self.ctrl_fm)
        btn_box.pack(fill=tk.X)

        self.btn_start = tk.Button(btn_box, text="ZAŽENI", bg="#ccffcc", width=12, command=self.start_simulacije)
        self.btn_start.pack(side=tk.LEFT, padx=2)

        self.btn_pause = tk.Button(btn_box, text="PAVZA", state=tk.DISABLED, width=12, command=self.toggle_pause)
        self.btn_pause.pack(side=tk.LEFT, padx=2)

        self.btn_restart = tk.Button(btn_box, text="RESTART", bg="#ffcccc", state=tk.DISABLED, width=12,
                                     command=self.restart_simulacije)
        self.btn_restart.pack(side=tk.LEFT, padx=2)

        self.btn_dodaj = tk.Button(btn_box, text="+ DODAJ AGENTA", bg="#cce5ff", command=self._dodaj_vrstico)
        self.btn_dodaj.pack(side=tk.LEFT, padx=20)

        tk.Label(btn_box, text="Način:").pack(side=tk.LEFT, padx=(10, 2))
        self.cmb_nacin = ttk.Combobox(btn_box, textvariable=self.nacin_sim,
                                      values=["stohastični", "deterministični"],
                                      width=15, state="readonly")
        self.cmb_nacin.pack(side=tk.LEFT)

        tk.Label(btn_box, text="Hitrost Sim (s):").pack(side=tk.LEFT, padx=(15, 2))
        self.ent_sim_speed = tk.Entry(btn_box, width=5)
        self.ent_sim_speed.insert(0, PRIVZETA_HITROST_SIM)
        self.ent_sim_speed.pack(side=tk.LEFT)

        tk.Label(btn_box, text="Osveževanje Grafa (s):").pack(side=tk.LEFT, padx=(15, 2))
        self.ent_graf_speed = tk.Entry(btn_box, width=5)
        self.ent_graf_speed.insert(0, PRIVZETA_HITROST_GRAF)
        self.ent_graf_speed.pack(side=tk.LEFT)

    def _zgradi_seznam_agentov(self):
        """Ustvari scrollable področje za vrstice agentov."""
        outer = tk.Frame(self.ctrl_fm, bd=1, relief=tk.SUNKEN)
        outer.pack(fill=tk.X, pady=10)

        canvas = tk.Canvas(outer, height=SEZNAM_AGENTOV_VISINA)
        scroll = ttk.Scrollbar(outer, orient="vertical", command=canvas.yview)
        self.seznam_fm = tk.Frame(canvas)

        self.seznam_fm.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.seznam_fm, anchor="nw")
        canvas.configure(yscrollcommand=scroll.set)

        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    def _dodaj_vrstico(self):
        """Doda novega agenta v UI — vzame najnižji prosti ID iz poola."""
        if not self._prosti_ids:
            return
        aid = self._prosti_ids.pop(0)
        barva = BARVE[aid]
        is_first = (aid == 0 and len(self.vrstice_ui) == 0)
        vrstica = AgentVrstica(self.seznam_fm, aid, barva,
                               lambda a=aid: self._odstrani_vrstico(a), is_first=is_first)
        self.vrstice_ui.append(vrstica)

    def _odstrani_vrstico(self, aid):
        """Odstrani agenta iz UI in vrne njegov ID nazaj v pool."""
        vrstica = next((v for v in self.vrstice_ui if v.agent_id == aid), None)
        if not vrstica:
            return
        vrstica.destroy()
        self.vrstice_ui.remove(vrstica)
        self._prosti_ids.append(aid)
        self._prosti_ids.sort()

    def _nastavi_predvajanje_ui(self, tece):
        """Preklopi UI elemente glede na to, ali simulacija teče ali ne."""
        if tece:
            self.btn_start.config(state=tk.DISABLED)
            self.btn_pause.config(state=tk.NORMAL)
            self.btn_restart.config(state=tk.NORMAL)
            self.btn_dodaj.config(state=tk.DISABLED)
            self.cmb_nacin.config(state=tk.DISABLED)
            for v in self.vrstice_ui: v.nastavi_stanje_brisanja(False)
        else:
            self.btn_start.config(state=tk.NORMAL)
            self.btn_pause.config(state=tk.DISABLED, text="PAVZA")
            self.btn_restart.config(state=tk.DISABLED)
            self.btn_dodaj.config(state=tk.NORMAL)
            self.cmb_nacin.config(state="readonly")
            for v in self.vrstice_ui: v.nastavi_stanje_brisanja(True)

    def start_simulacije(self):
        self._resetiran = False
        try:
            s_speed = float(self.ent_sim_speed.get())
            g_speed = float(self.ent_graf_speed.get())
        except ValueError:
            return

        for vrstica in self.vrstice_ui:
            params = vrstica.pridobi_parametre(s_speed)
            params['nacin'] = self.nacin_sim.get()

            aid = vrstica.agent_id
            thread = SimulacijaNit(self.data_queue, params, aid, self.ent_sim_speed)
            self.niti[aid] = thread
            self.zgodovine[aid] = []
            thread.start()

        self._nastavi_predvajanje_ui(True)
        self._procesiraj_vrsto()
        self.after(int(g_speed * 1000), self._osvezi_grafikon)

    def _procesiraj_vrsto(self):
        """Glavna zanka za posodabljanje pozicij agentov na platnu."""
        if self._resetiran: return

        try:
            while True:
                data = self.data_queue.get_nowait()
                aid = data['agent_id']

                self.zgodovine[aid].append((data['cas'], data['n']))
                if len(self.zgodovine[aid]) > MAX_ZGODOVINA:
                    self.zgodovine[aid].pop(0)

                tag = f"obj_{aid}"
                self.platno_sim.delete(tag)

                for x, y in data['pozicije']:
                    self.platno_sim.create_oval(x - 3, y - 3, x + 3, y + 3, fill=BARVE[aid],
                                                outline=BARVE_ORIS[aid], tags=tag)
        except queue.Empty:
            pass

        self._posodobi_stevec_populacije()
        self.after(SIM_OSVEZI_MS, self._procesiraj_vrsto)

    def _osvezi_grafikon(self):
        """Zanka za osveževanje grafa (ločena hitrost)."""
        if self._resetiran: return
        self.platno_graf.posodobi(self.zgodovine, list(self.niti.keys()))

        try:
            ms = max(GRAF_OSVEZI_MIN_MS, int(float(self.ent_graf_speed.get()) * 1000))
            self.after(ms, self._osvezi_grafikon)
        except:
            self.after(GRAF_OSVEZI_FALLBACK_MS, self._osvezi_grafikon)

    def _posodobi_stevec_populacije(self):
        skupaj = sum(h[-1][1] for h in self.zgodovine.values() if h)
        self.lbl_info.config(text=f"Skupna populacija: {skupaj}")

    def toggle_pause(self):
        je_pavzirano = any(t.paused for t in self.niti.values())
        for t in self.niti.values():
            t.paused = not je_pavzirano
        self.btn_pause.config(text="NADALJUJ" if not je_pavzirano else "PAVZA")

    def restart_simulacije(self):
        self._resetiran = True
        for t in self.niti.values(): t.stop()
        self.niti.clear()
        self.zgodovine.clear()

        # Izprazni vrsto — zavrzi vse zaostale pakete prejšnjega teka
        while not self.data_queue.empty():
            try:
                self.data_queue.get_nowait()
            except queue.Empty:
                break

        self.platno_sim.delete("all")

        # Popolno brisanje grafa in reset vseh notranjih stanj
        self.platno_graf.delete("all")
        self.platno_graf.linije_refs.clear()
        self.platno_graf._zadnje_skale = None
        self.platno_graf._zadnje_zgodovine = {}
        self.platno_graf._zadnji_aktivni_ids = []
        self.platno_graf._narisi_osi()

        self._nastavi_predvajanje_ui(False)

if __name__ == "__main__":
    app = EvolucijskaSimulacija()
    app.mainloop()
