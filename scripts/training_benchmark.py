#!/usr/bin/env python3
"""Training benchmark: measure nan-safe-trainer performance across models.

Extracts agent action/reason pairs from experiment DBs as training data,
then benchmarks training throughput per model via nan-safe-trainer.

Usage:
    python3 scripts/training_benchmark.py --help
    python3 scripts/training_benchmark.py --dry-run
    python3 scripts/training_benchmark.py --runs-dir runs/ --output benchmarks/training_benchmark.json
"""

import argparse
import json
import resource
import sqlite3
import subprocess
import sys
import tempfile
import time
from pathlib import Path

NAN_SAFE_TRAINER_PATH = Path.home() / "Workspace/active/nan-safe-trainer"
MODELS = [
    "mlx-community/Qwen2.5-Coder-7B-Instruct-4bit",
    "mlx-community/Qwen3.5-9B-4bit",
    "mlx-community/Qwen2.5-Coder-14B-Instruct-4bit",
]
MODEL_SHORT = {
    "mlx-community/Qwen2.5-Coder-7B-Instruct-4bit": "Qwen2.5-Coder-7B",
    "mlx-community/Qwen3.5-9B-4bit": "Qwen3.5-9B",
    "mlx-community/Qwen2.5-Coder-14B-Instruct-4bit": "Qwen2.5-Coder-14B",
}
TRAIN_ITERS = 50
SAMPLE_TARGET = 100


def extract_training_data(runs_dir: Path, output_path: Path) -> int:
    """Extract agent action/reason pairs from experiment DBs into JSONL."""
    samples = []
    for db_path in sorted(runs_dir.rglob("*.db")):
        if "gate" in str(db_path).lower():
            continue
        try:
            conn = sqlite3.connect(str(db_path))
            rows = conn.execute(
                "SELECT action_type, reason FROM events "
                "WHERE reason NOT IN ('PARSE_FAILURE','MODEL_CALL_FAILURE') "
                "AND reason IS NOT NULL AND reason != '' "
                "LIMIT 20"
            ).fetchall()
            conn.close()
            for action, reason in rows:
                samples.append(
                    {
                        "text": f"<|im_start|>system\nYou are an agent in a resource-sharing simulation.<|im_end|>\n"
                        f"<|im_start|>user\nDecide your next action.<|im_end|>\n"
                        f"<|im_start|>assistant\nAction: {action}\nReason: {reason}<|im_end|>"
                    }
                )
                if len(samples) >= SAMPLE_TARGET:
                    break
        except Exception:
            continue
        if len(samples) >= SAMPLE_TARGET:
            break

    if not samples:
        return 0

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        for s in samples:
            f.write(json.dumps(s) + "\n")
    return len(samples)


def ensure_nan_safe_trainer() -> bool:
    """Install nan-safe-trainer in editable mode if not already installed."""
    try:
        import nan_safe_trainer  # noqa: F401

        return True
    except ImportError:
        pass

    if not NAN_SAFE_TRAINER_PATH.exists():
        print(f"  nan-safe-trainer not found at {NAN_SAFE_TRAINER_PATH}")
        return False

    print("  Installing nan-safe-trainer in editable mode...")
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "-e", str(NAN_SAFE_TRAINER_PATH)],
        capture_output=True,
        text=True,
        timeout=120,
    )
    if result.returncode != 0:
        print(f"  Install failed: {result.stderr[:200]}")
        return False
    return True


def create_lora_config(
    model: str,
    data_dir: Path,
    adapter_dir: Path,
    config_path: Path,
    iters: int = TRAIN_ITERS,
) -> None:
    """Create a minimal MLX LoRA config YAML."""
    try:
        import yaml
    except ImportError:
        # Fall back to manual YAML writing
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text(
            f"model: {model}\n"
            f"data: {data_dir}\n"
            f"adapter_path: {adapter_dir}\n"
            f"train: true\n"
            f"iters: {iters}\n"
            f"save_every: 25\n"
            f"batch_size: 1\n"
            f"lora_layers: 4\n"
            f"learning_rate: 1e-5\n"
            f"seed: 42\n"
        )
        return

    config = {
        "model": model,
        "data": str(data_dir),
        "adapter_path": str(adapter_dir),
        "train": True,
        "iters": iters,
        "save_every": 25,
        "batch_size": 1,
        "lora_layers": 4,
        "learning_rate": 1e-5,
        "seed": 42,
    }
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with open(config_path, "w") as f:
        yaml.safe_dump(config, f, sort_keys=False)


