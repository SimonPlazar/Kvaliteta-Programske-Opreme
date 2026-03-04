import tkinter as tk
import threading
import queue
import time
import random


class SimulacijaNit(threading.Thread):
    def __init__(self, data_queue, parametri):
        super().__init__()
        self.data_queue = data_queue
        self.params = parametri
        self.running = True
        self.paused = False  # Dodana zastavica za pavzo
        self.daemon = True

    def run(self):
        populacija = int(self.params['st'])
        casovni_korak = 0

        while self.running:
            if not self.paused:
                # --- LOGIKA SIMULACIJE ---
                # Primer enačbe: Delta N = (R - S - K * N) * N
                r = self.params['r']
                s = self.params['s']
                k = self.params['k']

                delta_n = (r - s - k * populacija) * populacija
                populacija = max(0, populacija + delta_n)
                casovni_korak += 1

                # Vizualizacija bitij (omejimo na 150 krogcev za performans)
                st_za_izris = min(int(populacija), 150)
                pozicije = [(random.randint(10, 440), random.randint(10, 440)) for _ in range(st_za_izris)]

                podatki = {
                    'n': int(populacija),
                    'cas': casovni_korak,
                    'pozicije': pozicije
                }
                self.data_queue.put(podatki)

            # Spanje glede na nastavljeno hitrost
            time.sleep(self.params['speed'])

    def stop(self):
        self.running = False


