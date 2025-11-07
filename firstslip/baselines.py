import argparse
from ultralytics import YOLO, SAM


def run_yolo(source: str) -> None:
    model = YOLO(model="yolo11x.pt")
    model.predict(source=source, imgsz=960, conf=0.25, device=0, save=True)


def run_sam2(source: str) -> None:
    model = SAM("sam2.1_b.pt")
    model.predict(
        source=source,
        imgsz=1536,
        device="cpu",  # too big for my GPU
        project="runs",
        name="sam2_min",
        save=True,
        exist_ok=True,
        verbose=True,
    )


def run_finetuned_yolo():
    model = YOLO(model="/home/pino/github/sillypoint/firstslip/run_1/weights/best.pt")
    metrics = model.val(
        data="/home/pino/github/sillypoint/firstslip/data/defect_detect/augmented/shiny_whirlwind/dataset.yaml",
        split="test",
        imgsz=640,
        save=True,
        plots=True
    )
    print(metrics)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run YOLO and SAM2 baselines")
    # parser.add_argument(
    #     "--source",
    #     required=True,
    #     help="Path to image/video file or directory",
    # )
    # args = parser.parse_args()
    # run_yolo(source=args.source)
    # run_sam2(source=args.source)
    run_finetuned_yolo()


if __name__ == "__main__":
    main()
