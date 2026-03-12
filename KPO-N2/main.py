import tkinter as tk
import threading
import queue
import time
import random
import math

# --- KONFIGURACIJA IN KONSTANTE ---

# Barve tipov agentov
BARVA_M = "#3a7bd5"  # Miroljubno (modra)
BARVA_M_ORIS = "#1a4a8a"
BARVA_A = "#e03131"  # Agresivno (rdeča)
BARVA_A_ORIS = "#8b0000"
BARVA_HRANA = "#2ecc71"  # Hrana (zelena)
BARVA_ROB = "#cccccc"  # Rob polja

# Platno / agenti
PLATNO_SIM_VELIKOST = 450  # Širina/višina simulacijskega platna (px)
ROB_DEBELINA = 20  # Debelina roba (px) — bitja se spawna/vračajo sem
AGENT_POLMER = 5  # Polmer kroga agenta (px)
AGENT_HITROST = 6.0  # Pikslov na korak animacije (MOVE_TO / MOVE_BACK)
AGENT_OFFSET = 8  # Horizontalni odmik agentov na isti hrani (px)
HRANA_POLMER = 6  # Polmer oznake hrane (px)

# Simulacija
QUEUE_MAX = 100  # Maks. sporočil v vrsti
PRIVZETI_N0_M = "20"  # Začetno št. miroljubnih
PRIVZETI_N0_A = "20"  # Začetno št. agresivnih
PRIVZETI_HRANA = "25"  # Začetno št. parov hrane na generacijo
PRIVZETA_HITROST_SIM = "0.05"
PRIVZETA_HITROST_GRAF = "0.5"
SIM_OSVEZI_MS = 30  # Interval posodabljanja sim platna (ms)
GRAF_OSVEZI_MIN_MS = 50
GRAF_OSVEZI_FALLBACK_MS = 500
MAX_ZGODOVINA = 500  # Maks. točk zgodovine na tip

# Faze generacije
FAZA_SPAWN = 0
FAZA_PREMIK_DO = 1
FAZA_EVALVACIJA = 2
FAZA_PREMIK_OD = 3
FAZA_KONEC = 4

IMENA_FAZ = {
    FAZA_SPAWN: "Postavljanje",
    FAZA_PREMIK_DO: "Premik → hrana",
    FAZA_EVALVACIJA: "Evalvacija",
    FAZA_PREMIK_OD: "Premik → rob",
    FAZA_KONEC: "Konec generacije",
}

# Graf
GRAF_OX = 50
GRAF_OY = 400
GRAF_W = 350
GRAF_H = 350
GRAF_OS_X_KONEC = 410
GRAF_OS_Y_KONEC = 40
HOVER_FPS_MS = 16
HOVER_PIKA_R = 4
HOVER_TOOLTIP_DY = 13
MAX_TOCKE_GRAFA = 400

# UI
PLATNO_GRAF_VELIKOST = 450
SEZNAM_AGENTOV_VISINA = 80


# ---------------------------------------------------------------------------
# 1. DOMENSKI MODELI (MODEL)
# ---------------------------------------------------------------------------

