import argparse
from pathlib import Path

from ultralytics import SAM, YOLO


PROJECT_ROOT = Path(__file__).parent.parent
DEFAULT_TEST_IMAGES = PROJECT_ROOT / "data" / "defect_detect" / "augmented" / "incompetent_gig" / "images" / "test"
DEFAULT_FINETUNED_WEIGHTS = PROJECT_ROOT / "finetune_yolo" / "runs" / "run_1" / "weights" / "best.pt"
DEFAULT_RUNS_DIR = PROJECT_ROOT / "runs"
EVALS_ROOT = PROJECT_ROOT / "finetune_yolo" / "eval_runs"


def run_yolo(
    source: str,
    conf: float = 0.25,
    project: Path = DEFAULT_RUNS_DIR,
    name: str = "yolo11_baseline",
) -> None:
    """Quick helper for vanilla YOLO11 experiments."""
    model = YOLO("yolo11x.pt")
    model.predict(
        source=source,
        conf=conf,
        imgsz=960,
        device="0",
        save=True,
        project=str(project),
        name=name,
        exist_ok=True,
    )


def run_sam2(
    source: str,
    project: Path = DEFAULT_RUNS_DIR,
    name: str = "sam2_min",
) -> None:
    """Runs SAM 2.1 base checkpoint to produce masks."""
    model = SAM("sam2.1_b.pt")
    model.predict(
        source=source,
        imgsz=1536,
        device="cpu",  # large checkpoint, keep CPU-safe by default
        project=str(project),
        name=name,
        save=True,
        exist_ok=True,
        verbose=False,
    )


def _next_eval_run_name() -> str:
    EVALS_ROOT.mkdir(parents=True, exist_ok=True)
    existing = [int(p.name.split("_")[-1]) for p in EVALS_ROOT.glob("eval_*") if p.name.split("_")[-1].isdigit()]
    next_idx = (max(existing) + 1) if existing else 0
    return f"eval_{next_idx}"


def run_finetuned_yolo(source: str, conf: float) -> None:
    run_name = _next_eval_run_name()
    model = YOLO(model=str(DEFAULT_FINETUNED_WEIGHTS))
    model.predict(
        source=source,
        conf=conf,
        imgsz=960,
        device="0",
        save=True,
        show_labels=False,
        line_width=2,
        project=str(EVALS_ROOT),
        name=run_name,
        exist_ok=True,
    )
    print(f"Saved predictions to {EVALS_ROOT / run_name}")


def cli() -> None:
    parser = argparse.ArgumentParser(description="Run finetuned YOLO baseline predictions")
    parser.add_argument(
        "--source",
        default=str(DEFAULT_TEST_IMAGES),
        help="Path to an image/video file or a directory. Defaults to the test split.",
    )
    parser.add_argument(
        "--conf",
        type=float,
        default=0.3,
        help="Confidence threshold for predictions.",
    )
    args = parser.parse_args()

    run_finetuned_yolo(source=args.source, conf=args.conf)


if __name__ == "__main__":
    cli()
