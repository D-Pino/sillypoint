import json
import torch
from autogluon.multimodal import MultiModalPredictor

# Patch torch.load to avoid weights_only warning
original_load = torch.load


def load_with_weights_only_false(*args, **kwargs):
    kwargs.setdefault("weights_only", False)
    return original_load(*args, **kwargs)


torch.load = load_with_weights_only_false

# Load the trained model
predictor = MultiModalPredictor.load("/home/pino/github/sillypoint/ag/AutogluonModels/ag-20251101_150540")

# Load COCO annotations to get image paths
with open("/home/pino/github/sillypoint/firstslip/data/defect_detect/originals/_annotations.coco.json") as f:
    coco_data = json.load(f)

# Get image paths
image_files = [
    f"/home/pino/github/sillypoint/firstslip/data/defect_detect/{img['file_name']}" for img in coco_data["images"]
]

print(f"Found {len(image_files)} images\n")

# Run inference on each image
for img_path in image_files:
    print(f"Processing: {img_path}")
    predictions = predictor.predict(img_path)
    print(f"{predictions}\n")
