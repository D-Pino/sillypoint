import argparse
from collections import Counter, defaultdict
import json
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import cv2
import numpy as np
from wonderwords import RandomWord


@dataclass
class DefectPatch:
    src_image_id: int
    src_annotation_id: int
    category_id: int
    patch: np.ndarray  # BGR
    mask: np.ndarray  # float32 in [0, 1], single channel


def _clip_rect(x: int, y: int, w: int, h: int, img_w: int, img_h: int) -> tuple[int, int, int, int]:
    x = max(0, x)
    y = max(0, y)
    w = max(0, min(w, img_w - x))
    h = max(0, min(h, img_h - y))
    return x, y, w, h


def _feather_mask(h: int, w: int) -> np.ndarray:
    """Create a ring-feather alpha mask.

    The interior (beyond `feather` pixels from the edge) is exactly 1.0,
    and only the outer band smoothly rolls off to 0. This avoids washing
    out the defect interior while still hiding seams at the boundary.
    """
    # Size-adaptive feather: ~5% of min dimension, clamped to [1, 8]
    feather = int(max(1, min(8, round(min(h, w) * 0.05))))

    # Distance transform requires 8-bit single channel with non-zero foreground
    # and zeros where distance should go to 0 (the edges).
    base = np.ones((h, w), dtype=np.uint8)
    base[0, :] = 0
    base[-1, :] = 0
    base[:, 0] = 0
    base[:, -1] = 0

    # Distance to nearest zero pixel (i.e., distance to the edge)
    dist = cv2.distanceTransform(base, distanceType=cv2.DIST_L2, maskSize=3)
    mask = dist / float(max(1, feather))
    # Clamp to [0, 1]; interior beyond `feather` becomes exactly 1
    mask = np.clip(mask, 0.0, 1.0)
    # Slight gamma to keep the band gentle without dimming the interior
    mask = mask.astype(np.float32) ** 0.9
    return mask


def _rotate_with_bounds(
    img: np.ndarray,
    angle_deg: float,
    border_mode: int = cv2.BORDER_REFLECT,
    border_value: tuple[int, int, int] | int = 0,
    interp: int = cv2.INTER_LINEAR,
) -> np.ndarray:
    if angle_deg % 360 == 0:
        return img
    (h, w) = img.shape[:2]
    (cX, cY) = (w / 2.0, h / 2.0)
    M = cv2.getRotationMatrix2D(center=(cX, cY), angle=float(angle_deg), scale=1.0)
    cos = abs(M[0, 0])
    sin = abs(M[0, 1])
    nW = int((h * sin) + (w * cos))
    nH = int((h * cos) + (w * sin))
    M[0, 2] += (nW / 2.0) - cX
    M[1, 2] += (nH / 2.0) - cY
    return cv2.warpAffine(
        src=img,
        M=M,
        dsize=(nW, nH),
        flags=interp,
        borderMode=border_mode,
        borderValue=border_value,
    )


def _alpha_blend(dst: np.ndarray, src: np.ndarray, mask: np.ndarray, x: int, y: int) -> None:
    h, w = src.shape[:2]
    roi = dst[y : y + h, x : x + w]
    if mask.ndim == 2:
        mask3 = np.dstack([mask, mask, mask])
    else:
        mask3 = mask
    blended = (src.astype(dtype=np.float32) * mask3 + roi.astype(dtype=np.float32) * (1.0 - mask3)).astype(
        dtype=np.uint8
    )
    dst[y : y + h, x : x + w] = blended


def _rand_name(existing: set[str]) -> str:
    rw = RandomWord()
    for _ in range(10_000):
        adj = rw.word(include_categories=["adjective"])
        noun = rw.word(include_categories=["noun"])
        name = f"{adj}_{noun}".replace(" ", "").lower()
        if name not in existing:
            return name
    # Fallback with counter if somehow exhausted
    n = 1
    while True:
        candidate = f"{name}_{n}"
        if candidate not in existing:
            return candidate
        n += 1


