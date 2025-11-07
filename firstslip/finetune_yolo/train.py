import argparse
from pathlib import Path

from ultralytics import YOLO


def finetune_yolo(
    data_dir: str,
    model_name: str = "yolo11n.pt",
    epochs: int = 100,
    imgsz: int = 640,
    batch: int = 16,
    patience: int = 10,
    device: int = 0,
) -> None:
    dataset_dir = Path(data_dir).expanduser().resolve()
    yaml_path = dataset_dir / "dataset.yaml"
    if not yaml_path.exists():
        raise FileNotFoundError(f"dataset.yaml not found at {yaml_path}. Run prep_data.py first.")

    runs_dir = Path(__file__).parent / "yolo_finetune_runs"
    runs_dir.mkdir(parents=True, exist_ok=True)
    run_idx = (
        max(
            [int(p.name.split("_")[-1]) for p in runs_dir.glob("run_*") if p.name.split("_")[-1].isdigit()]
            or [-1]
        )
        + 1
    )
    run_name = f"run_{run_idx}"

    model = YOLO(model_name)
    results = model.train(
        data=str(yaml_path),
        epochs=epochs,
        imgsz=imgsz,
        batch=batch,
        name=run_name,
        project=str(runs_dir),
        patience=patience,
        save=True,
        device=device,
    )

    print(f"Training complete. Results saved to {runs_dir / run_name}")
    return results


def cli() -> None:
    parser = argparse.ArgumentParser(description="Fine-tune Ultralytics YOLO on a prepared dataset")
    parser.add_argument("--data-dir", required=True, help="Dataset root containing dataset.yaml")
    parser.add_argument("--model", default="yolo11n.pt", help="Pretrained YOLO weights to start from")
    parser.add_argument("--epochs", type=int, default=100, help="Training epochs")
    parser.add_argument("--imgsz", type=int, default=640, help="Training image size")
    parser.add_argument("--batch", type=int, default=16, help="Batch size")
    parser.add_argument("--patience", type=int, default=10, help="Early stopping patience")
    parser.add_argument("--device", type=int, default=0, help="Device id for training")
    args = parser.parse_args()
    finetune_yolo(
        data_dir=args.data_dir,
        model_name=args.model,
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        patience=args.patience,
        device=args.device,
    )


if __name__ == "__main__":
    cli()
