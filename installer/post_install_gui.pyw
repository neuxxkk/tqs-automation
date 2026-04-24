import sys
import os
import subprocess
import threading
import tkinter as tk
from tkinter import font as tkfont

# Suprime janela de console em subprocessos no Windows
CREATE_NO_WINDOW = 0x08000000

# ---------------------------------------------------------------------------
# Paleta — frontend_design.md
# ---------------------------------------------------------------------------
C_BG          = "#1e1e1c"   # cinza-900 — fundo geral
C_SURFACE     = "#2c2c2a"   # cinza-800 — painel de log
C_BORDER      = "#b4b2a9"   # cinza-300
C_TEXT_PRI    = "#f1efe8"   # cinza-100
C_TEXT_SEC    = "#b4b2a9"   # cinza-300
C_GREEN       = "#5a8a4a"   # verde-principal
C_GREEN_DARK  = "#3b6d11"   # verde-hover / sucesso
C_ERROR       = "#e24b4a"
C_TRACK       = "#2c2c2a"   # trilho da barra de progresso

APP_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

STEPS = [
    ("Atualizando pip...",                  ["-m", "pip", "install", "--upgrade", "pip"]),
    ("Instalando dependências principais...", ["-m", "pip", "install", "--upgrade",
                                              "xlsxwriter", "pillow", "streamlit", "fpdf2"]),
    ("Instalando PyMuPDF...",               ["-m", "pip", "install", "--only-binary=:all:", "PyMuPDF"]),
    ("Copiando arquivos para o TQS...",     [os.path.join(APP_ROOT, "src", "install_tqs_files.py")]),
]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def find_python():
    candidates = []
    try:
        import shutil
        if shutil.which("py"):
            candidates.append(("py", ["-3"]))
    except Exception:
        pass
    for name in ("python", "python3"):
        try:
            import shutil
            if shutil.which(name):
                candidates.append((name, []))
        except Exception:
            pass

    for exe, args in candidates:
        try:
            result = subprocess.run(
                [exe] + args + ["-c",
                    "import sys; exit(0 if getattr(sys,'_is_gil_enabled',lambda:True)() else 1)"],
                capture_output=True,
                creationflags=CREATE_NO_WINDOW,
            )
            if result.returncode == 0:
                return exe, args
        except Exception:
            pass
    return None, None


def make_cmd(py_exe, py_args, step_args):
    """Build the subprocess argv for one step."""
    script_arg = step_args[0] if (
        len(step_args) == 1 and not step_args[0].startswith("-")
    ) else None

    if script_arg:
        return [py_exe] + py_args + [script_arg]
    return [py_exe] + py_args + step_args


# ---------------------------------------------------------------------------
# GUI
# ---------------------------------------------------------------------------

