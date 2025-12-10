import argparse
from pathlib import Path

from ultralytics import YOLO


PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
DEFAULT_MODEL = "yolo11n.pt"
RUNS_DIR = PROJECT_ROOT / "data" / "defect_detect" / "runs"


def finetune_yolo(data_dir: str) -> None:
    dataset_yaml = Path(data_dir) / "dataset.yaml"
    if not dataset_yaml.exists():
        raise FileNotFoundError(f"dataset.yaml not found at {dataset_yaml}. Run prep_data.py first.")

    runs_dir = RUNS_DIR / "train_runs"
    runs_dir.mkdir(parents=True, exist_ok=True)
    run_idx = (
        max([int(p.name.split("_")[-1]) for p in runs_dir.glob("run_*") if p.name.split("_")[-1].isdigit()] or [-1]) + 1
    )
    run_name = f"run_{run_idx}"

    model = YOLO(DEFAULT_MODEL)
    results = model.train(
        data=dataset_yaml,
        epochs=20,
        batch=16,
        imgsz=512,
        device=0,
        project=str(runs_dir),
        name=run_name,
    )

    print(f"Training complete. Results saved to {runs_dir / run_name}")
    return results


def cli() -> None:
    parser = argparse.ArgumentParser(description="Fine-tune Ultralytics YOLO on a prepared dataset")
    parser.add_argument(
        "--data-dir",
        required=True,
        help="Dataset root containing dataset.yaml",
    )
    args = parser.parse_args()
    finetune_yolo(data_dir=args.data_dir)


if __name__ == "__main__":
    cli()
