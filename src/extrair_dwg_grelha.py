import os
import sys
import tkinter as tk
from tkinter import ttk

from TQS import TQSBuild, TQSExec

# Paleta Formula Engenharia
_C900 = "#1e1e1c"
_C800 = "#2c2c2a"
_C600 = "#6b6b6b"
_C100 = "#f1efe8"
_C50 = "#f8f7f4"
_VERDE = "#5a8a4a"
_VERDE_H = "#3b6d11"
_BRANCO = "#ffffff"

CONFIG_PROCESSAMENTO = {
    "titulo": "Grelha Nao Linear",
    "descricao": "Formas, pre-processamento linear de armaduras, analise nao linear e exportacao para DWG.",
    "etapa_config": "Configurando processamento linear + nao linear da grelha.",
    "etapa_exec": "Executando grelha nao linear com pre-processamento linear...",
    "detalhe_exec": "O TQS vai processar formas, armaduras lineares, analise nao linear e exportacao. Aguarde...",
    "mensagem_final": "Processamento da grelha nao linear concluido com sucesso.",
    "task_kwargs": {
        "floorPlan": 2,
        "floorDraw": 0,
        "slabs": 2,
        "beams": 2,
        "columnsData": 0,
        "columns": 0,
        "columnsReport": 0,
        "gridModel": 1,
        "gridAnalysis": 1,
        "gridNonLinear": 1,
        "gridDraw": 0,
        "gridExtr": 0,
        "gridBeamsTrnsf": 0,
        "gridSlabsTrnsf": 0,
        "frameModel": 0,
        "frameAnalysis": 0,
        "frameBeamsTrnsf": 0,
        "frameColumnsTrnsf": 0,
        "foundations": 0,
        "stairs": 0,
        "fire": 0,
        "precastPhases": 0,
    },
}