class Agent:
    """Eno bitje — miroljubno ('M') ali agresivno ('A')."""

    def __init__(self, tip: str, x: float, y: float):
        self.tip = tip  # 'M' ali 'A'
        self.x = x
        self.y = y
        self.cilj_x: float | None = None  # None = brez dodeljene hrane / cilja
        self.cilj_y: float | None = None
        self.zivo = True
        self.slot_index: int = 0  # 0 = levo, 1 = desno (offset pri hrani)
        self._hrana_par: 'HranaPar | None' = None  # referenca na dodeljeni par hrane

    # ------------------------------------------------------------------ #
    #  Lastnosti                                                           #
    # ------------------------------------------------------------------ #

    @property
    def ima_cilj(self) -> bool:
        """True če ima agent nastavljen cilj (hrana ali rob)."""
        return self.cilj_x is not None

    @property
    def ima_hrano(self) -> bool:
        """True če je agentu dodeljena hrana."""
        return self._hrana_par is not None

    # ------------------------------------------------------------------ #
    #  Hrana — dodelitev in sprostitev (food logic živi tukaj)            #
    # ------------------------------------------------------------------ #

    def dodeli_hrano(self, par: 'HranaPar', slot_idx: int):
        """
        Agent si izbere prosti slot pri paru hrane.
        Izračuna odmik glede na slot in nastavi cilj premikanja.
        Logika offseta živi v agentu — engine samo poveže agenta s parom.
        """
        self._hrana_par = par
        self.slot_index = slot_idx
        # Slot 0 → levo (-AGENT_OFFSET), slot 1 → desno (+AGENT_OFFSET)
        odmik = AGENT_OFFSET * (slot_idx * 2 - 1)
        self.cilj_x = par.x + odmik
        self.cilj_y = par.y

    def spusti_hrano(self):
        """Agent nima dodeljene hrane — počisti referenco in cilj."""
        self._hrana_par = None
        self.cilj_x = None
        self.cilj_y = None

    def je_pristel_do_hrane(self) -> bool:
        """True če je agent prispel do svojega cilja (hrane)."""
        if self.cilj_x is None:
            return True
        return math.hypot(self.cilj_x - self.x, self.cilj_y - self.y) < AGENT_HITROST

    # ------------------------------------------------------------------ #
    #  Premikanje                                                          #
    # ------------------------------------------------------------------ #

    def nastavi_cilj(self, cx: float, cy: float):
        """Nastavi cilj premikanja (npr. rob po evalvaciji)."""
        self.cilj_x = cx
        self.cilj_y = cy

    def premakni_do_cilja(self, hitrost: float) -> bool:
        """
        Premakni se en korak proti nastavljenemu cilju.
        Vrne True ko smo prispeli.
        """
        if self.cilj_x is None:
            return True
        dx = self.cilj_x - self.x
        dy = self.cilj_y - self.y
        razdalja = math.hypot(dx, dy)
        if razdalja <= hitrost:
            self.x = self.cilj_x
            self.y = self.cilj_y
            return True
        self.x += (dx / razdalja) * hitrost
        self.y += (dy / razdalja) * hitrost
        return False

    def premakni_nakljucno(self, hitrost: float, velikost: int, rob: int):
        """
        Naključno premikanje za agente brez dodeljene hrane.
        Ostane znotraj notranjosti polja.
        """
        kot = random.uniform(0, 2 * math.pi)
        self.x += math.cos(kot) * hitrost
        self.y += math.sin(kot) * hitrost
        margin = rob + AGENT_POLMER
        self.x = max(margin, min(velikost - margin, self.x))
        self.y = max(margin, min(velikost - margin, self.y))


class HranaPar:
    """Par hrane — sprejme največ 2 agenta."""

    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y
        self.agenti: list[Agent] = []  # 0, 1 ali 2 agenta
        self.pojedo: bool = False  # True ko vsi dodeljeni agenti prispejo

    @property
    def zaseden(self) -> bool:
        return len(self.agenti) >= 2

    def preveri_in_oznaci_pojedo(self):
        """
        Preveri ali so vsi dodeljeni agenti prispeli do hrane.
        Če ja, označi hrano kot pojedo (izgine z platna).
        Logika preverjanja živi tukaj — engine samo pokliče to metodo.
        """
        if self.pojedo or not self.agenti:
            return
        if all(ag.je_pristel_do_hrane() for ag in self.agenti):
            self.pojedo = True


# ---------------------------------------------------------------------------
# 2. PRAVILA TEORIJE IGER (strategija — zamenjajte brez da ostalo pade)
# ---------------------------------------------------------------------------

def evalviraj_par(agenti: list[Agent]) -> None:
    """
    Aplicira pravila Hawk-Dove igre na seznam agentov pri enem paru hrane.
    Modificira agent.zivo in-place; klone doda v seznam (engine jih pobere).

    Pravila (iz specifikacije):
      0 agentov       → nič
      1 agent         → preživi + 1 potomec istega tipa (razmnoži se)
      M + M           → oba preživita, brez potomcev
      A + A           → oba umreta
      M + A srečanje  → A vedno preživi, 50% potomec tipa A
                         M preživi z verjetnostjo 50%
    """
    n = len(agenti)
    if n == 0:
        return

    if n == 1:
        # Samo en agent — preživi in se razmnoži (en potomec)
        agenti[0].zivo = True
        klon = Agent(agenti[0].tip, agenti[0].x, agenti[0].y)
        klon.zivo = True
        agenti.append(klon)
        return

    a, b = agenti[0], agenti[1]
    tipi = {a.tip, b.tip}

    if tipi == {'M'}:
        # M + M → oba preživita, brez potomcev
        a.zivo = True
        b.zivo = True

    elif tipi == {'A'}:
        # A + A → oba umreta
        a.zivo = False
        b.zivo = False

    else:
        # M + A srečanje
        m = a if a.tip == 'M' else b  # miroljubno
        ag = a if a.tip == 'A' else b  # agresivno

        # Agresivno vedno preživi
        ag.zivo = True
        # Miroljubno preživi z 50% verjetnostjo
        m.zivo = random.random() < 0.5
        # Agresivno se razmnoži z 50% verjetnostjo
        if random.random() < 0.5:
            klon = Agent('A', ag.x, ag.y)
            klon.zivo = True
            agenti.append(klon)


# ---------------------------------------------------------------------------
# 3. SIMULACIJSKI ENGINE (LOGIKA)
# ---------------------------------------------------------------------------

