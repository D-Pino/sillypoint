from pathlib import Path

# Base paths
THIRDMAN_ROOT = Path(__file__).resolve().parents[2]
CACHE_DIR = Path.home() / ".cache"

# Robot and asset directories
ROBOTS_DIR = THIRDMAN_ROOT / "robots"
GLOBAL_ASSET_STORE = THIRDMAN_ROOT / "global_asset_store"
ROBOT_DESCRIPTIONS_DIR_ORIGINAL = CACHE_DIR / "robot_descriptions"

# Catalog
CATALOG_PATH = THIRDMAN_ROOT / "asset_catalog.json"

# Scene generation directories
GENERATED_SCENES_DIR = THIRDMAN_ROOT / "generated_scenes"
BASE_SCENE_PATH = THIRDMAN_ROOT / "base_scene.xml"

# Asset matching substrings for robot_descriptions harvesting
MATCH_SUBSTRINGS = ("MJCF_PATH", "MESH_PATHS")