class ProgressoGrelha(tk.Toplevel):
    """Janela de acompanhamento da extracao dos DWGs da grelha."""

    def __init__(self, parent: tk.Tk | None = None) -> None:
        if parent is None:
            self._root_owner = tk.Tk()
            self._root_owner.withdraw()
            super().__init__(self._root_owner)
        else:
            self._root_owner = None
            super().__init__(parent)

        self._close_requested = False
        self._closed = False
        self._selection_var: tk.StringVar | None = None

        self.title("Extracao de DWGs da Grelha")
        self.configure(bg=_C100)
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        self._build_ui()
        self.update_idletasks()
        self._center()

    def _build_ui(self) -> None:
        header = tk.Frame(self, bg=_C900, pady=14, padx=20)
        header.pack(fill="x")
        tk.Label(
            header,
            text="Extracao de DWGs da Grelha  -  TQS",
            font=("Segoe UI Semibold", 12),
            bg=_C900,
            fg=_BRANCO,
        ).pack(anchor="w")
        tk.Label(
            header,
            text="Execute a grelha nao linear e gere os desenhos em um unico fluxo",
            font=("Segoe UI", 9),
            bg=_C900,
            fg=_C600,
        ).pack(anchor="w")

        body = tk.Frame(self, bg=_C100, padx=24, pady=20)
        body.pack(fill="both", expand=True)

        self._etapa_var = tk.StringVar(value="Aguardando inicio...")
        tk.Label(
            body,
            textvariable=self._etapa_var,
            font=("Segoe UI", 10, "bold"),
            bg=_C100,
            fg=_C800,
        ).pack(anchor="w")

        self._detalhe_var = tk.StringVar(value="")
        tk.Label(
            body,
            textvariable=self._detalhe_var,
            font=("Segoe UI", 9),
            bg=_C100,
            fg=_C600,
            wraplength=390,
            justify="left",
        ).pack(anchor="w", pady=(2, 10))

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
            state="normal",
            command=self._on_close,
        )
        self._btn_fechar.pack(side="right")

    def _center(self) -> None:
        w, h = 460, 440
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw - w) // 2}+{(sh - h) // 2}")

    @property
    def cancelado(self) -> bool:
        return self._close_requested

    def _is_open(self) -> bool:
        if self._closed:
            return False
        try:
            return bool(self.winfo_exists())
        except tk.TclError:
            return False

    def _on_close(self) -> None:
        self._close_requested = True
        try:
            self._progress.stop()
        except (AttributeError, tk.TclError):
            pass

        if self._selection_var is not None:
            try:
                self._selection_var.set("")
            except tk.TclError:
                pass

        self.fechar(destroy_owner=self._selection_var is None)

    def fechar(self, destroy_owner: bool = True) -> None:
        if not self._closed:
            self._closed = True
            try:
                self.destroy()
            except tk.TclError:
                pass

        if destroy_owner and self._root_owner:
            try:
                self._root_owner.destroy()
            except tk.TclError:
                pass
            self._root_owner = None

    def set_etapa(self, texto: str) -> None:
        if not self._is_open():
            return
        self._etapa_var.set(texto)
        self._log(f"[ETAPA] {texto}")
        self.update()

    def set_detalhe(self, texto: str) -> None:
        if not self._is_open():
            return
        self._detalhe_var.set(texto)
        self.update()

    def set_progresso(self, atual: int, total: int, detalhe: str = "") -> None:
        if not self._is_open():
            return
        pct = int(atual / total * 100) if total > 0 else 0
        self._progress["value"] = pct
        self._prog_label.configure(text=f"{atual} / {total}  ({pct}%)")
        if detalhe:
            self._detalhe_var.set(detalhe)
            self._log(f"[OK] {detalhe}")
        self.update()

    def aguardar_opcao(self, etapa: str, detalhe: str, opcoes: list[tuple[str, str]]) -> str:
        if not self._is_open():
            return ""

        self._etapa_var.set(etapa)
        self._detalhe_var.set(detalhe)

        var = tk.StringVar(value="")
        self._selection_var = var
        botoes: list[tk.Button] = []

        for valor, label_btn in reversed(opcoes):
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
                command=lambda v=valor: var.set(v),
            )
            btn.pack(side="right", padx=(0, 8))
            botoes.append(btn)

        try:
            self.update()
            self.wait_variable(var)
            selecionado = var.get().strip()
        except tk.TclError:
            selecionado = ""
        finally:
            self._selection_var = None
            for btn in botoes:
                try:
                    btn.destroy()
                except tk.TclError:
                    pass

        if self._close_requested:
            self.fechar()
            return ""

        return selecionado

    def finalizar(self, mensagem: str = "Concluido com sucesso.") -> None:
        if not self._is_open():
            return
        self._etapa_var.set(mensagem)
        self._detalhe_var.set("")
        self._progress["value"] = 100
        self._prog_label.configure(text="100%")
        self._log(f"\n{mensagem}")
        self._btn_fechar.configure(state="normal")
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.update()

    def erro(self, mensagem: str) -> None:
        if not self._is_open():
            return
        self._etapa_var.set("Erro no processamento")
        self._detalhe_var.set(mensagem)
        self._log(f"\n[ERRO] {mensagem}")
        self._btn_fechar.configure(state="normal", bg="#e24b4a", activebackground="#c03b3a")
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.update()

    def _log(self, texto: str) -> None:
        if not self._is_open():
            return
        self._log_text.configure(state="normal")
        self._log_text.insert("end", texto + "\n")
        self._log_text.see("end")
        self._log_text.configure(state="disabled")


def _default_drive_root() -> str:
    drive, _ = os.path.splitdrive(os.getcwd())
    if drive:
        return drive + os.sep
    return os.path.abspath(os.sep)


def select_root_directory() -> str:
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