def _nakljucna_rob_tocka(velikost: int, rob: int) -> tuple[float, float]:
    """Vrne naključno točko na robu polja."""
    stran = random.randint(0, 3)
    if stran == 0:
        return float(random.randint(rob, velikost - rob)), float(rob)
    elif stran == 1:
        return float(random.randint(rob, velikost - rob)), float(velikost - rob)
    elif stran == 2:
        return float(rob), float(random.randint(rob, velikost - rob))
    else:
        return float(velikost - rob), float(random.randint(rob, velikost - rob))


def _nakljucna_notranja_tocka(velikost: int, rob: int) -> tuple[float, float]:
    """Vrne naključno točko v notranjosti (ne na robu)."""
    margin = rob + HRANA_POLMER + 10
    return (float(random.randint(margin, velikost - margin)),
            float(random.randint(margin, velikost - margin)))


class SimulacijaNit(threading.Thread):
    """
    Enotna simulacijska nit za oba tipa agentov.
    Fazni sistem: SPAWN → PREMIK_DO → EVALVACIJA → PREMIK_OD → KONEC → (ponovi)
    Na vsak tick (_korak) pošlje en payload v vrsto.
    """

    def __init__(self, data_queue: queue.Queue, n0_m: int, n0_a: int,
                 n_hrana: int, speed_entry: tk.Entry):
        super().__init__(daemon=True)
        self.data_queue = data_queue
        self.n0_m = n0_m
        self.n0_a = n0_a
        self.n_hrana = n_hrana
        self._speed_entry = speed_entry

        self._running = True
        self._paused = threading.Event()
        self._paused.set()  # set = teče, clear = pavza

        self.agenti: list[Agent] = []
        self.hrana: list[HranaPar] = []
        self.faza: int = FAZA_SPAWN
        self.generacija: int = 0
        self.graf_zgodovina: list[tuple[int, int, int]] = []  # (gen, n_M, n_A)

    # ------------------------------------------------------------------ #
    #  Javni vmesnik                                                       #
    # ------------------------------------------------------------------ #

    def stop(self):
        self._running = False
        self._paused.set()  # odblokira wait, da se nit zaključi

    def pauziraj(self):
        self._paused.clear()

    def nadaljuj(self):
        self._paused.set()

    @property
    def je_pavziran(self) -> bool:
        return not self._paused.is_set()

    # ------------------------------------------------------------------ #
    #  Zanka                                                               #
    # ------------------------------------------------------------------ #

    def run(self):
        while self._running:
            self._paused.wait()  # blokira, dokler ne nadaljujemo
            if not self._running:
                break
            self._korak()
            self._poslji_payload()
            time.sleep(self._get_speed())

    def _get_speed(self) -> float:
        try:
            val = float(self._speed_entry.get())
            if val > 0:
                return val
        except (ValueError, tk.TclError):
            pass
        return float(PRIVZETA_HITROST_SIM)

    # ------------------------------------------------------------------ #
    #  Fazni dispečer                                                      #
    # ------------------------------------------------------------------ #

    def _korak(self):
        if self.faza == FAZA_SPAWN:
            self._faza_spawn()
            self.faza = FAZA_PREMIK_DO

        elif self.faza == FAZA_PREMIK_DO:
            konec = self._faza_premik(na_hrano=True)
            if konec:
                self.faza = FAZA_EVALVACIJA

        elif self.faza == FAZA_EVALVACIJA:
            self._faza_evalvacija()
            self.faza = FAZA_PREMIK_OD

        elif self.faza == FAZA_PREMIK_OD:
            konec = self._faza_premik(na_hrano=False)
            if konec:
                self.faza = FAZA_KONEC

        elif self.faza == FAZA_KONEC:
            self._faza_konec()
            self.faza = FAZA_SPAWN

    # ------------------------------------------------------------------ #
    #  Posamezne faze                                                      #
    # ------------------------------------------------------------------ #

    def _faza_spawn(self):
        """Postavi hrano in agente; vsak agent si izbere prosti par hrane (maks. 2 na par)."""
        # Ustvari hrano v notranjosti
        self.hrana = [
            HranaPar(*_nakljucna_notranja_tocka(PLATNO_SIM_VELIKOST, ROB_DEBELINA))
            for _ in range(self.n_hrana)
        ]

        # Ustvari agente na robu (ali ohrani obstoječe pri naslednjih gen)
        if self.generacija == 0:
            self.agenti = (
                    [Agent('M', *_nakljucna_rob_tocka(PLATNO_SIM_VELIKOST, ROB_DEBELINA))
                     for _ in range(self.n0_m)] +
                    [Agent('A', *_nakljucna_rob_tocka(PLATNO_SIM_VELIKOST, ROB_DEBELINA))
                     for _ in range(self.n0_a)]
            )
        else:
            # Preseli preživele na rob, počisti stanje iz prejšnje generacije
            for ag in self.agenti:
                ag.x, ag.y = _nakljucna_rob_tocka(PLATNO_SIM_VELIKOST, ROB_DEBELINA)
                ag.spusti_hrano()  # počisti hrano in cilj
                ag.zivo = True

        # --- Dodelitev hrane ---
        # Vsak par hrane ponudi 2 slota. Agenti ki ne dobijo slota, tavajo naključno.
        random.shuffle(self.agenti)
        prosti_sloti: list[tuple[HranaPar, int]] = []
        for par in self.hrana:
            prosti_sloti.append((par, 0))  # slot levo
            prosti_sloti.append((par, 1))  # slot desno
        random.shuffle(prosti_sloti)

        for i, ag in enumerate(self.agenti):
            if i < len(prosti_sloti):
                par, slot_idx = prosti_sloti[i]
                par.agenti.append(ag)
                ag.dodeli_hrano(par, slot_idx)  # offset logika živi v Agent
            else:
                ag.spusti_hrano()  # ni prostega slota — tava naključno

    def _faza_premik(self, na_hrano: bool) -> bool:
        """
        Premakne vse agente en korak.
        na_hrano=True  → agenti s hrano gredo proti hrani; brez hrane tavajo naključno.
        na_hrano=False → vsi gredo proti robu (cilj nastavljen v evalvaciji).
        Vrne True ko so vsi agenti S CILJEM prispeli (brezcilje ne blokirajo).
        """
        vsi_prisli = True
        for ag in self.agenti:
            if ag.ima_hrano or (not na_hrano and ag.ima_cilj):
                # Premakni se proti cilju
                if not ag.premakni_do_cilja(AGENT_HITROST):
                    vsi_prisli = False
            elif na_hrano:
                # Nima hrane → tava naključno, ne blokira faze
                ag.premakni_nakljucno(AGENT_HITROST, PLATNO_SIM_VELIKOST, ROB_DEBELINA)

        return vsi_prisli

    def _faza_evalvacija(self):
        """
        Aplicira pravila Hawk-Dove na vsak par hrane.
        Agenti brez hrane (niso bili v nobenem paru) ne preživijo.
        Preživeli dobijo takoj rob-cilj za PREMIK_OD.
        Hrana se označi kot pojeda — izgine s platna ko se agenti začnejo vračati.
        """
        # Označi vso hrano kot pojedo — na platnu izgine od naslednjega ticka
        for par in self.hrana:
            par.pojedo = True

        novi_agenti: list[Agent] = []

        for par in self.hrana:
            if not par.agenti:
                continue
            evalviraj_par(par.agenti)
            for ag in par.agenti:
                if ag.zivo:
                    # Vsi preživeli (originali + kloni) sprostijo hrano-referenco
                    # in dobijo cilj za PREMIK_OD (rob)
                    ag.spusti_hrano()
                    ag.nastavi_cilj(*_nakljucna_rob_tocka(PLATNO_SIM_VELIKOST, ROB_DEBELINA))
                    novi_agenti.append(ag)

        self.agenti = novi_agenti

    def _faza_konec(self):
        """Zapiše statistiko, pripravi na naslednjo generacijo."""
        n_m = sum(1 for ag in self.agenti if ag.tip == 'M')
        n_a = sum(1 for ag in self.agenti if ag.tip == 'A')
        self.graf_zgodovina.append((self.generacija, n_m, n_a))
        if len(self.graf_zgodovina) > MAX_ZGODOVINA:
            self.graf_zgodovina.pop(0)
        self.generacija += 1

        # Če populacija izumre — ponastavi na začetne vrednosti
        if n_m + n_a == 0:
            self.agenti = (
                    [Agent('M', *_nakljucna_rob_tocka(PLATNO_SIM_VELIKOST, ROB_DEBELINA))
                     for _ in range(self.n0_m)] +
                    [Agent('A', *_nakljucna_rob_tocka(PLATNO_SIM_VELIKOST, ROB_DEBELINA))
                     for _ in range(self.n0_a)]
            )

    # ------------------------------------------------------------------ #
    #  Pošiljanje podatkov                                                 #
    # ------------------------------------------------------------------ #

    def _poslji_payload(self):
        """Pošlje en payload v vrsto. UI ga prebere v _procesiraj_vrsto."""
        payload = {
            'faza': self.faza,
            'faza_ime': IMENA_FAZ.get(self.faza, ''),
            'generacija': self.generacija,
            'agenti': [(ag.x, ag.y, ag.tip, ag.ima_hrano) for ag in self.agenti],
            # Pošlji samo hrano ki še ni pojeda — pojeda izgine z platna
            'hrana': [(h.x, h.y) for h in self.hrana if not h.pojedo],
            'graf_zgodovina': list(self.graf_zgodovina),
        }
        if self.data_queue.qsize() < QUEUE_MAX:
            self.data_queue.put(payload)


