import argparse
import json
import os
import subprocess
import sys
import tempfile
import threading
import time
import tkinter as tk
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from tkinter import messagebox, ttk

_C900 = "#1e1e1c"
_C800 = "#2c2c2a"
_C600 = "#6b6b6b"
_C300 = "#b4b2a9"
_C100 = "#f1efe8"
_C50 = "#f8f7f4"
_VERDE = "#5a8a4a"
_VERDE_H = "#3b6d11"
_BRANCO = "#ffffff"
_ERRO = "#e24b4a"

APP_ROOT = Path(__file__).resolve().parent.parent
GITHUB_API = "https://api.github.com/repos/neuxxkk/tqs-automation/releases/latest"
SETUP_ASSET_NAME = "Scripts-Formula-Setup.exe"
SETUP_URL = f"https://github.com/neuxxkk/tqs-automation/releases/latest/download/{SETUP_ASSET_NAME}"
VERSION_FILE = APP_ROOT / "version.txt"
UPDATE_STATE_FILE = APP_ROOT / ".update_state.json"
RELAUNCH_ENV = "SCRIPTS_FORMULA_RELAUNCH"
RELEASE_VERSION_ENV = "SCRIPTS_FORMULA_RELEASE_VERSION"
RELEASE_FINGERPRINT_ENV = "SCRIPTS_FORMULA_RELEASE_FINGERPRINT"
RELEASE_UPDATED_AT_ENV = "SCRIPTS_FORMULA_RELEASE_UPDATED_AT"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _local_version() -> str:
    try:
        return VERSION_FILE.read_text(encoding="utf-8").strip()
    except OSError:
        return "desconhecida"


def _load_update_state() -> dict:
    try:
        raw = json.loads(UPDATE_STATE_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError, json.JSONDecodeError):
        return {}
    return raw if isinstance(raw, dict) else {}


def persist_installed_release_state(
    version: str,
    fingerprint: str = "",
    asset_updated_at: str = "",
) -> None:
    payload = {
        "version": version.strip(),
        "installed_at": _utc_now_iso(),
        "saved_at": _utc_now_iso(),
    }
    if fingerprint.strip():
        payload["fingerprint"] = fingerprint.strip()
    if asset_updated_at.strip():
        payload["asset_updated_at"] = asset_updated_at.strip()

    UPDATE_STATE_FILE.write_text(
        json.dumps(payload, indent=2, ensure_ascii=True),
        encoding="utf-8",
    )


def _parse_timestamp(value: str) -> float | None:
    value = value.strip()
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()
    except ValueError:
        return None


def _select_setup_asset(release_data: dict) -> dict | None:
    assets = release_data.get("assets")
    if not isinstance(assets, list):
        return None

    for asset in assets:
        if isinstance(asset, dict) and asset.get("name") == SETUP_ASSET_NAME:
            return asset

    for asset in assets:
        if isinstance(asset, dict) and str(asset.get("name", "")).lower().endswith(".exe"):
            return asset

    return None


