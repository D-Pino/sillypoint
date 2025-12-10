import argparse
from enum import Enum
from pathlib import Path

from ultralytics import YOLO


PROJECT_ROOT = Path(__file__).parent.parent.parent
DEFAULT_FINETUNED_WEIGHTS = PROJECT_ROOT / "data" / "defect_detect" / "best.pt"
RUNS_DIR = PROJECT_ROOT / "data" / "defect_detect" / "runs"


class ModelChoice(str, Enum):
    baseline = "baseline"
    finetuned = "finetuned"


MODEL_WEIGHTS: dict[ModelChoice, str] = {
    ModelChoice.baseline: "yolo11x.pt",
    ModelChoice.finetuned: str(DEFAULT_FINETUNED_WEIGHTS),
}


def run_eval(model_choice: ModelChoice, data_dir: str, conf: float) -> None:
    dataset_yaml = Path(data_dir) / "dataset.yaml"
    weights = MODEL_WEIGHTS[model_choice]
    model = YOLO(model=weights)
    _ = model.val(
        data=dataset_yaml,
        imgsz=512,
        batch=1,
        save_json=True,
        conf=conf,
        device=0,
        plots=True,
        split="test",
        project=RUNS_DIR,
        name=f"eval_{model_choice}_{Path(data_dir).name}_{conf}",
        verbose=True,
        save_txt=True,
        save_conf=True,
    )


def run_predict(model_choice: ModelChoice, data_dir: str, conf: float) -> None:
    weights = MODEL_WEIGHTS[model_choice]
    model = YOLO(model=weights)
    _ = model.predict(
        source=data_dir,
        conf=conf,
        device=0,
        project=RUNS_DIR,
        name=f"predict_{model_choice}_{Path(data_dir).name}_{conf}",
        save=True,
        save_txt=True,
        save_conf=True,
        show_labels=False,
        show_conf=False,
    )


def cli() -> None:
    parser = argparse.ArgumentParser(description="Evaluate or predict with YOLO model")
    parser.add_argument(
        "--model",
        type=ModelChoice,
        choices=list(ModelChoice),
        default=ModelChoice.baseline,
        help="Which model to use: 'baseline' (YOLO11x) or 'finetuned'.",
    )
    parser.add_argument(
        "--conf",
        type=float,
        default=0.7,
        help="Confidence threshold for predictions.",
    )
    parser.add_argument(
        "--data-dir",
        help="Dataset root containing dataset.yaml (for eval mode)",
    )

    args = parser.parse_args()
    run_predict(
        model_choice=args.model,
        data_dir=args.data_dir,
        conf=args.conf,
    )

    # blur_levels = [3, 5, 7, 9, 13]
    conf_levels = [0.3, 0.5, 0.7, 0.9, 1.0]

    # for blur in blur_levels:
    #     blur_dir = Path(args.data_dir) / f"test_blurred_{blur}"
    for conf in conf_levels:
        run_predict(
            model_choice=args.model,
            data_dir=args.data_dir,
            conf=conf,
        )

    # run_eval(model_choice=args.model, data_dir=args.data_dir, conf=args.conf)


if __name__ == "__main__":
    cli()