# ---------------------------------------------------------------------------
# 4. UI KOMPONENTE (VIEW)
# ---------------------------------------------------------------------------

class NastavitvenaVrstica(tk.Frame):
    """
    Fiksna vrstica za nastavitve enega tipa agenta (M ali A).
    Brez gumba za brisanje — tipov je vedno natanko dva.
    """

    def __init__(self, parent, tip: str, barva: str, privzeti_n0: str):
        super().__init__(parent, bd=1, relief=tk.GROOVE, pady=3)
        self.tip = tip
        self.pack(fill=tk.X, pady=1)

        tk.Label(self, bg=barva, width=2).pack(side=tk.LEFT, padx=(3, 5))
        ime = "Miroljubno (M)" if tip == 'M' else "Agresivno (A)"
        tk.Label(self, text=ime, font=("Arial", 8, "bold"), width=14, anchor='w').pack(side=tk.LEFT)

        tk.Label(self, text="N0:", font=("Arial", 8)).pack(side=tk.LEFT, padx=(8, 1))
        self.ent_n0 = tk.Entry(self, width=6, font=("Arial", 8))
        self.ent_n0.insert(0, privzeti_n0)
        self.ent_n0.pack(side=tk.LEFT)

    def pridobi_n0(self) -> int:
        try:
            return max(0, int(self.ent_n0.get()))
        except ValueError:
            return 0

    def nastavi_vnos(self, omogoceno: bool):
        self.ent_n0.config(state=tk.NORMAL if omogoceno else tk.DISABLED)


