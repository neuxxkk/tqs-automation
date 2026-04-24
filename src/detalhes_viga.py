import os
import re
import shutil
import sys
import tkinter as tk
from tkinter import ttk

from TQS import TQSBuild, TQSExec

# Paleta Formula Engenharia
_C900  = "#1e1e1c"
_C800  = "#2c2c2a"
_C600  = "#6b6b6b"
_C100  = "#f1efe8"
_C50   = "#f8f7f4"
_VERDE = "#5a8a4a"
_VERDE_H = "#3b6d11"
_BRANCO = "#ffffff"


class ProgressoVigas(tk.Toplevel):
    """Janela de acompanhamento do dimensionamento de vigas."""

    def __init__(self, parent: tk.Tk | None = None) -> None:
        if parent is None:
            self._root_owner = tk.Tk()
            self._root_owner.withdraw()
            super().__init__(self._root_owner)
        else:
            self._root_owner = None
            super().__init__(parent)

        self.title("Dimensionamento de Vigas")
        self.configure(bg=_C100)
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", lambda: None)  # impede fechar manualmente

        self._build_ui()
        self.update_idletasks()
        self._center()

    def _build_ui(self) -> None:
        # cabeçalho
        header = tk.Frame(self, bg=_C900, pady=14, padx=20)
        header.pack(fill="x")
        tk.Label(
            header,
            text="Dimensionamento de Vigas  —  TQS",
            font=("Segoe UI Semibold", 12),
            bg=_C900,
            fg=_BRANCO,
        ).pack(anchor="w")
        tk.Label(
            header,
            text="Processando todos os pavimentos do edifício",
            font=("Segoe UI", 9),
            bg=_C900,
            fg=_C600,
        ).pack(anchor="w")

        body = tk.Frame(self, bg=_C100, padx=24, pady=20)
        body.pack(fill="both", expand=True)

        # Etapa atual
        self._etapa_var = tk.StringVar(value="Aguardando início...")
        tk.Label(
            body,
            textvariable=self._etapa_var,
            font=("Segoe UI", 10, "bold"),
            bg=_C100,
            fg=_C800,
        ).pack(anchor="w")

        # Detalhe / viga atual
        self._detalhe_var = tk.StringVar(value="")
        self._detalhe_label = tk.Label(
            body,
            textvariable=self._detalhe_var,
            font=("Segoe UI", 9),
            bg=_C100,
            fg=_C600,
        )
        self._detalhe_label.pack(anchor="w", pady=(2, 10))

        # Barra de progresso
        style = ttk.Style()
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
            length=380,
            mode="determinate",
        )
        self._progress.pack(fill="x", pady=(0, 6))

        self._prog_label = tk.Label(
            body,
            text="",
            font=("Segoe UI", 8),
            bg=_C100,
            fg=_C600,
        )
        self._prog_label.pack(anchor="e")

        # Log de atividade (scrollável)
        log_frame = tk.Frame(body, bg=_C100)
        log_frame.pack(fill="both", expand=True, pady=(12, 0))

        tk.Label(
            log_frame,
            text="LOG DE ATIVIDADE",
            font=("Segoe UI", 8, "bold"),
            bg=_C100,
            fg=_C600,
        ).pack(anchor="w")

        self._log_text = tk.Text(
            log_frame,
            height=8,
            font=("Consolas", 8),
            bg=_C50,
            fg=_C800,
            relief="flat",
            bd=1,
            wrap="word",
            state="disabled",
        )
        scrollbar = ttk.Scrollbar(log_frame, command=self._log_text.yview)
        self._log_text.configure(yscrollcommand=scrollbar.set)
        self._log_text.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self._btn_row = tk.Frame(body, bg=_C100)
        self._btn_row.pack(anchor="e", pady=(14, 0))

        self._btn_fechar = tk.Button(
            self._btn_row,
            text="Fechar",
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
            command=self._on_close,
        )
        self._btn_fechar.pack(side="right")

    def _center(self) -> None:
        w, h = 460, 480
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw - w) // 2}+{(sh - h) // 2}")

    def _on_close(self) -> None:
        self.destroy()
        if self._root_owner:
            self._root_owner.destroy()

    def set_etapa(self, texto: str) -> None:
        self._etapa_var.set(texto)
        self._log(f"[ETAPA] {texto}")
        self.update()

    def set_detalhe(self, texto: str) -> None:
        self._detalhe_var.set(texto)
        self.update()

    def set_progresso(self, atual: int, total: int, pavimento: str = "") -> None:
        pct = int(atual / total * 100) if total > 0 else 0
        self._progress["value"] = pct
        self._prog_label.configure(text=f"{atual} / {total}  ({pct}%)")
        if pavimento:
            self._detalhe_var.set(f"Processando: {pavimento}")
        self._log(f"[OK] {pavimento}  ({atual}/{total})")
        self.update()

    def finalizar(self, mensagem: str = "Concluído com sucesso.") -> None:
        self._etapa_var.set(mensagem)
        self._detalhe_var.set("")
        self._progress["value"] = 100
        self._prog_label.configure(text="100%")
        self._log(f"\n{mensagem}")
        self._btn_fechar.configure(state="normal")
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.update()

    def erro(self, mensagem: str) -> None:
        self._etapa_var.set("Erro no processamento")
        self._detalhe_var.set(mensagem)
        self._log(f"\n[ERRO] {mensagem}")
        self._btn_fechar.configure(state="normal", bg="#e24b4a", activebackground="#c03b3a")
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.update()

    def aguardar_selecao(self, etapa: str, detalhe: str, label_btn: str = "Selecionar") -> bool:
        """Mostra etapa + detalhe com botão de confirmação; bloqueia até o clique.

        Retorna True se o usuário clicou em Selecionar, False se fechou a janela.
        """
        self._etapa_var.set(etapa)
        self._detalhe_var.set(detalhe)

        var = tk.BooleanVar(value=False)

        btn = tk.Button(
            self._btn_row,
            text=label_btn,
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
            command=lambda: var.set(True),
        )
        btn.pack(side="right", padx=(0, 8))
        self.update()
        self.wait_variable(var)
        btn.destroy()
        return True

    def _log(self, texto: str) -> None:
        self._log_text.configure(state="normal")
        self._log_text.insert("end", texto + "\n")
        self._log_text.see("end")
        self._log_text.configure(state="disabled")