def load_coco_and_group(
    coco_json_path: Path,
) -> tuple[dict[str, Any], dict[int, dict[str, Any]], dict[int, list[dict[str, Any]]], dict[int, np.ndarray]]:
    with coco_json_path.open("r") as f:
        coco_data = json.load(f)
    base_dir = coco_json_path.parent

    images_meta = {im["id"]: im for im in coco_data.get("images", [])}
    annos_by_img = defaultdict(list)
    for ann in coco_data.get("annotations", []):
        annos_by_img[ann.get("image_id")].append(ann)

    images_bgr: dict[int, np.ndarray] = {}
    for img_id, meta in images_meta.items():
        img_path = base_dir / meta.get("file_name", "")
        if not img_path.exists():
            print(f"Warning: Image not found: {img_path}, skipping...")
            continue
        img = cv2.imread(filename=str(img_path))
        if img is None:
            print(f"Warning: Failed to read: {img_path}, skipping...")
            continue
        images_bgr[img_id] = img

    total_annotations = sum(len(anns) for anns in annos_by_img.values())
    print(f"Loaded {len(images_bgr)} images with {total_annotations} annotations")

    return coco_data, images_meta, annos_by_img, images_bgr


def build_patch_pool(
    images_bgr: dict[int, np.ndarray], annos_by_img: dict[int, list[dict[str, Any]]]
) -> list[DefectPatch]:
    pool: list[DefectPatch] = []
    for img_id, img in images_bgr.items():
        img_h, img_w = img.shape[:2]
        for ann in annos_by_img.get(img_id, []):
            # Just clip the bounding box to make sure it's in bounds
            x, y, w, h = ann.get("bbox", [0, 0, 0, 0])
            xi, yi, wi, hi = _clip_rect(x=int(x), y=int(y), w=int(w), h=int(h), img_w=img_w, img_h=img_h)
            if wi <= 0 or hi <= 0:
                continue
            # Extract patch
            patch = img[yi : yi + hi, xi : xi + wi].copy()
            # Make mask
            mask = _feather_mask(h=hi, w=wi)
            pool.append(
                DefectPatch(
                    src_image_id=img_id,
                    src_annotation_id=int(ann.get("id", 0)),
                    category_id=int(ann.get("category_id", 0)),
                    patch=patch,
                    mask=mask,
                )
            )
    print(f"Built patch pool with {len(pool)} defect patches")
    return pool


def inpaint_backgrounds(
    images_bgr: dict[int, np.ndarray], annos_by_img: dict[int, list[dict[str, Any]]]
) -> dict[int, np.ndarray]:
    bgs: dict[int, np.ndarray] = {}
    for img_id, img in images_bgr.items():
        h, w = img.shape[:2]
        mask = np.zeros(shape=(h, w), dtype=np.uint8)
        for ann in annos_by_img.get(img_id, []):
            x, y, bw, bh = ann.get("bbox", [0, 0, 0, 0])
            xi, yi, wi, hi = _clip_rect(x=int(x), y=int(y), w=int(bw), h=int(bh), img_w=w, img_h=h)
            if wi <= 0 or hi <= 0:
                continue
            cv2.rectangle(img=mask, pt1=(xi, yi), pt2=(xi + wi, yi + hi), color=255, thickness=-1)
        # Simple Telea inpainting
        inpainted = cv2.inpaint(src=img, inpaintMask=mask, inpaintRadius=6, flags=cv2.INPAINT_TELEA)
        bgs[img_id] = inpainted
    print(f"Inpainted {len(bgs)} background images")
    return bgs