class Grafikon(tk.Canvas):
    """
    Platno za izris grafa populacije skozi generacije.
    Dve fiksni liniji: Miroljubno (modra) in Agresivno (rdeča).
    Podpira hover z navpično črto in tooltip.
    """

    # Mapiranje ključev na barve in oznake
    _SERIJE = [
        ('M', BARVA_M, "Miroljubno"),
        ('A', BARVA_A, "Agresivno"),
    ]

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.ox, self.oy = GRAF_OX, GRAF_OY
        self.w, self.h = GRAF_W, GRAF_H
        self.linije_refs: dict[str, list] = {'M': [], 'A': []}
        self.zadnja_miska = (None, None)
        self._zadnja_zgodovina: list[tuple] = []
        self._zadnje_skale = None
        self.bind("<Motion>", lambda e: self._set_miska(e.x, e.y))
        self.bind("<Leave>", lambda e: self._clear_miska())
        self._narisi_osi()
        self._hover_loop()

    def _narisi_osi(self):
        self.delete("os")
        self.create_line(self.ox, self.oy, self.ox, GRAF_OS_Y_KONEC, arrow=tk.LAST, tags="os")
        self.create_line(self.ox, self.oy, GRAF_OS_X_KONEC, self.oy, arrow=tk.LAST, tags="os")
        self.create_text(self.ox - 20, GRAF_OS_Y_KONEC, text="N", tags="os")
        self.create_text(GRAF_OS_X_KONEC, self.oy + 20, text="t (gen)", tags="os")
        # Legenda
        self.delete("legenda")
        for i, (_, barva, ime) in enumerate(self._SERIJE):
            lx = GRAF_OX + i * 100
            ly = 14
            self.create_rectangle(lx, ly - 5, lx + 12, ly + 5, fill=barva, outline=barva, tags="legenda")
            self.create_text(lx + 16, ly, text=ime, anchor="w", font=("Arial", 8), tags="legenda")

    def reset(self):
        self.delete("all")
        self.linije_refs = {'M': [], 'A': []}
        self._zadnja_zgodovina = []
        self._zadnje_skale = None
        self._narisi_osi()

    def posodobi(self, zgodovina: list[tuple[int, int, int]]):
        """Prejme seznam (gen, n_M, n_A) in izriše obe liniji."""
        if not zgodovina:
            return

        self._zadnja_zgodovina = list(zgodovina)

        # Če je samo ena točka, jo podvojimo da dobimo vidno "piko" na grafu
        if len(zgodovina) == 1:
            zgodovina = [zgodovina[0], zgodovina[0]]

        # Izračun skal
        vsi_gen = [p[0] for p in zgodovina]
        vsi_n = [p[1] for p in zgodovina] + [p[2] for p in zgodovina]
        min_t, max_t = min(vsi_gen), max(vsi_gen)
        # Enojna točka — daj minimalni razpon da se izognemo deljenju z 0
        if max_t == min_t:
            max_t = min_t + 1
        max_n = max(vsi_n)
        pad = max(max_n * 0.05, 1)
        min_y, max_y = 0.0, max_n + pad
        skale = (min_t, max_t, min_y, max_y)
        self._zadnje_skale = skale

        # Izriši vsako serijo
        for idx, (kljuc, barva, _) in enumerate(self._SERIJE):
            n_idx = idx + 1  # pozicija v tuplju (gen, n_M, n_A)
            data = [(p[0], p[n_idx]) for p in zgodovina]
            tocke = self._pretvori(data, *skale)
            self._izrisi_pot(kljuc, tocke, barva)

    def _pretvori(self, data, min_t, max_t, min_y, max_y):
        rt, ry = max_t - min_t, max_y - min_y
        if len(data) > MAX_TOCKE_GRAFA:
            k = len(data) / MAX_TOCKE_GRAFA
            data = [data[int(j * k)] for j in range(MAX_TOCKE_GRAFA)]
        return [(self.ox + ((t - min_t) / rt) * self.w,
                 self.oy - ((n - min_y) / ry) * self.h) for t, n in data]

    def _izrisi_pot(self, kljuc: str, tocke: list, barva: str):
        linije = self.linije_refs[kljuc]
        potrebno = len(tocke) - 1
        for j in range(potrebno):
            c = (*tocke[j], *tocke[j + 1])
            if j < len(linije):
                self.coords(linije[j], *c)
            else:
                lid = self.create_line(*c, fill=barva, width=2, tags="pot")
                linije.append(lid)
        for j in range(potrebno, len(linije)):
            self.delete(linije[j])
        self.linije_refs[kljuc] = linije[:potrebno]

    # -- Hover --
    def _set_miska(self, x, y):
        self.zadnja_miska = (x, y)

    def _clear_miska(self):
        self.zadnja_miska = (None, None)
        self.delete("hover")

    def _hover_loop(self):
        self._osvezi_hover()
        self.after(HOVER_FPS_MS, self._hover_loop)

    def _osvezi_hover(self):
        self.delete("hover")
        mx, my = self.zadnja_miska
        if mx is None or not self._zadnje_skale or not self._zadnja_zgodovina:
            return
        if not (self.ox <= mx <= self.ox + self.w):
            return

        min_t, max_t, min_y, max_y = self._zadnje_skale
        rt, ry = max_t - min_t, max_y - min_y
        t_mis = min_t + ((mx - self.ox) / self.w) * rt

        self.create_line(mx, self.oy - self.h, mx, self.oy,
                         fill="#aaaaaa", dash=(4, 4), tags="hover")

        najblizja = min(self._zadnja_zgodovina, key=lambda p: abs(p[0] - t_mis))
        gen, n_m, n_a = najblizja

        besedila = [
            (BARVA_M, f"Miroljubno: {n_m}"),
            (BARVA_A, f"Agresivno:  {n_a}"),
        ]

        for idx, (kljuc, barva, _) in enumerate(self._SERIJE):
            n_val = najblizja[idx + 1]
            px = self.ox + ((gen - min_t) / rt) * self.w
            py = self.oy - ((n_val - min_y) / ry) * self.h
            r = HOVER_PIKA_R
            self.create_oval(px - r, py - r, px + r, py + r,
                             fill=barva, outline="white", tags="hover")

        tip_x = mx + 12
        tip_y = my - 10 - len(besedila) * HOVER_TOOLTIP_DY
        self.create_text(tip_x, tip_y, text=f"gen = {gen}",
                         fill="#333333", anchor="w", font=("Arial", 8, "bold"), tags="hover")
        for j, (col, txt) in enumerate(besedila):
            self.create_text(tip_x, tip_y + HOVER_TOOLTIP_DY * (j + 1), text=txt,
                             fill=col, anchor="w", font=("Arial", 8, "bold"), tags="hover")