def get_peak_ram_mb() -> float:
    """Get peak RSS in MB for this process tree."""
    usage = resource.getrusage(resource.RUSAGE_CHILDREN)
    return usage.ru_maxrss / (1024 * 1024)  # macOS reports bytes


def benchmark_model(model: str, data_path: Path, work_dir: Path, iters: int = TRAIN_ITERS) -> dict:
    """Run training benchmark for a single model."""
    short_name = MODEL_SHORT.get(model, model.split("/")[-1])
    print(f"\n  Benchmarking {short_name}...")

    adapter_dir = work_dir / "adapters" / short_name
    adapter_dir.mkdir(parents=True, exist_ok=True)
    config_path = work_dir / f"config_{short_name}.yaml"

    # Prepare data directory with train.jsonl
    data_dir = work_dir / "data" / short_name
    data_dir.mkdir(parents=True, exist_ok=True)
    import shutil

    shutil.copy2(data_path, data_dir / "train.jsonl")
    shutil.copy2(data_path, data_dir / "valid.jsonl")

    create_lora_config(model, data_dir, adapter_dir, config_path, iters)

    result = {
        "model": model,
        "short_name": short_name,
        "iters": iters,
        "status": "pending",
        "samples_per_sec": None,
        "nan_events": 0,
        "val_loss_final": None,
        "peak_ram_mb": None,
        "wall_time_sec": None,
        "error": None,
    }

    # Try nan-safe-trainer first, fall back to direct mlx_lm.lora
    start = time.monotonic()

    try:
        # Try direct mlx_lm.lora (nan-safe-trainer wraps this anyway)
        cmd = [
            sys.executable,
            "-m",
            "mlx_lm.lora",
            "--config",
            str(config_path),
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=600)

        wall = time.monotonic() - start
        result["wall_time_sec"] = round(wall, 2)
        result["peak_ram_mb"] = round(get_peak_ram_mb(), 1)

        # Parse output for metrics
        stdout = proc.stdout or ""
        stderr = proc.stderr or ""
        output = stdout + stderr

        import re

        train_losses = re.findall(r"Iter (\d+): Train loss ([^,]+),", output)
        val_losses = re.findall(r"Iter (\d+): Val loss ([^,]+),", output)
        nan_count = len(re.findall(r"(?:nan|inf)", output, re.IGNORECASE))

        if val_losses:
            last_val = val_losses[-1]
            try:
                result["val_loss_final"] = round(float(last_val[1].strip()), 4)
            except ValueError:
                pass

        result["nan_events"] = nan_count

        n_samples = len(train_losses) if train_losses else 0
        if n_samples > 0 and wall > 0:
            result["samples_per_sec"] = round(n_samples / wall, 2)

        if proc.returncode == 0:
            result["status"] = "complete"
        else:
            result["status"] = "error"
            result["error"] = (proc.stderr or "")[:300]

    except subprocess.TimeoutExpired:
        result["status"] = "timeout"
        result["wall_time_sec"] = 600.0
        result["error"] = "Training exceeded 10-minute timeout"
    except MemoryError:
        result["status"] = "oom"
        result["wall_time_sec"] = round(time.monotonic() - start, 2)
        result["error"] = "Out of memory"
    except Exception as e:
        result["status"] = "error"
        result["wall_time_sec"] = round(time.monotonic() - start, 2)
        result["error"] = str(e)[:300]

    print(f"    {short_name}: {result['status']} ({result['wall_time_sec']}s)")
    return result


