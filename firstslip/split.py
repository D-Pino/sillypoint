import argparse
import json
import random
import shutil
from pathlib import Path


def split_coco(coco_json_path: str, train_ratio: float, val_ratio: float, seed: int) -> None:
    coco_path = Path(coco_json_path)
    with coco_path.open("r") as f:
        coco = json.load(f)

    dataset_root = coco_path.parent
    images_root = dataset_root / "images"
    annotations_root = dataset_root / "annotations"
    images_root.mkdir(parents=True, exist_ok=True)
    annotations_root.mkdir(parents=True, exist_ok=True)

    images = coco["images"]
    annotations = coco["annotations"]
    categories = coco["categories"]

    ids = [im["id"] for im in images]
    random.seed(seed)
    random.shuffle(ids)

    n_total = len(ids)
    n_train = int(n_total * train_ratio)
    n_val = int(n_total * val_ratio)

    train_ids = set(ids[:n_train])
    val_ids = set(ids[n_train : n_train + n_val])
    test_ids = set(ids[n_train + n_val :])

    images_by_id = {im["id"]: im for im in images}

    splits = (("train", train_ids), ("val", val_ids), ("test", test_ids))
    for name, id_set in splits:
        split_image_dir = images_root / name
        split_image_dir.mkdir(parents=True, exist_ok=True)

        split_images = []
        for image_id in id_set:
            img_entry = images_by_id[image_id].copy()
            file_path = Path(img_entry["file_name"])
            img_entry["file_name"] = file_path.name
            split_images.append(img_entry)

            src = file_path if file_path.is_absolute() else dataset_root / file_path
            dst = split_image_dir / img_entry["file_name"]
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(src, dst)

        split_annotations = [a for a in annotations if a["image_id"] in id_set]

        out = {"images": split_images, "annotations": split_annotations, "categories": categories}
        with (annotations_root / f"{name}.json").open("w") as f:
            json.dump(out, f)

    print(f"Train images: {len(train_ids)}")
    print(f"Val images: {len(val_ids)}")
    print(f"Test images: {len(test_ids)}")
    print(f"Saved splits under {dataset_root / 'images'} and {dataset_root / 'annotations'}")


def cli():
    parser = argparse.ArgumentParser(description="Split COCO annotations into train/val/test")
    parser.add_argument(
        "--coco-json-path",
        required=True,
        help="Path to COCO JSON file",
    )
    parser.add_argument(
        "--train-ratio",
        type=float,
        default=0.8,
        help="Training set ratio (default: 0.8)",
    )
    parser.add_argument(
        "--val-ratio",
        type=float,
        default=0.1,
        help="Validation set ratio (default: 0.1)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=1337,
        help="Random seed (default: 1337)",
    )
    args = parser.parse_args()

    split_coco(
        coco_json_path=args.coco_json_path,
        train_ratio=args.train_ratio,
        val_ratio=args.val_ratio,
        seed=args.seed,
    )


if __name__ == "__main__":
    cli()
