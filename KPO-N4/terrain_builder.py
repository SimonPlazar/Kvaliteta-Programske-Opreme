import tkinter as tk
from tkinter import filedialog, messagebox
import json
import random
from noise import pnoise2

def generate_terrain_grid(width, height, cell_size, seed, scale, octaves, t_water, t_sand, t_grass, t_forest, t_mount):
    cols = width // cell_size
    rows = height // cell_size

    noise_grid = []
    min_n = float('inf')
    max_n = -float('inf')

    # Offset for seed instead of using 'base' parameter which can cause C-extension crashes
    seed_offset = float(seed) 

    for y in range(rows):
        row = []
        for x in range(cols):
            val = pnoise2((x + seed_offset) / scale, 
                          (y + seed_offset) / scale, 
                          octaves=octaves, 
                          persistence=0.5, 
                          lacunarity=2.0)
            row.append(val)
            if val < min_n: min_n = val
            if val > max_n: max_n = val
        noise_grid.append(row)

    grid_data = [] # Array of dicts or objects per cell

    for y in range(rows):
        row_data = []
        for x in range(cols):
            normalized = (noise_grid[y][x] - min_n) / (max_n - min_n + 1e-5)
            
            if normalized < t_water:
                ctype = 0 # Water
            elif normalized < t_sand:
                ctype = 1 # Sand
            elif normalized < t_grass:
                ctype = 2 # Grass
            elif normalized < t_forest:
                ctype = 3 # Forest
            elif normalized < t_mount:
                ctype = 4 # Mountain
            else:
                ctype = 5 # Peak

            # Store height value and type
            row_data.append({"h": round(normalized, 3), "t": ctype})
            
        grid_data.append(row_data)
        
    return grid_data

