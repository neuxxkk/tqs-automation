import os
import shutil
import subprocess
import sys
import tkinter as tk
import webbrowser
from pathlib import Path
from tkinter import messagebox
from tkinter import ttk


BASE_DIR = Path(__file__).resolve().parent
ACTIVITIES_URL = os.getenv("SISTEMA_ATIVIDADES_URL", "")

# Paleta Formula Engenharia
_C900 = "#1e1e1c"   # sidebar / header escuro
_C800 = "#2c2c2a"   # texto primário
_C600 = "#6b6b6b"   # texto secundário
_C300 = "#b4b2a9"   # bordas
_C100 = "#f1efe8"   # fundo geral
_C50  = "#f8f7f4"   # fundo de cards
_VERDE = "#5a8a4a"  # cor principal da marca
_VERDE_H = "#3b6d11" # hover
_BRANCO = "#ffffff"

_ABOUT_TEXTS = {
    "Dimensionar Vigas": (
        "Automatiza o dimensionamento e detalhamento de todas as vigas de um edifício no TQS.\n\n"
        "O script identifica os pavimentos, executa o processamento global (apenas vigas) e "
        "coleta os relatórios RELGER.LST gerados, renomeando-os no padrão 'Vigas <Pavimento>.LST' "
        "em uma pasta de destino escolhida por você."
    ),
    "Calculo de Beiral": (
        "Abre uma interface web (Streamlit) para cálculo estrutural de beirais em balanço.\n\n"
        "Informe a geometria da laje, as cargas permanentes e acidentais e os elementos de borda "
        "(nervura e guarda-corpo). O sistema calcula os momentos, aplica o majorador normativo "
        "(NBR 6118) e gera um memorial de cálculo em PDF pronto para entrega."
    ),
    "Auditoria ARMPIL": (
        "Abre a planilha Excel de auditoria do ARMPIL.\n\n"
        "Utilizada para conferência e registro dos dados de armação pilares extraídos do TQS. "
        "Permite revisar quantitativos, identificar inconsistências e documentar o processo de "
        "verificação estrutural."
    ),
}


class AboutDialog(tk.Toplevel):
    def __init__(self, parent: tk.Tk, tool_name: str, description: str) -> None:
        super().__init__(parent)
        self.title(f"Sobre — {tool_name}")
        self.configure(bg=_C100)
        self.resizable(False, False)
        self.grab_set()

        header = tk.Frame(self, bg=_C900, pady=14, padx=20)
        header.pack(fill="x")
        tk.Label(
            header,
            text=tool_name,
            font=("Segoe UI Semibold", 13),
            bg=_C900,
            fg=_BRANCO,
        ).pack(anchor="w")

        body = tk.Frame(self, bg=_C100, padx=24, pady=20)
        body.pack(fill="both", expand=True)

        tk.Label(
            body,
            text=description,
            font=("Segoe UI", 10),
            bg=_C100,
            fg=_C800,
            wraplength=380,
            justify="left",
        ).pack(anchor="w")

        tk.Button(
            body,
            text="Fechar",
            font=("Segoe UI", 10),
            bg=_VERDE,
            fg=_BRANCO,
            activebackground=_VERDE_H,
            activeforeground=_BRANCO,
            relief="flat",
            padx=18,
            pady=6,
            cursor="hand2",
            bd=0,
            command=self.destroy,
        ).pack(anchor="e", pady=(14, 0))

        self.update_idletasks()
        w, h = self.winfo_reqwidth(), self.winfo_reqheight()
        px = parent.winfo_x() + (parent.winfo_width() - w) // 2
        py = parent.winfo_y() + (parent.winfo_height() - h) // 2
        self.geometry(f"{w}x{h}+{px}+{py}")


class ScriptLauncherApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Automações Fórmula Engenharia")
        self.geometry("820x640")
        self.minsize(660, 500)
        self.configure(bg=_C100)

        self._running_processes: list[subprocess.Popen] = []
        self._configure_styles()
        self._build_ui()

    def _configure_styles(self) -> None:
        style = ttk.Style(self)
        style.theme_use("clam")

        style.configure("Sidebar.TFrame", background=_C900)
        style.configure("Main.TFrame", background=_C100)
        style.configure("Card.TFrame", background=_C50, borderwidth=0, relief="flat")

        style.configure(
            "Primary.TButton",
            font=("Segoe UI", 11, "bold"),
            foreground=_BRANCO,
            background=_VERDE,
            borderwidth=0,
            padding=(14, 10),
        )
        style.map("Primary.TButton", background=[("active", _VERDE_H), ("pressed", _VERDE_H)])

        style.configure(
            "Secondary.TButton",
            font=("Segoe UI", 11),
            foreground=_C800,
            background=_C50,
            borderwidth=1,
            padding=(14, 10),
        )
        style.map(
            "Secondary.TButton",
            background=[("active", _C100), ("pressed", _C100)],
            foreground=[("active", _C900)],
        )

        style.configure(
            "Info.TButton",
            font=("Segoe UI", 9),
            foreground=_C600,
            background=_C100,
            borderwidth=0,
            padding=(4, 4),
        )
        style.map("Info.TButton", foreground=[("active", _VERDE)])

    def _build_ui(self) -> None:
        # ── Sidebar escura ──────────────────────────────────────────────────
        sidebar = tk.Frame(self, bg=_C900, width=210)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        logo_frame = tk.Frame(sidebar, bg=_C900, pady=28, padx=16)
        logo_frame.pack(fill="x")
        tk.Label(logo_frame, text="FÓRMULA", font=("Segoe UI Semibold", 16), bg=_C900, fg=_BRANCO).pack(anchor="w")
        tk.Label(logo_frame, text="Engenharia e Consultoria", font=("Segoe UI", 8), bg=_C900, fg=_C300).pack(anchor="w")

        tk.Frame(sidebar, bg=_C800, height=1).pack(fill="x", padx=16, pady=(0, 20))

        tk.Label(sidebar, text="AUTOMAÇÕES", font=("Segoe UI", 8, "bold"), bg=_C900, fg=_C600).pack(anchor="w", padx=16, pady=(0, 8))

        # âncoras para scroll — preenchidas em _build_scrollable_content
        self._card_anchors: dict[str, tk.Frame] = {}

        nav_defs = [
            ("Dimensionar Vigas", "vigas", self._run_detalhes_viga),
            ("Cálculo de Beiral", "beiral", self._run_calc_beiral),
            ("Auditoria ARMPIL", "auditoria", self._open_auditoria_armpil),
        ]
        for label_text, key, action in nav_defs:
            lbl = tk.Label(
                sidebar, text=f"  {label_text}",
                font=("Segoe UI", 10), bg=_C900, fg=_C300,
                anchor="w", cursor="hand2", pady=7,
            )
            lbl.pack(fill="x", padx=8)
            lbl.bind("<Enter>", lambda e, w=lbl: w.configure(fg=_BRANCO, bg="#2c2c2a"))
            lbl.bind("<Leave>", lambda e, w=lbl: w.configure(fg=_C300, bg=_C900))
            lbl.bind("<Button-1>", lambda e, k=key, a=action: (self._scroll_to(k), a()))

        tk.Frame(sidebar, bg=_C900).pack(fill="y", expand=True)

        tk.Frame(sidebar, bg=_C800, height=1).pack(fill="x", padx=16, pady=(0, 4))

        upd_btn = tk.Label(
            sidebar, text="  Atualizar sistema",
            font=("Segoe UI", 10), bg=_C900, fg=_C300,
            anchor="w", cursor="hand2", pady=7,
        )
        upd_btn.pack(fill="x", padx=8)
        upd_btn.bind("<Enter>", lambda e: upd_btn.configure(fg=_BRANCO, bg=_C800))
        upd_btn.bind("<Leave>", lambda e: upd_btn.configure(fg=_C300, bg=_C900))
        upd_btn.bind("<Button-1>", lambda _e: self._run_updater())

        link_btn = tk.Label(
            sidebar, text="",
            font=("Segoe UI", 9, "underline"), bg=_C900, fg=_C600,
            cursor="hand2", pady=10, padx=16,
        )
        link_btn.pack(fill="x")
        link_btn.bind("<Button-1>", lambda _e: self._open_activities())
        link_btn.bind("<Enter>", lambda e: link_btn.configure(fg=_VERDE))
        link_btn.bind("<Leave>", lambda e: link_btn.configure(fg=_C600))

        # ── Área principal com scroll ───────────────────────────────────────
        main = tk.Frame(self, bg=_C100)
        main.pack(side="left", fill="both", expand=True)

        # cabeçalho fixo (fora do scroll)
        header = tk.Frame(main, bg=_C50, pady=20, padx=28)
        header.pack(fill="x")
        tk.Label(header, text="Central de Scripts", font=("Segoe UI Semibold", 18), bg=_C50, fg=_C800).pack(anchor="w")
        tk.Label(header, text="Escolha a automação que deseja executar", font=("Segoe UI", 10), bg=_C50, fg=_C600).pack(anchor="w")
        tk.Frame(main, bg=_C300, height=1).pack(fill="x")

        # Canvas + Scrollbar para a área de conteúdo
        scroll_frame = tk.Frame(main, bg=_C100)
        scroll_frame.pack(fill="both", expand=True)

        self._canvas = tk.Canvas(scroll_frame, bg=_C100, highlightthickness=0)
        scrollbar = ttk.Scrollbar(scroll_frame, orient="vertical", command=self._canvas.yview)
        self._canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        self._canvas.pack(side="left", fill="both", expand=True)

        self._scroll_inner = tk.Frame(self._canvas, bg=_C100)
        self._canvas_window = self._canvas.create_window((0, 0), window=self._scroll_inner, anchor="nw")

        self._scroll_inner.bind("<Configure>", self._on_inner_configure)
        self._canvas.bind("<Configure>", self._on_canvas_configure)
        self._canvas.bind("<MouseWheel>", self._on_mousewheel)
        self._scroll_inner.bind("<MouseWheel>", self._on_mousewheel)

        self._build_scrollable_content(self._scroll_inner)

    def _on_inner_configure(self, _event=None) -> None:
        self._canvas.configure(scrollregion=self._canvas.bbox("all"))

    def _on_canvas_configure(self, event) -> None:
        self._canvas.itemconfig(self._canvas_window, width=event.width)

    def _on_mousewheel(self, event) -> None:
        self._canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _scroll_to(self, key: str) -> None:
        anchor = self._card_anchors.get(key)
        if not anchor:
            return
        self._scroll_inner.update_idletasks()
        anchor_y = anchor.winfo_y()
        total_h = self._scroll_inner.winfo_height()
        canvas_h = self._canvas.winfo_height()
        if total_h <= canvas_h:
            return
        frac = max(0.0, min(1.0, anchor_y / (total_h - canvas_h)))
        self._canvas.yview_moveto(frac)

    def _build_scrollable_content(self, parent: tk.Frame) -> None:
        content = tk.Frame(parent, bg=_C100, padx=28, pady=24)
        content.pack(fill="x")

        # bind mousewheel nos cards também
        content.bind("<MouseWheel>", self._on_mousewheel)

        self._build_tool_card(
            parent=content, key="vigas",
            title="Dimensionar Vigas",
            description="Processa e coleta relatórios RELGER de todos os pavimentos via TQS.",
            action=self._run_detalhes_viga,
            btn_style="Primary.TButton",
            about_key="Dimensionar Vigas",
            steps=[
                ("1", "Selecione o diretório raiz do edifício a ser dimensionado"),
                ("2", "Selecione o diretório de destino para os arquivos .LST gerados"),
            ],
        )

        self._build_tool_card(
            parent=content, key="beiral",
            title="Cálculo de Beiral",
            description="Interface web para cálculo estrutural de beirais em balanço (NBR 6118).",
            action=self._run_calc_beiral,
            btn_style="Secondary.TButton",
            about_key="Calculo de Beiral",
        )

        self._build_tool_card(
            parent=content, key="auditoria",
            title="Auditoria ARMPIL",
            description="Planilha de conferência e registro de armação de pilares.",
            action=self._open_auditoria_armpil,
            btn_style="Secondary.TButton",
            about_key="Auditoria ARMPIL",
        )

    def _build_tool_card(
        self,
        parent: tk.Frame,
        key: str,
        title: str,
        description: str,
        action,
        btn_style: str,
        about_key: str,
        steps: list[tuple[str, str]] | None = None,
    ) -> None:
        card = tk.Frame(parent, bg=_C50, bd=0, pady=16, padx=18)
        card.pack(fill="x", pady=(0, 14))
        card.bind("<MouseWheel>", self._on_mousewheel)

        # registra âncora para navegação pela sidebar
        self._card_anchors[key] = card

        tk.Frame(card, bg=_VERDE, width=3).pack(side="left", fill="y", padx=(0, 14))

        inner = tk.Frame(card, bg=_C50)
        inner.pack(side="left", fill="both", expand=True)
        inner.bind("<MouseWheel>", self._on_mousewheel)

        top_row = tk.Frame(inner, bg=_C50)
        top_row.pack(fill="x")

        tk.Label(top_row, text=title, font=("Segoe UI Semibold", 12), bg=_C50, fg=_C800).pack(side="left")

        about_btn = tk.Label(top_row, text="?  sobre", font=("Segoe UI", 8), bg=_C50, fg=_C600, cursor="hand2")
        about_btn.pack(side="right", padx=(8, 0))
        about_btn.bind("<Button-1>", lambda _e, k=about_key, t=title: self._show_about(t, _ABOUT_TEXTS[k]))
        about_btn.bind("<Enter>", lambda e, w=about_btn: w.configure(fg=_VERDE))
        about_btn.bind("<Leave>", lambda e, w=about_btn: w.configure(fg=_C600))
        about_btn.bind("<MouseWheel>", self._on_mousewheel)

        tk.Label(
            inner, text=description,
            font=("Segoe UI", 9), bg=_C50, fg=_C600,
            wraplength=420, justify="left",
        ).pack(anchor="w", pady=(4, 8))

        if steps:
            steps_frame = tk.Frame(inner, bg=_C100, padx=10, pady=8)
            steps_frame.pack(fill="x", pady=(0, 10))
            steps_frame.bind("<MouseWheel>", self._on_mousewheel)

            tk.Label(
                steps_frame, text="COMO USAR",
                font=("Segoe UI", 7, "bold"), bg=_C100, fg=_C600,
            ).pack(anchor="w", pady=(0, 4))

            for num, text in steps:
                row = tk.Frame(steps_frame, bg=_C100)
                row.pack(fill="x", pady=2)
                row.bind("<MouseWheel>", self._on_mousewheel)

                badge = tk.Label(
                    row, text=num,
                    font=("Segoe UI", 8, "bold"), bg=_VERDE, fg=_BRANCO,
                    width=2, padx=4, pady=1,
                )
                badge.pack(side="left")
                badge.bind("<MouseWheel>", self._on_mousewheel)

                tk.Label(
                    row, text=text,
                    font=("Segoe UI", 9), bg=_C100, fg=_C800,
                    anchor="w",
                ).pack(side="left", padx=(8, 0))

        ttk.Button(inner, text="Executar", style=btn_style, command=action).pack(anchor="w")

    def _show_about(self, title: str, description: str) -> None:
        AboutDialog(self, title, description)

    def _python_command(self) -> list[str]:
        if not getattr(sys, "frozen", False):
            return [sys.executable]

        app_dir = Path(sys.executable).resolve().parent
        local_pythonw = app_dir / "pythonw.exe"
        local_python = app_dir / "python.exe"
        if local_pythonw.exists():
            return [str(local_pythonw)]
        if local_python.exists():
            return [str(local_python)]

        py_launcher = shutil.which("py")
        if py_launcher:
            return [py_launcher, "-3"]

        python_path = shutil.which("python")
        if python_path:
            return [python_path]

        python3_path = shutil.which("python3")
        if python3_path:
            return [python3_path]

        messagebox.showerror(
            "Python nao encontrado",
            "Nao foi possivel encontrar um interpretador Python para iniciar os scripts.",
        )
        return []

    def _candidate_roots(self) -> list[Path]:
        roots: list[Path] = []

        def add_root(path: Path) -> None:
            resolved = path.resolve()
            if resolved not in roots:
                roots.append(resolved)

        app_dir = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else BASE_DIR

        add_root(app_dir)
        add_root(app_dir / "codigo_fonte")
        add_root(app_dir.parent)
        add_root(app_dir.parent / "codigo_fonte")

        add_root(BASE_DIR)
        add_root(BASE_DIR / "codigo_fonte")
        add_root(BASE_DIR.parent)
        add_root(BASE_DIR.parent / "codigo_fonte")

        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            meipass_path = Path(meipass)
            add_root(meipass_path)
            add_root(meipass_path / "codigo_fonte")

        return roots

    def _resolve_file(self, file_name: str) -> Path | None:
        for root in self._candidate_roots():
            candidate = root / file_name
            if candidate.exists():
                return candidate
        return None

    def _run_silent_process(self, command: list[str], cwd: Path, label: str) -> None:
        creation_flags = 0
        startup_info = None

        if os.name == "nt":
            creation_flags = subprocess.CREATE_NO_WINDOW
            startup_info = subprocess.STARTUPINFO()
            startup_info.dwFlags |= subprocess.STARTF_USESHOWWINDOW

        process = subprocess.Popen(
            command,
            cwd=str(cwd),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
            creationflags=creation_flags,
            startupinfo=startup_info,
        )

        self._running_processes.append(process)
        self.after(1800, lambda: self._report_quick_failure(process, label, command))

    def _report_quick_failure(self, process: subprocess.Popen, label: str, command: list[str]) -> None:
        return_code = process.poll()
        if return_code is None:
            return

        if return_code == 0:
            return

        stderr_text = ""
        if process.stderr:
            stderr_text = process.stderr.read().strip()

        if not stderr_text:
            stderr_text = "Erro sem detalhes no stderr."

        cmd_txt = " ".join(command)
        messagebox.showerror(
            "Falha ao iniciar",
            f"Nao foi possivel iniciar {label}.\n\nComando:\n{cmd_txt}\n\nDetalhes:\n{stderr_text}",
        )

    def _run_python_script(self, script_name: str, extra_args: list[str] | None = None) -> None:
        script_path = self._resolve_file(script_name)
        if not script_path:
            roots_txt = "\n".join(str(p) for p in self._candidate_roots())
            messagebox.showerror(
                "Arquivo nao encontrado",
                f"Nao foi encontrado: {script_name}\n\nPastas verificadas:\n{roots_txt}",
            )
            return

        python_cmd = self._python_command()
        if not python_cmd:
            return

        command = python_cmd + [str(script_path)]
        if extra_args:
            command.extend(extra_args)

        try:
            self._run_silent_process(command, script_path.parent, script_name)
        except Exception as exc:
            messagebox.showerror("Erro ao executar", f"Falha ao abrir {script_name}:\n{exc}")

    def _run_updater(self) -> None:
        self._run_python_script("updater.py")

    def _run_detalhes_viga(self) -> None:
        self._run_python_script("detalhes_viga.py")

    def _run_calc_beiral(self) -> None:
        python_cmd = self._python_command()
        if not python_cmd:
            return

        script_path = self._resolve_file("calc_beiral.py")
        if not script_path:
            roots_txt = "\n".join(str(p) for p in self._candidate_roots())
            messagebox.showerror(
                "Arquivo nao encontrado",
                f"Nao foi encontrado: calc_beiral.py\n\nPastas verificadas:\n{roots_txt}",
            )
            return

        command = python_cmd + [
            "-m",
            "streamlit",
            "run",
            str(script_path),
            "--browser.gatherUsageStats",
            "false",
        ]

        try:
            self._run_silent_process(command, script_path.parent, "calc_beiral.py")
        except Exception as exc:
            messagebox.showerror("Erro ao executar", f"Falha ao abrir calc_beiral.py:\n{exc}")

    def _open_auditoria_armpil(self) -> None:
        xlsm = self._resolve_file("audit/auditoria_armpil_sele.xlsm")
        if not xlsm:
            candidate = BASE_DIR.parent / "audit" / "auditoria_armpil_sele.xlsm"
            if candidate.exists():
                xlsm = candidate
        if not xlsm:
            messagebox.showerror(
                "Arquivo nao encontrado",
                "Nao foi possivel encontrar auditoria_armpil_sele.xlsm.\n"
                "Verifique se o arquivo esta na pasta 'outros' do projeto.",
            )
            return
        try:
            os.startfile(str(xlsm))
        except Exception as exc:
            messagebox.showerror("Erro ao abrir", f"Nao foi possivel abrir a planilha:\n{exc}")

    def _open_activities(self) -> None:
        if not ACTIVITIES_URL:
            messagebox.showinfo(
                "Sistema de Atividades",
                "Defina a variavel de ambiente SISTEMA_ATIVIDADES_URL para abrir o sistema.",
            )
            return

        try:
            webbrowser.open_new_tab(ACTIVITIES_URL)
        except Exception as exc:
            messagebox.showerror("Erro ao abrir link", f"Nao foi possivel abrir o sistema:\n{exc}")


if __name__ == "__main__":
    app = ScriptLauncherApp()
    app.mainloop()