def build_manifest(
    coco_data: dict[str, Any],
    source_coco_path: str,
    images_meta: dict[int, dict[str, Any]],
    backgrounds: dict[int, np.ndarray],
    pool: list[DefectPatch],
    num_images: int,
    rng: random.Random,
    seed: int,
    run_name: str,
    same_source_only: bool,
    defects_per_image: int | None,
) -> dict[str, Any]:
    # Compute min/max defects per original image
    ann_counter = Counter(ann.get("image_id") for ann in coco_data.get("annotations", []))
    ann_counts = [ann_counter[img_id] for img_id in images_meta.keys()]
    # Use those to determine the range of defects per generated image
    min_k = (min(ann_counts) if ann_counts else 0) + 5
    max_k = (max(ann_counts) if ann_counts else 0) + 5

    bg_keys = list(backgrounds.keys())
    name_set = set()
    manifest_images: list[dict[str, Any]] = []
    defects_desc = f"{defects_per_image}" if defects_per_image is not None else f"{min_k}-{max_k}"
    print(f"Generating manifest for {num_images} images with {defects_desc} defects each")
    for _ in range(num_images):
        # Choose how many defects to place for this image
        k = defects_per_image if defects_per_image is not None else rng.randint(a=min_k, b=max_k)
        # Choose a random background image
        bg_img_id = rng.choice(seq=bg_keys)
        bg_meta = images_meta[bg_img_id]
        bg_file = bg_meta.get("file_name", "")
        bg_h, bg_w = backgrounds[bg_img_id].shape[:2]

        # Place the defects on the background image
        placements: list[dict[str, Any]] = []
        for __ in range(k):
            # Restrict to patches from the same source image as background if requested
            allowed_pool = pool if not same_source_only else [p for p in pool if p.src_image_id == bg_img_id]
            # Choose a random patch from the allowed pool
            patch_obj = rng.choice(seq=allowed_pool)
            # Choose a random rotation angle
            angle = rng.random() * 360.0
            # Rotate the patch to determine dimensions for placement
            # Use sharper resampling for the patch to keep detail
            rot_patch = _rotate_with_bounds(
                img=patch_obj.patch,
                angle_deg=angle,
                border_mode=cv2.BORDER_REFLECT,
                border_value=0,
                interp=cv2.INTER_LANCZOS4,
            )
            ph, pw = rot_patch.shape[:2]
            # Place the patch randomly on the background image
            x = rng.randint(a=0, b=bg_w - pw)
            y = rng.randint(a=0, b=bg_h - ph)
            placements.append(
                {
                    "src_image_id": patch_obj.src_image_id,
                    "src_annotation_id": patch_obj.src_annotation_id,
                    "category_id": patch_obj.category_id,
                    "rotation_deg": angle,
                    "x": x,
                    "y": y,
                    "w": int(pw),
                    "h": int(ph),
                }
            )

        name = _rand_name(existing=name_set)
        name_set.add(name)
        manifest_images.append(
            {
                "file_name": f"{name}.jpg",
                "background_file": bg_file,
                "background_image_id": bg_img_id,
                "placements": placements,
            }
        )

    manifest = {
        "meta": {
            "source_coco": source_coco_path,
            "categories": coco_data.get("categories", []),
            "backgrounds": [images_meta[i].get("file_name", "") for i in bg_keys],
            "seed": seed,
            "run_name": run_name,
            "same_source_only": same_source_only,
            "defects_per_image": defects_per_image,
        },
        "images": manifest_images,
    }
    return manifest


def execute_manifest(
    manifest: dict[str, Any],
    output_dir: Path,
    backgrounds: dict[int, np.ndarray],
    pool_by_key: dict[tuple[int, int], DefectPatch],
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)

    images_out: list[dict[str, Any]] = []
    annotations_out: list[dict[str, Any]] = []

    num_images_to_generate = len(manifest.get("images", []))
    print(f"Generating {num_images_to_generate} synthetic images...")

    # Compose images as specified
    image_id_counter = 0
    annotation_id_counter = 0
    for img_spec in manifest.get("images", []):
        # Get background image
        bg = backgrounds[img_spec.get("background_image_id")].copy()
        for placement_info in img_spec.get("placements", []):
            # Get patch from our pool
            key = (placement_info.get("src_image_id"), placement_info.get("src_annotation_id"))
            patch = pool_by_key.get(key)
            if patch is None:
                continue
            angle = placement_info.get("rotation_deg", 0.0)
            rot_patch = _rotate_with_bounds(
                img=patch.patch,
                angle_deg=angle,
                border_mode=cv2.BORDER_REFLECT,
                border_value=0,
                interp=cv2.INTER_LANCZOS4,
            )
            rot_mask = _rotate_with_bounds(
                img=patch.mask,
                angle_deg=angle,
                border_mode=cv2.BORDER_CONSTANT,
                border_value=0,
                interp=cv2.INTER_LINEAR,
            ).astype(dtype=np.float32)

            x, y = placement_info.get("x"), placement_info.get("y")
            _alpha_blend(dst=bg, src=rot_patch, mask=rot_mask, x=x, y=y)

        file_name = img_spec.get("file_name")
        out_path = output_dir / file_name
        cv2.imwrite(filename=str(out_path), img=bg)

        h, w = bg.shape[:2]
        images_out.append(
            {
                "id": image_id_counter,
                "license": 1,
                "file_name": file_name,
                "height": h,
                "width": w,
            }
        )

        for placement_info in img_spec.get("placements", []):
            annotations_out.append(
                {
                    "id": annotation_id_counter,
                    "image_id": image_id_counter,
                    "category_id": int(placement_info.get("category_id")),
                    "bbox": [
                        int(placement_info.get("x")),
                        int(placement_info.get("y")),
                        int(placement_info.get("w")),
                        int(placement_info.get("h")),
                    ],
                    "area": float(int(placement_info.get("w")) * int(placement_info.get("h"))),
                    "segmentation": [],
                    "iscrowd": 0,
                    "ignore": 0,
                }
            )
            annotation_id_counter += 1

        image_id_counter += 1

    coco_out = {
        "images": images_out,
        "annotations": annotations_out,
        "categories": manifest.get("meta", {}).get("categories", []),
    }
    print(f"Generated {len(images_out)} images with {len(annotations_out)} annotations")
    return coco_out


