import tkinter as tk
from tkinter import filedialog, messagebox
import json
import random
from dataclasses import dataclass
from noise import pnoise2


@dataclass(frozen=True)
class TerrainThresholds:
    water: float
    sand: float
    grass: float
    forest: float
    mountain: float

    @classmethod
    def normalized(cls, water, sand, grass, forest, mountain):
        normalized_sand = max(water, sand)
        normalized_grass = max(normalized_sand, grass)
        normalized_forest = max(normalized_grass, forest)
        normalized_mountain = max(normalized_forest, mountain)
        return cls(water, normalized_sand, normalized_grass, normalized_forest, normalized_mountain)

    def classify(self, normalized_height):
        if normalized_height < self.water:
            return 0
        if normalized_height < self.sand:
            return 1
        if normalized_height < self.grass:
            return 2
        if normalized_height < self.forest:
            return 3
        if normalized_height < self.mountain:
            return 4
        return 5


def _build_noise_grid(cols, rows, seed_offset, scale, octaves):
    noise_grid = []
    min_noise = float('inf')
    max_noise = -float('inf')

    for y in range(rows):
        row = []
        for x in range(cols):
            noise_value = pnoise2(
                (x + seed_offset) / scale,
                (y + seed_offset) / scale,
                octaves=octaves,
                persistence=0.5,
                lacunarity=2.0,
            )
            row.append(noise_value)
            min_noise = min(min_noise, noise_value)
            max_noise = max(max_noise, noise_value)
        noise_grid.append(row)

    return noise_grid, min_noise, max_noise

def generate_terrain_grid(
    width,
    height,
    cell_size,
    seed,
    scale,
    octaves,
    water_threshold,
    sand_threshold,
    grass_threshold,
    forest_threshold,
    mountain_threshold,
):
    cols = width // cell_size
    rows = height // cell_size

    thresholds = TerrainThresholds.normalized(
        water_threshold,
        sand_threshold,
        grass_threshold,
        forest_threshold,
        mountain_threshold,
    )

    # Use coordinate offset instead of the pnoise2 base parameter for better runtime stability.
    seed_offset = float(seed)
    noise_grid, min_n, max_n = _build_noise_grid(cols, rows, seed_offset, scale, octaves)

    grid_data = []

    for y in range(rows):
        row_data = []
        for x in range(cols):
            normalized = (noise_grid[y][x] - min_n) / (max_n - min_n + 1e-5)
            terrain_type = thresholds.classify(normalized)

            row_data.append({"h": round(normalized, 3), "t": terrain_type})
            
        grid_data.append(row_data)
        
    return grid_data

