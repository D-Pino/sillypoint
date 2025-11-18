import argparse
from pathlib import Path

from ultralytics import YOLO


DEFAULT_MODEL = "yolo11n.pt"


def finetune_yolo(data_dir: str) -> None:
    dataset_dir = Path(data_dir).expanduser().resolve()
    yaml_path = dataset_dir / "dataset.yaml"
    if not yaml_path.exists():
        raise FileNotFoundError(f"dataset.yaml not found at {yaml_path}. Run prep_data.py first.")

    runs_dir = Path(__file__).parent / "train_runs"
    runs_dir.mkdir(parents=True, exist_ok=True)
    run_idx = (
        max([int(p.name.split("_")[-1]) for p in runs_dir.glob("run_*") if p.name.split("_")[-1].isdigit()] or [-1]) + 1
    )
    run_name = f"run_{run_idx}"

    model = YOLO(DEFAULT_MODEL)
    results = model.train(
        data=str(yaml_path),
        name=run_name,
        project=str(runs_dir),
        save=True,
        device=0,
        epochs=20,
        batch=16,
        imgsz=512,
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