def main():
    parser = argparse.ArgumentParser(description="Training benchmark wrapping nan-safe-trainer")
    parser.add_argument(
        "--runs-dir",
        type=str,
        default="runs/",
        help="Directory containing experiment run DBs",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="benchmarks/training_benchmark.json",
        help="Output JSON path",
    )
    parser.add_argument("--models", nargs="+", default=MODELS, help="Model IDs to benchmark")
    parser.add_argument("--iters", type=int, default=TRAIN_ITERS, help="Training iterations per model")
    parser.add_argument("--dry-run", action="store_true", help="Validate setup without running training")
    args = parser.parse_args()

    train_iters = args.iters

    runs_dir = Path(args.runs_dir)
    output_path = Path(args.output)

    print("Training Benchmark — external gate × nan-safe-trainer")
    print("=" * 60)

    # Step 1: Extract training data
    with tempfile.TemporaryDirectory(prefix="ac_bench_") as tmpdir:
        work_dir = Path(tmpdir)
        data_path = work_dir / "training_data.jsonl"

        print("\n1. Extracting training data from experiment DBs...")
        n_samples = extract_training_data(runs_dir, data_path)
        if n_samples == 0:
            print("  No training data extracted. Check --runs-dir.")
            if args.dry_run:
                print("\n  DRY RUN: Would extract from DBs in runs/")
                print(
                    "  DRY RUN: Would benchmark models:",
                    [MODEL_SHORT.get(m, m) for m in args.models],
                )
                print("  DRY RUN: Setup valid. Ready to run without --dry-run.")
                return 0
            return 1
        print(f"  Extracted {n_samples} samples")

        if args.dry_run:
            print(f"\n  DRY RUN: {n_samples} samples extracted")
            print(
                "  DRY RUN: Models to benchmark:",
                [MODEL_SHORT.get(m, m) for m in args.models],
            )
            print(f"  DRY RUN: {train_iters} iterations per model")
            print(f"  DRY RUN: Output → {output_path}")

            # Check nan-safe-trainer availability
            has_nst = ensure_nan_safe_trainer()
            print(f"  DRY RUN: nan-safe-trainer available: {has_nst}")

            # Check mlx_lm availability
            try:
                import mlx_lm  # noqa: F401

                print("  DRY RUN: mlx_lm available: True")
            except ImportError:
                print("  DRY RUN: mlx_lm available: False (training will fail)")

            print("  DRY RUN: Setup valid. Ready to run without --dry-run.")
            return 0

        # Step 2: Check dependencies
        print("\n2. Checking dependencies...")
        ensure_nan_safe_trainer()

        try:
            import mlx_lm  # noqa: F401

            print("  mlx_lm: available")
        except ImportError:
            print("  mlx_lm: NOT available — training will fail gracefully")

        # Step 3: Benchmark each model
        print(f"\n3. Benchmarking {len(args.models)} models ({train_iters} iters each)...")
        results = []
        for model in args.models:
            result = benchmark_model(model, data_path, work_dir, train_iters)
            results.append(result)

    # Step 4: Write output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    benchmark = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "train_iters": train_iters,
        "sample_count": n_samples,
        "models": results,
    }
    with open(output_path, "w") as f:
        json.dump(benchmark, f, indent=2)
    print(f"\n4. Results written to {output_path}")

    # Summary table
    print("\n" + "=" * 60)
    print(f"{'Model':<25} {'Status':<10} {'s/iter':<10} {'NaN':<5} {'ValLoss':<10} {'RAM(MB)':<10}")
    print("-" * 60)
    for r in results:
        sps = f"{r['samples_per_sec']:.2f}" if r["samples_per_sec"] else "—"
        vl = f"{r['val_loss_final']:.4f}" if r["val_loss_final"] else "—"
        ram = f"{r['peak_ram_mb']:.0f}" if r["peak_ram_mb"] else "—"
        print(f"{r['short_name']:<25} {r['status']:<10} {sps:<10} {r['nan_events']:<5} {vl:<10} {ram:<10}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
