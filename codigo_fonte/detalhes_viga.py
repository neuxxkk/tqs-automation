import os
import re
import shutil
import sys

from TQS import TQSBuild, TQSExec


def _has_relger_in_vigas(level_dir):
    """Retorna True se existir VIGAS/RELGER.LST dentro do nivel informado."""
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
    """Abre dialogo para o usuario selecionar a pasta raiz do edificio."""
    initial_dir = _default_drive_root()

    try:
        import tkinter as tk
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
        # Em execucao sem interface grafica, evita bloquear em input.
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
    """Seleciona pasta de destino via dialogo grafico ou fallback para input no terminal."""
    try:
        import tkinter as tk
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


def copy_and_rename_files(files, dest_dir):
    """Copia cada RELGER encontrado para o destino no padrao Vigas <Nivel>.LST."""
    copied_count = 0
    for record in files:
        folder_name = record["folder_name"].strip()
        filename = f"Vigas {folder_name}.LST"
        destination_path = os.path.join(dest_dir, filename)

        shutil.copy2(record["source_path"], destination_path)
        copied_count += 1
        print(f"Copiado: {filename}")

    print(f"\n{copied_count} arquivo(s) copiado(s) para {dest_dir}")


def exportar_relger_vigas(root_dir=None):
    resolved_root = get_root_directory(root_dir)
    if not resolved_root:
        print("Operacao cancelada pelo usuario.")
        return

    print(f"Pasta raiz para busca dos RELGER: {resolved_root}")

    files = find_relger_files(resolved_root)
    if not files:
        print("Nenhum arquivo RELGER.LST encontrado.")
        return

    destination = select_destination()
    if not destination:
        print("Operacao cancelada pelo usuario.")
        return

    if not os.path.isdir(destination):
        print("Destino invalido. Operacao cancelada.")
        return

    copy_and_rename_files(files, destination)

def processar_todas_vigas():
    root_dir_para_exportacao = ""
    nprjpv, nprjed, nombde, nomedi, nompav, istat = TQSBuild.BuildingContext()

    if istat != 0:
        print("Contexto TQS nao identificado no diretorio atual.")
        print("Selecione a pasta raiz do edificio para tentar novamente.")

        root_dir_para_exportacao = get_root_directory()
        if not root_dir_para_exportacao:
            print("Operacao cancelada pelo usuario.")
            return

        try:
            os.chdir(root_dir_para_exportacao)
        except OSError as exc:
            print(f"Nao foi possivel acessar a pasta selecionada: {exc}")
            return

        nprjpv, nprjed, nombde, nomedi, nompav, istat = TQSBuild.BuildingContext()
        if istat != 0:
            print("Erro: a pasta selecionada nao corresponde a um edificio TQS valido.")
            return
    else:
        root_dir_para_exportacao = os.getcwd()

    print(f"Edifício identificado: {nomedi}")
    print("Preparando fila de processamento das vigas...")

    job = TQSExec.Job()

    tarefa_pasta = TQSExec.TaskFolder(nomedi, TQSExec.TaskFolder.FOLDER_FRAMES)
    job.EnterTask(tarefa_pasta)

    # Configura a tarefa de Processamento Global APENAS para detalhar e extrair relatórios
    tarefa_vigas = TQSExec.TaskGlobalProc(
        floorPlan=0, floorDraw=0, slabs=0, 
        
        beams=2,          # <--- ALTERADO DE 3 PARA 2 (Gera o RELGER e pula o desenho)
        
        columnsData=0, columns=0, columnsReport=0, 
        gridModel=0, gridDraw=0, gridExtr=0, gridAnalysis=0, 
        gridBeamsTrnsf=0, gridSlabsTrnsf=0, gridNonLinear=0, 
        frameModel=0, frameAnalysis=0, frameBeamsTrnsf=0, 
        frameColumnsTrnsf=0, foundations=0, stairs=0, 
        fire=0, precastPhases=0
    )
    
    job.EnterTask(tarefa_vigas)

    print("Iniciando o dimensionamento, detalhamento e desenho de todas as vigas...")
    job.Execute()
    
    print("Processamento de vigas concluído com sucesso!")
    print("Iniciando a coleta dos arquivos RELGER.LST...")
    exportar_relger_vigas(root_dir=root_dir_para_exportacao)

    

if __name__ == "__main__":
    processar_todas_vigas()
