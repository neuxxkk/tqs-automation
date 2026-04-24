import os
import subprocess
import sys
import tempfile
import threading
import tkinter as tk
import urllib.error
import urllib.request
from json import loads
from pathlib import Path
from tkinter import messagebox, ttk

_C900   = "#1e1e1c"
_C800   = "#2c2c2a"
_C600   = "#6b6b6b"
_C300   = "#b4b2a9"
_C100   = "#f1efe8"
_C50    = "#f8f7f4"
_VERDE  = "#5a8a4a"
_VERDE_H = "#3b6d11"
_BRANCO = "#ffffff"
_ERRO   = "#e24b4a"

GITHUB_API  = "https://api.github.com/repos/neuxxkk/tqs-automation/releases/latest"
SETUP_URL   = "https://github.com/neuxxkk/tqs-automation/releases/latest/download/Scripts-Formula-Setup.exe"
VERSION_FILE = Path(__file__).resolve().parent.parent / "version.txt"


def _local_version() -> str:
    try:
        return VERSION_FILE.read_text(encoding="utf-8").strip()
    except OSError:
        return "desconhecida"


def _fetch_latest_version() -> str:
    req = urllib.request.Request(GITHUB_API, headers={"User-Agent": "tqs-updater"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = loads(resp.read().decode())
    tag = data.get("tag_name", "")
    return tag.lstrip("v")


class UpdaterWindow(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Atualizar Scripts Fórmula")
        self.configure(bg=_C100)
        self.resizable(False, False)

        self._local_ver = _local_version()
        self._latest_ver: str = ""
        self._setup_path: str = ""

        self._build_ui()
        self.update_idletasks()
        w, h = 420, 300
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw - w) // 2}+{(sh - h) // 2}")

        threading.Thread(target=self._check_version, daemon=True).start()

    # ── UI ────────────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        header = tk.Frame(self, bg=_C900, pady=14, padx=20)
        header.pack(fill="x")
        tk.Label(header, text="Atualizar Sistema",
                 font=("Segoe UI Semibold", 12), bg=_C900, fg=_BRANCO).pack(anchor="w")
        tk.Label(header, text="Scripts Fórmula Engenharia",
                 font=("Segoe UI", 9), bg=_C900, fg=_C300).pack(anchor="w")

        body = tk.Frame(self, bg=_C100, padx=24, pady=20)
        body.pack(fill="both", expand=True)

        # versões
        ver_frame = tk.Frame(body, bg=_C100)
        ver_frame.pack(fill="x", pady=(0, 14))

        tk.Label(ver_frame, text="Versão instalada:",
                 font=("Segoe UI", 9), bg=_C100, fg=_C600).grid(row=0, column=0, sticky="w")
        tk.Label(ver_frame, text=self._local_ver,
                 font=("Segoe UI", 9, "bold"), bg=_C100, fg=_C800).grid(row=0, column=1, sticky="w", padx=(8, 0))

        tk.Label(ver_frame, text="Versão disponível:",
                 font=("Segoe UI", 9), bg=_C100, fg=_C600).grid(row=1, column=0, sticky="w", pady=(4, 0))
        self._latest_lbl = tk.Label(ver_frame, text="verificando...",
                                     font=("Segoe UI", 9, "bold"), bg=_C100, fg=_C600)
        self._latest_lbl.grid(row=1, column=1, sticky="w", padx=(8, 0), pady=(4, 0))

        # status / barra
        self._status_var = tk.StringVar(value="Verificando atualização...")
        tk.Label(body, textvariable=self._status_var,
                 font=("Segoe UI", 9), bg=_C100, fg=_C600,
                 wraplength=360, justify="left").pack(anchor="w", pady=(0, 8))

        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("Verde.Horizontal.TProgressbar",
                        troughcolor=_C100, background=_VERDE,
                        bordercolor=_C100, lightcolor=_VERDE, darkcolor=_VERDE_H)
        self._progress = ttk.Progressbar(body, style="Verde.Horizontal.TProgressbar",
                                          orient="horizontal", length=360, mode="indeterminate")
        self._progress.pack(fill="x")
        self._progress.start(12)

        # botões
        btn_row = tk.Frame(body, bg=_C100)
        btn_row.pack(anchor="e", pady=(20, 0))

        self._btn_atualizar = tk.Button(
            btn_row, text="Atualizar agora",
            font=("Segoe UI", 10), bg=_VERDE, fg=_BRANCO,
            disabledforeground="#a8c8a0",
            activebackground=_VERDE_H, activeforeground=_BRANCO,
            relief="flat", padx=18, pady=6, cursor="hand2", bd=0,
            state="disabled", command=self._start_download,
        )
        self._btn_atualizar.pack(side="right")

        tk.Button(
            btn_row, text="Fechar",
            font=("Segoe UI", 10), bg=_C100, fg=_C600,
            activebackground=_C300, activeforeground=_C800,
            relief="flat", padx=18, pady=6, cursor="hand2", bd=0,
            command=self.destroy,
        ).pack(side="right", padx=(0, 8))

    # ── lógica ────────────────────────────────────────────────────────────

    def _check_version(self) -> None:
        try:
            self._latest_ver = _fetch_latest_version()
        except Exception as exc:
            self.after(0, self._on_check_error, str(exc))
            return
        self.after(0, self._on_check_done)

    def _on_check_error(self, msg: str) -> None:
        self._progress.stop()
        self._progress.configure(mode="determinate")
        self._latest_lbl.configure(text="erro ao verificar", fg=_ERRO)
        self._status_var.set(f"Não foi possível verificar: {msg}")

    def _on_check_done(self) -> None:
        self._progress.stop()
        self._progress.configure(mode="determinate", value=0)
        self._latest_lbl.configure(text=self._latest_ver, fg=_C800)

        if self._latest_ver and self._latest_ver != self._local_ver:
            self._status_var.set(
                f"Nova versão disponível: {self._latest_ver}. "
                "Clique em 'Atualizar agora' para baixar e instalar."
            )
            self._btn_atualizar.configure(state="normal")
        else:
            self._status_var.set("O sistema já está na versão mais recente.")

    def _start_download(self) -> None:
        self._btn_atualizar.configure(state="disabled")
        self._status_var.set("Baixando instalador...")
        self._progress.configure(mode="determinate", value=0)
        threading.Thread(target=self._download, daemon=True).start()

    def _download(self) -> None:
        try:
            tmp = tempfile.mktemp(suffix=".exe", prefix="ScriptsFormula-Setup-")
            req = urllib.request.Request(SETUP_URL, headers={"User-Agent": "tqs-updater"})

            with urllib.request.urlopen(req, timeout=60) as resp:
                total = int(resp.headers.get("Content-Length", 0))
                downloaded = 0
                chunk = 1024 * 64
                with open(tmp, "wb") as f:
                    while True:
                        block = resp.read(chunk)
                        if not block:
                            break
                        f.write(block)
                        downloaded += len(block)
                        if total:
                            pct = int(downloaded / total * 100)
                            self.after(0, self._set_progress, pct, downloaded, total)

            self._setup_path = tmp
            self.after(0, self._on_download_done)
        except Exception as exc:
            self.after(0, self._on_download_error, str(exc))

    def _set_progress(self, pct: int, downloaded: int, total: int) -> None:
        self._progress["value"] = pct
        mb_done = downloaded / 1_048_576
        mb_total = total / 1_048_576
        self._status_var.set(f"Baixando... {mb_done:.1f} MB / {mb_total:.1f} MB  ({pct}%)")

    def _on_download_done(self) -> None:
        self._progress["value"] = 100
        self._status_var.set("Download concluído. Iniciando instalador...")
        self.after(400, self._launch_installer)

    def _on_download_error(self, msg: str) -> None:
        self._status_var.set(f"Erro no download: {msg}")
        self._btn_atualizar.configure(state="normal")

    def _launch_installer(self) -> None:
        try:
            subprocess.Popen([self._setup_path], creationflags=subprocess.CREATE_NEW_CONSOLE
                             if os.name == "nt" else 0)
        except Exception as exc:
            messagebox.showerror("Erro", f"Não foi possível iniciar o instalador:\n{exc}")
            return
        self.destroy()


if __name__ == "__main__":
    UpdaterWindow().mainloop()
