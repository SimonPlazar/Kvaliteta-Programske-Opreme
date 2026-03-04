import tkinter as tk
from tkinter import ttk
import threading
import queue
import time
import random

# Barvna paleta za različne agente
BARVE = ["blue", "red", "green", "orange", "purple", "brown", "teal", "magenta", "navy", "olive"]
BARVE_ORIS = ["darkblue", "darkred", "darkgreen", "darkorange", "indigo", "saddlebrown", "darkcyan", "darkmagenta",
              "midnightblue", "darkolivegreen"]

# Največje število točk v zgodovini na agenta
MAX_ZGODOVINA = 200
# Največje število točk za izris na grafu (redčenje)
MAX_TOCKE_GRAFA = 400


class Agent:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.move = 10

    def premakni(self, meja_w, meja_h):
        self.x += random.uniform(-self.move, self.move)
        self.y += random.uniform(-self.move, self.move)
        self.x = max(10, min(meja_w - 10, self.x))
        self.y = max(10, min(meja_h - 10, self.y))


class SimulacijaNit(threading.Thread):
    def __init__(self, data_queue, parametri, agent_id):
        super().__init__()
        self.data_queue = data_queue
        self.params = parametri
        self.agent_id = agent_id
        self.running = True
        self.paused = False
        self.daemon = True
        self.zavrnjeni_koraki = 0

        self.agenti = [Agent(random.randint(50, 400), random.randint(50, 400))
                       for _ in range(int(self.params['st']))]

    def run(self):
        casovni_korak = 0
        while self.running:
            if not self.paused:
                r = self.params['r']
                s = self.params['s']
                k = self.params['k']
                n = len(self.agenti)
                nacin = self.params.get('nacin', 'stohastični')

                if nacin == 'deterministični':
                    # Deterministična logistična enačba: ∆N = (R - S - K*N) * N
                    nova_generacija = []
                    delta = int((r - s - k * n) * n)

                    # obstoječi agenti preživijo (lahko dodaš pogoje)
                    for agent in self.agenti:
                        agent.premakni(450, 450)
                        nova_generacija.append(agent)

                    # dodamo nove agente če je delta pozitivna
                    if delta > 0:
                        for _ in range(delta):
                            nova_generacija.append(Agent(random.randint(50, 400), random.randint(50, 400)))

                    # če je delta negativen → populacija se zmanjša
                    elif delta < 0:
                        nova_generacija = nova_generacija[:delta]  # odstrani nekaj agentov

                    self.agenti = nova_generacija

                    # nova_generacija = []
                    # p_smrt = min(1.0, s + k * n)
                    # p_rojstvo = r * (1.0 - p_smrt)
                    #
                    # for agent in self.agenti:
                    #     agent.premakni(450, 450)
                    #     roll = random.random()
                    #
                    #     if roll < p_smrt:
                    #         pass  # umre
                    #     elif roll < p_smrt + p_rojstvo:
                    #         nova_generacija.append(agent)  # preživi
                    #         nova_generacija.append(Agent(agent.x, agent.y))  # + potomec
                    #     else:
                    #         nova_generacija.append(agent)  # samo preživi
                    #
                    # self.agenti = nova_generacija
                else:
                    # Stohastični način (originalni)
                    nova_generacija = []
                    for agent in self.agenti:
                        agent.premakni(450, 450)
                        # prilagojena smrtnost
                        verjetnost_smrti = s + k * n

                        # preveri razmnoževanje
                        if random.random() < r:
                            nova_generacija.append(Agent(random.randint(50, 400), random.randint(50, 400)))

                        # preveri ali agent umre
                        if random.random() < verjetnost_smrti:
                            continue  # agent umre

                        # agent preživi
                        nova_generacija.append(agent)

                    self.agenti = nova_generacija

                    # nova_generacija = []
                    # for agent in self.agenti:
                    #     agent.premakni(450, 450)
                    #     if random.random() < r:
                    #         nova_generacija.append(Agent(agent.x, agent.y))
                    #     p_smrt = s + (k * n)
                    #     if random.random() >= p_smrt:
                    #         nova_generacija.append(agent)
                    # self.agenti = nova_generacija

                pozicije_za_izris = [(a.x, a.y) for a in self.agenti[:1000]]

                podatki = {
                    'agent_id': self.agent_id,
                    'n': len(self.agenti),
                    'cas': casovni_korak,
                    'pozicije': pozicije_za_izris
                }
                # Prepreči kopičenje v vrsti - zavrži stare podatke če UI ne sledi
                if self.data_queue.qsize() < 50:
                    self.data_queue.put(podatki)
                else:
                    self.zavrnjeni_koraki += 1
                    print(f"[OPOZORILO] Agent {self.agent_id}: UI zaostaja! "
                          f"Korak t={casovni_korak} zavržen. "
                          f"Skupaj zavrnjenih: {self.zavrnjeni_koraki}")
                casovni_korak += 1

            time.sleep(self.params['speed'])

    def stop(self):
        self.running = False


