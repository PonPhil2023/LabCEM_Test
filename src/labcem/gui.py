import queue
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, ttk

import numpy as np
from matplotlib import rcParams
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from skimage.measure import marching_cubes

from labcem.agents.agent_pipeline import DomainAgentPipeline
from labcem.core.plugin.backend_registry import BackendRegistry
from labcem.core.plugin.kernel_manager import KernelManager
from labcem.orchestrator import LabCEMOrchestrator


rcParams["font.sans-serif"] = ["Microsoft JhengHei", "Segoe UI", "Arial Unicode MS", "DejaVu Sans"]
rcParams["axes.unicode_minus"] = False


class LabCEMGui(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("LabCEM LEAP71 SDF Workbench")
        self.geometry("1440x900")
        self.configure(bg="#eef3f8")

        self.result_queue = queue.Queue()
        self.current_grid = None
        self.current_mesh_verts = None
        self.current_mesh_faces = None
        self.current_spacing = 1.0
        self.current_origin = (0.0, 0.0, 0.0)
        self.live_update_job = None
        self.is_running = False
        self.pending_live = False
        self._pan_active = False
        self._pan_last = None
        self.knowledge_sources = []
        self.last_source_id = None

        self.kernel_manager = KernelManager()
        self.backend_registry = BackendRegistry()
        self.agent_pipeline = DomainAgentPipeline()

        self._init_styles()
        self._init_vars()
        self._build_ui()

        self.after(200, self._poll_result_queue)

    def _init_styles(self):
        style = ttk.Style()
        style.theme_use("clam")

        style.configure("TFrame", background="#eef3f8")
        style.configure("TLabelframe", background="#eef3f8", borderwidth=1, relief="solid")
        style.configure("TLabelframe.Label", font=("Microsoft JhengHei", 10, "bold"), background="#eef3f8")
        style.configure("Ribbon.TButton", padding=6, font=("Microsoft JhengHei", 10))
        style.configure("Action.TButton", padding=10, font=("Microsoft JhengHei", 10, "bold"), background="#0b57d0", foreground="#ffffff")
        style.map("Action.TButton", background=[("active", "#0046ad")])
        style.configure("Import.TButton", padding=6, background="#0e9f6e", foreground="#ffffff")
        style.map("Import.TButton", background=[("active", "#0b7f58")])
        style.configure("Extract.TButton", padding=6, background="#f59e0b", foreground="#1f2937")
        style.map("Extract.TButton", background=[("active", "#d97706")])
        style.configure("Schema.TButton", padding=6, background="#7c3aed", foreground="#ffffff")
        style.map("Schema.TButton", background=[("active", "#6d28d9")])
        style.configure("Review.TButton", padding=6, background="#ef4444", foreground="#ffffff")
        style.map("Review.TButton", background=[("active", "#dc2626")])
        style.configure("Status.TLabel", font=("Microsoft JhengHei", 9), background="#eef3f8")
        style.configure("Guide.TLabel", font=("Microsoft JhengHei", 9), background="#ecfdf5", foreground="#065f46")

    def _init_vars(self):
        kernels = self.kernel_manager.list_kernels() or ["acoustic_kernel"]
        backends = self.backend_registry.list_backends()

        self.domain_var = tk.StringVar(value="general")
        self.output_var = tk.StringVar(value="outputs/generated_geometry.json")
        self.resolution_var = tk.IntVar(value=24)
        self.lattice_var = tk.BooleanVar(value=False)
        self.attachment_var = tk.StringVar(value="")
        self.prompt_var = tk.StringVar(value="Generate torus SDF mesh with resolution variation")
        self.cli_health_var = tk.StringVar(value="CLI: Unknown")

        self.selected_kernel_var = tk.StringVar(value="acoustic_kernel" if "acoustic_kernel" in kernels else kernels[0])
        self.selected_backend_var = tk.StringVar(value="python_sdf" if "python_sdf" in backends else backends[0])
        self.selected_component_var = tk.StringVar(value="waveguide")
        self.selected_agent_mode_var = tk.StringVar(value="hybrid")
        self.source_id_var = tk.StringVar(value="source_id: (none)")
        self.llm_status_var = tk.StringVar(value="LLM: checking...")
        self.workflow_hint_var = tk.StringVar(value="流程指引：先選 Kernel/Component/Backend，再新增來源並按「匯入知識來源」。")

        self.status_vars = {
            "STEP1": tk.StringVar(value="待命 (Idle)"),
            "STEP2": tk.StringVar(value="待命 (Idle)"),
            "STEP3": tk.StringVar(value="待命 (Idle)"),
            "AI": tk.StringVar(value="就緒 (Ready)"),
        }
        self.cem_flow_defs = [
            ("L0", "Design Intent", "prompt/spec parser"),
            ("L1", "Knowledge Import", "pdf/docx/md/json/repo"),
            ("L2", "Knowledge Extract", "cards/formulas/rules"),
            ("L3", "Schema/Proposal", "schema + generated builder"),
            ("L4", "Review/Export", "review report + model export"),
        ]
        self.cem_flow_vars = {k: tk.StringVar(value="待命") for k, _n, _p in self.cem_flow_defs}
        self.cem_current_layer_var = tk.StringVar(value="Current: Idle")

    def _build_ui(self):
        ribbon = ttk.Frame(self, relief="flat", padding=(10, 5))
        ribbon.pack(side=tk.TOP, fill=tk.X, pady=(0, 1))

        prompt_frame = ttk.Frame(ribbon)
        prompt_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        ttk.Label(prompt_frame, text="求解提示詞 (Prompt):", font=("Microsoft JhengHei", 9, "bold")).pack(side=tk.LEFT, padx=5)
        prompt_entry = ttk.Entry(prompt_frame, textvariable=self.prompt_var, font=("Segoe UI", 11))
        prompt_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        prompt_entry.bind("<Return>", lambda _e: self.run_generation(live=False))

        ttk.Button(ribbon, text="▶ 執行計算 (Compute)", command=lambda: self.run_generation(live=False), style="Action.TButton").pack(side=tk.LEFT, padx=10)
        self.cli_health_label = ttk.Label(ribbon, textvariable=self.cli_health_var, font=("Segoe UI", 9, "bold"))
        self.cli_health_label.pack(side=tk.RIGHT, padx=10)

        ttk.Separator(self, orient=tk.HORIZONTAL).pack(fill=tk.X)

        main_pane = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        main_pane.pack(fill=tk.BOTH, expand=True)

        left_container = ttk.Frame(main_pane, width=390)
        main_pane.add(left_container, weight=1)

        self.left_canvas = tk.Canvas(left_container, bg="#eef3f8", highlightthickness=0)
        self.left_scrollbar = ttk.Scrollbar(left_container, orient=tk.VERTICAL, command=self.left_canvas.yview)
        self.left_canvas.configure(yscrollcommand=self.left_scrollbar.set)

        self.left_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.left_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        left_sidebar = ttk.Frame(self.left_canvas, padding=10, width=390)
        self.left_canvas_window = self.left_canvas.create_window((0, 0), window=left_sidebar, anchor="nw")

        left_sidebar.bind("<Configure>", lambda _e: self.left_canvas.configure(scrollregion=self.left_canvas.bbox("all")))
        self.left_canvas.bind("<Configure>", lambda e: self.left_canvas.itemconfigure(self.left_canvas_window, width=e.width))
        self.left_canvas.bind("<Enter>", self._bind_left_scroll)
        self.left_canvas.bind("<Leave>", self._unbind_left_scroll)

        guide_group = ttk.LabelFrame(left_sidebar, text=" 操作流程指引 ", padding=8)
        guide_group.pack(fill=tk.X, pady=(0, 8))
        ttk.Label(guide_group, text="1) 選 Kernel/Component/Backend  2) 新增來源  3) 匯入→擷取→Schema→草案→審核", style="Guide.TLabel", wraplength=340).pack(fill=tk.X, pady=(0, 4))
        ttk.Label(guide_group, textvariable=self.workflow_hint_var, style="Guide.TLabel", wraplength=340).pack(fill=tk.X)

        settings_group = ttk.LabelFrame(left_sidebar, text=" 設定 (Settings) ", padding=10)
        settings_group.pack(fill=tk.BOTH, expand=True)

        self._labeled_entry(settings_group, "領域 (Domain)", self.domain_var)
        self._labeled_entry(settings_group, "輸出路徑 (Output)", self.output_var)

        attach_label = ttk.Label(settings_group, text="知識檔 (Knowledge Attachment)", font=("Microsoft JhengHei", 9))
        attach_label.pack(anchor="w", pady=(10, 0))
        attach_row = ttk.Frame(settings_group)
        attach_row.pack(fill=tk.X, pady=2)
        ttk.Entry(attach_row, textvariable=self.attachment_var).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(attach_row, text="...", width=3, command=self._browse_attachment).pack(side=tk.LEFT, padx=(5, 0))

        res_label = ttk.Label(settings_group, text="體素解析度 (Voxel Resolution)", font=("Microsoft JhengHei", 9))
        res_label.pack(anchor="w", pady=(10, 0))
        res_row = ttk.Frame(settings_group)
        res_row.pack(fill=tk.X, pady=5)
        scale = ttk.Scale(res_row, from_=12, to=96, variable=self.resolution_var, orient=tk.HORIZONTAL, command=self._on_resolution_change)
        scale.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Label(res_row, textvariable=self.resolution_var, width=3).pack(side=tk.LEFT, padx=(5, 0))

        ttk.Checkbutton(settings_group, text="套用晶格 (Apply Lattice)", variable=self.lattice_var, command=self._schedule_live_update).pack(anchor="w", pady=10)

        agent_group = ttk.LabelFrame(left_sidebar, text=" Domain Kernel / Knowledge Import ", padding=8)
        agent_group.pack(fill=tk.BOTH, expand=True, pady=(10, 0))

        ttk.Label(agent_group, text="Domain Kernel").pack(anchor="w")
        self.kernel_combo = ttk.Combobox(agent_group, textvariable=self.selected_kernel_var, state="readonly", values=self.kernel_manager.list_kernels())
        self.kernel_combo.pack(fill=tk.X, pady=2)
        self.kernel_combo.bind("<<ComboboxSelected>>", lambda _e: self._refresh_components())

        ttk.Label(agent_group, text="Component").pack(anchor="w", pady=(4, 0))
        self.component_combo = ttk.Combobox(agent_group, textvariable=self.selected_component_var, state="readonly")
        self.component_combo.pack(fill=tk.X, pady=2)

        ttk.Label(agent_group, text="Backend").pack(anchor="w", pady=(4, 0))
        self.backend_combo = ttk.Combobox(agent_group, textvariable=self.selected_backend_var, state="readonly", values=["python_sdf", "mesh_sdf", "picogk", "openvdb"])
        self.backend_combo.pack(fill=tk.X, pady=2)

        ttk.Label(agent_group, text="Agent Mode").pack(anchor="w", pady=(4, 0))
        self.agent_mode_combo = ttk.Combobox(agent_group, textvariable=self.selected_agent_mode_var, state="readonly", values=["rules", "llm", "hybrid"])
        self.agent_mode_combo.pack(fill=tk.X, pady=2)

        llm_row = ttk.Frame(agent_group)
        llm_row.pack(fill=tk.X, pady=(4, 2))
        ttk.Label(llm_row, textvariable=self.llm_status_var, font=("Consolas", 8)).pack(side=tk.LEFT)
        ttk.Button(llm_row, text="檢查 LLM 狀態", command=self._refresh_llm_status).pack(side=tk.RIGHT)

        src_btn_row = ttk.Frame(agent_group)
        src_btn_row.pack(fill=tk.X, pady=(6, 2))
        ttk.Button(src_btn_row, text="新增檔案", command=self._add_files).pack(side=tk.LEFT)
        ttk.Button(src_btn_row, text="新增資料夾/GitHub Repo", command=self._add_folder).pack(side=tk.LEFT, padx=4)
        ttk.Button(src_btn_row, text="清空來源", command=self._clear_sources).pack(side=tk.RIGHT)

        self.source_listbox = tk.Listbox(agent_group, height=6, bg="#f8fbff", highlightbackground="#cbd5e1")
        self.source_listbox.pack(fill=tk.BOTH, expand=True, pady=3)

        action_row1 = ttk.Frame(agent_group)
        action_row1.pack(fill=tk.X, pady=(4, 2))
        ttk.Button(action_row1, text="匯入知識來源", command=self._ingest_sources, style="Import.TButton").pack(side=tk.LEFT)
        ttk.Button(action_row1, text="擷取知識卡", command=self._extract_cards, style="Extract.TButton").pack(side=tk.LEFT, padx=4)

        action_row2 = ttk.Frame(agent_group)
        action_row2.pack(fill=tk.X, pady=(2, 2))
        ttk.Button(action_row2, text="生成 Schema", command=self._generate_schema, style="Schema.TButton").pack(side=tk.LEFT)
        ttk.Button(action_row2, text="生成程式草案", command=self._propose_code, style="Schema.TButton").pack(side=tk.LEFT, padx=4)
        ttk.Button(action_row2, text="審核草案", command=self._review_proposal, style="Review.TButton").pack(side=tk.LEFT)

        ttk.Label(agent_group, textvariable=self.source_id_var, font=("Consolas", 8)).pack(anchor="w", pady=(4, 0))

        status_group = ttk.LabelFrame(left_sidebar, text=" 求解狀態 (Solver Status) ", padding=8)
        status_group.pack(fill=tk.X, side=tk.BOTTOM, pady=(10, 0))

        for key in ["STEP1", "STEP2", "STEP3", "AI"]:
            row = ttk.Frame(status_group)
            row.pack(fill=tk.X, pady=1)
            ttk.Label(row, text=f"{key}:", width=8, font=("Segoe UI", 8, "bold")).pack(side=tk.LEFT)
            ttk.Label(row, textvariable=self.status_vars[key], style="Status.TLabel").pack(side=tk.LEFT)

        flow_group = ttk.LabelFrame(left_sidebar, text=" CEM 思考流程 (Thinking Flow) ", padding=8)
        flow_group.pack(fill=tk.X, side=tk.BOTTOM, pady=(10, 0))
        ttk.Label(flow_group, textvariable=self.cem_current_layer_var, font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(0, 6))
        for key, name, pkg in self.cem_flow_defs:
            row = ttk.Frame(flow_group)
            row.pack(fill=tk.X, pady=1)
            ttk.Label(row, text=key, width=5, font=("Consolas", 8, "bold")).pack(side=tk.LEFT)
            ttk.Label(row, text=name, width=17, font=("Segoe UI", 8)).pack(side=tk.LEFT)
            ttk.Label(row, text=pkg, width=24, font=("Consolas", 7), foreground="#555555").pack(side=tk.LEFT)
            ttk.Label(row, textvariable=self.cem_flow_vars[key], width=8, font=("Segoe UI", 8, "bold")).pack(side=tk.RIGHT)

        right_content = ttk.PanedWindow(main_pane, orient=tk.VERTICAL)
        main_pane.add(right_content, weight=4)

        graphics_frame = tk.Frame(right_content, bg="white")
        right_content.add(graphics_frame, weight=3)
        self._build_graphics(graphics_frame)

        info_notebook = ttk.Notebook(right_content)
        right_content.add(info_notebook, weight=1)

        self.layer_log = tk.Text(info_notebook, height=8, wrap=tk.WORD, font=("Consolas", 9), bg="#ffffff", borderwidth=0)
        info_notebook.add(self.layer_log, text=" 訊息記錄 (Messages) ")

        self.chat_log = tk.Text(info_notebook, height=8, wrap=tk.WORD, font=("Microsoft JhengHei", 10), bg="#ffffff", borderwidth=0)
        info_notebook.add(self.chat_log, text=" AI 助手 (Label9 Summary) ")
        self.raw_cli_log = tk.Text(info_notebook, height=8, wrap=tk.WORD, font=("Consolas", 9), bg="#ffffff", borderwidth=0)
        info_notebook.add(self.raw_cli_log, text=" CLI 原始回覆 (Raw) ")

        self._refresh_components()
        self._refresh_llm_status()
        self._append_layer_log("系統就緒，等待輸入...")
        self._append_chat("LEAP71 SDF 流程已就緒。")
        self._set_cli_health(None)

    def _set_workflow_hint(self, text):
        self.workflow_hint_var.set(f"流程指引：{text}")

    def _get_agent_mode(self):
        return (self.selected_agent_mode_var.get() or "hybrid").strip().lower()

    def _refresh_llm_status(self):
        st = self.agent_pipeline.llm_status()
        enabled = st.get("enabled", False)
        provider = st.get("provider", "-")
        model = st.get("model", "-")
        key = "Found" if st.get("api_key_found") else "Missing"
        status_text = "Enabled" if enabled else "Disabled"
        self.llm_status_var.set(f"LLM {status_text} | {provider}/{model} | API Key: {key}")
        if not enabled:
            self._append_layer_log("LLM 未啟用，將使用規則式 Agent")

    def _refresh_components(self):
        kernel_id = self.selected_kernel_var.get().strip() or "acoustic_kernel"
        try:
            kernel = self.kernel_manager.get_active_kernel(kernel_id)
            components = kernel.list_components()
        except Exception:
            components = ["waveguide"]
        self.component_combo.configure(values=components)
        if self.selected_component_var.get() not in components:
            self.selected_component_var.set(components[0] if components else "waveguide")
        self._set_workflow_hint("已選擇 Kernel，請確認 Component 與 Backend，接著新增知識來源。")

    def _add_files(self):
        paths = filedialog.askopenfilenames(filetypes=[("Knowledge files", "*.pdf *.docx *.md *.txt *.json"), ("All files", "*.*")])
        for p in paths:
            if p not in self.knowledge_sources:
                self.knowledge_sources.append(p)
                self.source_listbox.insert(tk.END, p)
        if paths:
            self._set_workflow_hint("已加入檔案來源，下一步按「匯入知識來源」。")

    def _add_folder(self):
        p = filedialog.askdirectory()
        if p and p not in self.knowledge_sources:
            self.knowledge_sources.append(p)
            self.source_listbox.insert(tk.END, p)
            self._set_workflow_hint("已加入資料夾/Repo，下一步按「匯入知識來源」。")

    def _clear_sources(self):
        self.knowledge_sources = []
        self.source_listbox.delete(0, tk.END)
        self.last_source_id = None
        self.source_id_var.set("source_id: (none)")
        self._set_workflow_hint("來源已清空，請重新新增知識來源。")

    def _ingest_sources(self):
        kernel = self.selected_kernel_var.get().strip()
        if not self.knowledge_sources:
            self._append_layer_log("請先新增知識來源")
            return
        self._set_workflow_hint("正在匯入知識來源...完成後請按「擷取知識卡」。")
        self._set_cem_flow_running("L1")
        files = [p for p in self.knowledge_sources if Path(p).is_file()]
        dirs = [p for p in self.knowledge_sources if Path(p).is_dir()]
        for d in dirs:
            r = self.agent_pipeline.import_github_repo(kernel, d)
            self._log_agent_result("匯入資料夾", r)
            if r.get("source_id"):
                self.last_source_id = r["source_id"]
        if files:
            r = self.agent_pipeline.import_documents(kernel, files)
            self._log_agent_result("匯入檔案", r)
            if r.get("source_id"):
                self.last_source_id = r["source_id"]
        self.source_id_var.set(f"source_id: {self.last_source_id or '(none)'}")
        self._set_workflow_hint("匯入完成，請按「擷取知識卡」。")

    def _extract_cards(self):
        kernel = self.selected_kernel_var.get().strip()
        component = self.selected_component_var.get().strip()
        source_id = self.last_source_id or self.agent_pipeline.detect_source_id(kernel)
        if not source_id:
            self._append_layer_log("找不到 source_id，請先匯入知識來源")
            return
        self._set_workflow_hint("正在擷取知識卡...完成後請按「生成 Schema」。")
        self._set_cem_flow_running("L2")
        mode = self._get_agent_mode()
        r = self.agent_pipeline.extract_knowledge(kernel, source_id, component, mode=mode)
        self._log_agent_result("擷取知識卡", r)
        if mode == "llm" and not r.get("ok"):
            self._append_layer_log("LLM 未啟用，請設定 LABCEM_LLM_ENABLED=true 與 LABCEM_LLM_API_KEY。")
        self._set_workflow_hint("擷取完成，下一步請按「生成 Schema」。")

    def _generate_schema(self):
        self._set_workflow_hint("正在生成 Schema...完成後可生成程式草案。")
        self._set_cem_flow_running("L3")
        mode = self._get_agent_mode()
        r = self.agent_pipeline.generate_schema(self.selected_kernel_var.get().strip(), self.selected_component_var.get().strip(), mode=mode)
        self._log_agent_result("生成 Schema", r)
        self._set_workflow_hint("Schema 已完成，下一步請按「生成程式草案」。")

    def _propose_code(self):
        self._set_workflow_hint("正在生成程式草案...完成後請按「審核草案」。")
        self._set_cem_flow_running("L3")
        mode = self._get_agent_mode()
        r = self.agent_pipeline.propose_code(self.selected_kernel_var.get().strip(), self.selected_component_var.get().strip(), mode=mode)
        self._log_agent_result("生成程式草案", r)
        self._set_workflow_hint("草案已生成，下一步請按「審核草案」。")

    def _review_proposal(self):
        self._set_workflow_hint("正在審核草案...完成後可回到 Prompt 執行建模。")
        self._set_cem_flow_running("L4")
        mode = self._get_agent_mode()
        r = self.agent_pipeline.review_proposal(self.selected_kernel_var.get().strip(), self.selected_component_var.get().strip(), mode=mode)
        self._log_agent_result("審核草案", r)
        self._set_workflow_hint("審核完成，現在可以用上方 Prompt 進行 Build Model。")

    def _log_agent_result(self, title, result):
        self._append_layer_log(f"{title}: {result.get('message')}")
        for out in result.get("outputs", []):
            self._append_layer_log(f"  output: {out}")
        errs = result.get("errors", [])
        for e in errs:
            self._append_layer_log(f"  warning: {e}")
        if result.get("ok"):
            self._append_chat(f"{title} 完成")

    def _build_graphics(self, parent):
        self.fig = Figure(figsize=(6, 6), dpi=100, facecolor="white")
        self.ax = self.fig.add_subplot(111, projection="3d")
        self.ax.set_facecolor("white")
        self.ax.xaxis.pane.fill = False
        self.ax.yaxis.pane.fill = False
        self.ax.zaxis.pane.fill = False
        self.canvas3d = FigureCanvasTkAgg(self.fig, master=parent)
        self.canvas3d.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        toolbar_frame = ttk.Frame(parent)
        toolbar_frame.pack(side=tk.TOP, fill=tk.X)
        self.toolbar = NavigationToolbar2Tk(self.canvas3d, toolbar_frame, pack_toolbar=False)
        self.toolbar.update()
        self.toolbar.pack(side=tk.LEFT, fill=tk.X)
        self.canvas3d.mpl_connect("scroll_event", self._on_scroll_zoom)
        self.canvas3d.mpl_connect("button_press_event", self._on_mouse_press)
        self.canvas3d.mpl_connect("button_release_event", self._on_mouse_release)
        self.canvas3d.mpl_connect("motion_notify_event", self._on_mouse_move)
        self._draw_mesh_3d()

    def _labeled_entry(self, parent, label, var):
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.X, pady=5)
        ttk.Label(frame, text=label, font=("Microsoft JhengHei", 9)).pack(anchor="w")
        ttk.Entry(frame, textvariable=var).pack(fill=tk.X, pady=2)

    def _append_chat(self, text):
        self.chat_log.configure(state=tk.NORMAL)
        self.chat_log.insert(tk.END, text + "\n")
        self.chat_log.see(tk.END)
        self.chat_log.configure(state=tk.DISABLED)

    def _append_layer_log(self, text):
        self.layer_log.configure(state=tk.NORMAL)
        self.layer_log.insert(tk.END, f"> {text}\n")
        self.layer_log.see(tk.END)
        self.layer_log.configure(state=tk.DISABLED)

    def _set_raw_cli_output(self, text):
        self.raw_cli_log.configure(state=tk.NORMAL)
        self.raw_cli_log.delete("1.0", tk.END)
        self.raw_cli_log.insert(tk.END, text or "(empty)")
        self.raw_cli_log.configure(state=tk.DISABLED)

    def _set_cli_health(self, cli):
        if not cli:
            self.cli_health_var.set("CLI: Unknown")
            self.cli_health_label.configure(foreground="#555555")
            return
        if cli.get("ok"):
            self.cli_health_var.set("CLI: Healthy ({0})".format(cli.get("mode", "")))
            self.cli_health_label.configure(foreground="#1b8a3f")
        elif cli.get("available"):
            self.cli_health_var.set("CLI: Degraded ({0})".format(cli.get("reason", "")))
            self.cli_health_label.configure(foreground="#b26a00")
        else:
            self.cli_health_var.set("CLI: Offline")
            self.cli_health_label.configure(foreground="#b00020")

    def _set_cem_flow_running(self, layer_key):
        for key in self.cem_flow_vars:
            self.cem_flow_vars[key].set("待命")
        if layer_key in self.cem_flow_vars:
            self.cem_flow_vars[layer_key].set("進行中")
            self.cem_current_layer_var.set("Current: {0}".format(layer_key))

    def _set_cem_flow_from_steps(self, steps):
        status_map = {"done": "完成", "running": "進行中", "error": "錯誤"}
        for key in self.cem_flow_vars:
            self.cem_flow_vars[key].set("待命")
        current = "Idle"
        for item in steps or []:
            key = str(item.get("layer", "")).strip()
            st = str(item.get("status", "done")).lower()
            if key in self.cem_flow_vars:
                self.cem_flow_vars[key].set(status_map.get(st, st))
                current = key
        self.cem_current_layer_var.set("Current: {0}".format(current))

    def _browse_attachment(self):
        path = filedialog.askopenfilename(filetypes=[("Knowledge files", "*.pdf *.docx *.txt *.md *.json"), ("All files", "*.*")])
        if path:
            self.attachment_var.set(path)
            self._schedule_live_update()

    def _on_resolution_change(self, _value):
        self._schedule_live_update()

    def _schedule_live_update(self):
        if self.live_update_job is not None:
            self.after_cancel(self.live_update_job)
        self.live_update_job = self.after(350, lambda: self.run_generation(live=True))

    def _axis_limits(self):
        return (self.ax.get_xlim3d(), self.ax.get_ylim3d(), self.ax.get_zlim3d())

    def _set_axis_limits(self, xlim, ylim, zlim):
        self.ax.set_xlim3d(xlim)
        self.ax.set_ylim3d(ylim)
        self.ax.set_zlim3d(zlim)

    def _on_scroll_zoom(self, event):
        if event.xdata is None or event.ydata is None:
            return
        xlim, ylim, zlim = self._axis_limits()
        scale = 0.9 if event.button == "up" else 1.1
        cx = (xlim[0] + xlim[1]) / 2.0
        cy = (ylim[0] + ylim[1]) / 2.0
        cz = (zlim[0] + zlim[1]) / 2.0
        hx = (xlim[1] - xlim[0]) * 0.5 * scale
        hy = (ylim[1] - ylim[0]) * 0.5 * scale
        hz = (zlim[1] - zlim[0]) * 0.5 * scale
        self._set_axis_limits((cx - hx, cx + hx), (cy - hy, cy + hy), (cz - hz, cz + hz))
        self.canvas3d.draw_idle()

    def _on_mouse_press(self, event):
        if event.button == 3 and event.xdata is not None and event.ydata is not None:
            self._pan_active = True
            self._pan_last = (event.x, event.y)

    def _on_mouse_release(self, event):
        if event.button == 3:
            self._pan_active = False
            self._pan_last = None

    def _on_mouse_move(self, event):
        if not self._pan_active or self._pan_last is None or event.x is None or event.y is None:
            return
        dx = event.x - self._pan_last[0]
        dy = event.y - self._pan_last[1]
        self._pan_last = (event.x, event.y)
        xlim, ylim, zlim = self._axis_limits()
        fx = (xlim[1] - xlim[0]) * 0.002
        fy = (ylim[1] - ylim[0]) * 0.002
        fz = (zlim[1] - zlim[0]) * 0.002
        self._set_axis_limits((xlim[0] - dx * fx, xlim[1] - dx * fx), (ylim[0] + dy * fy, ylim[1] + dy * fy), (zlim[0] + dy * fz, zlim[1] + dy * fz))
        self.canvas3d.draw_idle()

    def _draw_mesh_3d(self):
        self.ax.clear()
        self.ax.set_xlabel("X")
        self.ax.set_ylabel("Y")
        self.ax.set_zlabel("Z")
        if self.current_grid is None and self.current_mesh_verts is None:
            self.ax.text2D(0.5, 0.5, "No Geometry Computed", transform=self.ax.transAxes, ha="center")
            self.canvas3d.draw()
            return
        try:
            if self.current_grid is not None:
                verts, faces, _, _ = marching_cubes(self.current_grid, level=0.0, spacing=(self.current_spacing, self.current_spacing, self.current_spacing))
                verts[:, 0] += float(self.current_origin[0])
                verts[:, 1] += float(self.current_origin[1])
                verts[:, 2] += float(self.current_origin[2])
            else:
                verts = self.current_mesh_verts
                faces = self.current_mesh_faces
            mesh = Poly3DCollection(verts[faces], alpha=0.85)
            mesh.set_facecolor("#6a8caf")
            mesh.set_edgecolor("#3b5998")
            mesh.set_linewidth(0.1)
            self.ax.add_collection3d(mesh)
            self.ax.auto_scale_xyz(verts[:, 0], verts[:, 1], verts[:, 2])
            self.ax.set_title("Result Geometry", fontsize=10)
            dx = float(np.max(verts[:, 0]) - np.min(verts[:, 0]))
            dy = float(np.max(verts[:, 1]) - np.min(verts[:, 1]))
            dz = float(np.max(verts[:, 2]) - np.min(verts[:, 2]))
            self.ax.text2D(0.02, 0.98, "三圍尺寸 | X:{0:.1f} Y:{1:.1f} Z:{2:.1f}".format(dx, dy, dz), transform=self.ax.transAxes, va="top")
        except Exception as exc:
            self._append_layer_log(f"渲染錯誤: {exc}")
        self.canvas3d.draw()

    def run_generation(self, live=False):
        if self.is_running:
            if live:
                self.pending_live = True
            return
        prompt = self.prompt_var.get().strip()
        if not prompt:
            return

        self._set_workflow_hint("正在建模計算中，完成後可檢視 3D 與輸出檔案。")
        self.is_running = True
        self.pending_live = False
        self.status_vars["STEP1"].set("Running...")
        self.status_vars["STEP2"].set("Running...")
        self.status_vars["STEP3"].set("Running...")
        self.status_vars["AI"].set("Computing...")
        self._set_cem_flow_running("L0")
        self._set_cli_health({"available": True, "ok": False, "reason": "running", "mode": "pending"})

        if not live:
            self._append_layer_log(f"啟動求解器: {prompt}")

        t = threading.Thread(target=self._worker_generate, args=(prompt, live), daemon=True)
        t.start()

    def _worker_generate(self, prompt, live):
        try:
            orchestrator = LabCEMOrchestrator(knowledge_root="knowledge/domains")
            result = orchestrator.run_from_prompt(
                prompt=prompt,
                domain="acoustic",
                kernel=self.selected_kernel_var.get().strip() or "acoustic_kernel",
                backend=self.selected_backend_var.get().strip() or "python_sdf",
                component_type=self.selected_component_var.get().strip() or "waveguide",
                output=self.output_var.get().strip() or "outputs/generated_geometry.json",
                voxel_resolution=int(self.resolution_var.get()),
            )
            payload = {"ok": True, "result": result, "live": live}
        except Exception as exc:
            payload = {"ok": False, "error": str(exc), "live": live}
        self.result_queue.put(payload)

    def _bind_left_scroll(self, _event=None):
        self.bind_all("<MouseWheel>", self._on_left_mousewheel)
        self.bind_all("<Button-4>", self._on_left_mousewheel)
        self.bind_all("<Button-5>", self._on_left_mousewheel)

    def _unbind_left_scroll(self, _event=None):
        self.unbind_all("<MouseWheel>")
        self.unbind_all("<Button-4>")
        self.unbind_all("<Button-5>")

    def _on_left_mousewheel(self, event):
        if hasattr(event, "delta") and event.delta:
            self.left_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        elif getattr(event, "num", None) == 4:
            self.left_canvas.yview_scroll(-1, "units")
        elif getattr(event, "num", None) == 5:
            self.left_canvas.yview_scroll(1, "units")
    def _poll_result_queue(self):
        try:
            payload = self.result_queue.get_nowait()
        except queue.Empty:
            self.after(200, self._poll_result_queue)
            return

        self.is_running = False
        if payload["ok"]:
            try:
                result = payload["result"]
                sdf_grid = result.get("sdf_grid", None)
                self.current_grid = None
                self.current_mesh_verts = None
                self.current_mesh_faces = None
                if sdf_grid is not None:
                    self.current_grid = np.array(sdf_grid, dtype=np.float32)
                    if self.current_grid.ndim == 3 and self.current_grid.shape[0] > 1:
                        res = int(result.get("voxel_resolution", self.current_grid.shape[0]))
                        span = float(result.get("sdf_span", 10.0))
                        self.current_spacing = (2.0 * span) / max(res - 1, 1)
                        self.current_origin = (-span, -span, -span)
                else:
                    v = result.get("mesh_verts", [])
                    f = result.get("mesh_faces", [])
                    if v and f:
                        self.current_mesh_verts = np.asarray(v, dtype=np.float32)
                        self.current_mesh_faces = np.asarray(f, dtype=np.int32)
                self._set_cem_flow_from_steps(result.get("pipeline_steps", []))
                self.status_vars["STEP1"].set("Success")
                self.status_vars["STEP2"].set("Success")
                self.status_vars["STEP3"].set("Success")
                self.status_vars["AI"].set("Complete")
                if not payload.get("live", False):
                    self._append_chat(f"AI 摘要: {result.get('label9_summary', '')}")
                    self._append_layer_log(f"輸出已儲存至: {result.get('output')}")
                    self._append_layer_log(f"生成來源(source): {result.get('source', 'unknown')}")
                    cli = result.get("cli_status", {})
                    self._set_cli_health(cli)
                    self._set_raw_cli_output(result.get("cli_raw_output", ""))
                    self._set_workflow_hint("建模完成，可調整參數後再次執行，或回到知識流程更新規格。")
                self._draw_mesh_3d()
            except Exception as exc:
                self.status_vars["AI"].set("Error")
                self._append_layer_log(f"結果處理失敗: {exc}")
        else:
            self._append_layer_log(f"錯誤: {payload['error']}")
            self.cem_current_layer_var.set("Current: Error")
            self._set_cli_health({"available": True, "ok": False, "reason": "runtime_error", "mode": "fallback"})

        if self.pending_live:
            self.pending_live = False
            self._schedule_live_update()

        self.after(200, self._poll_result_queue)


if __name__ == "__main__":
    app = LabCEMGui()
    app.mainloop()