def _has_relger_in_vigas(level_dir):
    if not os.path.isdir(level_dir):
        return False

    try:
        with os.scandir(level_dir) as entries:
            for entry in entries:
                if entry.is_dir() and entry.name.lower() == "vigas":
                    relger_path = os.path.join(entry.path, "RELGER.LST")
                    return os.path.isfile(relger_path)
    except OSError:
        return False

    return False


def _default_drive_root():
    drive, _ = os.path.splitdrive(os.getcwd())
    if drive:
        return drive + os.sep
    return os.path.abspath(os.sep)


def select_root_directory():
    initial_dir = _default_drive_root()

    try:
        from tkinter import filedialog

        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        selected = filedialog.askdirectory(
            title="Selecione a pasta raiz do edificio",
            initialdir=initial_dir,
            mustexist=True,
        )
        root.destroy()
        return selected.strip() if selected else ""
    except Exception:
        if sys.stdin and sys.stdin.isatty():
            return input("Informe o caminho da pasta raiz do edificio: ").strip()
        print("Nao foi possivel abrir o seletor de pasta raiz.")
        return ""


def get_root_directory(root_dir=None):
    """Resolve a pasta raiz do edificio com preferencia por contexto local do script."""
    if root_dir:
        root_dir = os.path.abspath(root_dir)
        return root_dir if os.path.isdir(root_dir) else ""

    selected_dir = select_root_directory()
    if not selected_dir:
        return ""

    selected_dir = os.path.abspath(selected_dir)
    return selected_dir if os.path.isdir(selected_dir) else ""


def _sort_key(record):
    match = re.match(r"^\s*(\d+)", record["folder_name"])
    if match:
        return (0, int(match.group(1)), record["folder_name"].lower())
    return (1, 9999, record["folder_name"].lower())


def find_relger_files(root_dir):
    """Busca arquivos RELGER.LST em subpastas no formato <nivel>/VIGAS/RELGER.LST."""
    files = []

    with os.scandir(root_dir) as level_entries:
        for level_entry in level_entries:
            if not level_entry.is_dir():
                continue

            vigas_path = None
            try:
                with os.scandir(level_entry.path) as sub_entries:
                    for sub_entry in sub_entries:
                        if sub_entry.is_dir() and sub_entry.name.lower() == "vigas":
                            vigas_path = sub_entry.path
                            break
            except OSError:
                continue

            if not vigas_path:
                continue

            relger_path = os.path.join(vigas_path, "RELGER.LST")
            if os.path.isfile(relger_path):
                files.append(
                    {
                        "folder_name": level_entry.name.strip(),
                        "source_path": relger_path,
                    }
                )

    files.sort(key=_sort_key)
    return files