class AgentVrstica:
    """Predstavlja eno vrstico parametrov za enega agenta v UI."""

    def __init__(self, parent_frame, idx, barva, on_delete_cb, is_first=False):
        self.idx = idx
        self.barva = barva
        self.frame = tk.Frame(parent_frame, bd=1, relief=tk.GROOVE, pady=2)
        self.frame.pack(fill=tk.X, pady=1)

        # Barvni indikator
        tk.Label(self.frame, bg=barva, width=2).pack(side=tk.LEFT, padx=(3, 5))

        tk.Label(self.frame, text=f"Agent {idx + 1}:", font=("Arial", 8, "bold")).pack(side=tk.LEFT)

        self.ent_st = self._entry("N0:", "50")
        self.ent_r = self._entry("R:", "0.1")
        self.ent_s = self._entry("S:", "0.05")
        self.ent_k = self._entry("K:", "0.0005")

        if not is_first:
            self.btn_delete = tk.Button(self.frame, text="✕", fg="red", command=on_delete_cb,
                                        relief=tk.FLAT, font=("Arial", 9, "bold"))
            self.btn_delete.pack(side=tk.RIGHT, padx=3)
        else:
            self.btn_delete = None

    def nastavi_brisanje(self, omogoceno: bool):
        if self.btn_delete is not None:
            self.btn_delete.config(state=tk.NORMAL if omogoceno else tk.DISABLED)

    def _entry(self, label, default):
        tk.Label(self.frame, text=label, font=("Arial", 8)).pack(side=tk.LEFT, padx=(4, 1))
        e = tk.Entry(self.frame, width=6, font=("Arial", 8))
        e.insert(0, default)
        e.pack(side=tk.LEFT)
        return e

    def get_params(self, speed):
        r = min(1.0, max(0.0, float(self.ent_r.get())))
        s = min(1.0, max(0.0, float(self.ent_s.get())))
        k = min(1.0, max(0.0, float(self.ent_k.get())))
        st = int(self.ent_st.get())
        return {'st': st, 'r': r, 's': s, 'k': k, 'speed': speed}

    def destroy(self):
        self.frame.destroy()


