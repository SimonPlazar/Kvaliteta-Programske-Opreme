import tkinter as tk
import threading
import queue
import time
import random


class Agent:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.move = 20

    def premakni(self, meja_w, meja_h):
        # Naključno premikanje za -3 do 3 piksle
        self.x += random.uniform(-self.move, self.move)
        self.y += random.uniform(-self.move, self.move)

        # Odboj od robov, da ne uidejo iz vidnega polja
        self.x = max(10, min(meja_w - 10, self.x))
        self.y = max(10, min(meja_h - 10, self.y))


class SimulacijaNit(threading.Thread):
    def __init__(self, data_queue, parametri):
        super().__init__()
        self.data_queue = data_queue
        self.params = parametri
        self.running = True
        self.paused = False
        self.daemon = True

        # Ustvarimo začetno populacijo objektov
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

                nova_generacija = []

                for agent in self.agenti:
                    # 1. Premikanje
                    agent.premakni(450, 450)

                    # 2. Rojstvo (se zgodi neodvisno od smrti)
                    # Če se bitje razmnoži, dodamo novega agenta
                    if random.random() < r:
                        nova_generacija.append(Agent(agent.x, agent.y))

                    # 3. Smrt (preverimo, če obstoječi agent preživi)
                    # P_smrti se povečuje s številom bitij (logistična omejitev)
                    p_smrt = s + (k * n)
                    if random.random() >= p_smrt:
                        nova_generacija.append(agent)

                self.agenti = nova_generacija

                # Limitiranje izrisa zaradi performanc (vseeno pa simuliramo vse!)
                # Prikazujemo do 1000 agentov, da Tkinter ne zmrzne
                pozicije_za_izris = [(a.x, a.y) for a in self.agenti[:1000]]

                podatki = {
                    'n': len(self.agenti),
                    'cas': casovni_korak,
                    'pozicije': pozicije_za_izris
                }
                self.data_queue.put(podatki)
                casovni_korak += 1

            time.sleep(self.params['speed'])

    def stop(self):
        self.running = False


