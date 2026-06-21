from __future__ import annotations

import csv
import random
import sys
from pathlib import Path
from tkinter import END, filedialog, messagebox
import tkinter as tk
from tkinter import ttk

try:
    from scheduler import Process, ScheduleResult, compare_all, run_algorithm
except ImportError:
    current_dir = Path(__file__).resolve().parent
    sys.path.append(str(current_dir))
    from scheduler import Process, ScheduleResult, compare_all, run_algorithm


PROCESS_COLORS = [
    "#38bdf8",  
    "#a78bfa",  
    "#34d399",  
    "#fbbf24",  
    "#fb7185",  
    "#60a5fa",  
    "#f472b6",  
    "#2dd4bf",  
    "#c084fc",  
    "#f97316",  
]

THEMES = {
    "dark": {
        "bg": "#020617",
        "panel": "#0f172a",
        "card": "#111827",
        "card2": "#1e293b",
        "line": "#334155",
        "fg": "#e5e7eb",
        "muted": "#94a3b8",
        "accent": "#38bdf8",
        "accent2": "#a78bfa",
        "success": "#22c55e",
        "danger": "#ef4444",
        "warning": "#f59e0b",
        "entry": "#0b1120",
        "table": "#0f172a",
        "table_head": "#1e293b",

    },
}


class ModernCPUSchedulingApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("CPU Scheduling Simulator")
        self.geometry("1280x860")
        self.minsize(1050, 700)

        self.theme_name = "dark"
        self.theme = THEMES[self.theme_name]
        self.configure(bg=self.theme["bg"])

        self.processes: list[Process] = []
        self.process_colors: dict[str, str] = {}
        self.last_result: ScheduleResult | None = None
        self._animation_token = 0

        self.pid_var = tk.StringVar(value="P1")
        self.arrival_var = tk.StringVar(value="0")
        self.burst_var = tk.StringVar(value="5")
        self.priority_var = tk.StringVar(value="1")
        self.algorithm_var = tk.StringVar(value="FCFS")
        self.quantum_var = tk.StringVar(value="2")
        self.status_var = tk.StringVar(value="Ready. Add processes, choose an algorithm, then run the simulator.")

        self._all_buttons: list[tk.Label] = []
        self._all_cards: list[tk.Frame] = []
        self._all_labels: list[tk.Label] = []
        self._all_entries: list[tk.Entry] = []
        self._algorithm_buttons: list[tk.Label] = []

        self._configure_ttk_style()
        self._build_layout()
        self.load_sample_data()

    # ------------------------------------------------------------------
    # UI PARTS
    # ------------------------------------------------------------------
    def _configure_ttk_style(self) -> None:
        style = ttk.Style(self)
        style.theme_use("clam")
        t = self.theme
        style.configure(
            "Modern.Treeview",
            background=t["table"],
            foreground=t["fg"],
            fieldbackground=t["table"],
            bordercolor=t["line"],
            rowheight=24,
            font=("Arial", 10),
        )
        style.configure(
            "Modern.Treeview.Heading",
            background=t["table_head"],
            foreground=t["fg"],
            relief="flat",
            font=("Arial", 10, "bold"),
        )
        style.map("Modern.Treeview", background=[("selected", t["accent"])])

    def _build_layout(self) -> None:
        self.header = tk.Frame(self, bg=self.theme["bg"], padx=20, pady=10)
        self.header.pack(fill="x")

        title_area = tk.Frame(self.header, bg=self.theme["bg"])
        title_area.pack(side="left", fill="x", expand=True)

        self.hero_title = tk.Label(
            title_area,
            text="CPU Scheduling Simulator",
            bg=self.theme["bg"],
            fg=self.theme["fg"],
            font=("Arial", 23, "bold"),
            anchor="w",
        )
        self.hero_title.pack(anchor="w")
        self._all_labels.append(self.hero_title)

        

        self.status_label = tk.Label(
            self,
            textvariable=self.status_var,
            bg=self.theme["panel"],
            fg=self.theme["accent"],
            font=("Arial", 10, "bold"),
            padx=16,
            pady=8,
            anchor="w",
        )
        self.status_label.pack(fill="x", padx=20)

        self.main = tk.Frame(self, bg=self.theme["bg"], padx=20, pady=10)
        self.main.pack(fill="both", expand=True)

        # Left sidebar is scrollable so the main RUN button is never lost on smaller Mac screens.
        self.sidebar_shell = self._card(self.main, padx=0, pady=0)
        self.sidebar_shell.pack(side="left", fill="y", padx=(0, 14))
        self.sidebar_shell.configure(width=390)
        self.sidebar_shell.pack_propagate(False)

        self.sidebar_canvas = tk.Canvas(
            self.sidebar_shell,
            bg=self.theme["card"],
            highlightthickness=0,
            bd=0,
            width=388,
        )
        self.sidebar_scrollbar = tk.Scrollbar(self.sidebar_shell, orient="vertical", command=self.sidebar_canvas.yview)
        self.sidebar_canvas.configure(yscrollcommand=self.sidebar_scrollbar.set)
        self.sidebar_scrollbar.pack(side="right", fill="y")
        self.sidebar_canvas.pack(side="left", fill="both", expand=True)

        self.sidebar = tk.Frame(self.sidebar_canvas, bg=self.theme["card"], padx=16, pady=16)
        self.sidebar_window = self.sidebar_canvas.create_window((0, 0), window=self.sidebar, anchor="nw")
        self.sidebar.bind("<Configure>", self._on_sidebar_configure)
        self.sidebar_canvas.bind("<Configure>", self._on_sidebar_canvas_configure)
        self.sidebar_canvas.bind_all("<MouseWheel>", self._on_mousewheel)

        self.content = tk.Frame(self.main, bg=self.theme["bg"])
        self.content.pack(side="left", fill="both", expand=True)

        self._build_sidebar()
        self._build_content()

    def _on_sidebar_configure(self, event=None) -> None:
        self.sidebar_canvas.configure(scrollregion=self.sidebar_canvas.bbox("all"))

    def _on_sidebar_canvas_configure(self, event) -> None:
        self.sidebar_canvas.itemconfigure(self.sidebar_window, width=event.width)

    def _on_mousewheel(self, event) -> None:
        # macOS and Windows both use MouseWheel, but the delta value differs.
        if event.delta:
            self.sidebar_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _build_sidebar(self) -> None:
        self._section_title(self.sidebar, "Configure Process")

        form = tk.Frame(self.sidebar, bg=self.theme["card"])
        form.pack(fill="x")

        self._form_row(form, "Process ID", self.pid_var)
        self._form_row(form, "Arrival Time", self.arrival_var)
        self._form_row(form, "Burst Time", self.burst_var)
        self._form_row(form, "Priority", self.priority_var)

        self._button(self.sidebar, "＋  ADD PROCESS", self.add_process, bg_key="accent", fg_key="bg", size="large").pack(fill="x", pady=(8, 6))

        quick_actions = tk.Frame(self.sidebar, bg=self.theme["card"])
        quick_actions.pack(fill="x", pady=(0, 4))
        self._button(quick_actions, "REMOVE", self.remove_selected_process, bg_key="warning", fg_key="bg", size="small").pack(side="left", fill="x", expand=True, padx=(0, 4))
        self._button(quick_actions, "CLEAR", self.clear_processes, bg_key="danger", fg_key="fg", size="small").pack(side="left", fill="x", expand=True, padx=(4, 0))

        q_row = tk.Frame(self.sidebar, bg=self.theme["card"], pady=4)
        q_row.pack(fill="x", pady=(4, 2))
        self._label(q_row, "Round Robin Quantum", muted=True).pack(anchor="w")
        q_entry = self._entry(q_row, self.quantum_var)
        q_entry.pack(fill="x", pady=(3, 0))

        self._divider(self.sidebar)
        self._section_title(self.sidebar, "Choose Algorithm")

        alg_box = tk.Frame(self.sidebar, bg=self.theme["card"])
        alg_box.pack(fill="x")
        for algorithm in ["FCFS", "SJF", "SRTF", "Round Robin", "Priority Scheduling"]:
            alg_button = self._clickable_label(
                alg_box,
                text=algorithm,
                command=lambda name=algorithm: self.select_algorithm(name),
                bg_key="card2",
                fg_key="fg",
                size="algorithm",
                anchor="w",
            )
            alg_button._algorithm_name = algorithm  # type: ignore[attr-defined]
            alg_button.pack(fill="x", pady=3)
            self._algorithm_buttons.append(alg_button)

        self.selected_algorithm_label = self._label(
            self.sidebar,
            f"Selected: {self.algorithm_var.get()}",
            muted=True,
            font=("Arial", 10, "bold"),
        )
        self.selected_algorithm_label.pack(fill="x", pady=(6, 0))
        self._refresh_algorithm_buttons()

        # Main action buttons are intentionally placed high and use label-based colored buttons
        # because native macOS Tk buttons often ignore background colors.
        self._button(self.sidebar, "▶  RUN SIMULATION", self.run_selected, bg_key="success", fg_key="bg", size="hero").pack(fill="x", pady=(10, 7))
        self._button(self.sidebar, "ANIMATE GANTT CHART", self.animate_selected, bg_key="accent2", fg_key="bg", size="large").pack(fill="x", pady=(0, 7))

        optional_grid = tk.Frame(self.sidebar, bg=self.theme["card"])
        optional_grid.pack(fill="x", pady=(2, 0))
        self._button(optional_grid, "RANDOM", self.generate_random_workload, bg_key="card2", fg_key="fg", size="small").pack(side="left", fill="x", expand=True, padx=(0, 3))
        self._button(optional_grid, "SAMPLE", self.load_sample_data, bg_key="card2", fg_key="fg", size="small").pack(side="left", fill="x", expand=True, padx=3)
        self._button(optional_grid, "EXPORT", self.export_csv, bg_key="card2", fg_key="fg", size="small").pack(side="left", fill="x", expand=True, padx=(3, 0))

        self._divider(self.sidebar)
        note = (
            "Notes:\n"
            "• Lower priority value = higher priority.\n"
            "• SJF and Priority are non-preemptive.\n"
            "• SRTF and RR are preemptive.\n"
            "• Use the scroll wheel if the sidebar is shorter than your screen."
        )
        self._label(self.sidebar, note, muted=True, wraplength=320, justify="left").pack(fill="x", pady=(2, 0))

    def _build_content(self) -> None:
        top_row = tk.Frame(self.content, bg=self.theme["bg"])
        top_row.pack(fill="x")

        self.process_card = self._card(top_row, padx=14, pady=14)
        self.process_card.pack(side="left", fill="both", expand=True, padx=(0, 12))
        self._section_title(self.process_card, "Process List")

        self.process_tree = ttk.Treeview(
            self.process_card,
            columns=("pid", "arrival", "burst", "priority", "color"),
            show="headings",
            height=5,
            style="Modern.Treeview",
        )
        for col, text, width in [
            ("pid", "Process ID", 95),
            ("arrival", "Arrival Time", 95),
            ("burst", "Burst Time", 95),
            ("priority", "Priority Value", 95),
            ("color", "Color", 105),
        ]:
            self.process_tree.heading(col, text=text)
            self.process_tree.column(col, width=width, anchor="center")
        self.process_tree.pack(fill="both", expand=True, pady=(4, 0))

        self.summary_card = self._card(top_row, padx=14, pady=14)
        self.summary_card.pack(side="left", fill="both")
        self.summary_card.configure(width=260)
        self.summary_card.pack_propagate(False)
        self._section_title(self.summary_card, "Performance Summary")
        self.summary_algorithm = self._big_stat(self.summary_card, "Algorithm", "-")
        self.summary_wait = self._big_stat(self.summary_card, "Avg Waiting Time", "-")
        self.summary_turn = self._big_stat(self.summary_card, "Avg Turnaround Time", "-")

        self.gantt_card = self._card(self.content, padx=14, pady=14)
        self.gantt_card.pack(fill="both", expand=True, pady=(12, 0))
        self.visual_title = self._section_title(self.gantt_card, "Gantt Chart")
        self.gantt_canvas = tk.Canvas(
            self.gantt_card,
            height=190,
            bg=self.theme["card2"],
            highlightthickness=1,
            highlightbackground=self.theme["line"],
        )
        self.gantt_canvas.pack(fill="both", expand=True, pady=(8, 0))

        bottom_row = tk.Frame(self.content, bg=self.theme["bg"])
        bottom_row.pack(fill="both", expand=True, pady=(12, 0))

        self.metrics_card = self._card(bottom_row, padx=14, pady=14)
        self.metrics_card.pack(side="left", fill="both", expand=True, padx=(0, 12))
        self._section_title(self.metrics_card, "Result Metrics")
        self.metrics_tree = ttk.Treeview(
            self.metrics_card,
            columns=("pid", "arrival", "burst", "priority", "completion", "waiting", "turnaround"),
            show="headings",
            height=5,
            style="Modern.Treeview",
        )
        for col, text, width in [
            ("pid", "Process ID", 60),
            ("arrival", "Arrival Time", 70),
            ("burst", "Burst Time", 70),
            ("priority", "Priority Value", 70),
            ("completion", "Completion", 85),
            ("waiting", "Waiting", 75),
            ("turnaround", "Turnaround", 90),
        ]:
            self.metrics_tree.heading(col, text=text)
            self.metrics_tree.column(col, width=width, anchor="center")
        self.metrics_tree.pack(fill="both", expand=True, pady=(4, 0))

        self._draw_empty_gantt()

    def _card(self, parent: tk.Misc, padx: int = 12, pady: int = 12) -> tk.Frame:
        frame = tk.Frame(parent, bg=self.theme["card"], padx=padx, pady=pady, highlightthickness=1, highlightbackground=self.theme["line"])
        self._all_cards.append(frame)
        return frame

    def _label(self, parent: tk.Misc, text: str, muted: bool = False, **kwargs) -> tk.Label:
        label = tk.Label(
            parent,
            text=text,
            bg=kwargs.pop("bg", self.theme["card"]),
            fg=self.theme["muted"] if muted else self.theme["fg"],
            font=kwargs.pop("font", ("Arial", 10)),
            **kwargs,
        )
        self._all_labels.append(label)
        return label

    def _section_title(self, parent: tk.Misc, text: str) -> tk.Label:
        label = self._label(parent, text, font=("Arial", 13, "bold"), anchor="w")
        label.pack(fill="x", pady=(0, 8))
        return label

    def _big_stat(self, parent: tk.Misc, title: str, value: str) -> tk.Label:
        box = tk.Frame(parent, bg=self.theme["card2"], padx=10, pady=3)
        box.pack(fill="x", pady=3)
        self._all_cards.append(box)
        self._label(box, title, muted=True, bg=self.theme["card2"], font=("Arial", 8, "bold")).pack(anchor="w")
        value_label = self._label(box, value, bg=self.theme["card2"], font=("Arial", 13, "bold"), anchor="w")
        value_label.pack(fill="x")
        return value_label

    def _divider(self, parent: tk.Misc) -> None:
        line = tk.Frame(parent, bg=self.theme["line"], height=1)
        line.pack(fill="x", pady=10)
        self._all_cards.append(line)

    def _form_row(self, parent: tk.Misc, text: str, variable: tk.StringVar) -> None:
        row = tk.Frame(parent, bg=self.theme["card"], pady=5)
        row.pack(fill="x")
        self._label(row, text, muted=True).pack(anchor="w")
        self._entry(row, variable).pack(fill="x", pady=(3, 0))

    def _entry(self, parent: tk.Misc, variable: tk.StringVar) -> tk.Entry:
        entry = tk.Entry(
            parent,
            textvariable=variable,
            bg=self.theme["entry"],
            fg=self.theme["fg"],
            insertbackground=self.theme["fg"],
            relief="flat",
            font=("Arial", 11),
            highlightthickness=1,
            highlightbackground=self.theme["line"],
            highlightcolor=self.theme["accent"],
        )
        self._all_entries.append(entry)
        return entry

    def _clickable_label(
        self,
        parent: tk.Misc,
        text: str,
        command,
        bg_key: str = "card2",
        fg_key: str = "fg",
        size: str = "medium",
        anchor: str = "center",
    ) -> tk.Label:
        if size == "hero":
            padx, pady, font = 18, 17, ("Arial", 15, "bold")
        elif size == "large":
            padx, pady, font = 16, 13, ("Arial", 13, "bold")
        elif size == "algorithm":
            padx, pady, font = 15, 10, ("Arial", 12, "bold")
        elif size == "small":
            padx, pady, font = 10, 8, ("Arial", 9, "bold")
        else:
            padx, pady, font = 14, 10, ("Arial", 10, "bold")

        label = tk.Label(
            parent,
            text=text,
            bg=self.theme[bg_key],
            fg=self.theme[fg_key],
            padx=padx,
            pady=pady,
            font=font,
            cursor="hand2",
            anchor=anchor,
            relief="flat",
            bd=0,
            highlightthickness=0,
            highlightbackground=self.theme["line"],
        )
        label._bg_key = bg_key  # type: ignore[attr-defined]
        label._fg_key = fg_key  # type: ignore[attr-defined]
        label._button_size = size  # type: ignore[attr-defined]
        label._command = command  # type: ignore[attr-defined]

        def on_click(_event=None):
            command()

        def on_enter(_event=None):
            # Keep the selected algorithm color stable; brighten other buttons on hover.
            if getattr(label, "_is_selected_algorithm", False):
                return
            label.configure(bg=self.theme["accent"] if bg_key == "card2" else self.theme[bg_key])

        def on_leave(_event=None):
            if getattr(label, "_is_selected_algorithm", False):
                return
            label.configure(bg=self.theme[bg_key])

        label.bind("<Button-1>", on_click)
        label.bind("<Return>", on_click)
        label.bind("<Enter>", on_enter)
        label.bind("<Leave>", on_leave)
        self._all_buttons.append(label)
        return label

    def _button(
        self,
        parent: tk.Misc,
        text: str,
        command,
        fill: str | None = "x",
        bg_key: str = "card2",
        fg_key: str = "fg",
        size: str = "medium",
    ) -> tk.Label:
        return self._clickable_label(parent, text, command, bg_key=bg_key, fg_key=fg_key, size=size)

    def select_algorithm(self, algorithm: str) -> None:
        """Select a scheduling algorithm using reliable macOS-friendly buttons."""
        self.algorithm_var.set(algorithm)
        if hasattr(self, "selected_algorithm_label"):
            self.selected_algorithm_label.configure(text=f"Selected: {algorithm}")
        self._refresh_algorithm_buttons()
        self.status_var.set(f"Selected algorithm: {algorithm}. Click Run Simulation to show the Gantt chart.")

    def _refresh_algorithm_buttons(self) -> None:
        """Visually mark the selected algorithm button."""
        selected = self.algorithm_var.get()
        for button in self._algorithm_buttons:
            name = getattr(button, "_algorithm_name", "")
            if name == selected:
                button._is_selected_algorithm = True  # type: ignore[attr-defined]
                button.configure(
                    bg=self.theme["accent"],
                    fg=self.theme["bg"],
                    text=f"✓  {name}",
                    relief="flat",
                    bd=0,
                    highlightbackground=self.theme["accent"],
                )
            else:
                button._is_selected_algorithm = False  # type: ignore[attr-defined]
                button.configure(
                    bg=self.theme["card2"],
                    fg=self.theme["fg"],
                    text=f"   {name}",
                    relief="flat",
                    bd=0,
                    highlightbackground=self.theme["line"],
                )

    # ------------------------------------------------------------------
    # PROCESS AND SIMULATION ACTIONS
    # ------------------------------------------------------------------
    def _next_color(self) -> str:
        return PROCESS_COLORS[len(self.process_colors) % len(PROCESS_COLORS)]

    def _parse_process_input(self) -> Process:
        pid = self.pid_var.get().strip()
        if not pid:
            raise ValueError("Process ID cannot be empty.")
        try:
            arrival = int(self.arrival_var.get())
            burst = int(self.burst_var.get())
            priority = int(self.priority_var.get())
        except ValueError as exc:
            raise ValueError("Arrival, burst, and priority must be integer values.") from exc
        if arrival < 0:
            raise ValueError("Arrival time must be zero or positive.")
        if burst <= 0:
            raise ValueError("Burst time must be greater than zero.")
        if priority < 0:
            raise ValueError("Priority value must be zero or positive.")
        if any(process.pid == pid for process in self.processes):
            raise ValueError(f"Process ID {pid} already exists.")
        return Process(pid, arrival, burst, priority)

    def add_process(self) -> None:
        try:
            process = self._parse_process_input()
        except Exception as exc:  # noqa: BLE001 - user-facing validation
            messagebox.showerror("Invalid Input", str(exc))
            return

        self.processes.append(process)
        self.process_colors[process.pid] = self._next_color()
        self._advance_default_pid()
        self._refresh_process_table()
        self.status_var.set(f"Added {process.pid}. Choose an algorithm and run the simulation.")

    def _advance_default_pid(self) -> None:
        existing_numbers = []
        for process in self.processes:
            if process.pid.upper().startswith("P") and process.pid[1:].isdigit():
                existing_numbers.append(int(process.pid[1:]))
        next_number = max(existing_numbers, default=0) + 1
        self.pid_var.set(f"P{next_number}")
        self.arrival_var.set("0")
        self.burst_var.set("4")
        self.priority_var.set("1")

    def remove_selected_process(self) -> None:
        selected = self.process_tree.selection()
        if not selected:
            messagebox.showinfo("No Selection", "Select one process from the table first.")
            return
        selected_pid = self.process_tree.item(selected[0], "values")[0]
        self.processes = [process for process in self.processes if process.pid != selected_pid]
        self.process_colors.pop(selected_pid, None)
        self.last_result = None
        self._refresh_process_table()
        self._refresh_metrics_table(None)
        self._draw_empty_gantt()
        self.status_var.set(f"Removed {selected_pid}.")

    def clear_processes(self) -> None:
        self.processes.clear()
        self.process_colors.clear()
        self.last_result = None
        self._refresh_process_table()
        self._refresh_metrics_table(None)
        self._draw_empty_gantt()
        self.status_var.set("All processes cleared.")

    def load_sample_data(self) -> None:
        self.processes = [
            Process("P1", 0, 7, 2),
            Process("P2", 2, 4, 1),
            Process("P3", 4, 1, 3),
            Process("P4", 5, 4, 2),
            Process("P5", 6, 3, 1),
        ]
        self.process_colors = {process.pid: PROCESS_COLORS[index % len(PROCESS_COLORS)] for index, process in enumerate(self.processes)}
        self.last_result = None
        self._refresh_process_table()
        self._refresh_metrics_table(None)
        self._draw_empty_gantt()
        self.status_var.set("Sample data loaded. Click Run Simulation or Animate Simulation.")

    def generate_random_workload(self) -> None:
        random_count = random.randint(5, 8)
        self.processes = []
        self.process_colors = {}
        for index in range(random_count):
            process = Process(
                pid=f"P{index + 1}",
                arrival=random.randint(0, 8),
                burst=random.randint(1, 10),
                priority=random.randint(1, 5),
            )
            self.processes.append(process)
            self.process_colors[process.pid] = PROCESS_COLORS[index % len(PROCESS_COLORS)]
        self.last_result = None
        self._refresh_process_table()
        self._refresh_metrics_table(None)
        self._draw_empty_gantt()
        self.status_var.set(f"Generated {random_count} random processes.")

    def run_selected(self) -> None:
        result = self._calculate_selected_result()
        if result is None:
            return
        self.last_result = result
        self._refresh_metrics_table(result)
        self._draw_gantt(result, animate=False)
        self.status_var.set(f"{result.algorithm} completed successfully.")

    def animate_selected(self) -> None:
        result = self._calculate_selected_result()
        if result is None:
            return
        self.last_result = result
        self._refresh_metrics_table(result)
        self._draw_gantt(result, animate=True)

    def _calculate_selected_result(self) -> ScheduleResult | None:
        try:
            quantum = int(self.quantum_var.get())
            result = run_algorithm(self.processes, self.algorithm_var.get(), quantum)
        except Exception as exc:  # noqa: BLE001 - user-facing validation
            messagebox.showerror("Simulation Error", str(exc))
            return None
        return result

    def compare_algorithms(self) -> None:
        try:
            quantum = int(self.quantum_var.get())
            results = compare_all(self.processes, quantum)
        except Exception as exc:  # noqa: BLE001 - user-facing validation
            messagebox.showerror("Comparison Error", str(exc))
            return

        self.comparison_results = results
        self.last_result = min(results, key=lambda item: item.avg_waiting)
        self._refresh_metrics_table(self.last_result)
        self._draw_gantt(self.last_result, animate=False)
        self._draw_comparison_chart(results)
        best_wait = min(results, key=lambda item: item.avg_waiting)
        best_turnaround = min(results, key=lambda item: item.avg_turnaround)
        self.status_var.set(
            f"Comparison completed. Best waiting time: {best_wait.algorithm}; "
            f"best turnaround time: {best_turnaround.algorithm}."
        )

    def export_csv(self) -> None:
        if self.last_result is None:
            messagebox.showinfo("No Result", "Run a simulation before exporting.")
            return

        output_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv")],
            title="Save Result CSV",
        )
        if not output_path:
            return

        with open(output_path, "w", newline="", encoding="utf-8") as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(["Algorithm", self.last_result.algorithm])
            writer.writerow(["Average Waiting Time", f"{self.last_result.avg_waiting:.2f}"])
            writer.writerow(["Average Turnaround Time", f"{self.last_result.avg_turnaround:.2f}"])
            writer.writerow([])
            writer.writerow(["PID", "Arrival", "Burst", "Priority", "Completion", "Waiting", "Turnaround"])
            for metric in self.last_result.metrics:
                writer.writerow([
                    metric.pid,
                    metric.arrival,
                    metric.burst,
                    metric.priority,
                    metric.completion,
                    metric.waiting,
                    metric.turnaround,
                ])
            writer.writerow([])
            writer.writerow(["Gantt Chart"])
            writer.writerow(["PID", "Start", "End"])
            for segment in self.last_result.segments:
                writer.writerow([segment.pid, segment.start, segment.end])

        self.status_var.set(f"Exported result to {output_path}.")
        messagebox.showinfo("Export Complete", f"Result saved to:\n{output_path}")

    # ------------------------------------------------------------------
    # TABLES AND CHARTS
    # ------------------------------------------------------------------
    def _refresh_process_table(self) -> None:
        for item in self.process_tree.get_children():
            self.process_tree.delete(item)
        for process in self.processes:
            color = self.process_colors.get(process.pid, self.theme["accent"])
            tag = f"tag_{process.pid}"
            self.process_tree.tag_configure(tag, foreground=color)
            self.process_tree.insert(
                "",
                END,
                values=(process.pid, process.arrival, process.burst, process.priority, color),
                tags=(tag,),
            )

    def _refresh_metrics_table(self, result: ScheduleResult | None) -> None:
        for item in self.metrics_tree.get_children():
            self.metrics_tree.delete(item)
        if result is None:
            self.summary_algorithm.configure(text="-")
            self.summary_wait.configure(text="-")
            self.summary_turn.configure(text="-")
            return

        for metric in result.metrics:
            color = self.process_colors.get(metric.pid, self.theme["accent"])
            tag = f"metric_{metric.pid}"
            self.metrics_tree.tag_configure(tag, foreground=color)
            self.metrics_tree.insert(
                "",
                END,
                values=(
                    metric.pid,
                    metric.arrival,
                    metric.burst,
                    metric.priority,
                    metric.completion,
                    metric.waiting,
                    metric.turnaround,
                ),
                tags=(tag,),
            )
        self.summary_algorithm.configure(text=result.algorithm)
        self.summary_wait.configure(text=f"{result.avg_waiting:.2f}")
        self.summary_turn.configure(text=f"{result.avg_turnaround:.2f}")

    def _draw_empty_gantt(self) -> None:
        self.gantt_canvas.delete("all")
        self.update_idletasks()
        width = max(self.gantt_canvas.winfo_width(), 640)
        height = max(self.gantt_canvas.winfo_height(), 160)
        self.gantt_canvas.create_text(
            width / 2,
            height / 2,
            text="Run or animate a simulation to display the Gantt chart.",
            fill=self.theme["muted"],
            font=("Arial", 13, "bold"),
            anchor="center",
        )

    def _draw_gantt(self, result: ScheduleResult, animate: bool = False) -> None:
        self._animation_token += 1
        token = self._animation_token
        self.gantt_canvas.delete("all")
        self.visual_title.configure(text=f"Gantt Chart — {result.algorithm}")
        self.update_idletasks()

        width = max(self.gantt_canvas.winfo_width(), 850)
        height = max(self.gantt_canvas.winfo_height(), 180)
        left = 54
        right = 28
        top = 52
        bar_height = 48
        max_time = max(segment.end for segment in result.segments) if result.segments else 1
        scale = max((width - left - right) / max(max_time, 1), 1)

        execution_text = " → ".join(result.execution_order) if result.execution_order else "IDLE"
        self.gantt_canvas.create_text(
            left,
            24,
            text=f"Execution Order: {execution_text}",
            fill=self.theme["fg"],
            font=("Arial", 11, "bold"),
            anchor="w",
        )
        axis_y = min(top + bar_height + 30, height - 42)
        self.gantt_canvas.create_line(left, axis_y, width - right, axis_y, fill=self.theme["line"])

        tick_step = max(1, max_time // 12)
        ticks = set(range(0, max_time + 1, tick_step)) | {0, max_time}
        for tick in sorted(ticks):
            x = left + tick * scale
            self.gantt_canvas.create_line(x, axis_y - 6, x, axis_y + 6, fill=self.theme["line"])
            self.gantt_canvas.create_text(x, axis_y + 18, text=str(tick), fill=self.theme["muted"], font=("Arial", 8))

        def draw_segment(index: int) -> None:
            if token != self._animation_token:
                return
            if index >= len(result.segments):
                self.status_var.set(f"Animation finished for {result.algorithm}.")
                return
            segment = result.segments[index]
            self._draw_one_segment(segment, left, top, bar_height, scale)
            if animate:
                self.status_var.set(f"Animating {result.algorithm}: {segment.pid} from {segment.start} to {segment.end}.")
                self.after(450, lambda: draw_segment(index + 1))
            else:
                draw_segment(index + 1)

        draw_segment(0)

    def _draw_one_segment(self, segment, left: int, top: int, bar_height: int, scale: float) -> None:
        x1 = left + segment.start * scale
        x2 = left + segment.end * scale
        color = "#475569" if segment.pid == "IDLE" else self.process_colors.get(segment.pid, self.theme["accent"])
        self.gantt_canvas.create_rectangle(x1, top, x2, top + bar_height, fill=color, outline=self.theme["bg"], width=2)
        if x2 - x1 >= 24:
            self.gantt_canvas.create_text(
                (x1 + x2) / 2,
                top + bar_height / 2,
                text=segment.pid,
                fill="#020617",
                font=("Arial", 11, "bold"),
            )
        else:
            self.gantt_canvas.create_text(
                (x1 + x2) / 2,
                top + bar_height / 2,
                text=segment.pid,
                fill="#020617",
                font=("Arial", 8, "bold"),
            )
        self.gantt_canvas.create_text(x1, top + bar_height + 14, text=str(segment.start), fill=self.theme["fg"], font=("Arial", 8, "bold"))
        self.gantt_canvas.create_text(x2, top + bar_height + 14, text=str(segment.end), fill=self.theme["fg"], font=("Arial", 8, "bold"))

    def _draw_empty_comparison(self) -> None:
        self.compare_canvas.delete("all")
        self.compare_canvas.create_text(
            205,
            110,
            text="Click Compare All\nto view ranking.",
            fill=self.theme["muted"],
            font=("Arial", 10, "bold"),
            justify="center",
            width=260,
        )

    def _draw_comparison_chart(self, results: list[ScheduleResult]) -> None:
        self.compare_canvas.delete("all")
        self.update_idletasks()
        width = max(self.compare_canvas.winfo_width(), 360)
        left = 112
        right = 100
        top = 30
        row_h = 36
        max_value = max(max(result.avg_waiting, result.avg_turnaround) for result in results) or 1

        self.compare_canvas.create_text(
            left,
            14,
            text="Wait / Turn",
            fill=self.theme["fg"],
            font=("Arial", 10, "bold"),
            anchor="w",
        )

        for index, result in enumerate(results):
            y = top + index * row_h
            name = result.algorithm.replace("Round Robin (q = ", "RR q = ").replace(")", "")
            self.compare_canvas.create_text(8, y + 11, text=name, fill=self.theme["fg"], font=("Arial", 8, "bold"), anchor="w")

            wait_w = (result.avg_waiting / max_value) * (width - left - right)
            turn_w = (result.avg_turnaround / max_value) * (width - left - right)
            self.compare_canvas.create_rectangle(left, y, left + wait_w, y + 11, fill=self.theme["accent"], outline="")
            self.compare_canvas.create_rectangle(left, y + 16, left + turn_w, y + 27, fill=self.theme["accent2"], outline="")

        legend_y = top + len(results) * row_h + 10
        self.compare_canvas.create_rectangle(12, legend_y, 24, legend_y + 10, fill=self.theme["accent"], outline="")
        self.compare_canvas.create_text(30, legend_y + 5, text="Average Waiting", fill=self.theme["muted"], font=("Arial", 8), anchor="w")
        self.compare_canvas.create_rectangle(150, legend_y, 162, legend_y + 10, fill=self.theme["accent2"], outline="")
        self.compare_canvas.create_text(168, legend_y + 5, text="Average Turnaround", fill=self.theme["muted"], font=("Arial", 8), anchor="w")

    # ------------------------------------------------------------------
    # THEME
    # ------------------------------------------------------------------
    def toggle_theme(self) -> None:
        self.theme_name = "light" if self.theme_name == "dark" else "dark"
        self.theme = THEMES[self.theme_name]
        self._apply_theme()

    def _apply_theme(self) -> None:
        t = self.theme
        self.configure(bg=t["bg"])
        self.header.configure(bg=t["bg"])
        self.main.configure(bg=t["bg"])
        self.content.configure(bg=t["bg"])
        self.status_label.configure(bg=t["panel"], fg=t["accent"])
        self.hero_title.configure(bg=t["bg"], fg=t["fg"])
        self.hero_subtitle.configure(bg=t["bg"], fg=t["muted"])
        if hasattr(self, "sidebar_canvas"):
            self.sidebar_canvas.configure(bg=t["card"])
            self.sidebar.configure(bg=t["card"])

        for frame in self._all_cards:
            try:
                frame.configure(bg=t["card"], highlightbackground=t["line"])
            except tk.TclError:
                pass
        for label in self._all_labels:
            try:
                current_text = label.cget("text")
                fg = t["muted"] if current_text in {"Process ID", "Arrival Time", "Burst Time", "Priority", "Round Robin Quantum"} else t["fg"]
                label.configure(bg=label.master.cget("bg"), fg=fg)
            except tk.TclError:
                pass
        for entry in self._all_entries:
            entry.configure(bg=t["entry"], fg=t["fg"], insertbackground=t["fg"], highlightbackground=t["line"], highlightcolor=t["accent"])
        for button in self._all_buttons:
            bg_key = getattr(button, "_bg_key", "card2")
            fg_key = getattr(button, "_fg_key", "fg")
            button.configure(bg=t[bg_key], fg=t[fg_key], highlightbackground=t["line"])
        self._refresh_algorithm_buttons()

        self.gantt_canvas.configure(bg=t["card2"], highlightbackground=t["line"])
        self._configure_ttk_style()
        self._refresh_process_table()
        if self.last_result is not None:
            self._refresh_metrics_table(self.last_result)
            self._draw_gantt(self.last_result, animate=False)
        else:
            self._refresh_metrics_table(None)
            self._draw_empty_gantt()

def main() -> None:
    app = ModernCPUSchedulingApp()
    app.mainloop()


if __name__ == "__main__":
    main()