def get_root_directory(root_dir: str | None = None) -> str:
    if root_dir:
        root_dir = os.path.abspath(root_dir)
        return root_dir if os.path.isdir(root_dir) else ""

    selected_dir = select_root_directory()
    if not selected_dir:
        return ""

    selected_dir = os.path.abspath(selected_dir)
    return selected_dir if os.path.isdir(selected_dir) else ""


def _abortar_se_cancelado(progresso: ProgressoGrelha) -> bool:
    if not progresso.cancelado:
        return False
    progresso.fechar()
    return True


def _aguardar_fechamento(progresso: ProgressoGrelha) -> None:
    if progresso.cancelado:
        progresso.fechar()
        return

    try:
        progresso.wait_window()
    except tk.TclError:
        pass
    finally:
        progresso.fechar()


def _obter_contexto_edificio(progresso: ProgressoGrelha) -> tuple[str | None, str | None]:
    nprjpv, nprjed, nombde, nomedi, nompav, istat = TQSBuild.BuildingContext()
    if istat == 0:
        return nomedi, None

    ok = progresso.aguardar_opcao(
        etapa="Selecione a pasta raiz do edificio",
        detalhe="Voce esta fora de um edificio TQS. Clique em Selecionar e escolha a pasta raiz do edificio.",
        opcoes=[("selecionar", "Selecionar")],
    )
    if ok != "selecionar":
        return None, None

    root_dir = get_root_directory()
    if not root_dir:
        return None, None

    try:
        os.chdir(root_dir)
    except OSError as exc:
        return None, f"Nao foi possivel acessar a pasta: {exc}"

    nprjpv, nprjed, nombde, nomedi, nompav, istat = TQSBuild.BuildingContext()
    if istat != 0:
        return None, "A pasta selecionada nao e um edificio TQS valido."

    return nomedi, None


def extrair_dwg_grelha() -> None:
    progresso = ProgressoGrelha()

    config = CONFIG_PROCESSAMENTO
    nomedi, erro_contexto = _obter_contexto_edificio(progresso)
    if not nomedi:
        if erro_contexto:
            progresso.erro(erro_contexto)
            _aguardar_fechamento(progresso)
            return
        if not progresso.cancelado:
            progresso.erro("Operacao cancelada pelo usuario.")
            _aguardar_fechamento(progresso)
        return

    progresso.set_etapa(f"Edificio: {nomedi}")
    progresso.set_progresso(1, 4, f"Contexto do edificio identificado. Processamento: {config['titulo']}.")
    if _abortar_se_cancelado(progresso):
        return

    progresso.set_progresso(2, 4, "Posicionando o gerenciador na pasta espacial.")
    job = TQSExec.Job()
    tarefa_pasta = TQSExec.TaskFolder(nomedi, TQSExec.TaskFolder.FOLDER_FRAMES)
    job.EnterTask(tarefa_pasta)
    if _abortar_se_cancelado(progresso):
        return

    progresso.set_progresso(3, 4, config["etapa_config"])
    tarefa_grelha = TQSExec.TaskGlobalProc(**config["task_kwargs"])
    job.EnterTask(tarefa_grelha)
    if _abortar_se_cancelado(progresso):
        return

    progresso.set_etapa(config["etapa_exec"])
    progresso.set_detalhe(config["detalhe_exec"])
    progresso._progress.configure(mode="indeterminate")
    progresso._progress.start(15)
    progresso.update()

    try:
        job.Execute()
    except Exception as exc:
        progresso._progress.stop()
        progresso._progress.configure(mode="determinate")
        progresso.erro(f"Falha ao executar a exportacao: {exc}")
        _aguardar_fechamento(progresso)
        return

    if _abortar_se_cancelado(progresso):
        return

    progresso._progress.stop()
    progresso._progress.configure(mode="determinate")
    progresso.set_progresso(4, 4, "Processamento finalizado.")
    progresso.finalizar(config["mensagem_final"])
    _aguardar_fechamento(progresso)


if __name__ == "__main__":
    extrair_dwg_grelha()