class InstallerWindow:
    LOG_H_COLLAPSED = 0
    LOG_H_EXPANDED  = 200

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Scripts Formula — Configuração")
        self.root.resizable(False, False)
        self.root.configure(bg=C_BG)
        self._set_icon()

        self._log_visible = False
        self._done        = False
        self._error       = False

        self.root.geometry("480x180")
        self.root.resizable(False, True)
        self.root.minsize(480, 180)
        self.root.maxsize(480, 9999)
        self._build_ui()
        self.root.update_idletasks()
        self._center()

        # start worker after first paint
        self.root.after(120, self._start_worker)

    # ------------------------------------------------------------------
    def _set_icon(self):
        ico = os.path.join(APP_ROOT, "assets", "imgs", "engenharia_formula_logo.ico")
        if os.path.exists(ico):
            try:
                self.root.iconbitmap(ico)
            except Exception:
                pass

    def _center(self):
        w = self.root.winfo_width()
        h = self.root.winfo_height()
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        self.root.geometry(f"+{x}+{y}")

    # ------------------------------------------------------------------
    def _build_ui(self):
        PAD = 32

        outer = tk.Frame(self.root, bg=C_BG)
        outer.pack(fill="both", expand=True, padx=PAD, pady=PAD)

        # Title
        title_font = tkfont.Font(family="Segoe UI", size=13, weight="bold")
        tk.Label(
            outer, text="Scripts Formula", font=title_font,
            bg=C_BG, fg=C_TEXT_PRI, anchor="w",
        ).pack(fill="x")

        tk.Label(
            outer, text="Configuração inicial do sistema",
            font=("Segoe UI", 9), bg=C_BG, fg=C_TEXT_SEC, anchor="w",
        ).pack(fill="x", pady=(2, 20))

        # Status label
        self._status_var = tk.StringVar(value="Iniciando...")
        tk.Label(
            outer, textvariable=self._status_var,
            font=("Segoe UI", 10), bg=C_BG, fg=C_TEXT_PRI,
            anchor="w", wraplength=400,
        ).pack(fill="x", pady=(0, 10))

        # Progress bar (canvas-based for full colour control)
        self._pb_frame = tk.Frame(outer, bg=C_TRACK, height=8, bd=0)
        self._pb_frame.pack(fill="x", pady=(0, 4))
        self._pb_frame.pack_propagate(False)

        self._pb_canvas = tk.Canvas(
            self._pb_frame, bg=C_TRACK, height=8,
            highlightthickness=0, bd=0,
        )
        self._pb_canvas.pack(fill="x", expand=True)
        self._pb_bar = self._pb_canvas.create_rectangle(0, 0, 0, 8, fill=C_GREEN, outline="")

        # Percent label
        self._pct_var = tk.StringVar(value="0%")
        tk.Label(
            outer, textvariable=self._pct_var,
            font=("Segoe UI", 8), bg=C_BG, fg=C_TEXT_SEC, anchor="e",
        ).pack(fill="x")

        # Toggle details button
        self._toggle_btn = tk.Button(
            outer,
            text="Ver detalhes  ▼",
            font=("Segoe UI", 9),
            bg=C_BG, fg=C_GREEN,
            activebackground=C_BG, activeforeground=C_GREEN_DARK,
            relief="flat", cursor="hand2", anchor="w", bd=0,
            command=self._toggle_log,
        )
        self._toggle_btn.pack(fill="x", pady=(10, 0))

        # Log panel (hidden initially)
        self._log_outer = tk.Frame(outer, bg=C_SURFACE, height=0)
        self._log_outer.pack(fill="x", pady=(6, 0))
        self._log_outer.pack_propagate(False)

        self._log_text = tk.Text(
            self._log_outer,
            bg=C_SURFACE, fg=C_TEXT_SEC,
            font=("Consolas", 8),
            relief="flat", bd=0,
            wrap="word",
            state="disabled",
            exportselection=False,
            cursor="arrow",
        )
        _sb = tk.Scrollbar(self._log_outer, command=self._log_text.yview,
                           bg=C_SURFACE, troughcolor=C_SURFACE,
                           relief="flat", bd=0, width=10)
        self._log_text.configure(yscrollcommand=_sb.set)
        _sb.pack(side="right", fill="y")
        self._log_text.pack(side="left", fill="both", expand=True, padx=8, pady=6)

        # Close button (hidden until done)
        self._close_btn = tk.Button(
            outer, text="Fechar",
            font=("Segoe UI", 10, "bold"),
            bg=C_GREEN, fg="#ffffff",
            activebackground=C_GREEN_DARK, activeforeground="#ffffff",
            relief="flat", cursor="hand2", bd=0, padx=16, pady=6,
            command=self.root.destroy,
        )

    # ------------------------------------------------------------------
    def _toggle_log(self):
        self._log_visible = not self._log_visible
        target_h = self.LOG_H_EXPANDED if self._log_visible else self.LOG_H_COLLAPSED
        btn_text  = ("Ocultar detalhes  ▲" if self._log_visible else "Ver detalhes  ▼")
        self._toggle_btn.config(text=btn_text)
        self._animate_log(target_h)

    def _animate_log(self, target_h: int, step: int = 20):
        cur = self._log_outer.winfo_height()
        # winfo_height returns 1 when not yet mapped — treat as 0
        if cur == 1:
            cur = 0
        diff = target_h - cur
        if diff == 0:
            return
        delta = min(step, abs(diff)) * (1 if diff > 0 else -1)
        new_h = cur + delta
        self._log_outer.config(height=new_h)
        if new_h != target_h:
            self.root.after(12, lambda: self._animate_log(target_h, step))

    # ------------------------------------------------------------------
    def _append_log(self, line: str):
        self._log_text.configure(state="normal")
        self._log_text.insert("end", line)
        self._log_text.see("end")
        self._log_text.configure(state="disabled")

    def _set_progress(self, pct: float):
        self._pb_canvas.update_idletasks()
        w = self._pb_canvas.winfo_width()
        bar_w = int(w * pct / 100)
        self._pb_canvas.coords(self._pb_bar, 0, 0, bar_w, 8)
        self._pct_var.set(f"{int(pct)}%")

    # ------------------------------------------------------------------
    def _start_worker(self):
        t = threading.Thread(target=self._run_steps, daemon=True)
        t.start()

    def _run_steps(self):
        py_exe, py_args = find_python()
        if py_exe is None:
            self.root.after(0, self._on_no_python)
            return

        total = len(STEPS)
        for i, (label, args) in enumerate(STEPS):
            pct_start = (i / total) * 100
            pct_end   = ((i + 1) / total) * 100

            self.root.after(0, self._status_var.set, label)
            self.root.after(0, self._set_progress, pct_start)

            cmd = make_cmd(py_exe, py_args, args)
            self.root.after(0, self._append_log, f"\n$ {' '.join(cmd)}\n")

            try:
                proc = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    creationflags=CREATE_NO_WINDOW,
                )
                for line in proc.stdout:
                    self.root.after(0, self._append_log, line)
                proc.wait()
            except Exception as exc:
                self.root.after(0, self._append_log, f"[ERRO] {exc}\n")
                self.root.after(0, self._on_error, str(exc))
                return

            if proc.returncode != 0:
                self.root.after(0, self._on_error,
                                f"Etapa falhou (código {proc.returncode}): {label}")
                return

            self.root.after(0, self._set_progress, pct_end)

        self.root.after(0, self._on_success)

    # ------------------------------------------------------------------
    def _on_success(self):
        self._status_var.set("Instalação concluída com sucesso.")
        self._set_progress(100)
        self._close_btn.config(bg=C_GREEN)
        self._close_btn.pack(pady=(16, 0))
        self._done = True

    def _on_error(self, msg: str):
        self._status_var.set(f"Falha: {msg}")
        self._close_btn.config(
            bg=C_ERROR, activebackground="#b33",
            text="Fechar",
        )
        self._close_btn.pack(pady=(16, 0))
        if not self._log_visible:
            self._toggle_log()
        self._error = True

    def _on_no_python(self):
        self._on_error(
            "Python não encontrado. Instale o Python 3.13 em python.org e tente novamente."
        )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    root = tk.Tk()
    app = InstallerWindow(root)
    root.mainloop()
    sys.exit(1 if app._error else 0)