def fetch_latest_release_info() -> dict:
    req = urllib.request.Request(GITHUB_API, headers={"User-Agent": "tqs-updater"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        release_data = json.loads(resp.read().decode("utf-8"))

    tag = str(release_data.get("tag_name", "")).strip()
    version = tag.lstrip("v")
    asset = _select_setup_asset(release_data) or {}
    digest = str(asset.get("digest", "")).strip()
    asset_updated_at = str(asset.get("updated_at", "")).strip()
    asset_id = asset.get("id")

    fingerprint = version
    if digest:
        fingerprint = f"{version}|{digest}"
    elif asset_updated_at:
        fingerprint = f"{version}|{asset_updated_at}"
    elif asset_id is not None:
        fingerprint = f"{version}|{asset_id}"

    return {
        "version": version,
        "tag_name": tag,
        "download_url": str(asset.get("browser_download_url") or SETUP_URL),
        "asset_name": str(asset.get("name") or SETUP_ASSET_NAME),
        "asset_updated_at": asset_updated_at,
        "fingerprint": fingerprint,
    }


def check_for_update() -> dict:
    local_version = _local_version()
    local_state = _load_update_state()
    remote = fetch_latest_release_info()

    reason = ""
    if remote["version"] and remote["version"] != local_version:
        reason = "new_version"
    else:
        local_fp = ""
        if str(local_state.get("version", "")).strip() == local_version:
            local_fp = str(local_state.get("fingerprint", "")).strip()

        remote_fp = str(remote.get("fingerprint", "")).strip()
        if local_fp and remote_fp and local_fp != remote_fp:
            reason = "new_package"
        else:
            installed_at = _parse_timestamp(str(local_state.get("installed_at", "")))
            remote_updated_at = _parse_timestamp(str(remote.get("asset_updated_at", "")))
            if (
                remote["version"] == local_version
                and not local_fp
                and installed_at is not None
                and remote_updated_at is not None
                and remote_updated_at > installed_at + 1
            ):
                reason = "new_package"

    return {
        "available": bool(reason),
        "reason": reason,
        "local_version": local_version,
        "latest_version": remote["version"],
        "setup_url": remote["download_url"],
        "release": remote,
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--app-pid", type=int, default=0)
    parser.add_argument("--auto-start-download", action="store_true")
    return parser.parse_args()


def _close_running_app(app_pid: int) -> None:
    if app_pid <= 0 or app_pid == os.getpid():
        return

    if os.name == "nt":
        subprocess.run(
            # Nao use /T aqui: o updater e filho da central e seria encerrado junto.
            ["taskkill", "/PID", str(app_pid), "/F"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
    else:
        try:
            os.kill(app_pid, 15)
        except OSError:
            pass

    time.sleep(0.8)


class UpdaterWindow(tk.Tk):
    def __init__(self, app_pid: int = 0, auto_start_download: bool = False) -> None:
        super().__init__()
        self.title("Atualizar Scripts Formula")
        self.configure(bg=_C100)
        self.resizable(False, False)

        self._app_pid = app_pid
        self._auto_start_download = auto_start_download
        self._local_ver = _local_version()
        self._latest_ver = ""
        self._setup_path = ""
        self._setup_url = SETUP_URL
        self._update_info: dict = {}

        self._build_ui()
        self.update_idletasks()
        w, h = 420, 300
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw - w) // 2}+{(sh - h) // 2}")

        threading.Thread(target=self._check_version, daemon=True).start()

    def _build_ui(self) -> None:
        header = tk.Frame(self, bg=_C900, pady=14, padx=20)
        header.pack(fill="x")
        tk.Label(
            header,
            text="Atualizar Sistema",
            font=("Segoe UI Semibold", 12),
            bg=_C900,
            fg=_BRANCO,
        ).pack(anchor="w")
        tk.Label(
            header,
            text="Scripts Formula Engenharia",
            font=("Segoe UI", 9),
            bg=_C900,
            fg=_C300,
        ).pack(anchor="w")

        body = tk.Frame(self, bg=_C100, padx=24, pady=20)
        body.pack(fill="both", expand=True)

        ver_frame = tk.Frame(body, bg=_C100)
        ver_frame.pack(fill="x", pady=(0, 14))

        tk.Label(
            ver_frame,
            text="Versao instalada:",
            font=("Segoe UI", 9),
            bg=_C100,
            fg=_C600,
        ).grid(row=0, column=0, sticky="w")
        tk.Label(
            ver_frame,
            text=self._local_ver,
            font=("Segoe UI", 9, "bold"),
            bg=_C100,
            fg=_C800,
        ).grid(row=0, column=1, sticky="w", padx=(8, 0))

        tk.Label(
            ver_frame,
            text="Versao disponivel:",
            font=("Segoe UI", 9),
            bg=_C100,
            fg=_C600,
        ).grid(row=1, column=0, sticky="w", pady=(4, 0))
        self._latest_lbl = tk.Label(
            ver_frame,
            text="verificando...",
            font=("Segoe UI", 9, "bold"),
            bg=_C100,
            fg=_C600,
        )
        self._latest_lbl.grid(row=1, column=1, sticky="w", padx=(8, 0), pady=(4, 0))

        self._status_var = tk.StringVar(value="Verificando atualizacao...")
        tk.Label(
            body,
            textvariable=self._status_var,
            font=("Segoe UI", 9),
            bg=_C100,
            fg=_C600,
            wraplength=360,
            justify="left",
        ).pack(anchor="w", pady=(0, 8))

        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure(
            "Verde.Horizontal.TProgressbar",
            troughcolor=_C100,
            background=_VERDE,
            bordercolor=_C100,
            lightcolor=_VERDE,
            darkcolor=_VERDE_H,
        )
        self._progress = ttk.Progressbar(
            body,
            style="Verde.Horizontal.TProgressbar",
            orient="horizontal",
            length=360,
            mode="indeterminate",
        )
        self._progress.pack(fill="x")
        self._progress.start(12)

        btn_row = tk.Frame(body, bg=_C100)
        btn_row.pack(anchor="e", pady=(20, 0))

        self._btn_atualizar = tk.Button(
            btn_row,
            text="Atualizar agora",
            font=("Segoe UI", 10),
            bg=_VERDE,
            fg=_BRANCO,
            disabledforeground="#a8c8a0",
            activebackground=_VERDE_H,
            activeforeground=_BRANCO,
            relief="flat",
            padx=18,
            pady=6,
            cursor="hand2",
            bd=0,
            state="disabled",
            command=self._start_download,
        )
        self._btn_atualizar.pack(side="right")

        tk.Button(
            btn_row,
            text="Fechar",
            font=("Segoe UI", 10),
            bg=_C100,
            fg=_C600,
            activebackground=_C300,
            activeforeground=_C800,
            relief="flat",
            padx=18,
            pady=6,
            cursor="hand2",
            bd=0,
            command=self.destroy,
        ).pack(side="right", padx=(0, 8))

    def _check_version(self) -> None:
        try:
            self._update_info = check_for_update()
        except Exception as exc:
            self.after(0, self._on_check_error, str(exc))
            return
        self.after(0, self._on_check_done)

    def _on_check_error(self, msg: str) -> None:
        self._progress.stop()
        self._progress.configure(mode="determinate")
        self._latest_lbl.configure(text="erro ao verificar", fg=_ERRO)
        self._status_var.set(f"Nao foi possivel verificar: {msg}")

    def _on_check_done(self) -> None:
        self._progress.stop()
        self._progress.configure(mode="determinate", value=0)

        self._latest_ver = str(self._update_info.get("latest_version", "")).strip()
        self._setup_url = str(self._update_info.get("setup_url") or SETUP_URL)
        reason = str(self._update_info.get("reason", "")).strip()
        available = bool(self._update_info.get("available"))

        latest_label = self._latest_ver or "indisponivel"
        if reason == "new_package" and self._latest_ver == self._local_ver:
            latest_label = f"{latest_label} (revisada)"
        self._latest_lbl.configure(text=latest_label, fg=_C800)

        if available:
            if reason == "new_package" and self._latest_ver == self._local_ver:
                self._status_var.set(
                    f"Ha um pacote revisado disponivel para a versao {self._latest_ver}. "
                    "Clique em 'Atualizar agora' para baixar e instalar."
                )
            else:
                self._status_var.set(
                    f"Nova versao disponivel: {self._latest_ver}. "
                    "Clique em 'Atualizar agora' para baixar e instalar."
                )
            self._btn_atualizar.configure(state="normal")
            if self._auto_start_download:
                self.after(200, self._start_download)
        else:
            self._status_var.set("O sistema ja esta na versao mais recente.")

    def _start_download(self) -> None:
        if not self._setup_url:
            self._status_var.set("Nao foi possivel localizar o instalador da atualizacao.")
            return

        self._btn_atualizar.configure(state="disabled")
        self._status_var.set("Baixando instalador...")
        self._progress.configure(mode="determinate", value=0)
        threading.Thread(target=self._download, daemon=True).start()

    def _download(self) -> None:
        try:
            tmp = tempfile.mktemp(suffix=".exe", prefix="ScriptsFormula-Setup-")
            req = urllib.request.Request(self._setup_url, headers={"User-Agent": "tqs-updater"})

            with urllib.request.urlopen(req, timeout=60) as resp:
                total = int(resp.headers.get("Content-Length", 0))
                downloaded = 0
                chunk = 1024 * 64
                with open(tmp, "wb") as file_handle:
                    while True:
                        block = resp.read(chunk)
                        if not block:
                            break
                        file_handle.write(block)
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
        self._status_var.set(f"Baixando... {mb_done:.1f} MB / {mb_total:.1f} MB ({pct}%)")

    def _on_download_done(self) -> None:
        self._progress["value"] = 100
        self._status_var.set("Download concluido. Iniciando instalador...")
        self.after(400, self._launch_installer)

    def _on_download_error(self, msg: str) -> None:
        self._status_var.set(f"Erro no download: {msg}")
        self._btn_atualizar.configure(state="normal")

    def _launch_installer(self) -> None:
        try:
            self._status_var.set("Fechando a versao atual e iniciando o instalador...")
            self.update_idletasks()
            _close_running_app(self._app_pid)
            env = os.environ.copy()
            env[RELAUNCH_ENV] = "1"

            release = self._update_info.get("release", {}) if isinstance(self._update_info, dict) else {}
            if release:
                env[RELEASE_VERSION_ENV] = str(release.get("version", "")).strip()
                env[RELEASE_FINGERPRINT_ENV] = str(release.get("fingerprint", "")).strip()
                env[RELEASE_UPDATED_AT_ENV] = str(release.get("asset_updated_at", "")).strip()

            subprocess.Popen(
                [self._setup_path],
                creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == "nt" else 0,
                env=env,
            )
        except Exception as exc:
            messagebox.showerror("Erro", f"Nao foi possivel iniciar o instalador:\n{exc}")
            return
        self.destroy()


if __name__ == "__main__":
    args = _parse_args()
    UpdaterWindow(
        app_pid=args.app_pid,
        auto_start_download=args.auto_start_download,
    ).mainloop()
