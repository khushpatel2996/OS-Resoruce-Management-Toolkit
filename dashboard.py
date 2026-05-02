import random
import subprocess
import time
import traceback
from pathlib import Path
import tkinter as tk
from tkinter import messagebox, ttk

from ai_tutor import QUICK_PROMPTS, build_tutor_response
from CPU_scheduling.advisor import analyze_and_recommend
from Memory_Management import comparator

BASE_DIR = Path(__file__).resolve().parent
CPU_DIR = BASE_DIR / "CPU_scheduling"
MEMORY_DIR = BASE_DIR / "Memory_Management"
SHARED_DIR = BASE_DIR / "Shared_Memory"

P = {
    "bg": "#060914",
    "bg2": "#0a1224",
    "card": "#121d35",
    "card2": "#192744",
    "card3": "#203050",
    "line": "#314768",
    "line2": "#445c82",
    "glass": "#66c7ff",
    "glass_soft": "#24385a",
    "input": "#0d1730",
    "input_hi": "#173058",
    "text": "#edf4ff",
    "muted": "#93a9cd",
    "blue": "#48a7ff",
    "blue2": "#7ac8ff",
    "green": "#29b38e",
    "green2": "#4bd1ac",
    "red": "#cf5264",
    "red2": "#f18190",
    "gold": "#e0b15d",
}

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("OS Resource Management Toolkit")
        self.root.geometry("1440x860")
        self.root.minsize(1180, 760)
        self.root.configure(bg=P["bg"])
        self.status = tk.StringVar(value="Dashboard ready")
        self.active_tab = "cpu"
        self.panels = {}
        self.tab_labels = {}
        self.cpu_count = tk.StringVar(value="3")
        self.cpu_algo = tk.StringVar(value="FCFS")
        self.cpu_quantum = tk.StringVar(value="2")
        self.cpu_advice_title = tk.StringVar(value="No recommendation yet")
        self.cpu_advice_reason = tk.StringVar(value="Enter process data and use the advisor to compare all CPU scheduling algorithms.")
        self.cpu_advice_tradeoff = tk.StringVar(value="Tradeoff: Waiting for workload analysis.")
        self.cpu_advice_ranking = tk.StringVar(value="Ranking: -")
        self.mem_mode = tk.StringVar(value="Contiguous Allocation")
        self.mem_allocation_type = tk.StringVar(value="Fixed Allocation")
        self.mem_contiguous_algo = tk.StringVar(value="First Fit")
        self.mem_block_count = tk.StringVar(value="5")
        self.mem_process_count = tk.StringVar(value="4")
        self.mem_block_rows = []
        self.mem_process_rows = []
        self.mem_page_count = tk.StringVar(value="13")
        self.mem_frames = tk.StringVar(value="3")
        self.mem_refs = tk.StringVar(value="7 0 1 2 0 3 0 4 2 3 0 3 2")
        self.tutor_question = tk.StringVar(value="Explain my current project result")
        self.tutor_mode = tk.StringVar(value="Context Aware")
        self.tutor_source = tk.StringVar(value="Auto")
        self.client_name = tk.StringVar()
        self.resource_id = tk.StringVar(value="R0")
        self.resource_warning = tk.StringVar(value="No conflicts detected.")
        self.resource_info = tk.StringVar(value="Manager ready. No resource events yet.")
        self.resource_queue_limit = 3
        self.cpu_rows = []
        self.cpu_result = None
        self.mem_result = None
        self.gantt_regions = []
        self.gantt_tooltip = None
        self.cpu_algorithms = [
            "FCFS",
            "SJF",
            "SRTF",
            "Round Robin",
            "Priority (Preemptive)",
            "Priority (Non-Preemptive)",
        ]
        self.cpu_programs = {
            "FCFS": "fcfs.c",
            "SJF": "sjf.c",
            "SRTF": "srtf.c",
            "Round Robin": "rr.c",
            "Priority (Preemptive)": "priority.c",
            "Priority (Non-Preemptive)": "priority_np.c",
        }
        self.resources = [{"id": i, "owner": None, "owner_pid": 0} for i in range(5)]
        self.waiting_by_resource = {i: [] for i in range(5)}
        self.active_clients = []
        self.resource_events = []
        self.resource_pid_seed = 4100
        self.monitor = {"cpu1": [0] * 10, "cpu2": [0] * 10, "mem1": [0] * 10, "mem2": [0] * 10}
        self.monitor_source = "Project simulation data"
        self._style()
        self._shell()
        self._tabs()
        self._panels()
        self.root.after_idle(lambda: self.switch_tab("cpu", False))
        self.update_resource_views()
        self.update_monitor()

    def _style(self):
        s = ttk.Style()
        s.theme_use("clam")
        s.configure(
            "Vertical.TScrollbar",
            background=P["card3"],
            troughcolor=P["bg2"],
            bordercolor=P["line"],
            arrowcolor=P["blue2"],
            darkcolor=P["card3"],
            lightcolor=P["card3"],
            gripcount=0,
        )
        s.configure(
            "Horizontal.TScrollbar",
            background=P["card3"],
            troughcolor=P["bg2"],
            bordercolor=P["line"],
            arrowcolor=P["blue2"],
            darkcolor=P["card3"],
            lightcolor=P["card3"],
            gripcount=0,
        )
        s.configure(
            "Dash.TCombobox",
            fieldbackground=P["input"],
            background=P["input"],
            foreground=P["text"],
            bordercolor=P["line"],
            lightcolor=P["line"],
            darkcolor=P["line"],
            arrowcolor=P["blue2"],
            padding=6,
        )
        s.map(
            "Dash.TCombobox",
            fieldbackground=[("readonly", P["input"]), ("focus", P["input_hi"])],
            foreground=[("readonly", P["text"])],
            selectbackground=[("readonly", P["input"])],
            selectforeground=[("readonly", P["text"])],
        )
        s.configure(
            "Cpu.Treeview",
            background=P["card2"],
            fieldbackground=P["card2"],
            foreground=P["text"],
            rowheight=28,
            bordercolor=P["line"],
            lightcolor=P["line"],
            darkcolor=P["line"],
            font=("Segoe UI", 9),
        )
        s.configure(
            "Cpu.Treeview.Heading",
            background=P["card3"],
            foreground=P["text"],
            bordercolor=P["line"],
            lightcolor=P["line"],
            darkcolor=P["line"],
            font=("Segoe UI Semibold", 9),
            padding=6,
        )
        s.map(
            "Cpu.Treeview",
            background=[("selected", P["blue"])],
            foreground=[("selected", "white")],
        )

    def _shell(self):
        shell = tk.Frame(self.root, bg=P["bg2"], highlightthickness=1, highlightbackground=P["line2"])
        shell.pack(expand=True, fill="both", padx=18, pady=18)
        self.backdrop = tk.Canvas(shell, bg=P["bg2"], bd=0, highlightthickness=0)
        self.backdrop.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.backdrop.tk.call("lower", self.backdrop._w)
        self.backdrop.bind("<Configure>", self.draw_backdrop)
        top = tk.Frame(shell, bg=P["bg2"], height=54)
        top.pack(fill="x")
        top.pack_propagate(False)
        tk.Label(top, text="OS RESOURCE MANAGEMENT TOOLKIT", bg=P["bg2"], fg=P["text"], font=("Segoe UI Semibold", 18)).pack(side="left", expand=True)
        self.tab_bar = tk.Frame(shell, bg=P["bg2"])
        self.tab_bar.pack(fill="x", padx=16, pady=(0, 10))
        self.host = tk.Frame(shell, bg=P["bg2"])
        self.host.pack(expand=True, fill="both", padx=16, pady=(0, 10))
        tk.Frame(shell, bg=P["glass_soft"], height=1).pack(fill="x", side="top")
        status = tk.Frame(shell, bg="#09101d", height=32, highlightthickness=1, highlightbackground=P["line2"])
        status.pack(fill="x", side="bottom")
        status.pack_propagate(False)
        tk.Label(status, textvariable=self.status, bg="#09101d", fg=P["blue2"], anchor="w", padx=16, font=("Segoe UI", 10)).pack(fill="both", expand=True)

    def draw_backdrop(self, event=None):
        if not hasattr(self, "backdrop"):
            return
        canvas = self.backdrop
        canvas.delete("all")
        width = max(canvas.winfo_width(), 1)
        height = max(canvas.winfo_height(), 1)
        canvas.create_rectangle(0, 0, width, height, fill=P["bg2"], outline="")
        for x1, y1, size, color in [
            (width * 0.06, height * 0.08, 220, "#10233f"),
            (width * 0.74, height * 0.10, 260, "#152c4b"),
            (width * 0.62, height * 0.58, 320, "#123656"),
            (width * 0.16, height * 0.70, 240, "#0f2a44"),
        ]:
            canvas.create_oval(x1, y1, x1 + size, y1 + size, fill=color, outline="")
        for x in range(0, width, 36):
            canvas.create_line(x, 0, x, height, fill="#0d1830")
        for y in range(0, height, 36):
            canvas.create_line(0, y, width, y, fill="#0d1830")

    def _tabs(self):
        for key, title in [("cpu", "CPU Scheduling"), ("memory", "Memory Management"), ("resource", "Resource Manager"), ("system", "System Monitor"), ("tutor", "AI Study Tutor")]:
            lbl = tk.Label(
                self.tab_bar,
                text=title,
                bg=P["card"],
                fg=P["muted"],
                padx=28,
                pady=12,
                font=("Segoe UI Semibold", 11),
                cursor="hand2",
                highlightthickness=1,
                highlightbackground=P["line"],
            )
            lbl.pack(side="left", padx=(0, 2))
            lbl.bind("<Button-1>", lambda e, k=key: self.switch_tab(k, True))
            lbl.bind("<Enter>", lambda e, k=key: self._hover_tab(k, True))
            lbl.bind("<Leave>", lambda e, k=key: self._hover_tab(k, False))
            self.tab_labels[key] = lbl

    def _panels(self):
        self.panels["cpu"] = self.build_cpu_panel(self.host)
        self.panels["memory"] = self.build_memory_panel(self.host)
        self.panels["resource"] = self.build_resource_panel(self.host)
        self.panels["system"] = self.build_system_panel(self.host)
        self.panels["tutor"] = self.build_tutor_panel(self.host)

    def switch_tab(self, key, animate=True):
        old = self.panels.get(self.active_tab)
        new = self.panels[key]
        self.active_tab = key
        for name, lbl in self.tab_labels.items():
            lbl.configure(
                bg=P["card3"] if name == key else P["card"],
                fg="white" if name == key else P["muted"],
                highlightbackground=P["blue2"] if name == key else P["line"],
            )
        self.host.update_idletasks()
        w, h = max(self.host.winfo_width(), 1), max(self.host.winfo_height(), 1)
        if old and old.winfo_manager() and animate and old != new:
            new.place(in_=self.host, x=w, y=0, width=w, height=h)
            def step(i=0):
                p = i / 12
                old.place_configure(x=int(-p * w), y=0, width=w, height=h)
                new.place_configure(x=int((1 - p) * w), y=0, width=w, height=h)
                if i < 12: self.root.after(18, lambda: step(i + 1))
                else:
                    old.place_forget()
                    new.place_configure(x=0, y=0, width=w, height=h)
            step()
        else:
            for panel in self.panels.values(): panel.place_forget()
            new.place(in_=self.host, x=0, y=0, relwidth=1, relheight=1)
        if key == "tutor":
            self.refresh_tutor_context()
        self.status.set({"cpu": "CPU scheduling ready", "memory": "Memory management ready", "resource": "Resource manager ready", "system": "System monitor running", "tutor": "AI Study Tutor ready"}[key])

    def _hover_tab(self, key, enter):
        if key == self.active_tab: return
        self.tab_labels[key].configure(bg=P["card2"] if enter else P["card"], fg=P["text"] if enter else P["muted"])

    def card(self, parent, title):
        card = tk.Frame(parent, bg=P["card"], highlightthickness=1, highlightbackground=P["line2"], bd=0)
        tk.Frame(card, bg=P["glass_soft"], height=1).pack(fill="x", side="top")
        head = tk.Frame(card, bg=P["card"])
        head.pack(fill="x", padx=16, pady=(12, 8))
        chip = tk.Frame(head, bg=P["card"])
        chip.pack(anchor="w")
        tk.Frame(chip, bg=P["glass"], width=26, height=3).pack(anchor="w", pady=(0, 6))
        tk.Label(chip, text=title, bg=P["card"], fg=P["text"], font=("Segoe UI Semibold", 12)).pack(anchor="w")
        tk.Frame(card, bg=P["line2"], height=1).pack(fill="x", padx=16)
        body = tk.Frame(card, bg=P["card"])
        body.pack(fill="both", expand=True, padx=16, pady=10)
        return card, body

    def btn(self, parent, text, cmd, bg, hover):
        b = tk.Button(
            parent,
            text=text,
            command=cmd,
            bg=bg,
            fg="white",
            activebackground=hover,
            activeforeground="white",
            relief="flat",
            bd=0,
            padx=16,
            pady=12,
            cursor="hand2",
            font=("Segoe UI Semibold", 11),
            highlightthickness=1,
            highlightbackground=P["line2"],
        )

        def on_enter(e):
            b.config(bg=hover)

        def on_leave(e):
            b.config(bg=bg)

        b.bind("<Enter>", on_enter)
        b.bind("<Leave>", on_leave)

        return b

    def field(self, parent, label, var, values=None):
        row = tk.Frame(parent, bg=P["card"])
        row.pack(fill="x", pady=6)
        tk.Label(row, text=label, bg=P["card"], fg=P["muted"], font=("Segoe UI", 10)).pack(anchor="w")
        if values:
            w = ttk.Combobox(row, textvariable=var, values=values, state="readonly", style="Dash.TCombobox")
        else:
            w = tk.Entry(
                row,
                textvariable=var,
                bg=P["input"],
                fg=P["text"],
                insertbackground=P["text"],
                relief="flat",
                font=("Segoe UI", 10),
                highlightthickness=1,
                highlightbackground=P["line"],
                highlightcolor=P["blue2"],
                bd=0,
            )
        w.pack(fill="x", pady=(6, 0))
        return w

    def create_scrollable_panel(self, parent):
        outer = tk.Frame(parent, bg=P["bg2"])
        canvas = tk.Canvas(outer, bg=P["bg2"], bd=0, highlightthickness=0)
        scrollbar = ttk.Scrollbar(outer, orient="vertical", command=canvas.yview, style="Vertical.TScrollbar")
        inner = tk.Frame(canvas, bg=P["bg2"])
        inner.bind(
            "<Configure>",
            lambda event: canvas.configure(scrollregion=canvas.bbox("all")),
        )
        window_id = canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        canvas.bind(
            "<Configure>",
            lambda event: canvas.itemconfigure(window_id, width=event.width),
        )
        canvas.bind("<Enter>", lambda event: canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")))
        canvas.bind("<Leave>", lambda event: canvas.unbind_all("<MouseWheel>"))
        return outer, inner

    def build_cpu_panel(self, parent):
        outer, panel = self.create_scrollable_panel(parent)
        panel.grid_columnconfigure(0, weight=1, minsize=0, uniform="cpu_cols")
        panel.grid_columnconfigure(1, weight=1, minsize=0, uniform="cpu_cols")
        panel.grid_rowconfigure(0, weight=7, minsize=420)
        panel.grid_rowconfigure(1, weight=3, minsize=220)
        left, body = self.card(panel, "CPU Scheduling")
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=4)
        combo = self.field(body, "Number of processes", self.cpu_count, [str(i) for i in range(1, 11)])
        combo.bind("<<ComboboxSelected>>", lambda e: self.rebuild_cpu_table())
        self.cpu_input_table_host = tk.Frame(body, bg=P["card"])
        self.cpu_input_table_host.pack(fill="x", pady=(10, 0))
        self.rebuild_cpu_table()
        self.quantum_row = tk.Frame(body, bg=P["card"])
        tk.Label(self.quantum_row, text="Time Quantum", bg=P["card"], fg=P["text"], font=("Segoe UI", 10)).pack(anchor="w")
        self.quantum_entry = tk.Entry(
            self.quantum_row,
            textvariable=self.cpu_quantum,
            bg=P["input"],
            fg=P["text"],
            insertbackground=P["text"],
            relief="flat",
            font=("Segoe UI", 10),
            highlightthickness=1,
            highlightbackground=P["line"],
            highlightcolor=P["blue2"],
            bd=0,
        )
        self.quantum_entry.pack(fill="x", pady=(6, 0))
        self.algorithm_combo = self.field(body, "Algorithm", self.cpu_algo, self.cpu_algorithms)
        self.algorithm_combo.bind("<<ComboboxSelected>>", lambda e: self.on_algorithm_change())
        self.btn(body, "Run Algorithm", self.run_cpu, P["blue"], P["blue2"]).pack(fill="x", pady=(12, 0))
        self.btn(body, "Suggest Best Algorithm", self.suggest_cpu_algorithm, P["green"], P["green2"]).pack(fill="x", pady=(8, 0))
        self.input_note = tk.Label(body, text="Editable table with priority column. Round Robin uses Time Quantum.", bg=P["card"], fg=P["muted"], font=("Segoe UI", 9))
        self.input_note.pack(anchor="w", pady=(8, 0))
        self.cpu_advisor_card = tk.Frame(body, bg=P["card2"], highlightthickness=1, highlightbackground=P["line"])
        self.cpu_advisor_card.pack(fill="x", pady=(12, 0))
        tk.Label(self.cpu_advisor_card, text="Smart Scheduler Advisor", bg=P["card2"], fg=P["text"], font=("Segoe UI Semibold", 10)).pack(anchor="w", padx=12, pady=(10, 4))
        tk.Label(self.cpu_advisor_card, textvariable=self.cpu_advice_title, bg=P["card2"], fg=P["green2"], font=("Segoe UI Semibold", 11), wraplength=250, justify="left").pack(anchor="w", padx=12)
        tk.Label(self.cpu_advisor_card, textvariable=self.cpu_advice_reason, bg=P["card2"], fg=P["text"], font=("Segoe UI", 9), wraplength=250, justify="left").pack(anchor="w", padx=12, pady=(6, 2))
        tk.Label(self.cpu_advisor_card, textvariable=self.cpu_advice_tradeoff, bg=P["card2"], fg=P["gold"], font=("Segoe UI", 9), wraplength=250, justify="left").pack(anchor="w", padx=12, pady=(0, 2))
        tk.Label(self.cpu_advisor_card, textvariable=self.cpu_advice_ranking, bg=P["card2"], fg=P["muted"], font=("Segoe UI", 8), wraplength=250, justify="left").pack(anchor="w", padx=12, pady=(0, 10))
        self.update_cpu_controls()
        result_card, result_body = self.card(panel, "Execution Results")
        result_card.grid(row=0, column=1, sticky="nsew", padx=(10, 0), pady=4)
        self.result_area = result_body
        self.result_canvas = tk.Canvas(result_body, bg=P["card"], bd=0, highlightthickness=0)
        self.result_scrollbar = ttk.Scrollbar(result_body, orient="vertical", command=self.result_canvas.yview, style="Vertical.TScrollbar")
        self.result_content = tk.Frame(self.result_canvas, bg=P["card"])
        self.result_content.bind(
            "<Configure>",
            lambda event: self.result_canvas.configure(scrollregion=self.result_canvas.bbox("all")),
        )
        self.result_window = self.result_canvas.create_window((0, 0), window=self.result_content, anchor="nw")
        self.result_canvas.configure(yscrollcommand=self.result_scrollbar.set)
        self.result_canvas.pack(side="left", fill="both", expand=True)
        self.result_scrollbar.pack(side="right", fill="y")
        self.result_canvas.bind(
            "<Configure>",
            lambda event: self.result_canvas.itemconfigure(self.result_window, width=event.width),
        )
        self.gantt_section = tk.Frame(self.result_content, bg=P["card2"], highlightthickness=1, highlightbackground=P["line"])
        self.gantt_section.pack(fill="x", pady=(0, 10))
        tk.Label(self.gantt_section, text="Gantt Chart", bg=P["card2"], fg=P["text"], font=("Segoe UI Semibold", 11)).pack(anchor="w", padx=14, pady=(12, 8))
        self.gantt_hint = tk.Label(
            self.gantt_section,
            text="Use the color legend and hover tooltip to identify process blocks.",
            bg=P["card2"],
            fg=P["muted"],
            font=("Segoe UI", 8),
        )
        self.gantt_hint.pack(anchor="w", padx=14, pady=(0, 6))
        self.gantt_canvas_frame = tk.Frame(self.gantt_section, bg=P["card2"])
        self.gantt_canvas_frame.pack(fill="x", padx=14, pady=(0, 12))
        self.gantt_canvas = tk.Canvas(self.gantt_canvas_frame, height=96, bg=P["card2"], bd=0, highlightthickness=0)
        self.gantt_scrollbar = ttk.Scrollbar(self.gantt_canvas_frame, orient="horizontal", command=self.gantt_canvas.xview, style="Horizontal.TScrollbar")
        self.gantt_canvas.configure(xscrollcommand=self.gantt_scrollbar.set)
        self.gantt_canvas.bind("<Motion>", self.on_gantt_hover)
        self.gantt_canvas.bind("<Leave>", self.hide_gantt_tooltip)
        self.gantt_canvas.pack(fill="x")
        self.gantt_scrollbar.pack(fill="x", pady=(6, 0))
        self.gantt_legend = tk.Frame(self.gantt_section, bg=P["card2"])
        self.gantt_legend.pack(fill="x", padx=14, pady=(4, 10))
        self.stats_section = tk.Frame(self.result_content, bg=P["card"])
        self.stats_section.pack(fill="x", pady=(0, 10))
        self.avg_tat_card, self.avg_tat_label, self.avg_tat_value = self.stat(self.stats_section, "Avg TAT", "-", P["blue"])
        self.avg_tat_card.pack(side="left", fill="x", expand=True, padx=(0, 6))
        self.avg_wt_card, self.avg_wt_label, self.avg_wt_value = self.stat(self.stats_section, "Avg WT", "-", P["green"])
        self.avg_wt_card.pack(side="left", fill="x", expand=True, padx=(6, 0))
        self.table_section = tk.Frame(self.result_content, bg=P["card2"], highlightthickness=1, highlightbackground=P["line"])
        self.table_section.pack(fill="both", expand=True)
        tk.Label(self.table_section, text="Result Table", bg=P["card2"], fg=P["text"], font=("Segoe UI Semibold", 11)).pack(anchor="w", padx=14, pady=(12, 8))
        self.cpu_result_table_frame = tk.Frame(self.table_section, bg=P["card2"])
        self.cpu_result_table_frame.pack(fill="both", expand=True, padx=14, pady=(0, 14))
        self.cpu_result_table = ttk.Treeview(
            self.cpu_result_table_frame,
            columns=("pid", "at", "bt", "pr", "ct", "tat", "wt"),
            show="headings",
            style="Cpu.Treeview",
            height=4,
        )
        for key, title, width in [
            ("pid", "PID", 44),
            ("at", "AT", 44),
            ("bt", "BT", 44),
            ("pr", "PR", 44),
            ("ct", "CT", 44),
            ("tat", "TAT", 50),
            ("wt", "WT", 44),
        ]:
            self.cpu_result_table.heading(key, text=title)
            self.cpu_result_table.column(key, width=width, anchor="center", stretch=True)
        self.cpu_result_table_scroll = tk.Scrollbar(self.cpu_result_table_frame, orient="vertical", command=self.cpu_result_table.yview)
        self.cpu_result_table.configure(yscrollcommand=self.cpu_result_table_scroll.set)
        self.cpu_result_table.pack(side="left", fill="both", expand=True)
        self.cpu_result_table_scroll.pack(side="right", fill="y")
        self.draw_gantt(self.gantt_canvas, [])
        self.render_result_table([])
        logs_card, logs_body = self.card(panel, "System Logs")
        logs_card.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=0, pady=(10, 4))
        self.cpu_logs = tk.Text(logs_body, bg="#0c1220", fg="#a7df9e", insertbackground="white", relief="flat", bd=0, font=("Cascadia Code", 9), padx=12, pady=12, height=8, wrap="word")
        self.cpu_logs.pack(side="left", fill="both", expand=True)
        self.logs_scrollbar = ttk.Scrollbar(logs_body, orient="vertical", command=self.cpu_logs.yview, style="Vertical.TScrollbar")
        self.cpu_logs.configure(yscrollcommand=self.logs_scrollbar.set)
        self.logs_scrollbar.pack(side="right", fill="y")
        self.log_cpu("[Ready] Configure processes and run an algorithm.")
        return outer

    def rebuild_cpu_table(self):
        for child in self.cpu_input_table_host.winfo_children(): child.destroy()
        count = int(self.cpu_count.get()) if self.cpu_count.get().isdigit() else 3
        self.cpu_rows = []
        priority_enabled = self.cpu_algo.get() in ("Priority (Preemptive)", "Priority (Non-Preemptive)")
        headers = ["PID", "AT", "BT"] + (["PR"] if priority_enabled else [])
        for c, h in enumerate(headers):
            tk.Label(self.cpu_input_table_host, text=h, bg=P["card2"], fg=P["text"], font=("Segoe UI Semibold", 9), width=7, pady=6,
                     highlightthickness=1, highlightbackground=P["line"]).grid(row=0, column=c, sticky="nsew")
        defaults = [("0", "6"), ("1", "2"), ("2", "4"), ("3", "3"), ("4", "5")]
        for i in range(count):
            tk.Label(self.cpu_input_table_host, text=f"P{i+1}", bg=P["card"], fg=P["text"], width=7, pady=6,
                     highlightthickness=1, highlightbackground=P["line"]).grid(row=i+1, column=0, sticky="nsew")
            at = tk.StringVar(value=defaults[i][0] if i < len(defaults) else str(i))
            bt = tk.StringVar(value=defaults[i][1] if i < len(defaults) else "1")
            pr = tk.StringVar(value=str(count - i))
            entries = []
            vars_to_render = [at, bt] + ([pr] if priority_enabled else [])
            for c, var in enumerate(vars_to_render, start=1):
                entry = tk.Entry(
                    self.cpu_input_table_host,
                    textvariable=var,
                    bg=P["input"],
                    fg=P["text"],
                    insertbackground=P["text"],
                    relief="flat",
                    justify="center",
                    highlightthickness=1,
                    highlightbackground=P["line"],
                    highlightcolor=P["blue2"],
                    bd=0,
                )
                entry.grid(row=i+1, column=c, sticky="nsew", padx=1, pady=1, ipadx=4, ipady=6)
                entries.append(entry)
            pr_entry = entries[2] if priority_enabled else None
            self.cpu_rows.append((f"P{i+1}", at, bt, pr, pr_entry))
        self.update_cpu_controls()

    def on_algorithm_change(self):
        self.rebuild_cpu_table()
        self.update_cpu_controls()

    def update_cpu_controls(self):
        if not hasattr(self, "quantum_row") or not hasattr(self, "algorithm_combo"):
            return
        algo = self.cpu_algo.get()
        show_quantum = algo == "Round Robin"
        priority_enabled = algo in ("Priority (Preemptive)", "Priority (Non-Preemptive)")
        if show_quantum:
            if not self.quantum_row.winfo_manager():
                self.quantum_row.pack(fill="x", pady=6, before=self.algorithm_combo.master)
        else:
            self.quantum_row.pack_forget()
        self.input_note.configure(
            text="Priority is enabled only for Priority (Preemptive) and Priority (Non-Preemptive). Round Robin uses Time Quantum."
        )

    def run_cpu(self):
        try:
            procs, quantum = self.collect_cpu_processes(require_rr_quantum=self.cpu_algo.get() == "Round Robin")
        except ValueError as e:
            error_msg = str(e) if str(e) else "Arrival time must be 0 or more, burst time must be greater than 0, priority must be a whole number, and Round Robin needs a valid time quantum."
            messagebox.showerror("CPU Scheduling", error_msg)
            return
        algo = self.cpu_algo.get()
        try:
            self.write_cpu_process_data(procs, quantum)
            output = self.run_cpu_c_program(algo)
            segs = self.read_gantt_segments()
            rows, avg_wt, avg_tat = self.parse_cpu_output(output, algo)
        except Exception as exc:
            messagebox.showerror("CPU Scheduling", str(exc))
            self.log_cpu(f"[Error] {exc}")
            return
        self.cpu_result = {"segs": segs, "rows": rows, "avg_tat": avg_tat, "avg_wt": avg_wt}
        self.render_cpu_result()
        self.log_cpu(f"[Run] {algo} finished for {len(rows)} processes using C scheduler.")
        self.status.set(f"{algo} completed")

    def collect_cpu_processes(self, require_rr_quantum=False):
        procs = []
        priorities = set()
        has_priority = False
        for pid, at, bt, pr, _ in self.cpu_rows:
            arrival, burst = float(at.get()), float(bt.get())
            if arrival < 0 or burst <= 0:
                raise ValueError
            if pr is not None:
                priority = int(pr.get())
                has_priority = True
                if priority in priorities:
                    raise ValueError(f"Duplicate priority {priority}! All priorities must be unique.")
                priorities.add(priority)
                procs.append({"pid": pid, "at": arrival, "bt": burst, "pr": priority})
            else:
                procs.append({"pid": pid, "at": arrival, "bt": burst, "pr": 0})
        quantum = float(self.cpu_quantum.get())
        if quantum <= 0 and require_rr_quantum:
            raise ValueError
        if quantum <= 0:
            quantum = 1.0
        return procs, quantum

    def suggest_cpu_algorithm(self):
        try:
            procs, quantum = self.collect_cpu_processes(require_rr_quantum=False)
            recommendation = analyze_and_recommend(procs, quantum)
        except ValueError:
            messagebox.showerror("CPU Scheduling", "Enter valid arrival times, burst times, priorities, and a positive time quantum before requesting advice.")
            return
        best = recommendation["recommended"]
        ranking_text = " > ".join(item["name"] for item in recommendation["ranking"][:3])
        self.cpu_advice_title.set(f"Recommended: {best}")
        self.cpu_advice_reason.set(f"Why: {recommendation['reason']}.")
        self.cpu_advice_tradeoff.set(f"Tradeoff: {recommendation['tradeoff']}.")
        self.cpu_advice_ranking.set(f"Top options: {ranking_text}")
        self.log_cpu(f"[Advisor] Recommended {best} using Python backend analysis.")
        self.status.set(f"Advisor recommends {best}")
        self.flash(self.cpu_advisor_card)

    def render_cpu_result(self):
        self.gantt_canvas.update_idletasks()
        self.draw_gantt(self.gantt_canvas, self.cpu_result["segs"])
        self.avg_tat_value.configure(text=f"{self.cpu_result['avg_tat']:.2f}")
        self.avg_wt_value.configure(text=f"{self.cpu_result['avg_wt']:.2f}")
        self.render_result_table(self.cpu_result["rows"])
        self.result_content.update_idletasks()
        self.flash(self.table_section)

    def render_result_table(self, rows):
        priority_enabled = self.cpu_algo.get() in ("Priority (Preemptive)", "Priority (Non-Preemptive)")
        visible_columns = ("pid", "at", "bt", "pr", "ct", "tat", "wt") if priority_enabled else ("pid", "at", "bt", "ct", "tat", "wt")
        self.cpu_result_table.configure(displaycolumns=visible_columns)
        for item in self.cpu_result_table.get_children():
            self.cpu_result_table.delete(item)
        if not rows:
            self.cpu_result_table.insert("", "end", values=("No data", "", "", "", "", "", ""))
            return
        for row in rows:
            vals = [row["pid"], row["at"], row["bt"], row["pr"], row["ct"], row["tat"], row["wt"]]
            formatted = []
            for value in vals:
                if isinstance(value, float):
                    formatted.append(f"{value:.0f}" if value.is_integer() else f"{value:.2f}")
                else:
                    formatted.append(value)
            self.cpu_result_table.insert("", "end", values=tuple(formatted))

    def stat(self, parent, label, value, color):
        card = tk.Frame(parent, bg=P["card2"], highlightthickness=1, highlightbackground=P["line"])
        tk.Frame(card, bg=P["glass_soft"], height=1).pack(fill="x", side="top")
        label_widget = tk.Label(card, text=label, bg=P["card2"], fg=P["muted"], font=("Segoe UI Semibold", 10))
        label_widget.pack(anchor="w", padx=14, pady=(12, 4))
        value_widget = tk.Label(card, text=value, bg=P["card2"], fg=color, font=("Segoe UI Semibold", 18))
        value_widget.pack(anchor="w", padx=14, pady=(0, 12))
        return card, label_widget, value_widget

    def draw_gantt(self, canvas, segs):
        canvas.delete("all")
        self.gantt_regions = []
        if hasattr(self, "gantt_legend"):
            for child in self.gantt_legend.winfo_children():
                child.destroy()
        canvas.update_idletasks()
        if not segs:
            canvas.create_text(20, 30, text="No execution data", fill=P["muted"], anchor="w", font=("Segoe UI", 10))
            canvas.configure(scrollregion=(0, 0, max(canvas.winfo_width(), 400), 96))
            return
        colors = [P["blue"], P["red"], P["green"], "#4ca6ff", "#8a72ff"]
        cmap, ci = {}, 0
        start, end = segs[0]["start"], segs[-1]["end"]
        total = max(end - start, 1)
        left, top = 16, 18
        visible_width = max(canvas.winfo_width() - 32, 420)
        width = max(visible_width, int(total * 22))
        canvas.create_line(left, top + 32, left + width, top + 32, fill=P["line"])
        for s in segs:
            if s["pid"] != "IDLE" and s["pid"] not in cmap:
                cmap[s["pid"]] = colors[ci % len(colors)]; ci += 1
        for pid, color in cmap.items():
            item = tk.Frame(self.gantt_legend, bg=P["card2"])
            item.pack(side="left", padx=(0, 12))
            tk.Label(item, width=2, bg=color, fg=color).pack(side="left", padx=(0, 6))
            tk.Label(item, text=pid, bg=P["card2"], fg=P["text"], font=("Segoe UI", 9)).pack(side="left")
        for s in segs:
            x1 = left + ((s["start"] - start) / total) * width
            x2 = left + ((s["end"] - start) / total) * width
            fill = "#1c263c" if s["pid"] == "IDLE" else cmap[s["pid"]]
            canvas.create_rectangle(x1, top, x2, top + 32, fill=fill, outline=fill)
            self.gantt_regions.append(
                {"x1": x1, "y1": top, "x2": x2, "y2": top + 32, "pid": s["pid"], "start": s["start"], "end": s["end"]}
            )
            canvas.create_line(x1, top + 32, x1, top + 38, fill=P["muted"])
            canvas.create_text(x1, top + 50, text=f"{s['start']:.0f}", fill=P["text"], anchor="n", font=("Segoe UI", 9))
        canvas.create_line(left + width, top + 32, left + width, top + 38, fill=P["muted"])
        canvas.create_text(left + width, top + 50, text=f"{end:.0f}", fill=P["text"], anchor="n", font=("Segoe UI", 9))
        canvas.configure(scrollregion=(0, 0, left + width + 20, 108))

    def on_gantt_hover(self, event):
        if not self.gantt_regions:
            self.hide_gantt_tooltip()
            return
        canvas_x = self.gantt_canvas.canvasx(event.x)
        canvas_y = self.gantt_canvas.canvasy(event.y)
        for region in self.gantt_regions:
            if region["x1"] <= canvas_x <= region["x2"] and region["y1"] <= canvas_y <= region["y2"]:
                label = f'{region["pid"]}: {region["start"]:.0f} -> {region["end"]:.0f}'
                if self.gantt_tooltip is None:
                    self.gantt_tooltip = tk.Label(
                        self.gantt_canvas,
                        text=label,
                        bg="#0b1322",
                        fg=P["text"],
                        font=("Segoe UI", 9),
                        padx=8,
                        pady=4,
                        highlightthickness=1,
                        highlightbackground=P["line"],
                    )
                else:
                    self.gantt_tooltip.configure(text=label)
                self.gantt_tooltip.place(x=event.x + 12, y=event.y + 12)
                return
        self.hide_gantt_tooltip()

    def hide_gantt_tooltip(self, event=None):
        if self.gantt_tooltip is not None:
            self.gantt_tooltip.place_forget()

    def log_cpu(self, text):
        if "Error" in text:
            color = "#ef4444"
        elif "Run" in text:
            color = "#22c55e"
        elif "Advisor" in text:
            color = "#3b82f6"
        else:
            color = "#a7df9e"

        self.cpu_logs.insert(tk.END, text + "\n")
        self.cpu_logs.tag_add(color, "end-2l", "end-1l")
        self.cpu_logs.tag_config(color, foreground=color)
        self.cpu_logs.see(tk.END)

    def flash(self, widget):
        seq = [P["blue"], P["blue2"], P["line"]]
        def step(i=0):
            widget.configure(highlightbackground=seq[i])
            if i < 2: self.root.after(90, lambda: step(i + 1))
        step()

    def write_cpu_process_data(self, procs, quantum):
        lines = [str(len(procs))]
        for proc in procs:
            lines.append(f'{proc["at"]:.2f} {proc["bt"]:.2f} {proc["pr"]}')
        lines.append(f"{quantum:.2f}")
        (CPU_DIR / "process_data.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")

    def run_cpu_c_program(self, algorithm):
        source_name = self.cpu_programs[algorithm]
        exe_name = Path(source_name).stem + ".exe"
        compile_run = subprocess.run(
            ["gcc", source_name, "-o", exe_name, "-lm"],
            cwd=CPU_DIR,
            capture_output=True,
            text=True,
        )
        if compile_run.returncode != 0:
            raise RuntimeError(f"GCC compile failed for {source_name}.\n{compile_run.stdout}\n{compile_run.stderr}".strip())

        exec_run = subprocess.run(
            [str(CPU_DIR / exe_name)],
            cwd=CPU_DIR,
            capture_output=True,
            text=True,
        )
        if exec_run.returncode != 0:
            raise RuntimeError(f"{algorithm} execution failed.\n{exec_run.stdout}\n{exec_run.stderr}".strip())
        return exec_run.stdout

    def read_gantt_segments(self):
        gantt_path = CPU_DIR / "gantt_data.txt"
        if not gantt_path.exists():
            raise RuntimeError("gantt_data.txt was not created by the CPU scheduler.")
        segments = []
        for line in gantt_path.read_text(encoding="utf-8").splitlines():
            parts = line.split()
            if len(parts) != 3:
                continue
            pid, start, duration = parts[0], float(parts[1]), float(parts[2])
            segments.append({"pid": pid, "start": start, "end": start + duration})
        if not segments:
            raise RuntimeError("No Gantt chart data was produced.")
        return segments

    def parse_cpu_output(self, output, algorithm):
        rows = []
        avg_wt = None
        avg_tat = None
        reading_rows = False
        has_priority = "Priority" in algorithm

        for raw_line in output.splitlines():
            line = raw_line.strip()
            if not line:
                continue

            if line.startswith("PID"):
                reading_rows = True
                continue

            if "Average Waiting Time" in line or "Average Waiting Time =" in line:
                avg_wt = float(line.split()[-1])
                reading_rows = False
                continue

            if "Average Turnaround Time" in line or "Average Turnaround Time =" in line:
                avg_tat = float(line.split()[-1])
                reading_rows = False
                continue

            if reading_rows:
                parts = line.split()
                token = parts[0]
                if not (token.startswith("P") or token.isdigit()):
                    continue
                if has_priority and len(parts) >= 7:
                    pid_text = token if token.startswith("P") else f"P{token}"
                    rows.append({
                        "pid": pid_text,
                        "at": float(parts[1]),
                        "bt": float(parts[2]),
                        "pr": int(parts[3]),
                        "ct": float(parts[4]),
                        "tat": float(parts[5]),
                        "wt": float(parts[6]),
                    })
                elif len(parts) >= 6:
                    pid_text = token if token.startswith("P") else f"P{token}"
                    pid_number = int(token[1:]) if token.startswith("P") else int(token)
                    rows.append({
                        "pid": pid_text,
                        "at": float(parts[1]),
                        "bt": float(parts[2]),
                        "pr": pid_number,
                        "ct": float(parts[3]),
                        "tat": float(parts[4]),
                        "wt": float(parts[5]),
                    })

        if not rows:
            raise RuntimeError(f"Could not parse result table from {algorithm} output.")
        if avg_wt is None:
            avg_wt = sum(row["wt"] for row in rows) / len(rows)
        if avg_tat is None:
            avg_tat = sum(row["tat"] for row in rows) / len(rows)
        return rows, avg_wt, avg_tat

    def build_memory_panel(self, parent):
        outer, panel = self.create_scrollable_panel(parent)
        panel.grid_columnconfigure(0, weight=3, minsize=320)
        panel.grid_columnconfigure(1, weight=7, minsize=620)
        left, body = self.card(panel, "Memory Management")
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=4)
        mode_combo = self.field(body, "Mode Selection", self.mem_mode, ["Contiguous Allocation", "Non-Contiguous Allocation (Paging)"])
        mode_combo.bind("<<ComboboxSelected>>", lambda e: self.on_memory_mode_change())
        self.mem_mode_host = tk.Frame(body, bg=P["card"])
        self.mem_mode_host.pack(fill="both", expand=True, pady=(10, 0))

        self.mem_contiguous_form = tk.Frame(self.mem_mode_host, bg=P["card"])
        self.field(self.mem_contiguous_form, "Number of Memory Blocks", self.mem_block_count)
        self.mem_blocks_host = tk.Frame(self.mem_contiguous_form, bg=P["card"])
        self.mem_blocks_host.pack(fill="x", pady=(8, 4))
        self.field(self.mem_contiguous_form, "Number of Processes", self.mem_process_count)
        self.mem_processes_host = tk.Frame(self.mem_contiguous_form, bg=P["card"])
        self.mem_processes_host.pack(fill="x", pady=(8, 4))
        self.field(self.mem_contiguous_form, "Allocation Type", self.mem_allocation_type, ["Fixed Allocation", "Variable Allocation"])
        self.mem_algorithm_combo = self.field(self.mem_contiguous_form, "Algorithm Selection", self.mem_contiguous_algo, ["First Fit", "Best Fit", "Worst Fit"])
        self.mem_algorithm_combo.bind("<<ComboboxSelected>>", lambda e: self.render_memory_result())
        self.btn(self.mem_contiguous_form, "Run Allocation", self.run_contiguous_memory, P["blue"], P["blue2"]).pack(fill="x", pady=(12, 0))
        tk.Label(
            self.mem_contiguous_form,
            text="Fixed Allocation uses one process per block. Variable Allocation splits free space dynamically and removes internal fragmentation.",
            bg=P["card"],
            fg=P["muted"],
            justify="left",
            wraplength=280,
            font=("Segoe UI", 9),
        ).pack(anchor="w", pady=(8, 0))

        self.mem_paging_form = tk.Frame(self.mem_mode_host, bg=P["card"])
        self.field(self.mem_paging_form, "Number of Pages", self.mem_page_count)
        self.field(self.mem_paging_form, "Reference String", self.mem_refs)
        self.field(self.mem_paging_form, "Number of Frames", self.mem_frames)
        self.btn(self.mem_paging_form, "Run Paging", self.run_paging_memory, P["blue"], P["blue2"]).pack(fill="x", pady=(12, 0))
        tk.Label(
            self.mem_paging_form,
            text="Run Paging compares FIFO and LRU, highlights page faults, and shows the better algorithm.",
            bg=P["card"],
            fg=P["muted"],
            justify="left",
            wraplength=280,
            font=("Segoe UI", 9),
        ).pack(anchor="w", pady=(8, 0))

        right, out = self.card(panel, "Execution Results")
        right.grid(row=0, column=1, sticky="nsew", padx=(10, 0), pady=4)
        self.mem_status = tk.StringVar(value="Configure Memory Management inputs and run a mode to populate the results panel.")
        tk.Label(out, textvariable=self.mem_status, bg=P["card"], fg=P["muted"], font=("Segoe UI", 10), wraplength=680, justify="left").pack(anchor="w", pady=(0, 12))
        self.mem_result_canvas = tk.Canvas(out, bg=P["card"], bd=0, highlightthickness=0)
        self.mem_result_scrollbar = tk.Scrollbar(out, orient="vertical", command=self.mem_result_canvas.yview)
        self.mem_result_content = tk.Frame(self.mem_result_canvas, bg=P["card"])
        self.mem_result_content.bind(
            "<Configure>",
            lambda event: self.mem_result_canvas.configure(scrollregion=self.mem_result_canvas.bbox("all")),
        )
        self.mem_result_window = self.mem_result_canvas.create_window((0, 0), window=self.mem_result_content, anchor="nw")
        self.mem_result_canvas.configure(yscrollcommand=self.mem_result_scrollbar.set)
        self.mem_result_canvas.pack(side="left", fill="both", expand=True)
        self.mem_result_scrollbar.pack(side="right", fill="y")
        self.mem_result_canvas.bind(
            "<Configure>",
            lambda event: self.mem_result_canvas.itemconfigure(self.mem_result_window, width=event.width),
        )

        self.mem_block_count.trace_add("write", lambda *_: self.schedule_memory_table_refresh())
        self.mem_process_count.trace_add("write", lambda *_: self.schedule_memory_table_refresh())
        self.rebuild_memory_tables()
        self.on_memory_mode_change(initial=True)
        return outer

    def on_memory_mode_change(self, initial=False):
        for frame in (self.mem_contiguous_form, self.mem_paging_form):
            frame.pack_forget()
        if self.mem_mode.get() == "Contiguous Allocation":
            self.mem_contiguous_form.pack(fill="both", expand=True)
            if initial and not self.mem_result:
                self.mem_status.set("Set memory blocks, process sizes, allocation type, and then run allocation to compare First Fit, Best Fit, and Worst Fit.")
        else:
            self.mem_paging_form.pack(fill="both", expand=True)
            if initial and not self.mem_result:
                self.mem_status.set("Set the page count, reference string, and frame count, then run paging to compare FIFO and LRU.")
        self.render_memory_result()

    def schedule_memory_table_refresh(self):
        job = getattr(self, "mem_table_job", None)
        if job:
            self.root.after_cancel(job)
        self.mem_table_job = self.root.after(140, self.rebuild_memory_tables)

    def rebuild_memory_tables(self):
        self.mem_table_job = None
        self.mem_block_rows = self.build_memory_size_table(
            self.mem_blocks_host,
            "Block",
            self.safe_positive_count(self.mem_block_count.get(), 5, 12),
            self.mem_block_rows,
            ["120", "350", "200", "500", "275"],
        )
        self.mem_process_rows = self.build_memory_size_table(
            self.mem_processes_host,
            "Process",
            self.safe_positive_count(self.mem_process_count.get(), 4, 12),
            self.mem_process_rows,
            ["95", "180", "320", "110"],
        )

    def build_memory_size_table(self, host, prefix, count, existing_rows, defaults):
        for child in host.winfo_children():
            child.destroy()
        count = max(1, min(count, 12))
        existing_values = [var.get() for _, var in existing_rows]
        rows = []
        tk.Label(host, text=f"{prefix} ID", bg=P["card2"], fg=P["text"], font=("Segoe UI Semibold", 9), width=11, pady=6,
                 highlightthickness=1, highlightbackground=P["line"]).grid(row=0, column=0, sticky="nsew")
        tk.Label(host, text="Size (e.g. 12MB 256KB)", bg=P["card2"], fg=P["text"], font=("Segoe UI Semibold", 9), width=13, pady=6,
                 highlightthickness=1, highlightbackground=P["line"]).grid(row=0, column=1, sticky="nsew")
        for idx in range(count):
            tk.Label(host, text=f"{prefix[0]}{idx + 1}" if prefix == "Process" else f"B{idx + 1}", bg=P["card"], fg=P["text"], width=11, pady=6,
                     highlightthickness=1, highlightbackground=P["line"]).grid(row=idx + 1, column=0, sticky="nsew")
            default_value = existing_values[idx] if idx < len(existing_values) else defaults[idx] if idx < len(defaults) else "100"
            container = tk.Frame(host, bg=P["card"])
            container.grid(row=idx + 1, column=1, sticky="nsew", padx=1, pady=1)

            var = tk.StringVar(value=default_value)

            entry = tk.Entry(
                container,
                textvariable=var,
                bg=P["bg2"],
                fg=P["text"],
                insertbackground=P["text"],
                relief="flat",
                justify="center"
            )
            entry.pack(fill="x", ipady=6)

            preview = tk.Label(
                container,
                text="",
                bg=P["card"],
                fg="#9ca3af",
                font=("Segoe UI", 8)
            )
            preview.pack(anchor="e")

            entry.bind(
                "<KeyRelease>",
                lambda e, ent=entry, v=var, p=preview: self.validate_size_entry(ent, v, p)
            )

            rows.append((f"{prefix[0]}{idx + 1}" if prefix == "Process" else f"B{idx + 1}", var))
        return rows

    def safe_positive_count(self, value, fallback, maximum):
        try:
            parsed = int(value)
            if parsed <= 0:
                raise ValueError
            return min(parsed, maximum)
        except ValueError:
            return fallback

    def unit_to_bytes(self, value, unit):
        factors = {"Bytes": 1, "KB": 1024, "MB": 1024 * 1024}
        return value * factors[unit]

    def format_size_input(self, value):
        import re

        def replace_unit(match):
            number = match.group(1)
            spacer = match.group(2)
            unit = match.group(3).lower()
            unit_map = {
                "mb": "MB",
                "kb": "KB",
                "gb": "GB",
                "bit": "bit",
                "bits": "bit",
                "b": "B",
                "byte": "B",
                "bytes": "B",
            }
            return f"{number}{spacer}{unit_map[unit]}"

        return re.sub(
            r"(\d+(?:\.\d+)?)(\s*)(mb|kb|gb|bits?|bytes?|b)\b",
            replace_unit,
            value,
            flags=re.IGNORECASE,
        )

    def parse_complex_size(self, value):
        import re
        value = value.lower().strip()
        matches = re.findall(r"(\d+(?:\.\d+)?)(?:\s*)(mb|kb|gb|bits?|bytes?|b)\b", value)
        if not matches:
            raise ValueError("No valid size found")
        total_bytes = 0
        multipliers = {
            "mb": 1024 * 1024,
            "kb": 1024,
            "gb": 1024 * 1024 * 1024,
            "bit": 1 / 8,
            "bits": 1 / 8,
            "b": 1,
            "byte": 1,
            "bytes": 1,
        }
        for num, unit in matches:
            total_bytes += float(num) * multipliers[unit]
        return total_bytes

    def validate_size_entry(self, entry, var, preview_label):
        value = var.get()

        try:
            formatted = self.format_size_input(value)
            var.set(formatted)

            size_bytes = self.parse_complex_size(formatted)
            size_mb = size_bytes / (1024 * 1024)

            preview_label.config(text=f"≈ {size_mb:.2f} MB", fg="#22c55e")
            entry.config(bg="#052e16")

        except:
            preview_label.config(text="Invalid format", fg="#ef4444")
            entry.config(bg="#3f1d1d")

    def format_bytes(self, value):
        if value >= 1024 * 1024:
            return f"{value / (1024 * 1024):.2f} MB"
        if value >= 1024:
            return f"{value / 1024:.2f} KB"
        return f"{value:.0f} Bytes"

    def memory_section(self, parent, title):
        wrap = tk.Frame(parent, bg=P["card2"], highlightthickness=1, highlightbackground=P["line"])
        tk.Frame(wrap, bg=P["glass_soft"], height=1).pack(fill="x", side="top")
        tk.Label(wrap, text=title, bg=P["card2"], fg=P["text"], font=("Segoe UI Semibold", 11)).pack(anchor="w", padx=14, pady=(12, 8))
        body = tk.Frame(wrap, bg=P["card2"])
        body.pack(fill="both", expand=True, padx=14, pady=(0, 14))
        return wrap, body

    def clear_memory_results(self):
        for child in self.mem_result_content.winfo_children():
            child.destroy()

    def render_memory_result(self):
        if not hasattr(self, "mem_result_content"):
            return
        self.clear_memory_results()
        active_mode = "contiguous" if self.mem_mode.get() == "Contiguous Allocation" else "paging"
        if not self.mem_result or self.mem_result["mode"] != active_mode:
            placeholder = tk.Frame(self.mem_result_content, bg=P["card2"], highlightthickness=1, highlightbackground=P["line"])
            placeholder.pack(fill="x")
            tk.Label(placeholder, text="No execution data", bg=P["card2"], fg=P["text"], font=("Segoe UI Semibold", 12)).pack(anchor="w", padx=14, pady=(14, 6))
            tk.Label(
                placeholder,
                text="The result panel will show allocation visualizations, fragmentation, utilization, page-fault comparisons, and detailed tables after you run the active mode.",
                bg=P["card2"],
                fg=P["muted"],
                justify="left",
                wraplength=660,
                font=("Segoe UI", 10),
            ).pack(anchor="w", padx=14, pady=(0, 14))
            return
        if self.mem_result["mode"] == "contiguous":
            self.render_contiguous_results()
        else:
            self.render_paging_results()

    def run_contiguous_memory(self):
        try:
            blocks = self.read_memory_sizes_for_input(self.mem_block_rows, "memory blocks")
            processes = self.read_memory_sizes_for_input(self.mem_process_rows, "processes")
            self.run_memory_allocation_program(blocks, processes)
            self.mem_result = self.parse_memory_results()
            # Use comparator module to determine best algorithm
            comparison_result = comparator.compare_contiguous_methods(self.mem_result)
            self.mem_result["best"] = comparison_result["best_algorithm"]
            self.mem_result["comparison_ranking"] = comparison_result["ranking"]
        except (ValueError, RuntimeError) as exc:
            messagebox.showerror("Memory Management", str(exc))
            return
        self.mem_result["selected"] = self.mem_contiguous_algo.get()
        selected = self.mem_result["algorithms"][self.mem_contiguous_algo.get()]
        warning = " Some processes could not be allocated due to external fragmentation." if selected["external_fragmentation_warning"] else ""
        self.mem_status.set(
            f"{self.mem_result['allocation_type']} completed. Best Algorithm: {self.mem_result['best']}. "
            f"{selected['allocated_count']} of {len(processes)} processes allocated using {self.mem_contiguous_algo.get()}."
            f"{warning}"
        )
        self.render_memory_result()
        self.status.set("Contiguous memory allocation completed")

    def read_memory_sizes_for_input(self, rows, label):
        values = []
        for name, var in rows:
            try:
                self.parse_complex_size(var.get())  # validate
            except ValueError:
                raise ValueError(f"Enter valid sizes for all {label}.")
            values.append((name, var.get()))  # return formatted string
        return values

    def run_memory_allocation_program(self, blocks, processes):
        exe_name = "memory_allocation.exe"
        compile_run = subprocess.run(
            ["gcc", "memory_allocation.c", "-o", exe_name, "-lm"],
            cwd=MEMORY_DIR,
            capture_output=True,
            text=True,
        )
        if compile_run.returncode != 0:
            raise RuntimeError(f"GCC compile failed for memory_allocation.c.\n{compile_run.stdout}\n{compile_run.stderr}".strip())

        mode_token = "VARIABLE" if self.mem_allocation_type.get() == "Variable Allocation" else "FIXED"
        lines = [mode_token, str(len(blocks))]
        lines.extend(size for _, size in blocks)
        lines.append(str(len(processes)))
        lines.extend(size for _, size in processes)
        exec_run = subprocess.run(
            [str(MEMORY_DIR / exe_name), "--no-visualize"],
            cwd=MEMORY_DIR,
            capture_output=True,
            text=True,
            input="\n".join(lines) + "\n",
        )
        if exec_run.returncode != 0:
            raise RuntimeError(f"memory_allocation execution failed.\n{exec_run.stdout}\n{exec_run.stderr}".strip())

    def parse_memory_results(self):
        result_path = MEMORY_DIR / "memory_results.txt"
        if not result_path.exists():
            raise RuntimeError("memory_results.txt was not created by the Memory Management module.")

        mode_map = {"FIXED": "Fixed Allocation", "VARIABLE": "Variable Allocation"}
        algo_map = {"FIRST": "First Fit", "BEST": "Best Fit", "WORST": "Worst Fit"}
        meta = {"mode": "contiguous", "blocks": [], "processes": [], "algorithms": {}, "best": "First Fit"}
        current = None

        for raw in result_path.read_text(encoding="utf-8").splitlines():
            if not raw.strip():
                continue
            parts = raw.split()
            tag = parts[0]
            if tag == "MODE":
                meta["allocation_type"] = mode_map.get(parts[1], parts[1].title())
            elif tag == "BLOCK":
                meta["blocks"].append({"id": parts[1], "size_bytes": int(parts[2])})
            elif tag == "PROCESS":
                meta["processes"].append({"id": parts[1], "size_bytes": int(parts[2])})
            elif tag == "ALGO":
                current = {
                    "rows": [],
                    "blocks": [],
                    "allocated_count": 0,
                    "failed": 0,
                    "internal_fragmentation": 0,
                    "external_fragmentation": 0,
                    "utilization": 0.0,
                    "external_fragmentation_warning": False,
                }
                meta["algorithms"][algo_map[parts[1]]] = current
            elif tag == "SUMMARY" and current is not None:
                current["allocated_count"] = int(parts[1])
                current["failed"] = int(parts[2])
                current["internal_fragmentation"] = int(parts[3])
                current["external_fragmentation"] = int(parts[4])
                current["utilization"] = float(parts[5])
                current["external_fragmentation_warning"] = bool(int(parts[6]))
            elif tag == "ROW" and current is not None:
                allocated = bool(int(parts[2]))
                current["rows"].append(
                    {
                        "process": parts[1],
                        "allocated": allocated,
                        "block": f"B{parts[3]}" if allocated and int(parts[3]) > 0 else "-",
                        "block_size_bytes": int(parts[4]),
                        "process_size_bytes": int(parts[5]),
                        "internal_fragmentation": int(parts[6]),
                    }
                )
            elif tag == "BLOCKSTATE" and current is not None:
                process_list = parts[5] if len(parts) > 5 else "NONE"
                current["blocks"].append(
                    {
                        "id": parts[1],
                        "size_bytes": int(parts[2]),
                        "remaining_bytes": int(parts[3]),
                        "allocated": bool(int(parts[4])),
                        "process": process_list.replace(",", ", ") if process_list != "NONE" else None,
                    }
                )
            elif tag == "BEST_ALGO":
                meta["best"] = algo_map[parts[1]]

        meta["selected"] = self.mem_contiguous_algo.get()
        return meta

    def render_contiguous_results(self):
        selected = self.mem_contiguous_algo.get()
        self.mem_result["selected"] = selected
        selected_result = self.mem_result["algorithms"].get(selected, self.mem_result["algorithms"][self.mem_result["best"]])
        self.mem_result["selected"] = selected if selected in self.mem_result["algorithms"] else self.mem_result["best"]

        highlight = tk.Frame(self.mem_result_content, bg=P["card2"], highlightthickness=1, highlightbackground=P["line"])
        highlight.pack(fill="x", pady=(0, 10))
        tk.Label(highlight, text=f"Best Algorithm ({self.mem_result['allocation_type']})", bg=P["card2"], fg=P["muted"], font=("Segoe UI", 10)).pack(anchor="w", padx=14, pady=(12, 4))
        tk.Label(highlight, text=self.mem_result["best"], bg=P["card2"], fg=P["blue2"], font=("Segoe UI Semibold", 20)).pack(anchor="w", padx=14, pady=(0, 12))

        summary_row = tk.Frame(self.mem_result_content, bg=P["card"])
        summary_row.pack(fill="x", pady=(0, 10))
        summary_colors = {"First Fit": P["blue"], "Best Fit": P["green"], "Worst Fit": P["gold"]}
        for idx, name in enumerate(("First Fit", "Best Fit", "Worst Fit")):
            result = self.mem_result["algorithms"][name]
            card, _, _ = self.stat(summary_row, name, self.format_bytes(result["internal_fragmentation"]), summary_colors[name])
            card.pack(side="left", fill="x", expand=True, padx=(0 if idx == 0 else 5, 0 if idx == 2 else 5))
            tk.Label(
                card,
                text=(
                    f"Internal: {self.format_bytes(result['internal_fragmentation'])} | "
                    f"External: {'YES' if result['external_fragmentation_warning'] else 'NO'} "
                    f"({self.format_bytes(result['external_fragmentation'])})"
                ),
                bg=P["card2"],
                fg=P["muted"],
                font=("Segoe UI", 9),
            ).pack(anchor="w", padx=14, pady=(0, 4))
            tk.Label(card, text=f"{result['allocated_count']} allocated | {result['utilization']:.1f}% utilized", bg=P["card2"], fg=P["muted"], font=("Segoe UI", 9)).pack(anchor="w", padx=14, pady=(0, 10))

        if selected_result["external_fragmentation_warning"]:
            warning = tk.Frame(self.mem_result_content, bg="#24131c", highlightthickness=1, highlightbackground=P["red"])
            warning.pack(fill="x", pady=(0, 10))
            tk.Label(
                warning,
                text="Some processes could not be allocated due to external fragmentation.",
                bg="#24131c",
                fg="#ffb3bf",
                font=("Segoe UI Semibold", 10),
            ).pack(anchor="w", padx=14, pady=12)

        viz_wrap, viz_body = self.memory_section(self.mem_result_content, f"Memory Visualization ({self.mem_result['allocation_type']} | {self.mem_result['selected']})")
        viz_wrap.pack(fill="x", pady=(0, 10))
        viz_height = max(170, 46 + len(selected_result["blocks"]) * 52)
        viz_canvas = tk.Canvas(viz_body, height=viz_height, bg=P["card2"], bd=0, highlightthickness=0)
        viz_canvas.pack(fill="x")
        self.draw_contiguous_visualization(viz_canvas, selected_result)

        stats_row = tk.Frame(self.mem_result_content, bg=P["card"])
        stats_row.pack(fill="x", pady=(0, 10))
        internal_card, _, _ = self.stat(stats_row, "Internal Fragmentation", self.format_bytes(selected_result["internal_fragmentation"]), P["blue"])
        internal_card.pack(side="left", fill="x", expand=True, padx=(0, 4))
        external_card, _, _ = self.stat(
            stats_row,
            "External Fragmentation",
            "YES" if selected_result["external_fragmentation_warning"] else "NO",
            P["gold"],
        )
        external_card.pack(side="left", fill="x", expand=True, padx=4)
        tk.Label(
            external_card,
            text=f"Size: {self.format_bytes(selected_result['external_fragmentation'])}",
            bg=P["card2"],
            fg=P["muted"],
            font=("Segoe UI", 9),
        ).pack(anchor="w", padx=14, pady=(0, 10))
        util_card, _, _ = self.stat(stats_row, "Memory Utilization %", f"{selected_result['utilization']:.1f}%", P["green"])
        util_card.pack(side="left", fill="x", expand=True, padx=(4, 0))

        table_wrap, table_body = self.memory_section(self.mem_result_content, f"Result Table ({self.mem_result['allocation_type']} | {self.mem_result['selected']})")
        table_wrap.pack(fill="both", expand=True)
        self.draw_contiguous_table(table_body, selected_result["rows"])
        self.flash(table_wrap)

    def draw_contiguous_visualization(self, canvas, result):
        canvas.delete("all")
        blocks = result["blocks"]
        if not blocks:
            canvas.create_text(20, 24, text="No memory blocks configured", fill=P["muted"], anchor="w", font=("Segoe UI", 10))
            return
        w = max(canvas.winfo_width(), 620)
        left, top = 18, 24
        bar_width = w - 76
        row_height = 52
        bar_height = 22
        colors = [P["blue"], P["green"], "#4ca6ff", "#3f7fff", "#52b39f", "#7a9cff"]
        for idx, block in enumerate(blocks):
            y1 = top + idx * row_height
            used_bytes = block["size_bytes"] - block["remaining_bytes"]
            ratio = 0 if block["size_bytes"] == 0 else used_bytes / block["size_bytes"]
            canvas.create_text(left, y1 + 11, text=block["id"], fill=P["text"], anchor="w", font=("Segoe UI Semibold", 9))
            canvas.create_rectangle(left + 40, y1, left + 40 + bar_width, y1 + bar_height, fill="#0c1220", outline=P["line"])
            if used_bytes > 0:
                canvas.create_rectangle(left + 40, y1, left + 40 + (bar_width * ratio), y1 + bar_height, fill=colors[idx % len(colors)], outline="")
            if block["remaining_bytes"] > 0:
                free_start = left + 40 + (bar_width * ratio)
                canvas.create_rectangle(free_start, y1, left + 40 + bar_width, y1 + bar_height, fill="#2a3346", outline="")
            if block["allocated"]:
                internal = sum(row["internal_fragmentation"] for row in result["rows"] if row["block"] == block["id"] and row["allocated"])
                label = (
                    f"{block['process']} | Used {self.format_bytes(used_bytes)} / Free {self.format_bytes(block['remaining_bytes'])}"
                    f" | Internal {self.format_bytes(internal)}"
                )
            else:
                label = f"Free | {self.format_bytes(block['size_bytes'])}"
            canvas.create_text(left + 48, y1 + bar_height + 14, text=label, fill=P["muted"], anchor="w", font=("Segoe UI", 8))
        content_height = top + len(blocks) * row_height + 18
        canvas.configure(height=max(170, content_height), scrollregion=(0, 0, w, content_height))

    def draw_contiguous_table(self, parent, rows):
        table = ttk.Treeview(parent, columns=("process", "block", "internal", "status"), show="headings", style="Cpu.Treeview", height=min(max(len(rows), 4), 8))
        headings = [("process", "Process", 120), ("block", "Block Assigned", 160), ("internal", "Internal Fragmentation", 180), ("status", "Status", 120)]
        for key, title, width in headings:
            table.heading(key, text=title)
            table.column(key, width=width, anchor="center", stretch=True)
        table.tag_configure("unallocated", foreground="#ffb3bf")
        scrollbar = tk.Scrollbar(parent, orient="vertical", command=table.yview)
        table.configure(yscrollcommand=scrollbar.set)
        table.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        for row in rows:
            values = (
                row["process"],
                row["block"],
                self.format_bytes(row["internal_fragmentation"]) if row["allocated"] else "-",
                "Allocated" if row["allocated"] else "Unallocated",
            )
            table.insert("", "end", values=values, tags=("unallocated",) if not row["allocated"] else ())

    def run_paging_memory(self):
        try:
            page_count = int(self.mem_page_count.get())
            frames = int(self.mem_frames.get())
            refs = [int(x) for x in self.mem_refs.get().split()]
            if page_count <= 0 or frames <= 0 or not refs:
                raise ValueError
            required_pages = max(refs) + 1
            if page_count < required_pages:
                raise ValueError(f"Number of pages must be at least {required_pages} to accommodate the reference string.")
            if any(page < 0 or page >= page_count for page in refs):
                raise ValueError
        except ValueError as e:
            messagebox.showerror("Memory Management", str(e) if str(e) else "Enter a valid page count, frame count, and space-separated reference string using page numbers within range.")
            return
        try:
            self.run_paging_program(refs, frames)
            self.mem_result = self.parse_paging_results(page_count)
            # Use comparator module to determine best algorithm
            comparison_result = comparator.compare_paging_methods(self.mem_result)
            self.mem_result["better"] = comparison_result["best_algorithm"]
            self.mem_result["comparison_ranking"] = comparison_result["ranking"]
        except RuntimeError as exc:
            messagebox.showerror("Memory Management", str(exc))
            return
        self.mem_status.set(
            f"Paging completed across {len(refs)} references. "
            f"FIFO faults: {self.mem_result['algorithms']['FIFO']['fault_count']}, "
            f"LRU faults: {self.mem_result['algorithms']['LRU']['fault_count']}, Better Algorithm: {self.mem_result['better']}."
        )
        self.render_memory_result()
        self.status.set("Paging comparison completed")

    def run_paging_program(self, refs, frames):
        exe_name = "page_replacement.exe"
        compile_run = subprocess.run(
            ["gcc", "page_replacement.c", "-o", exe_name, "-lm"],
            cwd=MEMORY_DIR,
            capture_output=True,
            text=True,
        )
        if compile_run.returncode != 0:
            raise RuntimeError(f"GCC compile failed for page_replacement.c.\n{compile_run.stdout}\n{compile_run.stderr}".strip())
        exec_run = subprocess.run(
            [str(MEMORY_DIR / exe_name), "--no-visualize"],
            cwd=MEMORY_DIR,
            capture_output=True,
            text=True,
            input="\n".join([str(len(refs)), " ".join(str(ref) for ref in refs), str(frames)]) + "\n",
        )
        if exec_run.returncode != 0:
            raise RuntimeError(f"page_replacement execution failed.\n{exec_run.stdout}\n{exec_run.stderr}".strip())

    def parse_paging_results(self, page_count):
        result_path = MEMORY_DIR / "paging_results.txt"
        if not result_path.exists():
            raise RuntimeError("paging_results.txt was not created by the Memory Management module.")
        parsed = {"mode": "paging", "page_count": page_count, "algorithms": {}}
        current = None
        for raw in result_path.read_text(encoding="utf-8").splitlines():
            if not raw.strip():
                continue
            parts = raw.split()
            tag = parts[0]
            if tag == "REFS":
                parsed["refs"] = [int(x) for x in parts[1:]]
            elif tag == "FRAMES":
                parsed["frames"] = int(parts[1])
            elif tag == "ALGO":
                current = {"states": [], "faults": [], "fault_count": 0}
                parsed["algorithms"][parts[1]] = current
            elif tag == "SUMMARY" and current is not None:
                current["fault_count"] = int(parts[1])
            elif tag == "STEP" and current is not None:
                current["faults"].append(bool(int(parts[2])))
                current["states"].append(["-" if int(value) == -1 else int(value) for value in parts[3:]])
            elif tag == "BETTER":
                parsed["better"] = parts[1]
        return parsed

    def render_paging_results(self):
        highlight = tk.Frame(self.mem_result_content, bg=P["card2"], highlightthickness=1, highlightbackground=P["line"])
        highlight.pack(fill="x", pady=(0, 10))
        tk.Label(highlight, text="Better Algorithm", bg=P["card2"], fg=P["muted"], font=("Segoe UI", 10)).pack(anchor="w", padx=14, pady=(12, 4))
        tk.Label(highlight, text=self.mem_result["better"], bg=P["card2"], fg=P["blue2"], font=("Segoe UI Semibold", 20)).pack(anchor="w", padx=14, pady=(0, 12))

        stats_row = tk.Frame(self.mem_result_content, bg=P["card"])
        stats_row.pack(fill="x", pady=(0, 10))

        colors = [P["blue"], P["green"], P["gold"], "#ff7f50"]

        for i, (name, data) in enumerate(self.mem_result["algorithms"].items()):
            card, _, _ = self.stat(stats_row, f"{name} Page Faults", str(data["fault_count"]), colors[i % len(colors)])
            card.pack(side="left", fill="x", expand=True, padx=4)

        graph_wrap, graph_body = self.memory_section(self.mem_result_content, "Page Fault Comparison")
        graph_wrap.pack(fill="x", pady=(0, 10))

        graph_canvas = tk.Canvas(graph_body, height=180, bg=P["card2"], bd=0, highlightthickness=0)
        graph_canvas.pack(fill="x")

        self.draw_page_fault_chart(graph_canvas)

        for algo in self.mem_result["algorithms"]:
            wrap, body = self.memory_section(self.mem_result_content, f"{algo} Result")
            wrap.pack(fill="x", pady=(0, 10))

            self.draw_paging_table(
                body,
                self.mem_result["refs"],
                self.mem_result["algorithms"][algo]["states"],
                self.mem_result["algorithms"][algo]["faults"],
                algo
            )

            if algo == self.mem_result["better"] or self.mem_result["better"] == "Tie":
                self.flash(wrap)

    def draw_page_fault_chart(self, canvas):
        canvas.delete("all")

        values = []
        colors = [P["blue"], P["green"], P["gold"], "#ff7f50"]

        for i, (name, data) in enumerate(self.mem_result["algorithms"].items()):
            values.append((name, data["fault_count"], colors[i % len(colors)]))

            w = max(canvas.winfo_width(), 620)
            h = max(canvas.winfo_height(), 180)
            left, base = 72, h - 30

            max_val = max(value for _, value, _ in values) or 1

            canvas.create_line(left, 18, left, base, fill=P["line"])
            canvas.create_line(left, base, w - 40, base, fill=P["line"])

            for idx, (name, value, color) in enumerate(values):
                x1 = left + 70 + idx * 140
                x2 = x1 + 80

            bar_height = (value / max_val) * 110

            canvas.create_rectangle(x1, base - bar_height, x2, base, fill=color, outline=color)
            canvas.create_text((x1 + x2) / 2, base + 16, text=name, fill=P["text"], font=("Segoe UI Semibold", 10))
            canvas.create_text((x1 + x2) / 2, base - bar_height - 14, text=str(value), fill=P["text"], font=("Segoe UI", 10))

    def draw_paging_table(self, parent, refs, states, faults, algorithm):
        grid = tk.Frame(parent, bg=P["card2"])
        grid.pack(fill="x")
        tk.Label(grid, text=f"{algorithm} / Ref", bg=P["bg2"], fg=P["text"], width=10, pady=8,
                 highlightthickness=1, highlightbackground=P["line"], font=("Segoe UI Semibold", 9)).grid(row=0, column=0, sticky="nsew")
        for col, ref in enumerate(refs, start=1):
            bg = P["red"] if faults[col - 1] else P["bg2"]
            tk.Label(grid, text=str(ref), bg=bg, fg="white" if faults[col - 1] else P["text"], width=4, pady=8,
                     highlightthickness=1, highlightbackground=P["line"], font=("Segoe UI Semibold", 9)).grid(row=0, column=col, sticky="nsew")
        frame_count = len(states[0]) if states else 0
        for frame_idx in range(frame_count):
            tk.Label(grid, text=f"Frame {frame_idx + 1}", bg=P["bg2"], fg=P["text"], width=10, pady=8,
                     highlightthickness=1, highlightbackground=P["line"], font=("Segoe UI Semibold", 9)).grid(row=frame_idx + 1, column=0, sticky="nsew")
            for col, state in enumerate(states, start=1):
                tk.Label(grid, text=str(state[frame_idx]), bg=P["card2"], fg=P["text"], width=4, pady=8,
                         highlightthickness=1, highlightbackground=P["line"]).grid(row=frame_idx + 1, column=col, sticky="nsew")
        tk.Label(grid, text="Fault", bg=P["bg2"], fg=P["text"], width=10, pady=8,
                 highlightthickness=1, highlightbackground=P["line"], font=("Segoe UI Semibold", 9)).grid(row=frame_count + 1, column=0, sticky="nsew")
        for col, fault in enumerate(faults, start=1):
            tk.Label(grid, text="Yes" if fault else "No", bg=P["card2"], fg=P["red"] if fault else P["green"], width=4, pady=8,
                     highlightthickness=1, highlightbackground=P["line"]).grid(row=frame_count + 1, column=col, sticky="nsew")

    def build_resource_panel(self, parent):
        outer, panel = self.create_scrollable_panel(parent)
        panel.grid_columnconfigure(0, weight=3, minsize=320)
        panel.grid_columnconfigure(1, weight=7, minsize=620)
        left, body = self.card(panel, "Resource Manager")
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=4)

        client_wrap, client_body = self.memory_section(body, "Client Section")
        client_wrap.pack(fill="x", pady=(0, 10))
        self.field(client_body, "Client Name", self.client_name)
        self.btn(client_body, "Login", self.login_client, P["blue"], P["blue2"]).pack(fill="x", pady=(10, 0))
        tk.Label(client_body, text="Active Clients", bg=P["card2"], fg=P["muted"], font=("Segoe UI", 9)).pack(anchor="w", pady=(10, 6))
        self.client_list = tk.Frame(client_body, bg=P["card2"])
        self.client_list.pack(fill="x")

        action_wrap, action_body = self.memory_section(body, "Action Section")
        action_wrap.pack(fill="x", pady=(0, 10))
        self.field(action_body, "Select Resource", self.resource_id, [f"R{i}" for i in range(5)])
        self.btn(action_body, "Request Resource", self.request_resource, P["green"], P["green2"]).pack(fill="x", pady=(10, 6))
        self.btn(action_body, "Release Resource", self.release_resource, P["red"], P["red2"]).pack(fill="x", pady=6)
        self.btn(action_body, "Logout", self.logout_client, P["gold"], "#e0b55f").pack(fill="x", pady=(6, 0))

        table_wrap, table_body = self.memory_section(body, "Resource Status Table")
        table_wrap.pack(fill="both", expand=True, pady=(0, 10))
        self.resource_table = tk.Frame(table_body, bg=P["card2"])
        self.resource_table.pack(fill="both", expand=True)

        queue_wrap, queue_body = self.memory_section(body, "Waiting Queue")
        queue_wrap.pack(fill="x")
        self.queue_row = tk.Frame(queue_body, bg=P["card2"])
        self.queue_row.pack(fill="x")

        right, out = self.card(panel, "Execution Results")
        right.grid(row=0, column=1, sticky="nsew", padx=(10, 0), pady=4)
        tk.Label(out, textvariable=self.resource_info, bg=P["card"], fg=P["muted"], font=("Segoe UI", 10), wraplength=680, justify="left").pack(anchor="w", pady=(0, 12))
        self.resource_result_canvas = tk.Canvas(out, bg=P["card"], bd=0, highlightthickness=0)
        self.resource_result_scrollbar = tk.Scrollbar(out, orient="vertical", command=self.resource_result_canvas.yview)
        self.resource_result_content = tk.Frame(self.resource_result_canvas, bg=P["card"])
        self.resource_result_content.bind(
            "<Configure>",
            lambda event: self.resource_result_canvas.configure(scrollregion=self.resource_result_canvas.bbox("all")),
        )
        self.resource_result_window = self.resource_result_canvas.create_window((0, 0), window=self.resource_result_content, anchor="nw")
        self.resource_result_canvas.configure(yscrollcommand=self.resource_result_scrollbar.set)
        self.resource_result_canvas.pack(side="left", fill="both", expand=True)
        self.resource_result_scrollbar.pack(side="right", fill="y")
        self.resource_result_canvas.bind(
            "<Configure>",
            lambda event: self.resource_result_canvas.itemconfigure(self.resource_result_window, width=event.width),
        )

        status_row = tk.Frame(self.resource_result_content, bg=P["card"])
        status_row.pack(fill="x", pady=(0, 10))
        self.manager_status_card, self.manager_status_label, self.manager_status_value = self.stat(status_row, "Manager Running", "Yes", P["green"])
        self.manager_status_card.pack(side="left", fill="x", expand=True, padx=(0, 4))
        self.active_clients_card, self.active_clients_label, self.active_clients_value = self.stat(status_row, "Active Clients", "0", P["blue"])
        self.active_clients_card.pack(side="left", fill="x", expand=True, padx=4)
        self.total_resources_card, self.total_resources_label, self.total_resources_value = self.stat(status_row, "Total Resources", "5", P["gold"])
        self.total_resources_card.pack(side="left", fill="x", expand=True, padx=(4, 0))

        graph_wrap, graph_body = self.memory_section(self.resource_result_content, "System Graphs")
        graph_wrap.pack(fill="x", pady=(0, 10))
        graph_row = tk.Frame(graph_body, bg=P["card2"])
        graph_row.pack(fill="x")
        self.resource_usage_chart = tk.Canvas(graph_row, bg=P["card2"], height=190, bd=0, highlightthickness=0)
        self.resource_usage_chart.pack(side="left", fill="both", expand=True, padx=(0, 8))
        self.resource_queue_chart = tk.Canvas(graph_row, bg=P["card2"], height=190, bd=0, highlightthickness=0)
        self.resource_queue_chart.pack(side="left", fill="both", expand=True, padx=(8, 0))

        log_wrap, log_body = self.memory_section(self.resource_result_content, "Event Log")
        log_wrap.pack(fill="both", expand=True, pady=(0, 10))
        self.resource_log_frame = tk.Frame(log_body, bg=P["card2"])
        self.resource_log_frame.pack(fill="both", expand=True)
        self.resource_log_table = ttk.Treeview(
            self.resource_log_frame,
            columns=("time", "client", "pid", "resource", "action"),
            show="headings",
            style="Cpu.Treeview",
            height=8,
        )
        for key, title, width in [
            ("time", "Time", 180),
            ("client", "Client", 110),
            ("pid", "PID", 80),
            ("resource", "Resource", 90),
            ("action", "Action", 110),
        ]:
            self.resource_log_table.heading(key, text=title)
            self.resource_log_table.column(key, width=width, anchor="center", stretch=True)
        self.resource_log_scroll = tk.Scrollbar(self.resource_log_frame, orient="vertical", command=self.resource_log_table.yview)
        self.resource_log_table.configure(yscrollcommand=self.resource_log_scroll.set)
        self.resource_log_table.pack(side="left", fill="both", expand=True)
        self.resource_log_scroll.pack(side="right", fill="y")

        warning_wrap, warning_body = self.memory_section(self.resource_result_content, "Warning Panel")
        warning_wrap.pack(fill="x")
        self.resource_warning_box = tk.Frame(warning_body, bg="#24131c", highlightthickness=1, highlightbackground=P["red"])
        self.resource_warning_box.pack(fill="x")
        tk.Label(self.resource_warning_box, textvariable=self.resource_warning, bg="#24131c", fg="#ffb3bf", font=("Segoe UI Semibold", 10), justify="left", wraplength=640).pack(anchor="w", padx=12, pady=10)

        self.update_resource_views()
        return outer

    def selected_resource_index(self):
        rid = self.resource_id.get().strip().upper()
        if rid.startswith("R") and rid[1:].isdigit():
            idx = int(rid[1:])
            if 0 <= idx < len(self.resources):
                return idx
        raise ValueError("Select a valid resource from R0 to R4.")

    def get_client_record(self, name):
        return next((client for client in self.active_clients if client["name"] == name), None)

    def login_client(self):
        name = self.client_name.get().strip()
        if not name:
            messagebox.showerror("Resource Manager", "Enter a client name to login.")
            return
        existing = self.get_client_record(name)
        if existing:
            self.resource_info.set(f"{name} is already active with PID {existing['pid']}.")
            self.resource_warning.set("No conflicts detected.")
            self.update_resource_views()
            return
        self.resource_pid_seed += 17
        pid = self.resource_pid_seed
        self.active_clients.append({"name": name, "pid": pid})
        self.append_resource_event(name, pid, "-", "LOGIN")
        self.resource_info.set(f"{name} logged in with PID {pid}.")
        self.resource_warning.set("No conflicts detected.")
        self.client_name.set("")
        self.update_resource_views()
        self.status.set("Client login processed")

    def request_resource(self):
        client = self.client_name.get().strip()
        if not client:
            messagebox.showerror("Resource Manager", "Enter an active client name before requesting a resource.")
            return
        record = self.get_client_record(client)
        if record is None:
            messagebox.showerror("Resource Manager", "Client is not active. Login first.")
            return
        try:
            rid = self.selected_resource_index()
        except ValueError as exc:
            messagebox.showerror("Resource Manager", str(exc))
            return
        item = self.resources[rid]
        resource_label = f"R{rid}"
        if item["owner"] is None:
            item["owner"] = client
            item["owner_pid"] = record["pid"]
            self.resource_info.set(f"{client} acquired {resource_label}.")
            self.resource_warning.set("No conflicts detected.")
            self.append_resource_event(client, record["pid"], resource_label, "ALLOCATED")
        else:
            queue = self.waiting_by_resource[rid]
            if client in queue:
                self.resource_info.set(f"{client} is already waiting for {resource_label}.")
            elif len(queue) >= self.resource_queue_limit:
                self.resource_info.set(f"Waiting queue for {resource_label} is full.")
                self.resource_warning.set(
                    f"Queue limit reached for {resource_label}. Owner {item['owner']} should release the resource for waiting clients."
                )
                self.append_resource_event(client, record["pid"], resource_label, "QUEUE_FULL")
            else:
                queue.append(client)
                self.resource_info.set(f"{client} is waiting for {resource_label}.")
                self.resource_warning.set(
                    f"Conflict detected on {resource_label}. Owner {item['owner']} has been warned to release the resource."
                )
                self.append_resource_event(client, record["pid"], resource_label, "WAITING")
        self.update_resource_views()
        self.status.set("Resource request processed")

    def release_resource(self):
        client = self.client_name.get().strip()
        if not client:
            messagebox.showerror("Resource Manager", "Enter the active client name releasing the resource.")
            return
        record = self.get_client_record(client)
        if record is None:
            messagebox.showerror("Resource Manager", "Client is not active.")
            return
        try:
            rid = self.selected_resource_index()
        except ValueError as exc:
            messagebox.showerror("Resource Manager", str(exc))
            return
        item = self.resources[rid]
        resource_label = f"R{rid}"
        if item["owner"] != client:
            messagebox.showerror("Resource Manager", f"{client} does not own {resource_label}.")
            return
        queue = self.waiting_by_resource[rid]
        self.append_resource_event(client, record["pid"], resource_label, "RELEASED")
        if queue:
            nxt_name = queue.pop(0)
            nxt_record = self.get_client_record(nxt_name)
            item["owner"] = nxt_name
            item["owner_pid"] = nxt_record["pid"] if nxt_record else 0
            self.append_resource_event(nxt_name, item["owner_pid"], resource_label, "ALLOCATED")
            self.resource_info.set(f"{resource_label} released by {client} and reassigned to {nxt_name}.")
            self.resource_warning.set("No conflicts detected.")
        else:
            item["owner"] = None
            item["owner_pid"] = 0
            self.resource_info.set(f"{resource_label} released by {client}.")
            self.resource_warning.set("No conflicts detected.")
        self.update_resource_views()
        self.status.set("Resource release processed")

    def logout_client(self):
        client = self.client_name.get().strip()
        if not client:
            messagebox.showerror("Resource Manager", "Enter the active client name to logout.")
            return
        record = self.get_client_record(client)
        if record is None:
            messagebox.showerror("Resource Manager", "Client is not active.")
            return
        owned_resources = [f"R{resource['id']}" for resource in self.resources if resource["owner"] == client]
        if owned_resources:
            owned_text = ", ".join(owned_resources)
            self.resource_warning.set(
                f"{client} cannot logout while owning {owned_text}. Release all owned resources first."
            )
            messagebox.showerror("Resource Manager", "Client must release all owned resources before logout.")
            self.update_resource_views()
            return
        for rid, resource in enumerate(self.resources):
            self.waiting_by_resource[rid] = [name for name in self.waiting_by_resource[rid] if name != client]
        self.active_clients = [item for item in self.active_clients if item["name"] != client]
        self.append_resource_event(client, record["pid"], "-", "LOGOUT")
        self.resource_info.set(f"{client} logged out.")
        self.resource_warning.set("No conflicts detected.")
        self.client_name.set("")
        self.update_resource_views()
        self.status.set("Client logout processed")

    def append_resource_event(self, client, pid, resource, action):
        timestamp = time.strftime("%H:%M:%S")
        event = {"time": timestamp, "client": client, "pid": pid, "resource": resource, "action": action}
        self.resource_events.append(event)
        self.resource_events = self.resource_events[-60:]
        log_path = SHARED_DIR / "resource_log.txt"
        try:
            with log_path.open("a", encoding="utf-8") as fp:
                fp.write(f"{timestamp:<10} {client:<12} {pid:<8} {resource:<10} {action}\n")
        except OSError:
            pass

    def draw_resource_bar_chart(self, canvas, title, labels, values, color):
        canvas.delete("all")
        w = max(canvas.winfo_width(), 280)
        h = max(canvas.winfo_height(), 180)
        left, top, base = 34, 28, h - 28
        canvas.create_text(left, 12, text=title, fill=P["text"], anchor="w", font=("Segoe UI Semibold", 10))
        max_val = max(values) if values and max(values) > 0 else 1
        bar_space = max((w - left - 24) / max(len(labels), 1), 52)
        for idx, (label, value) in enumerate(zip(labels, values)):
            x1 = left + idx * bar_space + 12
            x2 = x1 + min(42, bar_space - 14)
            bar_height = (value / max_val) * (base - top - 8)
            canvas.create_rectangle(x1, base - bar_height, x2, base, fill=color, outline=color)
            canvas.create_text((x1 + x2) / 2, base + 14, text=label, fill=P["text"], font=("Segoe UI", 8))
            canvas.create_text((x1 + x2) / 2, base - bar_height - 10, text=str(value), fill=P["muted"], font=("Segoe UI", 8))
        canvas.create_line(left, top, left, base, fill=P["line"])
        canvas.create_line(left, base, w - 16, base, fill=P["line"])

    def update_resource_views(self):
        if not hasattr(self, "resource_table"):
            return
        for child in self.client_list.winfo_children():
            child.destroy()
        if not self.active_clients:
            tk.Label(self.client_list, text="No active clients", bg=P["card2"], fg=P["muted"], font=("Segoe UI", 10)).pack(anchor="w")
        for client in self.active_clients:
            chip = tk.Frame(self.client_list, bg=P["card"], highlightthickness=1, highlightbackground=P["line"])
            chip.pack(fill="x", pady=4)
            tk.Label(chip, text=client["name"], bg=P["card"], fg=P["text"], font=("Segoe UI Semibold", 10)).pack(side="left", padx=(10, 8), pady=8)
            tk.Label(chip, text=f"PID {client['pid']}", bg=P["card"], fg=P["blue2"], font=("Segoe UI", 9)).pack(side="left", pady=8)

        for child in self.resource_table.winfo_children():
            child.destroy()
        for c, h in enumerate(["Resource ID", "Status", "Owner"]):
            tk.Label(self.resource_table, text=h, bg=P["bg2"], fg=P["text"], width=12, pady=8,
                     highlightthickness=1, highlightbackground=P["line"], font=("Segoe UI Semibold", 10)).grid(row=0, column=c, sticky="nsew")
        for r, item in enumerate(self.resources, start=1):
            vals = [f"R{item['id']}", "FREE" if item["owner"] is None else "BUSY", item["owner"] or "-"]
            for c, v in enumerate(vals):
                fg = P["green"] if c == 1 and v == "FREE" else P["red"] if c == 1 else P["text"]
                tk.Label(self.resource_table, text=v, bg=P["card2"], fg=fg, width=12, pady=8,
                         highlightthickness=1, highlightbackground=P["line"]).grid(row=r, column=c, sticky="nsew")

        for child in self.queue_row.winfo_children():
            child.destroy()
        has_waiting = any(self.waiting_by_resource[rid] for rid in self.waiting_by_resource)
        if not has_waiting:
            tk.Label(self.queue_row, text="No waiting clients", bg=P["card2"], fg=P["muted"], font=("Segoe UI", 10)).pack(anchor="w")
        for rid in range(len(self.resources)):
            row = tk.Frame(self.queue_row, bg=P["card2"])
            row.pack(fill="x", pady=3)
            tk.Label(row, text=f"R{rid}", bg=P["card2"], fg=P["text"], width=6, anchor="w", font=("Segoe UI Semibold", 9)).pack(side="left")
            names = self.waiting_by_resource[rid]
            if not names:
                tk.Label(row, text="No queue", bg=P["card2"], fg=P["muted"], font=("Segoe UI", 9)).pack(side="left")
            else:
                chip_host = tk.Frame(row, bg=P["card2"])
                chip_host.pack(side="left", fill="x", expand=True)
                for idx, name in enumerate(names):
                    color = [P["red"], P["green"], P["blue"], P["gold"]][idx % 4]
                    chip = tk.Label(
                        chip_host,
                        text=name,
                        bg=color,
                        fg="white",
                        padx=10,
                        pady=4,
                        font=("Segoe UI Semibold", 9),
                        highlightthickness=1,
                        highlightbackground=P["line"],
                    )
                    chip.grid(row=idx // 3, column=idx % 3, padx=(0, 6), pady=3, sticky="w")

        self.manager_status_value.configure(text="Yes")
        self.active_clients_value.configure(text=str(len(self.active_clients)))
        self.total_resources_value.configure(text=str(len(self.resources)))

        usage_vals = [1 if resource["owner"] else 0 for resource in self.resources]
        queue_vals = [len(self.waiting_by_resource[rid]) for rid in range(len(self.resources))]
        self.draw_resource_bar_chart(self.resource_usage_chart, "Resource Usage Graph", [f"R{i}" for i in range(len(self.resources))], usage_vals, P["blue"])
        self.draw_resource_bar_chart(self.resource_queue_chart, "Waiting Queue Graph", [f"R{i}" for i in range(len(self.resources))], queue_vals, P["gold"])

        for item in self.resource_log_table.get_children():
            self.resource_log_table.delete(item)
        for event in self.resource_events[-30:]:
            self.resource_log_table.insert("", "end", values=(event["time"], event["client"], event["pid"], event["resource"], event["action"]))
        self.refresh_active()

    def build_tutor_panel(self, parent):
        outer = tk.Frame(parent, bg=P["bg2"])
        outer.grid_columnconfigure(0, weight=0, minsize=250)
        outer.grid_columnconfigure(1, weight=1, minsize=620)
        outer.grid_rowconfigure(0, weight=1)

        sidebar = tk.Frame(outer, bg="#0b1324", highlightthickness=1, highlightbackground=P["line2"])
        sidebar.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=4)
        main = tk.Frame(outer, bg=P["bg2"], highlightthickness=1, highlightbackground=P["line2"])
        main.grid(row=0, column=1, sticky="nsew", pady=4)
        main.grid_rowconfigure(1, weight=1)
        main.grid_columnconfigure(0, weight=1)

        tk.Label(sidebar, text="AI Tutor", bg="#0b1324", fg=P["text"], font=("Segoe UI Semibold", 15)).pack(anchor="w", padx=14, pady=(16, 10))
        self.btn(sidebar, "New Chat", self.new_tutor_chat, P["blue"], P["blue2"]).pack(fill="x", padx=14, pady=(0, 14))
        tk.Label(sidebar, text="History", bg="#0b1324", fg=P["muted"], font=("Segoe UI Semibold", 10)).pack(anchor="w", padx=14, pady=(4, 8))
        self.tutor_history_frame = tk.Frame(sidebar, bg="#0b1324")
        self.tutor_history_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        header = tk.Frame(main, bg=P["bg2"])
        header.grid(row=0, column=0, sticky="ew", padx=22, pady=(18, 8))
        tk.Label(header, text="Ask anything about Operating Systems", bg=P["bg2"], fg=P["text"], font=("Segoe UI Semibold", 18)).pack(anchor="center")
        tk.Label(header, text="CPU scheduling, memory management, paging, resources, debugging, and viva preparation", bg=P["bg2"], fg=P["muted"], font=("Segoe UI", 10)).pack(anchor="center", pady=(4, 0))

        chat_wrap = tk.Frame(main, bg=P["bg2"])
        chat_wrap.grid(row=1, column=0, sticky="nsew", padx=22, pady=8)
        self.tutor_output = tk.Text(
            chat_wrap,
            bg=P["bg2"],
            fg=P["text"],
            insertbackground=P["text"],
            relief="flat",
            bd=0,
            padx=18,
            pady=18,
            wrap="word",
            font=("Segoe UI", 11),
        )
        self.tutor_output.pack(side="left", fill="both", expand=True)
        tutor_scroll = ttk.Scrollbar(chat_wrap, orient="vertical", command=self.tutor_output.yview, style="Vertical.TScrollbar")
        self.tutor_output.configure(yscrollcommand=tutor_scroll.set)
        tutor_scroll.pack(side="right", fill="y")
        self.tutor_output.tag_configure("heading", foreground=P["blue2"], font=("Segoe UI Semibold", 12))
        self.tutor_output.tag_configure("muted", foreground=P["muted"])
        self.tutor_output.tag_configure("normal", foreground=P["text"], spacing3=4)
        self.tutor_output.tag_configure("user", foreground="white", background=P["card3"], lmargin1=18, lmargin2=18, rmargin=18, spacing1=8, spacing3=8)
        self.tutor_output.tag_configure("assistant", foreground=P["text"], background=P["card"], lmargin1=18, lmargin2=18, rmargin=18, spacing1=8, spacing3=12)
        self.tutor_output.configure(state="disabled")

        composer = tk.Frame(main, bg=P["bg2"])
        composer.grid(row=2, column=0, sticky="ew", padx=22, pady=(8, 20))
        composer.grid_columnconfigure(0, weight=1)
        self.tutor_entry = tk.Entry(
            composer,
            textvariable=self.tutor_question,
            bg=P["input"],
            fg=P["text"],
            insertbackground=P["text"],
            relief="flat",
            font=("Segoe UI", 11),
            highlightthickness=1,
            highlightbackground=P["line"],
            highlightcolor=P["blue2"],
        )
        self.tutor_entry.grid(row=0, column=0, sticky="ew", ipady=13, padx=(0, 8))
        self.tutor_entry.bind("<Return>", lambda event: self.ask_tutor())
        self.btn(composer, "Send", self.ask_tutor, P["blue"], P["blue2"]).grid(row=0, column=1, sticky="e")

        self.tutor_chats = []
        self.current_tutor_chat = []
        self.new_tutor_chat()
        return outer

    def use_tutor_prompt(self, prompt):
        self.tutor_question.set(prompt)
        self.ask_tutor()

    def ask_tutor(self):
        question = self.tutor_question.get().strip()
        if not question:
            return
        response = build_tutor_response(question, self.collect_tutor_context(), "Auto")
        self.current_tutor_chat.append(("You", question))
        self.current_tutor_chat.append(("Tutor", response))
        self.tutor_question.set("")
        self.render_tutor_chat()
        self.refresh_tutor_history()
        self.status.set("AI Study Tutor generated a contextual answer")

    def new_tutor_chat(self):
        if hasattr(self, "current_tutor_chat") and self.current_tutor_chat:
            title = self.current_tutor_chat[0][1][:32] or "New chat"
            self.tutor_chats.insert(0, {"title": title, "messages": list(self.current_tutor_chat)})
        self.current_tutor_chat = [("Tutor", "Hi, ask me any OS question. For example: what is starvation in priority scheduling?")]
        self.tutor_question.set("")
        self.render_tutor_chat()
        self.refresh_tutor_history()
        if hasattr(self, "tutor_entry"):
            self.tutor_entry.focus_set()

    def open_tutor_chat(self, index):
        if index < 0 or index >= len(self.tutor_chats):
            return
        self.current_tutor_chat = list(self.tutor_chats[index]["messages"])
        self.render_tutor_chat()

    def refresh_tutor_history(self):
        if not hasattr(self, "tutor_history_frame"):
            return
        for child in self.tutor_history_frame.winfo_children():
            child.destroy()
        if not self.tutor_chats:
            tk.Label(self.tutor_history_frame, text="No previous chats", bg="#0b1324", fg=P["muted"], font=("Segoe UI", 9)).pack(anchor="w", padx=4, pady=4)
            return
        for idx, chat in enumerate(self.tutor_chats[:8]):
            item = tk.Label(
                self.tutor_history_frame,
                text=chat["title"],
                bg=P["card"],
                fg=P["text"],
                anchor="w",
                cursor="hand2",
                padx=10,
                pady=9,
                font=("Segoe UI", 9),
            )
            item.pack(fill="x", pady=3)
            item.bind("<Button-1>", lambda event, i=idx: self.open_tutor_chat(i))

    def clear_tutor(self):
        self.current_tutor_chat = []
        self.render_tutor_chat()
        self.status.set("AI Study Tutor cleared")

    def tutor_insert(self, text):
        if not hasattr(self, "tutor_output"):
            return
        self.tutor_output.configure(state="normal")
        self.tutor_output.delete("1.0", tk.END)
        for line in text.splitlines():
            tag = "heading" if line and not line.startswith(("-", "1.", "2.", "3.", "4.", "5.", "6.", "7.")) and len(line) < 70 and line.endswith(":") is False else "normal"
            if line.startswith("Context:"):
                tag = "muted"
            self.tutor_output.insert(tk.END, line + "\n", tag)
        self.tutor_output.configure(state="disabled")
        self.tutor_output.see("1.0")

    def render_tutor_chat(self):
        if not hasattr(self, "tutor_output"):
            return
        self.tutor_output.configure(state="normal")
        self.tutor_output.delete("1.0", tk.END)
        for sender, message in self.current_tutor_chat:
            tag = "user" if sender == "You" else "assistant"
            self.tutor_output.insert(tk.END, f"{sender}\n", "heading" if sender == "Tutor" else "muted")
            self.tutor_output.insert(tk.END, message.strip() + "\n\n", tag)
        self.tutor_output.configure(state="disabled")
        self.tutor_output.see(tk.END)

    def refresh_tutor_context(self):
        return

    def collect_tutor_context(self):
        resource_waiting = sum(len(queue) for queue in self.waiting_by_resource.values())
        return {
            "cpu": self.cpu_result,
            "memory": self.mem_result,
            "resource": {
                "busy": sum(1 for item in self.resources if item["owner"]),
                "waiting": resource_waiting,
                "total": len(self.resources),
                "events": len(self.resource_events),
            },
        }

    def build_system_panel(self, parent):
        outer, panel = self.create_scrollable_panel(parent)
        panel.grid_columnconfigure(0, weight=1)
        panel.grid_columnconfigure(1, weight=1)
        panel.grid_rowconfigure(0, weight=1)
        panel.grid_rowconfigure(1, weight=1)
        cpu, cbody = self.card(panel, "CPU Usage")
        cpu.grid(row=0, column=0, columnspan=2, sticky="nsew", pady=(4, 10))
        tk.Label(cbody, text="Simulation load from CPU scheduling output and resource queue pressure", bg=P["card"], fg=P["muted"], font=("Segoe UI", 9)).pack(anchor="w", pady=(0, 6))
        self.cpu_chart = tk.Canvas(cbody, bg=P["card"], height=220, bd=0, highlightthickness=0)
        self.cpu_chart.pack(fill="both", expand=True)
        mem, mbody = self.card(panel, "Memory Usage")
        mem.grid(row=1, column=0, sticky="nsew", padx=(0, 10), pady=4)
        tk.Label(mbody, text="Simulation load from memory utilization, fragmentation, and page faults", bg=P["card"], fg=P["muted"], font=("Segoe UI", 9)).pack(anchor="w", pady=(0, 6))
        self.mem_chart = tk.Canvas(mbody, bg=P["card"], height=180, bd=0, highlightthickness=0)
        self.mem_chart.pack(fill="both", expand=True)
        proc, pbody = self.card(panel, "Active Processes")
        proc.grid(row=1, column=1, sticky="nsew", padx=(10, 0), pady=4)
        self.active_box = tk.Frame(pbody, bg=P["card"])
        self.active_box.pack(fill="both", expand=True)
        return outer

    def refresh_active(self):
        if not hasattr(self, "active_box"): return
        for child in self.active_box.winfo_children(): child.destroy()
        waiting_names = []
        for queue in self.waiting_by_resource.values():
            waiting_names.extend(queue)
        names = [r["owner"] for r in self.resources if r["owner"]] + waiting_names
        if self.cpu_result:
            names += [s["pid"] for s in self.cpu_result["segs"] if s["pid"] != "IDLE"]
        seen = []
        for name in names:
            if name and name not in seen: seen.append(name)
        if not seen: seen = ["P1", "P2"]
        colors = [P["blue"], P["green"], P["red"], P["gold"]]
        for i, name in enumerate(seen[:6]):
            card = tk.Frame(self.active_box, bg=P["card2"], highlightthickness=1, highlightbackground=P["line"])
            card.pack(fill="x", pady=6)
            tk.Label(card, text=name, bg=P["card2"], fg=colors[i % len(colors)], font=("Segoe UI Semibold", 12)).pack(anchor="w", padx=14, pady=(10, 2))
            tk.Label(card, text="Active in current simulator state", bg=P["card2"], fg=P["muted"], font=("Segoe UI", 9)).pack(anchor="w", padx=14, pady=(0, 10))

    def draw_chart(self, canvas, series, labels):
        canvas.delete("all")
        w, h = max(canvas.winfo_width(), 480), max(canvas.winfo_height(), 180)
        left, top, right, bottom = 44, 18, w - 20, h - 24
        for text, ratio in labels:
            y = top + (1 - ratio) * (bottom - top)
            canvas.create_line(left, y, right, y, fill=P["line"])
            canvas.create_text(18, y, text=text, fill=P["muted"], font=("Segoe UI", 8))
        for i in range(10):
            x = left + i * ((right - left) / 9)
            canvas.create_line(x, top, x, bottom, fill=P["line"])
        for points, color in series:
            mx, coords = max(max(points), 1), []
            for i, v in enumerate(points):
                x = left + i * ((right - left) / (len(points) - 1))
                y = bottom - (v / mx) * (bottom - top)
                coords += [x, y]
            canvas.create_line(coords, fill=color, width=2, smooth=True)

    def update_monitor(self):
        try:
            metrics = self.read_project_monitor_metrics()
        except Exception:
            metrics = {"cpu1": 0, "cpu2": 0, "mem1": 0, "mem2": 0}
        for key, value in metrics.items():
            vals = self.monitor[key]
            self.monitor[key] = vals[1:] + [max(0, min(100, value))]
        if hasattr(self, "cpu_chart"):
            self.draw_chart(self.cpu_chart, [(self.monitor["cpu1"], "#f0c15a"), (self.monitor["cpu2"], "#79d5b1")], [("100", 1.0), ("75", 0.75), ("50", 0.5), ("25", 0.25)])
            self.draw_chart(self.mem_chart, [(self.monitor["mem1"], "#d56666"), (self.monitor["mem2"], "#a5db9c")], [("100", 1.0), ("75", 0.75), ("50", 0.5), ("25", 0.25)])
        self.refresh_active()
        self.root.after(1200, self.update_monitor)

    def read_project_monitor_metrics(self):
        cpu_load = 0.0
        cpu_wait_pressure = 0.0
        if self.cpu_result:
            segments = self.cpu_result.get("segs", [])
            total_time = sum(max(0, seg.get("end", 0) - seg.get("start", 0)) for seg in segments)
            busy_time = sum(max(0, seg.get("end", 0) - seg.get("start", 0)) for seg in segments if seg.get("pid") != "IDLE")
            cpu_load = (busy_time / total_time) * 100 if total_time else 0.0
            avg_wt = float(self.cpu_result.get("avg_wt", 0) or 0)
            avg_tat = max(float(self.cpu_result.get("avg_tat", 1) or 1), 1)
            cpu_wait_pressure = min(100, (avg_wt / avg_tat) * 100)
        else:
            process_count = int(self.cpu_count.get()) if self.cpu_count.get().isdigit() else 0
            cpu_load = min(100, process_count * 9)

        busy_resources = sum(1 for item in self.resources if item["owner"])
        waiting_clients = sum(len(queue) for queue in self.waiting_by_resource.values())
        resource_pressure = min(100, (busy_resources / max(len(self.resources), 1)) * 70 + waiting_clients * 10)

        memory_load = 0.0
        memory_pressure = 0.0
        if self.mem_result:
            if self.mem_result.get("mode") == "contiguous":
                selected = self.mem_result.get("selected") or self.mem_result.get("best")
                data = self.mem_result.get("algorithms", {}).get(selected, {})
                memory_load = float(data.get("utilization", 0.0) or 0.0)
                total_block_size = sum(block.get("size_bytes", 0) for block in self.mem_result.get("blocks", [])) or 1
                frag = (data.get("internal_fragmentation", 0) or 0) + (data.get("external_fragmentation", 0) or 0)
                memory_pressure = min(100, (frag / total_block_size) * 100 + (data.get("failed", 0) or 0) * 12)
            elif self.mem_result.get("mode") == "paging":
                refs = max(len(self.mem_result.get("refs", [])), 1)
                better = self.mem_result.get("better")
                data = self.mem_result.get("algorithms", {}).get(better, {})
                faults = data.get("fault_count", 0) or 0
                frames = self.mem_result.get("frames", 0) or 0
                page_count = max(self.mem_result.get("page_count", 1) or 1, 1)
                memory_load = min(100, (frames / page_count) * 100)
                memory_pressure = min(100, (faults / refs) * 100)
        else:
            blocks = int(self.mem_block_count.get()) if self.mem_block_count.get().isdigit() else 0
            processes = int(self.mem_process_count.get()) if self.mem_process_count.get().isdigit() else 0
            memory_load = min(100, (processes / max(blocks, 1)) * 55)

        return {
            "cpu1": max(cpu_load, resource_pressure),
            "cpu2": cpu_wait_pressure,
            "mem1": memory_load,
            "mem2": memory_pressure,
        }

    def fcfs(self, procs):
        procs = sorted(procs, key=lambda p: (p["at"], p["pid"]))
        t, segs, rows = 0, [], []
        for p in procs:
            if t < p["at"]: segs.append({"pid": "IDLE", "start": t, "end": p["at"]}); t = p["at"]
            start, end = t, t + p["bt"]
            segs.append({"pid": p["pid"], "start": start, "end": end})
            rows.append({**p, "ct": end, "tat": end - p["at"], "wt": end - p["at"] - p["bt"]})
            t = end
        return segs, rows

    def sjf(self, procs):
        pool, t, segs, done = [dict(p) for p in procs], 0, [], []
        while pool:
            ready = [p for p in pool if p["at"] <= t]
            if not ready:
                nt = min(p["at"] for p in pool)
                segs.append({"pid": "IDLE", "start": t, "end": nt})
                t = nt
                continue
            cur = min(ready, key=lambda p: (p["bt"], p["at"], p["pid"]))
            pool.remove(cur)
            end = t + cur["bt"]
            segs.append({"pid": cur["pid"], "start": t, "end": end})
            done.append({**cur, "ct": end, "tat": end - cur["at"], "wt": end - cur["at"] - cur["bt"]})
            t = end
        return segs, sorted(done, key=lambda p: p["pid"])

    def srtf(self, procs):
        jobs = [dict(p, rem=p["bt"]) for p in procs]
        t, segs, done = 0, [], {}
        while len(done) < len(jobs):
            ready = [p for p in jobs if p["at"] <= t and p["pid"] not in done and p["rem"] > 0]
            if not ready:
                next_time = min(p["at"] for p in jobs if p["pid"] not in done and p["rem"] > 0)
                segs.append({"pid": "IDLE", "start": t, "end": next_time})
                t = next_time
                continue
            cur = min(ready, key=lambda p: (p["rem"], p["at"], p["pid"]))
            start = t
            step = min(1, cur["rem"])
            t += step
            cur["rem"] -= step
            segs.append({"pid": cur["pid"], "start": start, "end": t})
            if cur["rem"] <= 0:
                done[cur["pid"]] = {**cur, "ct": t, "tat": t - cur["at"], "wt": t - cur["at"] - cur["bt"]}
        return self.merge_segments(segs), [done[p["pid"]] for p in sorted(jobs, key=lambda p: p["pid"])]

    def priority_preemptive(self, procs):
        jobs = [dict(p, rem=p["bt"]) for p in procs]
        t, segs, done = 0, [], {}
        while len(done) < len(jobs):
            ready = [p for p in jobs if p["at"] <= t and p["pid"] not in done and p["rem"] > 0]
            if not ready:
                next_time = min(p["at"] for p in jobs if p["pid"] not in done and p["rem"] > 0)
                segs.append({"pid": "IDLE", "start": t, "end": next_time})
                t = next_time
                continue
            cur = min(ready, key=lambda p: (p["pr"], p["at"], p["pid"]))
            start = t
            step = min(1, cur["rem"])
            t += step
            cur["rem"] -= step
            segs.append({"pid": cur["pid"], "start": start, "end": t})
            if cur["rem"] <= 0:
                done[cur["pid"]] = {**cur, "ct": t, "tat": t - cur["at"], "wt": t - cur["at"] - cur["bt"]}
        return self.merge_segments(segs), [done[p["pid"]] for p in sorted(jobs, key=lambda p: p["pid"])]

    def priority_non_preemptive(self, procs):
        pool, t, segs, done = [dict(p) for p in procs], 0, [], []
        while pool:
            ready = [p for p in pool if p["at"] <= t]
            if not ready:
                nt = min(p["at"] for p in pool)
                segs.append({"pid": "IDLE", "start": t, "end": nt})
                t = nt
                continue
            cur = min(ready, key=lambda p: (p["pr"], p["at"], p["pid"]))
            pool.remove(cur)
            end = t + cur["bt"]
            segs.append({"pid": cur["pid"], "start": t, "end": end})
            done.append({**cur, "ct": end, "tat": end - cur["at"], "wt": end - cur["at"] - cur["bt"]})
            t = end
        return segs, sorted(done, key=lambda p: p["pid"])

    def rr(self, procs, q):
        jobs = sorted([dict(p, rem=p["bt"]) for p in procs], key=lambda p: (p["at"], p["pid"]))
        i, t, segs, ready, done = 0, 0, [], [], {}
        while len(done) < len(jobs):
            while i < len(jobs) and jobs[i]["at"] <= t: ready.append(jobs[i]); i += 1
            if not ready:
                nt = jobs[i]["at"]
                segs.append({"pid": "IDLE", "start": t, "end": nt})
                t = nt
                continue
            cur = ready.pop(0)
            run = min(q, cur["rem"])
            segs.append({"pid": cur["pid"], "start": t, "end": t + run})
            t += run
            cur["rem"] -= run
            while i < len(jobs) and jobs[i]["at"] <= t: ready.append(jobs[i]); i += 1
            if cur["rem"] > 0: ready.append(cur)
            else: done[cur["pid"]] = {**cur, "ct": t, "tat": t - cur["at"], "wt": t - cur["at"] - cur["bt"]}
        return self.merge_segments(segs), [done[p["pid"]] for p in sorted(jobs, key=lambda p: p["pid"])]

    def merge_segments(self, segs):
        if not segs:
            return []
        merged = [segs[0].copy()]
        for seg in segs[1:]:
            last = merged[-1]
            if last["pid"] == seg["pid"] and abs(last["end"] - seg["start"]) < 1e-9:
                last["end"] = seg["end"]
            else:
                merged.append(seg.copy())
        return merged

root = tk.Tk()
try:
    App(root)
    root.mainloop()
except Exception:
    (BASE_DIR / "crash_log.txt").write_text(traceback.format_exc(), encoding="utf-8")
    raise
