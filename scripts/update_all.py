from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT / "scripts"


def _run_step(label: str, script_name: str) -> None:
    script_path = SCRIPTS_DIR / script_name
    print(f"\n== {label} ==", flush=True)
    subprocess.run([sys.executable, str(script_path)], cwd=ROOT, check=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the World Cup predictor pipeline.")
    parser.add_argument(
        "--skip-build",
        action="store_true",
        help="Skip raw Excel ingestion and reuse committed processed CSV files.",
    )
    args = parser.parse_args()

    if not args.skip_build:
        _run_step("Datasets actualizados", "01_build_datasets.py")
    else:
        print("== Datasets actualizados ==", flush=True)
        print("SKIP raw Excel ingestion; reusing data/processed CSV files", flush=True)

    _run_step("Predicciones generadas", "02_generate_predictions.py")
    _run_step("Simulacion completada", "03_run_simulation.py")
    _run_step("Auditoria actualizada", "04_audit_results.py")
    _run_step("Outputs finales exportados", "03_export_outputs.py")

    print("\nPipeline completo", flush=True)
    print("OK datasets", flush=True)
    print("OK predicciones", flush=True)
    print("OK simulacion", flush=True)
    print("OK auditoria", flush=True)
    print("OK outputs", flush=True)


if __name__ == "__main__":
    main()