class TerrainBuilder(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Terrain Builder")
        self.grid_data = []

        # Default settings
        self.sim_width = 1200
        self.sim_height = 420
        self.cell_size = 10

        self._build_ui()
        self.generate_terrain()

    def _build_ui(self):
        # Top frame for Canvas
        top_frame = tk.Frame(self)
        top_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        self.canvas = tk.Canvas(top_frame, bg="black", width=self.sim_width, height=self.sim_height)
        self.canvas.pack(pady=10)

        # Bottom frame for Controls
        ctrl = tk.Frame(self)
        ctrl.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)

        # Base parameters
        col1 = tk.Frame(ctrl)
        col1.pack(side=tk.LEFT, padx=10, fill=tk.Y)
        
        tk.Label(col1, text="Width:").grid(row=0, column=0, sticky="e", pady=2)
        self.ent_w = tk.Entry(col1, width=10)
        self.ent_w.insert(0, str(self.sim_width))
        self.ent_w.grid(row=0, column=1)

        tk.Label(col1, text="Height:").grid(row=1, column=0, sticky="e", pady=2)
        self.ent_h = tk.Entry(col1, width=10)
        self.ent_h.insert(0, str(self.sim_height))
        self.ent_h.grid(row=1, column=1)

        tk.Label(col1, text="Cell Size:").grid(row=2, column=0, sticky="e", pady=2)
        self.ent_cell = tk.Entry(col1, width=10)
        self.ent_cell.insert(0, str(self.cell_size))
        self.ent_cell.grid(row=2, column=1)

        tk.Label(col1, text="Seed (-1 rand):").grid(row=3, column=0, sticky="e", pady=2)
        self.ent_seed = tk.Entry(col1, width=10)
        self.ent_seed.insert(0, "-1")
        self.ent_seed.grid(row=3, column=1)

        # Noise parameters
        col2 = tk.Frame(ctrl)
        col2.pack(side=tk.LEFT, padx=20, fill=tk.Y)
        
        tk.Label(col2, text="Noise Scale (Freq):").pack()
        self.scl_scale = tk.Scale(col2, from_=5, to=200, orient=tk.HORIZONTAL)
        self.scl_scale.set(50)
        self.scl_scale.pack(fill=tk.X)

        tk.Label(col2, text="Octaves:").pack()
        self.scl_oct = tk.Scale(col2, from_=1, to=8, orient=tk.HORIZONTAL)
        self.scl_oct.set(4)
        self.scl_oct.pack(fill=tk.X)

        # Biomes row 1
        col3 = tk.Frame(ctrl)
        col3.pack(side=tk.LEFT, padx=10, fill=tk.Y)
        
        tk.Label(col3, text="Water Thresh:").pack()
        self.scl_water = tk.Scale(col3, from_=0.0, to=1.0, resolution=0.01, orient=tk.HORIZONTAL)
        self.scl_water.set(0.40)
        self.scl_water.pack()

        tk.Label(col3, text="Sand Thresh:").pack()
        self.scl_sand = tk.Scale(col3, from_=0.0, to=1.0, resolution=0.01, orient=tk.HORIZONTAL)
        self.scl_sand.set(0.425)
        self.scl_sand.pack()

        # Biomes row 2
        col4 = tk.Frame(ctrl)
        col4.pack(side=tk.LEFT, padx=10, fill=tk.Y)
        
        tk.Label(col4, text="Grass Thresh:").pack()
        self.scl_grass = tk.Scale(col4, from_=0.0, to=1.0, resolution=0.01, orient=tk.HORIZONTAL)
        self.scl_grass.set(0.775)
        self.scl_grass.pack()

        tk.Label(col4, text="Forest Thresh:").pack()
        self.scl_forest = tk.Scale(col4, from_=0.0, to=1.0, resolution=0.01, orient=tk.HORIZONTAL)
        self.scl_forest.set(0.925)
        self.scl_forest.pack()

        # Biomes row 3
        col5 = tk.Frame(ctrl)
        col5.pack(side=tk.LEFT, padx=10, fill=tk.Y)
        
        tk.Label(col5, text="Mount Thresh:").pack()
        self.scl_mount = tk.Scale(col5, from_=0.0, to=1.0, resolution=0.01, orient=tk.HORIZONTAL)
        self.scl_mount.set(0.975)
        self.scl_mount.pack()

        # Buttons
        col6 = tk.Frame(ctrl)
        col6.pack(side=tk.RIGHT, padx=20, fill=tk.Y)
        
        tk.Button(col6, text="Random Seed & Generate", command=self.generate_random_seed, bg="#ddd").pack(fill=tk.X, pady=5)
        tk.Button(col6, text="Generate Preview", command=self.generate_terrain, bg="#ddd").pack(fill=tk.X, pady=5)
        tk.Button(col6, text="Save Terrain", command=self.save_terrain, bg="#b3e5fc").pack(fill=tk.X, pady=5)

    def generate_random_seed(self):
        self.ent_seed.delete(0, tk.END)
        self.ent_seed.insert(0, str(random.randint(0, 999999)))
        self.generate_terrain()

    def generate_terrain(self):
        try:
            self.sim_width = int(self.ent_w.get())
            self.sim_height = int(self.ent_h.get())
            self.cell_size = int(self.ent_cell.get())
            seed = int(self.ent_seed.get())
            if seed == -1:
                seed = random.randint(0, 999999)
            scale = float(self.scl_scale.get())
            octaves = int(self.scl_oct.get())

            t_water = float(self.scl_water.get())
            t_sand = max(t_water, float(self.scl_sand.get()))
            t_grass = max(t_sand, float(self.scl_grass.get()))
            t_forest = max(t_grass, float(self.scl_forest.get()))
            t_mount = max(t_forest, float(self.scl_mount.get()))

        except ValueError:
            messagebox.showerror("Error", "Invalid parameter values.")
            return

        cols = self.sim_width // self.cell_size
        rows = self.sim_height // self.cell_size

        self.grid_data = generate_terrain_grid(
            self.sim_width, self.sim_height, self.cell_size, seed, scale, octaves,
            t_water, t_sand, t_grass, t_forest, t_mount
        )

        colors = {
            0: "#2196f3", # Water
            1: "#f4d03f", # Sand
            2: "#2ecc71", # Grass
            3: "#1b5e20", # Forest
            4: "#795548", # Mountain
            5: "#fdfefe"  # Peak
        }

        self.canvas.delete("all")
        self.canvas.config(width=self.sim_width, height=self.sim_height)

        for y in range(rows):
            for x in range(cols):
                ctype = self.grid_data[y][x]["t"]
                color = colors.get(ctype, "#000")
                wx = x * self.cell_size
                wy = y * self.cell_size
                self.canvas.create_rectangle(wx, wy, wx+self.cell_size, wy+self.cell_size, fill=color, outline="")

    def save_terrain(self):
        if not self.grid_data:
            messagebox.showwarning("Warning", "Generate terrain first!")
            return
            
        filepath = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")], 
            initialdir="terrains",
            title="Save Terrain"
        )
        if filepath:
            data = {
                "width": self.sim_width,
                "height": self.sim_height,
                "cell_size": self.cell_size,
                "grid": self.grid_data
            }
            with open(filepath, "w") as f:
                json.dump(data, f)
            messagebox.showinfo("Success", f"Terrain saved successfully to {filepath}")

if __name__ == "__main__":
    app = TerrainBuilder()
    app.mainloop()
