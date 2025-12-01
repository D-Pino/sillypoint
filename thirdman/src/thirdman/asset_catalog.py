import importlib
import json
import pkgutil
import re
import shutil
from pathlib import Path

import mujoco
import robot_descriptions
from lxml import etree


CATALOG_PATH = Path(__file__).resolve().parents[2] / "asset_catalog.json"
ASSET_ROOT = Path(__file__).resolve().parents[2] / "assets"
MATCH_SUBSTRINGS = ("MJCF_PATH", "URDF_PATH", "MESH_PATHS")
ROBOT_DESCRIPTIONS_CACHE = Path.home() / ".cache" / "robot_descriptions"


def _resolve_package_uri(package_uri: str, urdf_path: Path) -> str:
    """Resolve package:// URIs to actual file paths.
    
    Example: package://r2_description/meshes/file.dae
    """
    if not package_uri.startswith("package://"):
        return package_uri
    
    # Extract package name and relative path
    match = re.match(r"package://([^/]+)/(.+)", package_uri)
    if not match:
        return package_uri
    
    package_name, rel_path = match.groups()
    
    # Search for the package in robot_descriptions cache
    # The package directory is typically named <package_name> somewhere in the cache
    for root_dir in ROBOT_DESCRIPTIONS_CACHE.iterdir():
        if not root_dir.is_dir():
            continue
        
        # Look for the package directory
        for subdir in root_dir.rglob(package_name):
            if subdir.is_dir():
                resolved = subdir / rel_path
                if resolved.exists():
                    return str(resolved)
    
    # Fallback: try relative to URDF directory
    urdf_parent = urdf_path.parent
    potential_path = urdf_parent / rel_path
    if potential_path.exists():
        return str(potential_path)
    
    print(f"Warning: Could not resolve package URI: {package_uri}")
    return package_uri


def _preprocess_urdf(urdf_path: Path) -> Path:
    """Preprocess URDF to resolve package:// URIs before MuJoCo loads it."""
    with open(urdf_path, "r") as f:
        content = f.read()
    
    # Find all package:// URIs in mesh filename attributes
    pattern = r'filename="(package://[^"]+)"'
    
    def replace_uri(match):
        uri = match.group(1)
        resolved = _resolve_package_uri(uri, urdf_path)
        return f'filename="{resolved}"'
    
    modified_content = re.sub(pattern, replace_uri, content)
    
    # If no changes, return original
    if modified_content == content:
        return urdf_path
    
    # Write to temporary file
    temp_path = urdf_path.parent / f"{urdf_path.stem}_preprocessed.urdf"
    with open(temp_path, "w") as f:
        f.write(modified_content)
    
    return temp_path


def convert_urdf_to_mjcf(urdf_path: Path) -> Path:
    """Convert a URDF file to MJCF and save it mirroring the original structure."""
    # Preprocess to handle package:// URIs
    preprocessed_urdf = _preprocess_urdf(urdf_path)
    
    # Compute output path: mirror original location but in ASSET_ROOT
    rel_to_cache = urdf_path.relative_to(ROBOT_DESCRIPTIONS_CACHE)
    out_path = ASSET_ROOT / rel_to_cache.parent / f"{urdf_path.stem}.xml"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Convert URDF to MJCF
    model = mujoco.MjModel.from_xml_path(str(preprocessed_urdf))
    mujoco.mj_saveLastXML(str(out_path), model)
    
    # Clean up temporary file if created
    if preprocessed_urdf != urdf_path:
        preprocessed_urdf.unlink()
    
    return out_path


def normalize_mjcf(mjcf_path: Path) -> Path:
    """Normalize an MJCF file by copying assets and rewriting paths to absolute."""
    tree = etree.parse(str(mjcf_path))
    root = tree.getroot()
    
    if root.tag != "mujoco":
        raise ValueError(f"Expected <mujoco> root, got <{root.tag}>")
    
    base_dir = mjcf_path.parent
    
    # Read compiler directories
    compiler = root.find("compiler")
    meshdir = ""
    texturedir = ""
    assetdir = ""
    
    if compiler is not None:
        meshdir = compiler.get("meshdir", "")
        texturedir = compiler.get("texturedir", "")
        assetdir = compiler.get("assetdir", "")
    
    # Process asset elements
    asset_elem = root.find("asset")
    if asset_elem is not None:
        for tag in ("mesh", "texture", "skin", "hfield"):
            for elem in asset_elem.findall(tag):
                file_attr = elem.get("file")
                if not file_attr:
                    continue
                
                # Determine the source absolute path
                file_path = Path(file_attr)
                if file_path.is_absolute():
                    src_abs = file_path
                else:
                    # Choose appropriate directory based on element type
                    if tag == "mesh":
                        local_dir = meshdir or assetdir
                    elif tag == "texture":
                        local_dir = texturedir or assetdir
                    else:
                        local_dir = assetdir
                    
                    src_abs = base_dir / local_dir / file_attr
                
                # Skip if source doesn't exist
                if not src_abs.exists():
                    print(f"Warning: Asset not found: {src_abs}")
                    continue
                
                # Compute destination: mirror the structure from robot_descriptions cache
                if src_abs.is_relative_to(ROBOT_DESCRIPTIONS_CACHE):
                    rel_to_cache = src_abs.relative_to(ROBOT_DESCRIPTIONS_CACHE)
                    dest_abs = ASSET_ROOT / rel_to_cache
                else:
                    # If not in cache, put it in a generic location
                    dest_abs = ASSET_ROOT / "external" / src_abs.name
                
                # Copy the file
                dest_abs.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(str(src_abs), str(dest_abs))
                
                # Update the file attribute to absolute path
                elem.set("file", str(dest_abs))
    
    # Remove compiler asset directories (not needed with absolute paths)
    if compiler is not None:
        for attr in ("meshdir", "texturedir", "assetdir"):
            if attr in compiler.attrib:
                del compiler.attrib[attr]
    
    # Compute output path: mirror original location in ASSET_ROOT
    if mjcf_path.is_relative_to(ROBOT_DESCRIPTIONS_CACHE):
        rel_to_cache = mjcf_path.relative_to(ROBOT_DESCRIPTIONS_CACHE)
        out_path = ASSET_ROOT / rel_to_cache
    else:
        # If not in cache, put it in a generic location
        out_path = ASSET_ROOT / "external" / mjcf_path.name
    
    out_path.parent.mkdir(parents=True, exist_ok=True)
    tree.write(str(out_path), encoding="utf-8", xml_declaration=True, pretty_print=True)
    
    return out_path


