import shutil
import subprocess
import sys
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
SOURCE_DIR = BASE_DIR / "arquivos"
TARGET_DIR = Path(r"C:\TQSW\EXEC\PYTHON")
PIP_DEPENDENCIES = ["xlsxwriter", "pillow"]


def _log(msg: str) -> None:
    print(msg, flush=True)


def install_pip_dependencies() -> None:
    _log("Instalando dependencias Python...")
    cmd = [sys.executable, "-m", "pip", "install", "--upgrade", *PIP_DEPENDENCIES]
    subprocess.run(cmd, check=True)
    _log("Dependencias instaladas com sucesso.")


def copy_item(src: Path, dst: Path) -> None:
    if src.is_dir():
        shutil.copytree(src, dst, dirs_exist_ok=True)
    else:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)


def install_scripts_to_tqs() -> None:
    if not SOURCE_DIR.exists():
        raise FileNotFoundError(f"Pasta de origem nao encontrada: {SOURCE_DIR}")

    TARGET_DIR.mkdir(parents=True, exist_ok=True)
    _log(f"Copiando conteudo de {SOURCE_DIR} para {TARGET_DIR}...")

    for item in SOURCE_DIR.iterdir():
        destination = TARGET_DIR / item.name
        copy_item(item, destination)
        _log(f"Copiado: {item.name}")

    _log("Copia concluida com sucesso.")


def main() -> int:
    try:
        install_pip_dependencies()
        install_scripts_to_tqs()
    except subprocess.CalledProcessError as exc:
        _log(f"Erro ao instalar dependencias: {exc}")
        return 1
    except Exception as exc:
        _log(f"Erro na instalacao: {exc}")
        return 1

    _log("Instalacao finalizada.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