# ---------------------------------------------------------------------------
# 5. GLAVNA APLIKACIJA (CONTROLLER)
# ---------------------------------------------------------------------------

class EvolucijskaSimulacija(tk.Tk):

    def __init__(self):
        super().__init__()
        self.title("Evolucija Agresije — Hawk-Dove")

        self.nit: SimulacijaNit | None = None
        self.data_queue: queue.Queue = queue.Queue()
        self._resetiran = False
        self._zadnji_payload: dict | None = None

        self._ustvari_vmesnik()

    # ------------------------------------------------------------------ #
    #  Gradnja vmesnika                                                    #
    # ------------------------------------------------------------------ #

    def _ustvari_vmesnik(self):
        root_fm = tk.Frame(self, padx=10, pady=10)
        root_fm.pack(fill=tk.BOTH, expand=True)

        top_fm = tk.Frame(root_fm)
        top_fm.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # Simulacijsko platno
        self.platno_sim = tk.Canvas(top_fm, width=PLATNO_SIM_VELIKOST, height=PLATNO_SIM_VELIKOST,
                                    bg="#1a1a2e", relief=tk.SUNKEN, bd=1)
        self.platno_sim.pack(side=tk.LEFT, padx=5)
        self._narisi_rob_sim()

        # Grafikon
        self.platno_graf = Grafikon(top_fm, width=PLATNO_GRAF_VELIKOST, height=PLATNO_GRAF_VELIKOST,
                                    bg="#fdfdfd", relief=tk.SUNKEN, bd=1)
        self.platno_graf.pack(side=tk.RIGHT, padx=5)

        # Nadzorna plošča
        self.ctrl_fm = tk.LabelFrame(root_fm, text=" Nadzor simulacije ", padx=10, pady=8)
        self.ctrl_fm.pack(side=tk.BOTTOM, fill=tk.X, pady=8)

        self._zgradi_gumbe()
        self._zgradi_nastavitve()

        self.lbl_info = tk.Label(root_fm, text="Generacija: 0 | M: 0 | A: 0 | Faza: —",
                                 font=("Arial", 9, "bold"))
        self.lbl_info.pack(side=tk.BOTTOM, anchor="e")

    def _narisi_rob_sim(self):
        """Izriše označen rob polja."""
        s = PLATNO_SIM_VELIKOST
        r = ROB_DEBELINA
        self.platno_sim.create_rectangle(r, r, s - r, s - r,
                                         outline=BARVA_ROB, dash=(4, 4), tags="rob")

    def _zgradi_gumbe(self):
        btn_box = tk.Frame(self.ctrl_fm)
        btn_box.pack(fill=tk.X)

        self.btn_start = tk.Button(btn_box, text="ZAŽENI", bg="#ccffcc", width=12,
                                   command=self.start_simulacije)
        self.btn_start.pack(side=tk.LEFT, padx=2)

        self.btn_pause = tk.Button(btn_box, text="PAVZA", state=tk.DISABLED, width=12,
                                   command=self.toggle_pause)
        self.btn_pause.pack(side=tk.LEFT, padx=2)

        self.btn_restart = tk.Button(btn_box, text="RESTART", bg="#ffcccc", state=tk.DISABLED, width=12,
                                     command=self.restart_simulacije)
        self.btn_restart.pack(side=tk.LEFT, padx=2)

        tk.Label(btn_box, text="Hitrost Sim (s):").pack(side=tk.LEFT, padx=(20, 2))
        self.ent_sim_speed = tk.Entry(btn_box, width=6)
        self.ent_sim_speed.insert(0, PRIVZETA_HITROST_SIM)
        self.ent_sim_speed.pack(side=tk.LEFT)

        tk.Label(btn_box, text="Osveževanje Grafa (s):").pack(side=tk.LEFT, padx=(15, 2))
        self.ent_graf_speed = tk.Entry(btn_box, width=6)
        self.ent_graf_speed.insert(0, PRIVZETA_HITROST_GRAF)
        self.ent_graf_speed.pack(side=tk.LEFT)

    def _zgradi_nastavitve(self):
        """Dve fiksni vrstici (M, A) + vrstica za hrano — vse skupaj v isti plošči."""
        outer = tk.Frame(self.ctrl_fm, bd=1, relief=tk.SUNKEN)
        outer.pack(fill=tk.X, pady=6)

        self.vrstica_m = NastavitvenaVrstica(outer, 'M', BARVA_M, PRIVZETI_N0_M)
        self.vrstica_a = NastavitvenaVrstica(outer, 'A', BARVA_A, PRIVZETI_N0_A)

        # Vrstica za hrano
        hrana_fm = tk.Frame(outer, bd=1, relief=tk.GROOVE, pady=3)
        hrana_fm.pack(fill=tk.X, pady=1)
        tk.Label(hrana_fm, bg=BARVA_HRANA, width=2).pack(side=tk.LEFT, padx=(3, 5))
        tk.Label(hrana_fm, text="Parov hrane", font=("Arial", 8, "bold"),
                 width=14, anchor='w').pack(side=tk.LEFT)
        tk.Label(hrana_fm, text="N:", font=("Arial", 8)).pack(side=tk.LEFT, padx=(8, 1))
        self.ent_hrana = tk.Entry(hrana_fm, width=6, font=("Arial", 8))
        self.ent_hrana.insert(0, PRIVZETI_HRANA)
        self.ent_hrana.pack(side=tk.LEFT)

    # ------------------------------------------------------------------ #
    #  Upravljanje simulacije                                              #
    # ------------------------------------------------------------------ #

    def _nastavi_predvajanje_ui(self, tece: bool):
        if tece:
            self.btn_start.config(state=tk.DISABLED)
            self.btn_pause.config(state=tk.NORMAL, text="PAVZA")
            self.btn_restart.config(state=tk.NORMAL)
            self.ent_hrana.config(state=tk.DISABLED)
            self.vrstica_m.nastavi_vnos(False)
            self.vrstica_a.nastavi_vnos(False)
        else:
            self.btn_start.config(state=tk.NORMAL)
            self.btn_pause.config(state=tk.DISABLED, text="PAVZA")
            self.btn_restart.config(state=tk.DISABLED)
            self.ent_hrana.config(state=tk.NORMAL)
            self.vrstica_m.nastavi_vnos(True)
            self.vrstica_a.nastavi_vnos(True)

    def start_simulacije(self):
        self._resetiran = False
        try:
            n_hrana = max(1, int(self.ent_hrana.get()))
        except ValueError:
            return

        n0_m = self.vrstica_m.pridobi_n0()
        n0_a = self.vrstica_a.pridobi_n0()

        self.nit = SimulacijaNit(
            data_queue=self.data_queue,
            n0_m=n0_m,
            n0_a=n0_a,
            n_hrana=n_hrana,
            speed_entry=self.ent_sim_speed,
        )
        self.nit.start()

        self._nastavi_predvajanje_ui(True)
        self._procesiraj_vrsto()
        self._osvezi_grafikon()

    def toggle_pause(self):
        if self.nit is None:
            return
        if self.nit.je_pavziran:
            self.nit.nadaljuj()
            self.btn_pause.config(text="PAVZA")
        else:
            self.nit.pauziraj()
            self.btn_pause.config(text="NADALJUJ")

    def restart_simulacije(self):
        self._resetiran = True
        if self.nit:
            self.nit.stop()
            self.nit = None

        # Izprazni vrsto
        while not self.data_queue.empty():
            try:
                self.data_queue.get_nowait()
            except queue.Empty:
                break

        self._zadnji_payload = None

        self.platno_sim.delete("all")
        self._narisi_rob_sim()
        self.platno_graf.reset()
        self.lbl_info.config(text="Generacija: 0 | M: 0 | A: 0 | Faza: —")
        self._nastavi_predvajanje_ui(False)

    # ------------------------------------------------------------------ #
    #  Posodabljanje UI (after zanki)                                      #
    # ------------------------------------------------------------------ #

    def _procesiraj_vrsto(self):
        """Glavna animacijska zanka — bere iz queue in osvežuje platno."""
        if self._resetiran:
            return

        # Poberi zadnji payload (preskoči zastarele)
        zadnji = None
        try:
            while True:
                zadnji = self.data_queue.get_nowait()
        except queue.Empty:
            pass

        if zadnji is not None:
            self._zadnji_payload = zadnji
            self._izrisi_sim(zadnji)
            self._posodobi_info(zadnji)

        self.after(SIM_OSVEZI_MS, self._procesiraj_vrsto)

    def _izrisi_sim(self, payload: dict):
        """Izriše vse agente in hrano na simulacijsko platno."""
        self.platno_sim.delete("agenti")
        self.platno_sim.delete("hrana")

        # Hrana
        r = HRANA_POLMER
        for hx, hy in payload['hrana']:
            self.platno_sim.create_oval(hx - r, hy - r, hx + r, hy + r,
                                        fill=BARVA_HRANA, outline="#1a8a4a",
                                        width=1, tags="hrana")

        # Agenti — (x, y, tip, ima_hrano)
        for ax, ay, tip, ima_hrano in payload['agenti']:
            barva = BARVA_M if tip == 'M' else BARVA_A
            oris = BARVA_M_ORIS if tip == 'M' else BARVA_A_ORIS
            ar = AGENT_POLMER
            # Agenti brez hrane so nekoliko prosojni (tanjši obrob, svetlejša barva)
            self.platno_sim.create_oval(ax - ar, ay - ar, ax + ar, ay + ar,
                                        fill=barva, outline=oris,
                                        width=2 if ima_hrano else 1,
                                        tags="agenti")

    def _posodobi_info(self, payload: dict):
        n_m = sum(1 for _, _, t, _ in payload['agenti'] if t == 'M')
        n_a = sum(1 for _, _, t, _ in payload['agenti'] if t == 'A')
        gen = payload['generacija']
        faza = payload['faza_ime']
        self.lbl_info.config(text=f"Generacija: {gen} | M: {n_m} | A: {n_a} | Faza: {faza}")

    def _osvezi_grafikon(self):
        """Ločena, počasnejša zanka za osveževanje grafa."""
        if self._resetiran:
            return

        if self._zadnji_payload and self._zadnji_payload['graf_zgodovina']:
            self.platno_graf.posodobi(self._zadnji_payload['graf_zgodovina'])

        try:
            ms = max(GRAF_OSVEZI_MIN_MS, int(float(self.ent_graf_speed.get()) * 1000))
        except (ValueError, tk.TclError):
            ms = GRAF_OSVEZI_FALLBACK_MS

        self.after(ms, self._osvezi_grafikon)


if __name__ == "__main__":
    app = EvolucijskaSimulacija()
    app.mainloop()