class TerrainBuilder(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Terrain Builder")
        self.grid_data = []

        self.sim_width = 1200
        self.sim_height = 420
        self.cell_size = 10

        self._build_ui()
        self.generate_terrain()

    def _build_ui(self):
        top_frame = tk.Frame(self)
        top_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        self.canvas = tk.Canvas(top_frame, bg="black", width=self.sim_width, height=self.sim_height)
        self.canvas.pack(pady=10)

        ctrl = tk.Frame(self)
        ctrl.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)

        col1 = tk.Frame(ctrl)
        col1.pack(side=tk.LEFT, padx=10, fill=tk.Y)
        
        tk.Label(col1, text="Width:").grid(row=0, column=0, sticky="e", pady=2)
        self.entry_width = tk.Entry(col1, width=10)
        self.entry_width.insert(0, str(self.sim_width))
        self.entry_width.grid(row=0, column=1)

        tk.Label(col1, text="Height:").grid(row=1, column=0, sticky="e", pady=2)
        self.entry_height = tk.Entry(col1, width=10)
        self.entry_height.insert(0, str(self.sim_height))
        self.entry_height.grid(row=1, column=1)

        tk.Label(col1, text="Cell Size:").grid(row=2, column=0, sticky="e", pady=2)
        self.entry_cell_size = tk.Entry(col1, width=10)
        self.entry_cell_size.insert(0, str(self.cell_size))
        self.entry_cell_size.grid(row=2, column=1)

        tk.Label(col1, text="Seed (-1 rand):").grid(row=3, column=0, sticky="e", pady=2)
        self.entry_seed = tk.Entry(col1, width=10)
        self.entry_seed.insert(0, "-1")
        self.entry_seed.grid(row=3, column=1)

        col2 = tk.Frame(ctrl)
        col2.pack(side=tk.LEFT, padx=20, fill=tk.Y)
        
        tk.Label(col2, text="Noise Scale (Freq):").pack()
        self.scale_noise_frequency = tk.Scale(col2, from_=5, to=200, orient=tk.HORIZONTAL)
        self.scale_noise_frequency.set(50)
        self.scale_noise_frequency.pack(fill=tk.X)

        tk.Label(col2, text="Octaves:").pack()
        self.scale_octaves = tk.Scale(col2, from_=1, to=8, orient=tk.HORIZONTAL)
        self.scale_octaves.set(4)
        self.scale_octaves.pack(fill=tk.X)

        col3 = tk.Frame(ctrl)
        col3.pack(side=tk.LEFT, padx=10, fill=tk.Y)
        
        tk.Label(col3, text="Water Thresh:").pack()
        self.scale_water_threshold = tk.Scale(col3, from_=0.0, to=1.0, resolution=0.01, orient=tk.HORIZONTAL)
        self.scale_water_threshold.set(0.40)
        self.scale_water_threshold.pack()

        tk.Label(col3, text="Sand Thresh:").pack()
        self.scale_sand_threshold = tk.Scale(col3, from_=0.0, to=1.0, resolution=0.01, orient=tk.HORIZONTAL)
        self.scale_sand_threshold.set(0.425)
        self.scale_sand_threshold.pack()

        col4 = tk.Frame(ctrl)
        col4.pack(side=tk.LEFT, padx=10, fill=tk.Y)
        
        tk.Label(col4, text="Grass Thresh:").pack()
        self.scale_grass_threshold = tk.Scale(col4, from_=0.0, to=1.0, resolution=0.01, orient=tk.HORIZONTAL)
        self.scale_grass_threshold.set(0.775)
        self.scale_grass_threshold.pack()

        tk.Label(col4, text="Forest Thresh:").pack()
        self.scale_forest_threshold = tk.Scale(col4, from_=0.0, to=1.0, resolution=0.01, orient=tk.HORIZONTAL)
        self.scale_forest_threshold.set(0.925)
        self.scale_forest_threshold.pack()

        col5 = tk.Frame(ctrl)
        col5.pack(side=tk.LEFT, padx=10, fill=tk.Y)
        
        tk.Label(col5, text="Mount Thresh:").pack()
        self.scale_mountain_threshold = tk.Scale(col5, from_=0.0, to=1.0, resolution=0.01, orient=tk.HORIZONTAL)
        self.scale_mountain_threshold.set(0.975)
        self.scale_mountain_threshold.pack()

        col6 = tk.Frame(ctrl)
        col6.pack(side=tk.RIGHT, padx=20, fill=tk.Y)
        
        tk.Button(col6, text="Random Seed & Generate", command=self.generate_random_seed, bg="#ddd").pack(fill=tk.X, pady=5)
        tk.Button(col6, text="Generate Preview", command=self.generate_terrain, bg="#ddd").pack(fill=tk.X, pady=5)
        tk.Button(col6, text="Save Terrain", command=self.save_terrain, bg="#b3e5fc").pack(fill=tk.X, pady=5)

    def generate_random_seed(self):
        self.entry_seed.delete(0, tk.END)
        self.entry_seed.insert(0, str(random.randint(0, 999999)))
        self.generate_terrain()

    def generate_terrain(self):
        try:
            self.sim_width = int(self.entry_width.get())
            self.sim_height = int(self.entry_height.get())
            self.cell_size = int(self.entry_cell_size.get())
            seed = int(self.entry_seed.get())
            if seed == -1:
                seed = random.randint(0, 999999)
            scale = float(self.scale_noise_frequency.get())
            octaves = int(self.scale_octaves.get())
            thresholds = TerrainThresholds.normalized(
                float(self.scale_water_threshold.get()),
                float(self.scale_sand_threshold.get()),
                float(self.scale_grass_threshold.get()),
                float(self.scale_forest_threshold.get()),
                float(self.scale_mountain_threshold.get()),
            )

        except ValueError:
            messagebox.showerror("Error", "Invalid parameter values.")
            return

        cols = self.sim_width // self.cell_size
        rows = self.sim_height // self.cell_size

        self.grid_data = generate_terrain_grid(
            self.sim_width, self.sim_height, self.cell_size, seed, scale, octaves,
            thresholds.water,
            thresholds.sand,
            thresholds.grass,
            thresholds.forest,
            thresholds.mountain,
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
                terrain_type = self.grid_data[y][x]["t"]
                color = colors.get(terrain_type, "#000")
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