class GlavnoOkno(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Evolucijska Simulacija - Rast Populacije")
        
        # Prilagodimo okno, da bo dovolj prostora za dva kvadrata 450x450 + kontrole
        # self.geometry("1000x650")

        self.podatki_zgodovina = []
        self.data_queue = queue.Queue()
        self.sim_thread = None

        self.zadnja_miska_x = None
        self.zadnja_miska_y = None

        self._ustvari_vmesnik()

    def _ustvari_vmesnik(self):
        # --- ZGORNJI DEL: KVADRATNA PLATNA ---
        frame_top = tk.Frame(self)
        frame_top.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Platno za bitja (Kvadrat 450x450)
        self.canvas_sim = tk.Canvas(frame_top, width=450, height=450, bg="white", highlightthickness=1,
                                    highlightbackground="black")
        self.canvas_sim.pack(side=tk.LEFT, padx=10)

        # Platno za graf (Kvadrat 450x450)
        self.canvas_graf = tk.Canvas(frame_top, width=450, height=450, bg="#fdfdfd", highlightthickness=1,
                                     highlightbackground="black")
        self.canvas_graf.pack(side=tk.RIGHT, padx=10)
        self.canvas_graf.bind("<Motion>", self._hover_graf)

        self._narisi_osi()

        # --- SPODNJI DEL: NADZORNA PLOŠČA ---
        frame_ctrl = tk.LabelFrame(self, text=" Nadzor simulacije ", padx=10, pady=10)
        frame_ctrl.pack(side=tk.BOTTOM, fill=tk.X, padx=20, pady=10)

        # Vrstica za parametre
        inputs_frame = tk.Frame(frame_ctrl)
        inputs_frame.pack(side=tk.TOP, fill=tk.X)

        tk.Label(inputs_frame, text="N0:").grid(row=0, column=0)
        self.ent_st = tk.Entry(inputs_frame, width=5);
        self.ent_st.insert(0, "10")
        self.ent_st.grid(row=0, column=1, padx=5)

        tk.Label(inputs_frame, text="R:").grid(row=0, column=2)
        self.ent_r = tk.Entry(inputs_frame, width=5);
        self.ent_r.insert(0, "0.1")
        self.ent_r.grid(row=0, column=3, padx=5)

        tk.Label(inputs_frame, text="S:").grid(row=0, column=4)
        self.ent_s = tk.Entry(inputs_frame, width=5);
        self.ent_s.insert(0, "0.05")
        self.ent_s.grid(row=0, column=5, padx=5)

        tk.Label(inputs_frame, text="K:").grid(row=0, column=6)
        self.ent_k = tk.Entry(inputs_frame, width=8);
        self.ent_k.insert(0, "0.0005")
        self.ent_k.grid(row=0, column=7, padx=5)

        tk.Label(inputs_frame, text="Osveževanje (s):").grid(row=0, column=8)
        self.ent_speed = tk.Entry(inputs_frame, width=5);
        self.ent_speed.insert(0, "0.05")
        self.ent_speed.grid(row=0, column=9, padx=5)

        # Vrstica za gumbe
        buttons_frame = tk.Frame(frame_ctrl, pady=10)
        buttons_frame.pack(side=tk.TOP, fill=tk.X)

        self.btn_start = tk.Button(buttons_frame, text="Zaženi", command=self._start_simulacija, width=10, bg="#ccffcc")
        self.btn_start.pack(side=tk.LEFT, padx=5)

        self.btn_pause = tk.Button(buttons_frame, text="Pavza", command=self._toggle_pause, width=10, state=tk.DISABLED)
        self.btn_pause.pack(side=tk.LEFT, padx=5)

        self.btn_restart = tk.Button(buttons_frame, text="Ponovi (Restart)", command=self._restart_simulacija, width=15,
                                     bg="#ffcccc")
        self.btn_restart.pack(side=tk.LEFT, padx=5)

        self.lbl_info = tk.Label(buttons_frame, text="Trenutna populacija: 0", font=("Arial", 10, "bold"), padx=20)
        self.lbl_info.pack(side=tk.RIGHT)

    def _narisi_osi(self):
        self.canvas_graf.delete("os")
        # Koordinati za kvadrat 450x450
        self.canvas_graf.create_line(50, 400, 50, 40, arrow=tk.LAST, tags="os")  # Y
        self.canvas_graf.create_line(50, 400, 410, 400, arrow=tk.LAST, tags="os")  # X
        self.canvas_graf.create_text(30, 40, text="N", tags="os")
        self.canvas_graf.create_text(410, 420, text="t", tags="os")

    def _start_simulacija(self):
        if self.sim_thread and self.sim_thread.is_alive():
            return  # Že teče

        parametri = {
            'st': self.ent_st.get(),
            'r': float(self.ent_r.get()),
            's': float(self.ent_s.get()),
            'k': float(self.ent_k.get()),
            'speed': float(self.ent_speed.get())
        }

        self.sim_thread = SimulacijaNit(self.data_queue, parametri)
        self.sim_thread.start()

        self.btn_start.config(state=tk.DISABLED)
        self.btn_pause.config(state=tk.NORMAL, text="Pavza")
        self.btn_restart.config(state=tk.NORMAL)
        self._osvezi_prikaz()

    def _toggle_pause(self):
        if self.sim_thread:
            self.sim_thread.paused = not self.sim_thread.paused
            new_text = "Nadaljuj" if self.sim_thread.paused else "Pavza"
            self.btn_pause.config(text=new_text)

    def _restart_simulacija(self):
        # 1. Ustavi nit
        if self.sim_thread:
            self.sim_thread.stop()

        # 2. Pobriši podatke
        self.podatki_zgodovina = []
        self.canvas_sim.delete("all")
        self.canvas_graf.delete("pot", "hover")
        self.lbl_info.config(text="Trenutna populacija: 0")

        # 3. Omogoči ponoven zagon
        self.btn_start.config(state=tk.NORMAL)
        self.btn_pause.config(state=tk.DISABLED, text="Pavza")

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

        # Preverimo, če sploh imamo podatke in če je bila miška že nad grafom
        if not self.podatki_zgodovina or self.zadnja_miska_x is None:
            return

        # Parametri grafa (morajo biti enaki kot v _izris_grafa)
        ox, oy = 50, 400
        w, h = 350, 350
        max_t = self.podatki_zgodovina[-1][0]
        max_n = max(p[1] for p in self.podatki_zgodovina)
        if max_n < 10: max_n = 10

        # Izračunamo 't' iz piksla miške
        t_miska = ((self.zadnja_miska_x - ox) / w) * max_t

        # Najdemo najbližjo točko v zgodovini
        # Omejimo iskanje na realno območje grafa
        if ox <= self.zadnja_miska_x <= ox + w:
            najblizja = min(self.podatki_zgodovina, key=lambda p: abs(p[0] - t_miska))

            # Preračunamo piksle za točko na grafu
            px = ox + (najblizja[0] / max_t) * w
            py = oy - (najblizja[1] / max_n) * h

            # Narišemo navpično črto
            self.canvas_graf.create_line(px, 50, px, 400, fill="#cccccc", dash=(4, 4), tags="hover")

            # Narišemo piko na grafu, ki sledi črti
            self.canvas_graf.create_oval(px - 4, py - 4, px + 4, py + 4, fill="red", outline="white", tags="hover")

            # Izpišemo vrednost
            self.canvas_graf.create_text(
                px, self.zadnja_miska_y - 15,
                text=f"t: {najblizja[0]}\nN: {najblizja[1]}",
                anchor="s", font=("Arial", 9, "bold"), justify=tk.CENTER,
                fill="black", tags="hover"
            )

    def _izris_grafa(self):
        if len(self.podatki_zgodovina) < 2: return
        self.canvas_graf.delete("pot")

        max_t = self.podatki_zgodovina[-1][0]
        max_n = max(p[1] for p in self.podatki_zgodovina)
        if max_n < 10: max_n = 10

        # Dimenzije grafa znotraj platna
        w, h = 350, 350  # uporabna širina/višina
        ox, oy = 50, 400  # izvor (0,0) v pikslih

        prejsnja = None
        for t, n in self.podatki_zgodovina:
            px = ox + (t / max_t) * w
            py = oy - (n / max_n) * h

            if prejsnja:
                self.canvas_graf.create_line(prejsnja[0], prejsnja[1], px, py, fill="red", width=2, tags="pot")
            prejsnja = (px, py)


if __name__ == "__main__":
    app = GlavnoOkno()
    app.mainloop()
