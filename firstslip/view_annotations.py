import fiftyone as fo
import fiftyone.types as fot

DATASET_NAME = "Defect Detect"
IMAGES_DIR = "data/defect_detect/images"
COCO_JSON = "data/defect_detect/annotations_coco.json"

if fo.dataset_exists(DATASET_NAME):
    fo.delete_dataset(DATASET_NAME)

dataset = fo.Dataset.from_dir(
    data_path=IMAGES_DIR,
    labels_path=COCO_JSON,
    dataset_type=fot.COCODetectionDataset,
    name=DATASET_NAME,
    include_id=True,
)

session = fo.launch_app(dataset, address="0.0.0.0", port=5151)
session.wait()
