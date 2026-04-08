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


class ScriptLauncherApp(tk.Tk):
	def __init__(self) -> None:
		super().__init__()
		self.title("Automacoes TQS")
		self.geometry("620x360")
		self.minsize(540, 320)
		self.configure(bg="#f4f7fb")

		self._configure_styles()
		self._build_ui()
		self._running_processes: list[subprocess.Popen] = []

	def _configure_styles(self) -> None:
		style = ttk.Style(self)
		style.theme_use("clam")

		style.configure(
			"Card.TFrame",
			background="#ffffff",
			borderwidth=0,
			relief="flat",
		)

		style.configure(
			"Primary.TButton",
			font=("Segoe UI", 11, "bold"),
			foreground="#ffffff",
			background="#0d6efd",
			borderwidth=0,
			padding=(14, 10),
		)
		style.map(
			"Primary.TButton",
			background=[("active", "#0b5ed7"), ("pressed", "#0a58ca")],
		)

		style.configure(
			"Secondary.TButton",
			font=("Segoe UI", 11, "bold"),
			foreground="#0d6efd",
			background="#e9f1ff",
			borderwidth=0,
			padding=(14, 10),
		)
		style.map(
			"Secondary.TButton",
			background=[("active", "#d8e8ff"), ("pressed", "#c9ddff")],
		)

	def _build_ui(self) -> None:
		outer = ttk.Frame(self, padding=24, style="Card.TFrame")
		outer.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.9, relheight=0.85)

		title = tk.Label(
			outer,
			text="Central de Scripts",
			font=("Segoe UI Semibold", 20),
			bg="#ffffff",
			fg="#12263f",
		)
		title.pack(pady=(16, 4))

		subtitle = tk.Label(
			outer,
			text="Escolha qual automacao voce deseja executar",
			font=("Segoe UI", 11),
			bg="#ffffff",
			fg="#5c6f82",
		)
		subtitle.pack(pady=(0, 20))

		actions_frame = tk.Frame(outer, bg="#ffffff")
		actions_frame.pack(fill="x", padx=34)

		btn_detalhes = ttk.Button(
			actions_frame,
			text="Detalhes da Viga",
			style="Primary.TButton",
			command=self._run_detalhes_viga,
		)
		btn_detalhes.pack(fill="x", pady=(0, 10))

		btn_beiral = ttk.Button(
			actions_frame,
			text="Calculo de Beiral",
			style="Secondary.TButton",
			command=self._run_calc_beiral,
		)
		btn_beiral.pack(fill="x")

		link_btn = tk.Label(
			outer,
			text="Sistema de Atividades",
			font=("Segoe UI", 10, "underline"),
			bg="#ffffff",
			fg="#0d6efd",
			cursor="hand2",
		)
		link_btn.pack(pady=(22, 0))
		link_btn.bind("<Button-1>", lambda _event: self._open_activities())

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

		# Estrutura nova do projeto:
		# tqs-automation/
		#   codigo_fonte/*.py
		#   executaveis/*.bat|*.exe
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