def generate_data(
    coco_json_path: str,
    output_dir: str | None,
    num_images: int,
    seed: int,
    plan_only: bool,
    same_source_only: bool,
    defects_per_image: int | None,
) -> None:
    coco_path = Path(coco_json_path)
    if not coco_path.exists():
        raise FileNotFoundError(f"COCO JSON file not found: {coco_json_path}")

    # Seed global RNGs for full reproducibility (including wonderwords)
    random.seed(seed)
    np.random.seed(seed)
    rng = random.Random(seed)

    coco_data, images_meta, annos_by_img, images_bgr = load_coco_and_group(coco_json_path=coco_path)

    # Compute pool and backgrounds
    pool = build_patch_pool(images_bgr=images_bgr, annos_by_img=annos_by_img)
    bgs = inpaint_backgrounds(images_bgr=images_bgr, annos_by_img=annos_by_img)

    # Create a deterministic random run directory under the chosen base output
    base_out_dir = Path(output_dir) if output_dir else (coco_path.parent.parent / "augmented")
    run_name = _rand_name(existing=set())
    run_dir = base_out_dir / run_name
    print(f"Output directory: {run_dir}")
    run_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = run_dir / "manifest.json"
    annotations_out_path = run_dir / "annotations_coco.json"

    manifest = build_manifest(
        coco_data=coco_data,
        source_coco_path=str(coco_path),
        images_meta=images_meta,
        backgrounds=bgs,
        pool=pool,
        num_images=num_images,
        rng=rng,
        seed=seed,
        run_name=run_name,
        same_source_only=same_source_only,
        defects_per_image=defects_per_image,
    )
    with manifest_path.open("w") as f:
        json.dump(manifest, f, indent=2)
    print(f"Saved manifest to {manifest_path}")

    if plan_only:
        return

    pool_by_key = {(p.src_image_id, p.src_annotation_id): p for p in pool}
    coco_out = execute_manifest(
        manifest=manifest,
        output_dir=run_dir,
        backgrounds=bgs,
        pool_by_key=pool_by_key,
    )
    with annotations_out_path.open("w") as f:
        json.dump(coco_out, f, indent=2)
    print(f"Saved synthetic images to {run_dir}")
    print(f"Saved COCO annotations to {annotations_out_path}")


def cli() -> None:
    parser = argparse.ArgumentParser(description="Synthetic defect data generator")
    parser.add_argument(
        "--coco-json-path",
        default="data/defect_detect/scales_cropped_out/_annotations.coco.json",
        help="Path to source COCO JSON",
    )
    parser.add_argument(
        "--output-dir",
        help="Directory to save synthetic images and annotations (default: <coco_dir>/../augmented)",
    )
    parser.add_argument(
        "--num-images", type=int, default=100, help="Number of synthetic images to generate (default: 100)"
    )
    parser.add_argument("--seed", type=int, default=2321, help="Random seed")
    parser.add_argument("--plan-only", action="store_true", help="Just create the manifest, no images")
    parser.add_argument(
        "--same-source-only",
        action="store_true",
        help="If set, only place defects from the same source image as the chosen background",
    )
    parser.add_argument(
        "--defects-per-image",
        type=int,
        help="If set, force this number of defects per generated image (default: random per image)",
    )

    args = parser.parse_args()
    generate_data(
        coco_json_path=args.coco_json_path,
        output_dir=args.output_dir,
        num_images=args.num_images,
        seed=args.seed,
        plan_only=args.plan_only,
        same_source_only=args.same_source_only,
        defects_per_image=args.defects_per_image,
    )


if __name__ == "__main__":
    cli()