class GlavnoOkno(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Evolucijska Simulacija - Rast Populacije")

        # Prilagodimo okno, da bo dovolj prostora za dva kvadrata 450x450 + kontrole
        # self.geometry("1000x650")
        self.nacin_simulacije = tk.StringVar(value="agenti")

        self.podatki_zgodovina = []
        self.data_queue = queue.Queue()
        self.sim_thread = None

        self.zadnja_miska_x = None
        self.zadnja_miska_y = None

        self.w, self.h = 350, 350  # uporabna širina/višina
        self.ox, self.oy = 50, 400  # izvor (0,0) v pikslih

        self._ustvari_vmesnik()

    def _ustvari_vmesnik(self):
        main_container = tk.Frame(self, padx=5, pady=5)
        main_container.pack(fill=tk.BOTH, expand=True)

        frame_top = tk.Frame(main_container)
        frame_top.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.canvas_sim = tk.Canvas(frame_top, width=450, height=450, bg="white", highlightthickness=1,
                                    highlightbackground="gray")
        self.canvas_sim.pack(side=tk.LEFT, padx=2, pady=2)

        self.canvas_graf = tk.Canvas(frame_top, width=450, height=450, bg="#fdfdfd", highlightthickness=1,
                                     highlightbackground="gray")
        self.canvas_graf.pack(side=tk.RIGHT, padx=2, pady=2)
        self.canvas_graf.bind("<Motion>", self._hover_graf)

        self._narisi_osi()

        frame_ctrl = tk.LabelFrame(main_container, text=" Nadzor (Parametri 0-1) ", padx=5, pady=5)
        frame_ctrl.pack(side=tk.BOTTOM, fill=tk.X, pady=(5, 0))

        inputs_frame = tk.Frame(frame_ctrl)
        inputs_frame.pack(side=tk.LEFT)

        params = [("N0:", "ent_st", "50"), ("R:", "ent_r", "0.1"),
                  ("S:", "ent_s", "0.05"), ("K:", "ent_k", "0.0005"),
                  ("Osveževanje:", "ent_speed", "0.1")]

        for i, (label, attr, default) in enumerate(params):
            tk.Label(inputs_frame, text=label).grid(row=0, column=i * 2, padx=(5, 2))
            entry = tk.Entry(inputs_frame, width=6)
            entry.insert(0, default)
            entry.grid(row=0, column=i * 2 + 1)
            setattr(self, attr, entry)

        buttons_frame = tk.Frame(frame_ctrl)
        buttons_frame.pack(side=tk.RIGHT)

        self.btn_start = tk.Button(buttons_frame, text="Zaženi", command=self._start_simulacija, bg="#ccffcc")
        self.btn_start.pack(side=tk.LEFT, padx=2)

        self.btn_pause = tk.Button(buttons_frame, text="Pavza", command=self._toggle_pause, state=tk.DISABLED)
        self.btn_pause.pack(side=tk.LEFT, padx=2)

        self.btn_restart = tk.Button(buttons_frame, text="Restart", command=self._restart_simulacija, bg="#ffcccc", state=tk.DISABLED)
        self.btn_restart.pack(side=tk.LEFT, padx=2)

        self.lbl_info = tk.Label(main_container, text="Populacija: 0", font=("Arial", 9, "bold"))
        self.lbl_info.pack(side=tk.BOTTOM, anchor="e")

    def _narisi_osi(self):
        self.canvas_graf.delete("os")
        # Koordinati za kvadrat 450x450
        self.canvas_graf.create_line(50, 400, 50, 40, arrow=tk.LAST, tags="os")  # Y
        self.canvas_graf.create_line(50, 400, 410, 400, arrow=tk.LAST, tags="os")  # X
        self.canvas_graf.create_text(30, 40, text="N", tags="os")
        self.canvas_graf.create_text(410, 420, text="t", tags="os")

    def _start_simulacija(self):
        if self.sim_thread and self.sim_thread.is_alive(): return

        try:
            # Validacija in branje parametrov
            r = min(1.0, max(0.0, float(self.ent_r.get())))
            s = min(1.0, max(0.0, float(self.ent_s.get())))
            k = min(1.0, max(0.0, float(self.ent_k.get())))
            st = int(self.ent_st.get())
            speed = float(self.ent_speed.get())

            # Posodobimo vnosna polja, če so bile vrednosti izven meja
            self.ent_r.delete(0, tk.END);
            self.ent_r.insert(0, str(r))
            self.ent_s.delete(0, tk.END);
            self.ent_s.insert(0, str(s))
            self.ent_k.delete(0, tk.END);
            self.ent_k.insert(0, str(k))
        except ValueError:
            print("Napačen vnos parametrov!")
            return

        parametri = {'st': st, 'r': r, 's': s, 'k': k, 'speed': speed}
        self.sim_thread = SimulacijaNit(self.data_queue, parametri)
        self.sim_thread.start()
        self.btn_start.config(state=tk.DISABLED)   # ne moreš dvakrat zagnati
        self.btn_pause.config(state=tk.NORMAL)
        self.btn_restart.config(state=tk.NORMAL)   # zdaj lahko restartaš
        self._osvezi_prikaz()

    def _toggle_pause(self):
        if self.sim_thread:
            self.sim_thread.paused = not self.sim_thread.paused
            new_text = "Nadaljuj" if self.sim_thread.paused else "Pavza"
            self.btn_pause.config(text=new_text)

    def _restart_simulacija(self):
        if self.sim_thread:
            self.sim_thread.stop()
        self.podatki_zgodovina = []
        self.canvas_sim.delete("all")
        self.canvas_graf.delete("pot", "hover")
        self.lbl_info.config(text="Trenutna populacija: 0")
        self._narisi_osi()

        self.btn_start.config(state=tk.NORMAL)       # spet lahko zaženemo
        self.btn_pause.config(state=tk.DISABLED, text="Pavza")
        self.btn_restart.config(state=tk.DISABLED)   # ni simulacije za restartati

    def _osvezi_prikaz(self):
        """Glavna UI zanka, ki skrbi za prenos podatkov iz niti na zaslon."""
        novi_podatki_prisli = False

        try:
            # 'Poberemo' vse podatke, ki so se nabrali v vrsti, da UI ne zaostaja
            while True:
                podatki = self.data_queue.get_nowait()
                novi_podatki_prisli = True

                # 1. Posodobimo besedilo o populaciji
                self.lbl_info.config(text=f"Trenutna populacija: {podatki['n']}")

                # 2. Izris bitij (pobrišemo stara, narišemo nova)
                self.canvas_sim.delete("bitje")
                for x, y in podatki['pozicije']:
                    self.canvas_sim.create_oval(
                        x - 3, y - 3, x + 3, y + 3,
                        fill="blue", outline="darkblue", tags="bitje"
                    )

                # 3. Shranimo v zgodovino za graf
                self.podatki_zgodovina.append((podatki['cas'], podatki['n']))

        except queue.Empty:
            # Vrsta je prazna, gremo naprej na izris
            pass

        # Če smo v tem ciklu dobili nove podatke, osvežimo grafiko
        if novi_podatki_prisli:
            self._izris_grafa()
            # KLJUČNO: Osvežimo hover, tudi če miška miruje,
            # saj se je časovna skala grafa pod njo spremenila!
            self._osvezi_hover_vizualizacijo()

        # Nadaljujemo zanko, dokler nit teče
        if self.sim_thread and self.sim_thread.running:
            self.after(30, self._osvezi_prikaz)

    def _hover_graf(self, event):
        """Sproži se ob vsakem premiku miške nad grafom."""
        self.zadnja_miska_x = event.x
        self.zadnja_miska_y = event.y
        self._osvezi_hover_vizualizacijo()

    def _osvezi_hover_vizualizacijo(self):
        """Dejanski izris hover elementov na podlagi shranjenih koordinat miške."""
        self.canvas_graf.delete("hover")

        if not self.podatki_zgodovina or self.zadnja_miska_x is None:
            return

        max_t = self.podatki_zgodovina[-1][0]
        # DODAJ TA POGOJ:
        if max_t <= 0:
            return

        # MEJE:
        # x mora biti med 50 in 400 (50 + 350)
        # y mora biti med 50 in 400 (400 - 350)
        v_coni_x = self.ox <= self.zadnja_miska_x <= (self.ox + self.w)
        v_coni_y = (self.oy - self.h) <= self.zadnja_miska_y <= self.oy

        # Če miška NI v tem kvadratu, hoverja ne izrišemo in prekinemo funkcijo
        if not (v_coni_x and v_coni_y):
            return

        max_t = self.podatki_zgodovina[-1][0]
        max_n = max(p[1] for p in self.podatki_zgodovina)
        if max_n < 10: max_n = 10

        t_miska = ((self.zadnja_miska_x - self.ox) / self.w) * max_t
        najblizja = min(self.podatki_zgodovina, key=lambda p: abs(p[0] - t_miska))

        px = self.ox + (najblizja[0] / max_t) * self.w
        py = self.oy - (najblizja[1] / max_n) * self.h

        # Izris črte, pike in besedila...
        self.canvas_graf.create_line(px, self.oy - self.h, px, self.oy, fill="#cccccc", dash=(4, 4), tags="hover")
        self.canvas_graf.create_oval(px - 4, py - 4, px + 4, py + 4, fill="red", outline="white", tags="hover")

        self.canvas_graf.create_text(
            px, self.zadnja_miska_y - 15,
            text=f"t: {najblizja[0]}\nN: {int(najblizja[1])}",
            anchor="s", font=("Arial", 9, "bold"), justify=tk.CENTER,
            fill="black", tags="hover"
        )

    def _izris_grafa(self):
        if len(self.podatki_zgodovina) < 2: return
        self.canvas_graf.delete("pot")

        max_t = self.podatki_zgodovina[-1][0]
        if max_t <= 0:
            return

        max_n = max(p[1] for p in self.podatki_zgodovina)
        if max_n < 10: max_n = 10

        prejsnja = None
        for t, n in self.podatki_zgodovina:
            px = self.ox + (t / max_t) * self.w
            py = self.oy - (n / max_n) * self.h

            if prejsnja:
                self.canvas_graf.create_line(prejsnja[0], prejsnja[1], px, py, fill="red", width=2, tags="pot")
            prejsnja = (px, py)


if __name__ == "__main__":
    app = GlavnoOkno()
    app.mainloop()
