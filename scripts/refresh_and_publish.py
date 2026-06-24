"""One-command refresh: site real-stats sync + predictor pipeline + publish + push.

Replaces the manual runbook in README.md ("Proceso completo de actualizacion")
with a single command. Usage:

    python scripts/refresh_and_publish.py [--site-dir PATH] [--dry-run]

Steps, in order, any failure stops the run before anything is committed:
  1. Copy the latest mundial_fifa_2026_actualizado_*.xlsx /
     Estadisticas_ultimos20_*.xlsx from the site's _planning/Mundial_2026/
     into this repo's data/raw/.
  2. Run the site's own npm run sync:estadisticas (real stats, no model).
  3. Run this repo's ruff + pytest, then the full update_all.py pipeline.
  4. Commit + push this repo (--dry-run skips this). If the scheduled cron
     job here pushed in the meantime, retries by resetting to the new
     origin/main and regenerating, up to 3 times.
  5. Copy data/outputs/*.json into the site's src/data/mundial-2026/ --
     always the just-pushed version, even after a step-4 retry.
  6. npm run build in the site to confirm it compiles.
  7. Commit + push the site (--dry-run skips this).
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Callable

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SITE_DIR = ROOT.parent / "edgar-sierra"


def run(cmd: list[str], cwd: Path, label: str) -> None:
    print(f"\n== {label} ==", flush=True)
    subprocess.run(cmd, cwd=cwd, check=True)


def run_npm(script: str, cwd: Path, label: str) -> None:
    print(f"\n== {label} ==", flush=True)
    subprocess.run(f"npm run {script}", cwd=cwd, shell=True, check=True)


def latest_file(directory: Path, prefix: str) -> Path:
    matches = sorted(directory.glob(f"{prefix}*.xlsx"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not matches:
        raise FileNotFoundError(f"No '{prefix}*.xlsx' file found in {directory}.")
    return matches[0]


def copy_latest_excel_files(site_dir: Path) -> list[Path]:
    planning_dir = site_dir / "_planning" / "Mundial_2026"
    if not planning_dir.exists():
        raise FileNotFoundError(f"Missing {planning_dir} -- is --site-dir correct?")

    raw_dir = ROOT / "data" / "raw"
    copied = []
    for prefix in ("mundial_fifa_2026_actualizado_", "Estadisticas_ultimos20_"):
        source = latest_file(planning_dir, prefix)
        destination = raw_dir / source.name
        shutil.copyfile(source, destination)
        copied.append(destination)
        print(f"  copiado: {source.name}")
    return copied


def publish_outputs_to_site(site_dir: Path) -> None:
    outputs_dir = ROOT / "data" / "outputs"
    site_data_dir = site_dir / "src" / "data" / "mundial-2026"
    for output_file in outputs_dir.glob("*.json"):
        shutil.copyfile(output_file, site_data_dir / output_file.name)
        print(f"  publicado: {output_file.name}")


def git_commit_and_push(
    repo_dir: Path,
    paths: list[str],
    message: str,
    dry_run: bool,
    regenerate: Callable[[], None] | None = None,
    max_attempts: int = 3,
) -> bool:
    """Commit + push paths in repo_dir.

    The scheduled GitHub Action in this repo can push to main between this
    script's commit and its push (it ran mid-run once already). If push is
    rejected as non-fast-forward, the generated files in `paths` are fully
    reproducible from data/raw + data/processed, so the safe recovery is:
    fetch, hard-reset to the new origin/main, regenerate, and retry the
    commit+push -- never a manual merge of machine-generated CSV/JSON.
    `regenerate` is only needed for repos where paths are produced by a
    pipeline step (the predictor); the site has nothing to regenerate here
    since it was already copied/built before this is called.
    """
    status = subprocess.run(
        ["git", "status", "--porcelain", *paths], cwd=repo_dir, check=True, capture_output=True, text=True
    )
    if not status.stdout.strip():
        print(f"  {repo_dir.name}: sin cambios, no hay nada que commitear.")
        return False

    if dry_run:
        print(f"  {repo_dir.name}: --dry-run, deja los cambios sin commitear:")
        print(status.stdout)
        return True

    for attempt in range(1, max_attempts + 1):
        subprocess.run(["git", "add", *paths], cwd=repo_dir, check=True)
        subprocess.run(["git", "commit", "-m", message], cwd=repo_dir, check=True)
        push = subprocess.run(["git", "push", "origin", "main"], cwd=repo_dir, capture_output=True, text=True)
        if push.returncode == 0:
            print(f"  {repo_dir.name}: commiteado y pusheado.")
            return True

        if "rejected" not in push.stderr or attempt == max_attempts:
            print(push.stderr)
            raise RuntimeError(f"git push fallo en {repo_dir.name} (intento {attempt}/{max_attempts}).")
        if regenerate is None:
            print(push.stderr)
            raise RuntimeError(f"git push rechazado en {repo_dir.name} y no hay forma de regenerar para reintentar.")

        print(f"  {repo_dir.name}: push rechazado (otra corrida pusheo primero), reintentando ({attempt}/{max_attempts})...")
        subprocess.run(["git", "fetch", "origin"], cwd=repo_dir, check=True)
        subprocess.run(["git", "reset", "--hard", "origin/main"], cwd=repo_dir, check=True)
        regenerate()

    return False


def main() -> None:
    parser = argparse.ArgumentParser(description="Refresh stats + model outputs and publish to edgarsierra.com.")
    parser.add_argument("--site-dir", type=Path, default=DEFAULT_SITE_DIR, help="Ruta local de edgarsierra.com.")
    parser.add_argument("--dry-run", action="store_true", help="Corre todo pero no commitea ni pushea.")
    args = parser.parse_args()

    site_dir = args.site_dir.resolve()
    if not site_dir.exists():
        raise FileNotFoundError(f"No existe {site_dir}. Pasa --site-dir si edgarsierra.com no esta en esa ruta.")

    print("== Copiando Excel mas reciente al predictor ==", flush=True)
    copy_latest_excel_files(site_dir)

    run_npm("sync:estadisticas", site_dir, "Capa 1: estadisticas reales (edgarsierra.com)")

    def run_predictor_pipeline() -> None:
        run([sys.executable, "-m", "ruff", "check", "."], ROOT, "ruff (predictor)")
        run([sys.executable, "-m", "pytest", "-q"], ROOT, "pytest (predictor)")
        run([sys.executable, "scripts/update_all.py"], ROOT, "Capa 2: pipeline completo (predictor)")

    run_predictor_pipeline()

    predictor_changed = git_commit_and_push(
        ROOT,
        ["data/processed", "data/outputs", "data/frozen", "data/raw/resultados_nuevos.csv", "src/config.py"],
        "chore: refresh model outputs via refresh_and_publish.py",
        args.dry_run,
        regenerate=run_predictor_pipeline,
    )

    print("\n== Publicando outputs del predictor al sitio ==", flush=True)
    publish_outputs_to_site(site_dir)

    run_npm("build", site_dir, "Build de edgarsierra.com")

    site_changed = git_commit_and_push(
        site_dir,
        ["src/data/mundial-2026"],
        "chore: sync World Cup data via refresh_and_publish.py",
        args.dry_run,
    )

    print("\nListo.")
    print(f"  predictor: {'actualizado' if predictor_changed else 'sin cambios'}")
    print(f"  sitio: {'actualizado' if site_changed else 'sin cambios'}")


if __name__ == "__main__":
    main()