def _resolve_asset_paths(
    submodule_name: str,
    attr_name: str,
    value: str | list[str],
    match_substring: str,
) -> dict[str, dict[str, str]]:
    """Return assets resolved from an attribute value with metadata."""

    if isinstance(value, list):
        candidate_paths = [p for p in value if isinstance(p, str)]
    elif isinstance(value, str):
        candidate_paths = [value]
    else:
        return {}

    assets = dict()
    for raw_path in candidate_paths:
        p = Path(raw_path)
        if p.is_dir():
            for entry in p.iterdir():
                key = f"{submodule_name}::{attr_name}::{p.name}::{entry.name}"
                assets[key] = {"path": str(entry), "match_substring": match_substring}
        else:
            key = f"{submodule_name}::{attr_name}::{p.name}"
            assets[key] = {"path": str(p), "match_substring": match_substring}

    return assets


def _build_catalog() -> dict[str, dict[str, str]]:
    all_assets = dict()
    
    ASSET_ROOT.mkdir(parents=True, exist_ok=True)

    for module_info in pkgutil.iter_modules(robot_descriptions.__path__):
        submodule_name = module_info.name
        if not submodule_name.endswith(("_description")):
            continue

        try:
            mod = importlib.import_module(name=f"robot_descriptions.{submodule_name}")
        except Exception:
            # Best-effort harvesting; just skip modules that fail to import
            print(f"Error importing {submodule_name}")
            continue

        for attr_name in dir(mod):
            match_substring = next((s for s in MATCH_SUBSTRINGS if s in attr_name), None)
            if match_substring is None:
                continue

            value = getattr(mod, attr_name, None)
            if value is None:
                continue

            all_assets.update(
                _resolve_asset_paths(
                    submodule_name=submodule_name,
                    attr_name=attr_name,
                    value=value,
                    match_substring=match_substring,
                )
            )
    
    # Post-process: normalize MJCF and URDF assets
    normalized_assets: dict[str, dict[str, str]] = {}
    
    for key, record in all_assets.items():
        match_substring = record["match_substring"]
        orig_path = Path(record["path"])
        
        try:
            if match_substring == "URDF_PATH" and orig_path.suffix.lower() == ".urdf":
                # Convert URDF to MJCF, then normalize
                print(f"Converting URDF: {orig_path.name}")
                mjcf_path = convert_urdf_to_mjcf(urdf_path=orig_path)
                normalized_path = normalize_mjcf(mjcf_path=mjcf_path)
                
                # Store absolute path to normalized MJCF
                normalized_assets[key] = {
                    "path": str(normalized_path),
                    "match_substring": match_substring,
                }
            
            elif match_substring == "MJCF_PATH":
                # Normalize MJCF directly
                print(f"Normalizing MJCF: {orig_path.name}")
                normalized_path = normalize_mjcf(mjcf_path=orig_path)
                
                # Store absolute path to normalized MJCF
                normalized_assets[key] = {
                    "path": str(normalized_path),
                    "match_substring": match_substring,
                }
            
            else:
                # Keep MESH_PATHS and other types as-is
                normalized_assets[key] = record
        
        except Exception as e:
            print(f"Error normalizing {key}: {e}")
            # Keep original on error
            normalized_assets[key] = record

    # Sort for determinism.
    return dict(sorted(normalized_assets.items()))


def load_asset_catalog() -> dict[str, dict[str, str]]:
    """Load the cached asset catalog, building and saving it if needed."""

    if CATALOG_PATH.exists():
        with CATALOG_PATH.open(mode="r") as f:
            return json.load(fp=f)

    catalog = _build_catalog()
    with CATALOG_PATH.open(mode="w") as f:
        json.dump(obj=catalog, fp=f, indent=2, sort_keys=True)
    return catalog


if __name__ == "__main__":
    catalog = load_asset_catalog()
    print(catalog)