def select_destination():
    try:
        from tkinter import filedialog

        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        destination = filedialog.askdirectory(title="Selecione a pasta de destino para os RELGER")
        root.destroy()
        return destination.strip() if destination else ""
    except Exception:
        if sys.stdin and sys.stdin.isatty():
            return input("Informe o caminho da pasta de destino: ").strip()
        print("Nao foi possivel abrir o seletor de pasta de destino.")
        return ""


def processar_todas_vigas():
    progresso = ProgressoVigas()

    root_dir_para_exportacao = ""
    nprjpv, nprjed, nombde, nomedi, nompav, istat = TQSBuild.BuildingContext()

    if istat != 0:
        ok = progresso.aguardar_selecao(
            etapa="Selecione a pasta raíz do edifício",
            detalhe="Clique em Selecionar e escolha a pasta raíz do edifício a ser dimensionado.",
        )
        if not ok:
            progresso.erro("Operação cancelada pelo usuário.")
            progresso.wait_window()
            return
        root_dir_para_exportacao = get_root_directory()
        if not root_dir_para_exportacao:
            progresso.erro("Operação cancelada pelo usuário.")
            progresso.mainloop() if hasattr(progresso, "_root_owner") and progresso._root_owner else progresso.wait_window()
            return

        try:
            os.chdir(root_dir_para_exportacao)
        except OSError as exc:
            progresso.erro(f"Não foi possível acessar a pasta: {exc}")
            progresso.wait_window()
            return

        nprjpv, nprjed, nombde, nomedi, nompav, istat = TQSBuild.BuildingContext()
        if istat != 0:
            progresso.erro("A pasta selecionada não é um edifício TQS válido.")
            progresso.wait_window()
            return
    else:
        root_dir_para_exportacao = os.getcwd()

    progresso.set_etapa(f"Edifício: {nomedi}")
    progresso.set_detalhe("Preparando fila de processamento das vigas...")

    files_preview = find_relger_files(root_dir_para_exportacao)
    total_pavimentos = len(files_preview) if files_preview else "?"

    progresso.set_etapa("Executando dimensionamento (abra EDITW para detalhes)...")
    progresso.set_detalhe(f"{total_pavimentos} pavimento(s) detectado(s). Aguarde o TQS processar...")
    progresso._progress.configure(mode="indeterminate")
    progresso._progress.start(15)
    progresso.update()

    job = TQSExec.Job()
    tarefa_pasta = TQSExec.TaskFolder(nomedi, TQSExec.TaskFolder.FOLDER_FRAMES)
    job.EnterTask(tarefa_pasta)

    tarefa_vigas = TQSExec.TaskGlobalProc(
        floorPlan=0, floorDraw=0, slabs=0,
        beams=2,
        columnsData=0, columns=0, columnsReport=0,
        gridModel=0, gridDraw=0, gridExtr=0, gridAnalysis=0,
        gridBeamsTrnsf=0, gridSlabsTrnsf=0, gridNonLinear=0,
        frameModel=0, frameAnalysis=0, frameBeamsTrnsf=0,
        frameColumnsTrnsf=0, foundations=0, stairs=0,
        fire=0, precastPhases=0,
    )
    job.EnterTask(tarefa_vigas)
    job.Execute()

    progresso._progress.stop()
    progresso._progress.configure(mode="determinate")
    progresso._progress["value"] = 50

    files = find_relger_files(root_dir_para_exportacao)
    if not files:
        progresso.erro("Nenhum RELGER.LST encontrado após o processamento.")
        progresso.wait_window()
        return

    ok = progresso.aguardar_selecao(
        etapa="Selecione a pasta de destino dos LSTs",
        detalhe=f"{len(files)} arquivo(s) encontrado(s). Clique em Selecionar e escolha onde salvar os LSTs.",
    )
    if not ok:
        progresso.erro("Destino não selecionado. Operação cancelada.")
        progresso.wait_window()
        return

    destination = select_destination()
    if not destination:
        progresso.erro("Destino não selecionado. Operação cancelada.")
        progresso.wait_window()
        return

    if not os.path.isdir(destination):
        progresso.erro("Pasta de destino inválida.")
        progresso.wait_window()
        return

    progresso.set_etapa("Copiando e renomeando arquivos...")
    total = len(files)
    for i, record in enumerate(files, start=1):
        folder_name = record["folder_name"].strip()
        filename = f"Vigas {folder_name}.LST"
        destination_path = os.path.join(destination, filename)
        shutil.copy2(record["source_path"], destination_path)
        progresso.set_progresso(i, total, folder_name)

    progresso.finalizar(f"Concluído! {total} arquivo(s) exportado(s) para:\n{destination}")
    progresso.wait_window()


if __name__ == "__main__":
    processar_todas_vigas()
