import csv
import queue
import statistics
import threading
import tkinter as tk
from tkinter import filedialog
from tkinter import ttk


class CsvAnalyzerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("CSV Analyzer")
        self.geometry("1200x700")

        self._load_queue = queue.Queue()
        self._current_path = None
        self._rows = []
        self._headers = []
        self._stats = []

        self._build_ui()
        self.after(100, self._poll_load_queue)

    def _build_ui(self):
        root = ttk.Frame(self, padding=10)
        root.pack(fill=tk.BOTH, expand=True)

        self._build_top_bar(root)
        self._build_main_area(root)

    def _build_top_bar(self, parent):
        bar = ttk.Frame(parent)
        bar.pack(fill=tk.X)

        self.path_var = tk.StringVar(value="No file selected")
        ttk.Label(bar, text="CSV:").pack(side=tk.LEFT)
        self.path_label = ttk.Label(bar, textvariable=self.path_var, width=80)
        self.path_label.pack(side=tk.LEFT, padx=(6, 10))

        self.btn_open = ttk.Button(bar, text="Open CSV", command=self._open_csv)
        self.btn_open.pack(side=tk.LEFT)

        self.loading_var = tk.StringVar(value="")
        ttk.Label(bar, textvariable=self.loading_var, foreground="#555555").pack(side=tk.LEFT, padx=10)

    def _build_main_area(self, parent):
        main = ttk.PanedWindow(parent, orient=tk.HORIZONTAL)
        main.pack(fill=tk.BOTH, expand=True, pady=(10, 0))

        left = ttk.Frame(main)
        right = ttk.Frame(main)
        main.add(left, weight=3)
        main.add(right, weight=2)

        self._build_preview_table(left)
        self._build_stats_table(right)
        self._build_column_detail(right)

    def _build_preview_table(self, parent):
        ttk.Label(parent, text="Preview (first 200 rows)").pack(anchor="w")
        container = ttk.Frame(parent)
        container.pack(fill=tk.BOTH, expand=True)

        self.preview_table = ttk.Treeview(container, show="headings")
        vsb = ttk.Scrollbar(container, orient="vertical", command=self.preview_table.yview)
        hsb = ttk.Scrollbar(container, orient="horizontal", command=self.preview_table.xview)
        self.preview_table.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.preview_table.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        hsb.pack(side=tk.BOTTOM, fill=tk.X)

    def _build_stats_table(self, parent):
        ttk.Label(parent, text="Numeric Column Stats").pack(anchor="w")
        self.stats_table = ttk.Treeview(
            parent,
            columns=("column", "count", "min", "max", "mean", "stdev"),
            show="headings",
            height=10,
        )
        for col, label in [
            ("column", "Column"),
            ("count", "Count"),
            ("min", "Min"),
            ("max", "Max"),
            ("mean", "Mean"),
            ("stdev", "Std"),
        ]:
            self.stats_table.heading(col, text=label)
            self.stats_table.column(col, width=90 if col != "column" else 140, anchor="w")

        self.stats_table.pack(fill=tk.X)
        self.stats_table.bind("<<TreeviewSelect>>", self._on_stat_selected)

    def _build_column_detail(self, parent):
        ttk.Label(parent, text="Selected Column Details").pack(anchor="w", pady=(10, 0))
        self.detail_text = tk.Text(parent, height=10, wrap=tk.WORD)
        self.detail_text.pack(fill=tk.BOTH, expand=True)
        self.detail_text.config(state=tk.DISABLED)

    def _set_loading(self, is_loading):
        self.btn_open.config(state=tk.DISABLED if is_loading else tk.NORMAL)
        self.loading_var.set("Loading..." if is_loading else "")

    def _open_csv(self):
        path = filedialog.askopenfilename(
            title="Open CSV",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
        )
        if not path:
            return

        self._current_path = path
        self.path_var.set(path)
        self._set_loading(True)

        thread = threading.Thread(target=self._load_csv_worker, args=(path,), daemon=True)
        thread.start()

    def _load_csv_worker(self, path):
        try:
            with open(path, "r", newline="", encoding="utf-8") as file:
                reader = csv.DictReader(file)
                headers = reader.fieldnames or []
                rows = []
                for row in reader:
                    rows.append(row)

            stats = self._compute_numeric_stats(headers, rows)
            preview_rows = rows[:200]

            self._load_queue.put({
                "path": path,
                "headers": headers,
                "rows": rows,
                "preview": preview_rows,
                "stats": stats,
            })
        except Exception as exc:
            self._load_queue.put({"error": str(exc)})

    def _compute_numeric_stats(self, headers, rows):
        stats = []
        for header in headers:
            values = []
            for row in rows:
                raw = row.get(header, "")
                if raw is None:
                    continue
                raw = str(raw).strip()
                if raw == "":
                    continue
                try:
                    values.append(float(raw))
                except ValueError:
                    values = []
                    break

            if not values:
                continue

            count = len(values)
            min_val = min(values)
            max_val = max(values)
            mean_val = statistics.mean(values)
            stdev_val = statistics.stdev(values) if count > 1 else 0.0

            stats.append({
                "column": header,
                "count": count,
                "min": min_val,
                "max": max_val,
                "mean": mean_val,
                "stdev": stdev_val,
            })

        return stats

    def _poll_load_queue(self):
        while not self._load_queue.empty():
            payload = self._load_queue.get_nowait()
            if "error" in payload:
                self._show_error(payload["error"])
            else:
                self._apply_loaded_data(payload)

        self.after(100, self._poll_load_queue)

    def _apply_loaded_data(self, payload):
        self._headers = payload["headers"]
        self._rows = payload["rows"]
        self._stats = payload["stats"]

        self._populate_preview_table(payload["preview"], self._headers)
        self._populate_stats_table(self._stats)
        self._show_detail_text("Select a numeric column to see details.")
        self._set_loading(False)

    def _populate_preview_table(self, rows, headers):
        self.preview_table.delete(*self.preview_table.get_children())
        self.preview_table["columns"] = headers

        for header in headers:
            self.preview_table.heading(header, text=header)
            self.preview_table.column(header, width=120, anchor="w")

        for row in rows:
            values = [row.get(header, "") for header in headers]
            self.preview_table.insert("", tk.END, values=values)

    def _populate_stats_table(self, stats):
        self.stats_table.delete(*self.stats_table.get_children())
        for row in stats:
            self.stats_table.insert(
                "",
                tk.END,
                values=(
                    row["column"],
                    row["count"],
                    f"{row['min']:.3f}",
                    f"{row['max']:.3f}",
                    f"{row['mean']:.3f}",
                    f"{row['stdev']:.3f}",
                ),
            )

    def _on_stat_selected(self, _event):
        selection = self.stats_table.selection()
        if not selection:
            return

        item = self.stats_table.item(selection[0])
        values = item.get("values", [])
        if not values:
            return

        detail = (
            f"Column: {values[0]}\n"
            f"Count: {values[1]}\n"
            f"Min: {values[2]}\n"
            f"Max: {values[3]}\n"
            f"Mean: {values[4]}\n"
            f"Std: {values[5]}\n"
        )
        self._show_detail_text(detail)

    def _show_detail_text(self, text):
        self.detail_text.config(state=tk.NORMAL)
        self.detail_text.delete("1.0", tk.END)
        self.detail_text.insert(tk.END, text)
        self.detail_text.config(state=tk.DISABLED)

    def _show_error(self, message):
        self._set_loading(False)
        self._show_detail_text(f"Error while loading CSV:\n{message}")


if __name__ == "__main__":
    app = CsvAnalyzerApp()
    app.mainloop()