class GlavnoOkno(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Evolucijska Simulacija - Rast Populacije")

        self.zadnja_miska_x = None
        self.zadnja_miska_y = None

        self.w, self.h = 350, 350
        self.ox, self.oy = 50, 400

        # Seznam vrstic agentov (UI)
        self.agent_vrstice: list[AgentVrstica] = []
        # Aktivne simulacijske niti: {agent_id: SimulacijaNit}
        self.sim_niti: dict[int, SimulacijaNit] = {}
        # Zgodovina podatkov: {agent_id: [(t, n), ...]}
        self.zgodovine: dict[int, list] = {}
        # Skupna vrsta za vse niti
        self.data_queue = queue.Queue()

        self._naslednji_id = 0  # naraščajoč ID za agente
        self._resetiran = False  # zastavica za preprečitev izrisa po restartu
        self.nacin_simulacije = tk.StringVar(value="stohastični")

        # Ločen interval za graf (redkejše osveževanje)
        self._graf_interval_ms = 500  # osveži graf vsakih 500ms
        # Sledenje canvas line ID-jem za vsak agent {aid: [line_id, ...]}
        self._graf_linije: dict[int, list] = {}

        self._ustvari_vmesnik()

    # ------------------------------------------------------------------ #
    #  Gradnja vmesnika
    # ------------------------------------------------------------------ #
    def _ustvari_vmesnik(self):
        main_container = tk.Frame(self, padx=5, pady=5)
        main_container.pack(fill=tk.BOTH, expand=True)

        # ---- Zgornji del: simulacijo + graf ----
        frame_top = tk.Frame(main_container)
        frame_top.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.canvas_sim = tk.Canvas(frame_top, width=450, height=450, bg="white",
                                    highlightthickness=1, highlightbackground="gray")
        self.canvas_sim.pack(side=tk.LEFT, padx=2, pady=2)

        self.canvas_graf = tk.Canvas(frame_top, width=450, height=450, bg="#fdfdfd",
                                     highlightthickness=1, highlightbackground="gray")
        self.canvas_graf.pack(side=tk.RIGHT, padx=2, pady=2)
        self.canvas_graf.bind("<Motion>", self._hover_graf)
        self._narisi_osi()

        # ---- Spodnji del: nadzor ----
        frame_ctrl = tk.LabelFrame(main_container, text=" Nadzor ", padx=5, pady=5)
        frame_ctrl.pack(side=tk.BOTTOM, fill=tk.X, pady=(5, 0))

        # Gumbi za splošno upravljanje
        buttons_frame = tk.Frame(frame_ctrl)
        buttons_frame.pack(side=tk.TOP, fill=tk.X)

        self.btn_start = tk.Button(buttons_frame, text="Zaženi vse", command=self._start_vse, bg="#ccffcc")
        self.btn_start.pack(side=tk.LEFT, padx=2)

        self.btn_pause = tk.Button(buttons_frame, text="Pavza vse", command=self._toggle_pause_vse,
                                   state=tk.DISABLED)
        self.btn_pause.pack(side=tk.LEFT, padx=2)

        self.btn_restart = tk.Button(buttons_frame, text="Restart vse", command=self._restart_vse,
                                     bg="#ffcccc", state=tk.DISABLED)
        self.btn_restart.pack(side=tk.LEFT, padx=2)

        self.btn_dodaj = tk.Button(buttons_frame, text="+ Dodaj agenta", command=self._dodaj_vrstico,
                                   bg="#cce5ff")
        self.btn_dodaj.pack(side=tk.LEFT, padx=10)

        # Način simulacije
        nacin_frame = tk.LabelFrame(buttons_frame, text="Način", padx=4, pady=2)
        nacin_frame.pack(side=tk.LEFT, padx=(5, 10))
        self.rb_stohastični = tk.Radiobutton(nacin_frame, text="Stohastični", variable=self.nacin_simulacije,
                                             value="stohastični")
        self.rb_stohastični.pack(side=tk.LEFT)
        self.rb_deterministični = tk.Radiobutton(nacin_frame, text="Deterministični  ∆N=(R−S−K·N)·N",
                                                 variable=self.nacin_simulacije, value="deterministični")
        self.rb_deterministični.pack(side=tk.LEFT)

        # Globalno osveževanje simulacije
        tk.Label(buttons_frame, text="Sim (s):").pack(side=tk.LEFT, padx=(15, 2))
        self.ent_speed = tk.Entry(buttons_frame, width=6)
        self.ent_speed.insert(0, "0.1")
        self.ent_speed.pack(side=tk.LEFT)

        # Osveževanje grafa
        tk.Label(buttons_frame, text="Graf (s):").pack(side=tk.LEFT, padx=(8, 2))
        self.ent_graf_speed = tk.Entry(buttons_frame, width=6)
        self.ent_graf_speed.insert(0, "0.5")
        self.ent_graf_speed.pack(side=tk.LEFT)

        self.btn_nastavi = tk.Button(buttons_frame, text="Nastavi", command=self._nastavi_speed, state=tk.DISABLED)
        self.btn_nastavi.pack(side=tk.LEFT, padx=3)

        # Scrollable območje za vrstice agentov
        agents_outer = tk.Frame(frame_ctrl, bd=1, relief=tk.SUNKEN)
        agents_outer.pack(side=tk.TOP, fill=tk.X, pady=(5, 0))

        canvas_scroll = tk.Canvas(agents_outer, height=110, highlightthickness=0)
        scrollbar = ttk.Scrollbar(agents_outer, orient="vertical", command=canvas_scroll.yview)
        canvas_scroll.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas_scroll.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.agents_frame = tk.Frame(canvas_scroll)
        self.agents_frame_id = canvas_scroll.create_window((0, 0), window=self.agents_frame, anchor="nw")

        def _on_frame_configure(e):
            canvas_scroll.configure(scrollregion=canvas_scroll.bbox("all"))

        def _on_canvas_configure(e):
            canvas_scroll.itemconfig(self.agents_frame_id, width=e.width)

        self.agents_frame.bind("<Configure>", _on_frame_configure)
        canvas_scroll.bind("<Configure>", _on_canvas_configure)

        # Mousewheel scrolling
        def _on_mousewheel(e):
            canvas_scroll.yview_scroll(int(-1 * (e.delta / 120)), "units")

        canvas_scroll.bind("<MouseWheel>", _on_mousewheel)

        # Info label (skupna populacija)
        self.lbl_info = tk.Label(main_container, text="Skupna populacija: 0", font=("Arial", 9, "bold"))
        self.lbl_info.pack(side=tk.BOTTOM, anchor="e")

        # Prva (privzeta) vrstica agenta
        self._dodaj_vrstico()

    # ------------------------------------------------------------------ #
    #  Upravljanje vrstic agentov
    # ------------------------------------------------------------------ #
    def _dodaj_vrstico(self):
        idx = len(self.agent_vrstice)
        barva = BARVE[idx % len(BARVE)]
        is_first = (idx == 0)

        def on_delete(i=idx):
            self._izbrisi_vrstico(i)

        vrstica = AgentVrstica(self.agents_frame, idx, barva, on_delete, is_first)
        self.agent_vrstice.append(vrstica)

    def _izbrisi_vrstico(self, idx):
        # Poiščemo vrstico po indeksu (agent_vrstice se ne sme reshuffleati med tekom)
        # Poiščemo objekt po .idx
        target = None
        for v in self.agent_vrstice:
            if v.idx == idx:
                target = v
                break
        if target is None:
            return
        target.destroy()
        self.agent_vrstice.remove(target)

    # ------------------------------------------------------------------ #
    #  Simulacija
    # ------------------------------------------------------------------ #
    def _start_vse(self):
        if self.sim_niti:
            return  # že teče

        self.zgodovine.clear()
        self._naslednji_id = 0
        self._resetiran = False

        try:
            speed = float(self.ent_speed.get())
        except ValueError:
            speed = 0.1

        try:
            self._graf_interval_ms = max(100, int(float(self.ent_graf_speed.get()) * 1000))
        except ValueError:
            self._graf_interval_ms = 500

        nacin = self.nacin_simulacije.get()

        for vrstica in self.agent_vrstice:
            try:
                params = vrstica.get_params(speed)
                params['nacin'] = nacin
            except ValueError:
                print(f"Napačen vnos za agenta {vrstica.idx + 1}!")
                continue

            agent_id = self._naslednji_id
            self._naslednji_id += 1
            self.zgodovine[agent_id] = []

            nit = SimulacijaNit(self.data_queue, params, agent_id)
            self.sim_niti[agent_id] = nit
            nit.start()

        if self.sim_niti:
            self.btn_start.config(state=tk.DISABLED)
            self.btn_pause.config(state=tk.NORMAL)
            self.btn_restart.config(state=tk.NORMAL)
            self.btn_dodaj.config(state=tk.DISABLED)
            self.btn_nastavi.config(state=tk.DISABLED)
            self.rb_stohastični.config(state=tk.DISABLED)
            self.rb_deterministični.config(state=tk.DISABLED)
            for vrstica in self.agent_vrstice:
                vrstica.nastavi_brisanje(False)
            self._osvezi_prikaz()
            self.after(self._graf_interval_ms, self._osvezi_graf)

    def _toggle_pause_vse(self):
        any_paused = any(n.paused for n in self.sim_niti.values())
        for nit in self.sim_niti.values():
            nit.paused = not any_paused
        if not any_paused:
            # Prehod v pavzo
            self.btn_pause.config(text="Nadaljuj vse")
            self.btn_nastavi.config(state=tk.NORMAL)
        else:
            # Nadaljevanje — Nastavi ni več potreben
            self.btn_pause.config(text="Pavza vse")
            self.btn_nastavi.config(state=tk.DISABLED)

    def _restart_vse(self):
        self._resetiran = True  # ustavi izrisovanje takoj

        for nit in self.sim_niti.values():
            nit.stop()
        self.sim_niti.clear()
        self.zgodovine.clear()

        # Izpraznimo vrsto, da ne pride do zaostalih podatkov
        while not self.data_queue.empty():
            try:
                self.data_queue.get_nowait()
            except queue.Empty:
                break

        self.canvas_sim.delete("all")
        self.canvas_graf.delete("pot", "hover", "legenda")
        self._graf_linije.clear()
        self._narisi_osi()
        self.lbl_info.config(text="Skupna populacija: 0")

        self.btn_start.config(state=tk.NORMAL)
        self.btn_pause.config(state=tk.DISABLED, text="Pavza vse")
        self.btn_restart.config(state=tk.DISABLED)
        self.btn_dodaj.config(state=tk.NORMAL)
        self.btn_nastavi.config(state=tk.DISABLED)
        self.rb_stohastični.config(state=tk.NORMAL)
        self.rb_deterministični.config(state=tk.NORMAL)
        for vrstica in self.agent_vrstice:
            vrstica.nastavi_brisanje(True)

    def _nastavi_speed(self):
        try:
            speed = float(self.ent_speed.get())
        except ValueError:
            speed = None
        if speed is not None:
            for nit in self.sim_niti.values():
                nit.params['speed'] = speed

        try:
            graf_speed = float(self.ent_graf_speed.get())
            self._graf_interval_ms = max(100, int(graf_speed * 1000))
        except ValueError:
            pass

    # ------------------------------------------------------------------ #
    #  Prikaz
    # ------------------------------------------------------------------ #
    def _osvezi_prikaz(self):
        if self._resetiran:
            return

        novi_podatki_prisli = False

        try:
            while True:
                podatki = self.data_queue.get_nowait()
                novi_podatki_prisli = True
                aid = podatki['agent_id']

                if aid not in self.zgodovine:
                    self.zgodovine[aid] = []
                self.zgodovine[aid].append((podatki['cas'], podatki['n']))
                # Drseče okno - ohrani samo zadnjih MAX_ZGODOVINA točk
                if len(self.zgodovine[aid]) > MAX_ZGODOVINA:
                    self.zgodovine[aid] = self.zgodovine[aid][-MAX_ZGODOVINA:]

                # Izris bitij na platnu simulacije
                tag = f"bitje_{aid}"
                barva_idx = list(self.sim_niti.keys()).index(aid) if aid in self.sim_niti else 0
                fill = BARVE[barva_idx % len(BARVE)]
                outline = BARVE_ORIS[barva_idx % len(BARVE_ORIS)]

                self.canvas_sim.delete(tag)
                for x, y in podatki['pozicije']:
                    self.canvas_sim.create_oval(x - 3, y - 3, x + 3, y + 3,
                                                fill=fill, outline=outline, tags=tag)

        except queue.Empty:
            pass

        if novi_podatki_prisli:
            self._posodobi_skupno_populacijo()
            # Graf in hover se osvežujeta v ločenem ciklu (_osvezi_graf)

        if any(n.running for n in self.sim_niti.values()):
            try:
                speed = float(self.ent_speed.get())
            except ValueError:
                speed = 0.1
            # UI osveževanje je vsaj 30ms, sicer enako kot simulacijski korak
            interval_ms = max(30, int(speed * 1000))
            self.after(interval_ms, self._osvezi_prikaz)

    def _osvezi_graf(self):
        """Ločen cikel za osveževanje grafa - neodvisen od simulacije."""
        if self._resetiran:
            return
        self._izris_grafa()
        self._osvezi_hover_vizualizacijo()
        if any(n.running for n in self.sim_niti.values()):
            self.after(self._graf_interval_ms, self._osvezi_graf)

    def _posodobi_skupno_populacijo(self):
        skupaj = 0
        for zgodovina in self.zgodovine.values():
            if zgodovina:
                skupaj += zgodovina[-1][1]
        self.lbl_info.config(text=f"Skupna populacija: {skupaj}")

    # ------------------------------------------------------------------ #
    #  Graf
    # ------------------------------------------------------------------ #
    def _narisi_osi(self):
        self.canvas_graf.delete("os")
        self.canvas_graf.create_line(50, 400, 50, 40, arrow=tk.LAST, tags="os")
        self.canvas_graf.create_line(50, 400, 410, 400, arrow=tk.LAST, tags="os")
        self.canvas_graf.create_text(30, 40, text="N", tags="os")
        self.canvas_graf.create_text(410, 420, text="t", tags="os")

    def _izris_grafa(self):
        # Globalni min/max za drsno okno x-osi in skupno skalo y-osi
        global_min_t = None
        global_max_t = None
        global_min_n = None
        global_max_n = None
        for zgodovina in self.zgodovine.values():
            if len(zgodovina) >= 2:
                t_zac = zgodovina[0][0]
                t_kon = zgodovina[-1][0]
                vse_n = [p[1] for p in zgodovina]
                global_min_t = t_zac if global_min_t is None else min(global_min_t, t_zac)
                global_max_t = t_kon if global_max_t is None else max(global_max_t, t_kon)
                global_min_n = min(vse_n) if global_min_n is None else min(global_min_n, min(vse_n))
                global_max_n = max(vse_n) if global_max_n is None else max(global_max_n, max(vse_n))

        if global_max_t is None or global_max_t == global_min_t:
            return

        razpon_n = max(1, global_max_n - global_min_n)
        padding_n = razpon_n * 0.10
        y_min = max(0, global_min_n - padding_n)
        y_max = global_max_n + padding_n
        razpon_y = y_max - y_min
        razpon_t = global_max_t - global_min_t

        agent_ids = list(self.sim_niti.keys())

        # Briši legendo in odvečne agentove linije
        self.canvas_graf.delete("legenda")
        aktivni_aids = set(agent_ids)
        for aid in list(self._graf_linije.keys()):
            if aid not in aktivni_aids:
                for lid in self._graf_linije[aid]:
                    self.canvas_graf.delete(lid)
                del self._graf_linije[aid]

        for i, aid in enumerate(agent_ids):
            zgodovina = self.zgodovine.get(aid, [])
            if len(zgodovina) < 2:
                continue

            barva = BARVE[i % len(BARVE)]

            # Redčenje
            if len(zgodovina) > MAX_TOCKE_GRAFA:
                korak = len(zgodovina) / MAX_TOCKE_GRAFA
                zgodovina_izris = [zgodovina[int(j * korak)] for j in range(MAX_TOCKE_GRAFA)]
                if zgodovina_izris[-1] != zgodovina[-1]:
                    zgodovina_izris.append(zgodovina[-1])
            else:
                zgodovina_izris = zgodovina

            # Pretvori v canvas koordinate
            tocke = []
            for t, n in zgodovina_izris:
                px = self.ox + ((t - global_min_t) / razpon_t) * self.w
                py = self.oy - ((n - y_min) / razpon_y) * self.h
                tocke.append((px, py))

            potrebnih_crt = len(tocke) - 1
            obstojecih_crt = len(self._graf_linije.get(aid, []))

            if aid not in self._graf_linije:
                self._graf_linije[aid] = []

            linije = self._graf_linije[aid]

            # Recikliraj obstoječe linije z coords(), dodaj nove, briši odvečne
            for j in range(potrebnih_crt):
                x1, y1 = tocke[j]
                x2, y2 = tocke[j + 1]
                if j < obstojecih_crt:
                    self.canvas_graf.coords(linije[j], x1, y1, x2, y2)
                else:
                    lid = self.canvas_graf.create_line(x1, y1, x2, y2,
                                                       fill=barva, width=2, tags="pot")
                    linije.append(lid)

            # Briši odvečne linije če je točk zdaj manj (npr. po restartu)
            for j in range(potrebnih_crt, obstojecih_crt):
                self.canvas_graf.delete(linije[j])
            self._graf_linije[aid] = linije[:potrebnih_crt]

        # Legenda
        for i, aid in enumerate(agent_ids):
            barva = BARVE[i % len(BARVE)]
            lx = 60 + i * 80
            ly = 20
            self.canvas_graf.create_rectangle(lx, ly - 6, lx + 16, ly + 6,
                                              fill=barva, outline=barva, tags="legenda")
            self.canvas_graf.create_text(lx + 22, ly, text=f"A{i + 1}", anchor="w",
                                         font=("Arial", 8), tags="legenda")

    # ------------------------------------------------------------------ #
    #  Hover
    # ------------------------------------------------------------------ #
    def _hover_graf(self, event):
        self.zadnja_miska_x = event.x
        self.zadnja_miska_y = event.y
        self._osvezi_hover_vizualizacijo()

    def _osvezi_hover_vizualizacijo(self):
        self.canvas_graf.delete("hover")

        if not self.zgodovine or self.zadnja_miska_x is None:
            return

        v_coni_x = self.ox <= self.zadnja_miska_x <= (self.ox + self.w)
        v_coni_y = (self.oy - self.h) <= self.zadnja_miska_y <= self.oy
        if not (v_coni_x and v_coni_y):
            return

        global_min_t = None
        global_max_t = None
        global_min_n = None
        global_max_n = None
        for zgodovina in self.zgodovine.values():
            if len(zgodovina) >= 2:
                t_zac = zgodovina[0][0]
                t_kon = zgodovina[-1][0]
                vse_n = [p[1] for p in zgodovina]
                global_min_t = t_zac if global_min_t is None else min(global_min_t, t_zac)
                global_max_t = t_kon if global_max_t is None else max(global_max_t, t_kon)
                global_min_n = min(vse_n) if global_min_n is None else min(global_min_n, min(vse_n))
                global_max_n = max(vse_n) if global_max_n is None else max(global_max_n, max(vse_n))

        if global_max_t is None or global_max_t == global_min_t:
            return

        razpon_n = max(1, global_max_n - global_min_n)
        padding_n = razpon_n * 0.10
        y_min = max(0, global_min_n - padding_n)
        y_max = global_max_n + padding_n
        razpon_y = y_max - y_min

        razpon_t = global_max_t - global_min_t
        t_miska = global_min_t + ((self.zadnja_miska_x - self.ox) / self.w) * razpon_t

        # Navpična črta
        self.canvas_graf.create_line(self.zadnja_miska_x, self.oy - self.h,
                                     self.zadnja_miska_x, self.oy,
                                     fill="#cccccc", dash=(4, 4), tags="hover")

        agent_ids = list(self.sim_niti.keys())
        tekst_vrstice = []

        for i, aid in enumerate(agent_ids):
            zgodovina = self.zgodovine.get(aid, [])
            if len(zgodovina) < 2:
                continue

            barva = BARVE[i % len(BARVE)]
            najblizja = min(zgodovina, key=lambda p: abs(p[0] - t_miska))

            px = self.ox + ((najblizja[0] - global_min_t) / razpon_t) * self.w
            py = self.oy - ((najblizja[1] - y_min) / razpon_y) * self.h

            self.canvas_graf.create_oval(px - 4, py - 4, px + 4, py + 4,
                                         fill=barva, outline="white", tags="hover")

            tekst_vrstice.append((barva, f"A{i + 1} t:{najblizja[0]} N:{int(najblizja[1])}"))

        # Izpis besedila za vsak agent
        base_y = self.zadnja_miska_y - 15 - (len(tekst_vrstice) - 1) * 14
        for j, (barva, tekst) in enumerate(tekst_vrstice):
            self.canvas_graf.create_text(
                self.zadnja_miska_x, base_y + j * 14,
                text=tekst, anchor="s", font=("Arial", 8, "bold"),
                fill=barva, tags="hover"
            )


if __name__ == "__main__":
    app = GlavnoOkno()
    app.mainloop()
