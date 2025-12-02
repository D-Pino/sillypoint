import importlib
import json
import pkgutil
import re
import shutil
from pathlib import Path

import mujoco
import robot_descriptions
from lxml import etree

from thirdman.common import (
    CATALOG_PATH,
    GLOBAL_ASSET_STORE,
    MATCH_SUBSTRINGS,
    ROBOT_DESCRIPTIONS_DIR_ORIGINAL,
    ROBOTS_DIR,
)


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
    for root_dir in ROBOT_DESCRIPTIONS_DIR_ORIGINAL.iterdir():
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
    raise NotImplementedError("This function is not implemented yet")
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

    # Compute output path: mirror original location but in ROBOTS_DIR
    rel_to_cache = urdf_path.relative_to(ROBOT_DESCRIPTIONS_DIR_ORIGINAL)
    out_path = ROBOTS_DIR / rel_to_cache.parent / f"{urdf_path.stem}.xml"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Convert URDF to MJCF
    model = mujoco.MjModel.from_xml_path(str(preprocessed_urdf))
    mujoco.mj_saveLastXML(str(out_path), model)

    # Clean up temporary file if created
    if preprocessed_urdf != urdf_path:
        preprocessed_urdf.unlink()

    return out_path


"""
This work is kinda awkward. I've seen stuff like:

- scene.xml includes a component.xml
- component.xml sets meshdir with <compiler> (scene.xml does not)
- however, component.xml sets meshdir relative to scene.xml, because it knows it only exists to be included
- therefore, when individually considering either of these, I cant "find" the meshes properly, so neither of these will work in the final catalog

TODO: Find a way to figure out when an xml is just designed to be included. Start from the parent xml, and recursively figure out the "include"s so that
I can find all the meshes, and import these as independent assets. Maybe use mjcf parser itself? Maybe revamp everything to find a better way to split into "components"

"""


def normalize_mjcf(mjcf_path: Path) -> Path | None:
    """Normalize an MJCF file by centralizing assets and stripping compiler directory attributes"""

    # Get output path: we mirror the original location, but within new ROBOTS_DIR
    out_path = ROBOTS_DIR / mjcf_path.relative_to(ROBOT_DESCRIPTIONS_DIR_ORIGINAL)

    # Get compiler tag and its attributes
    tree = etree.parse(str(mjcf_path))
    root = tree.getroot()
    compiler = root.find("compiler")

    if compiler is not None:
        # If compiler tag exists, we need to find the references, copy them to the global asset store,
        # and remove the compiler attributes that reference directories that won't exist
        dir_attrs = ("meshdir", "texturedir", "assetdir")
        base_dir = mjcf_path.parent
        for attr_name in dir_attrs:
            attr_value = compiler.get(attr_name, "")
            if not attr_value:
                continue

            # Resolve the directory path
            attr_path = Path(attr_value)
            src_dir = attr_path if attr_path.is_absolute() else base_dir / attr_path

            # Skip if directory doesn't exist
            if not src_dir.exists():
                print(
                    f"Warning: {attr_name} directory not found: {src_dir}. It's possible this xml is designed explicitly"
                    "to be included, and the writer specified a directory that only makes sense relative to the real scene"
                    "definition, and hence doesn't make sense as we consider this a standalone asset."
                )
                return None

            # Copy all files from source directory to global asset store
            # preserving relative paths from the source directory root
            for src_file in src_dir.rglob("*"):
                if not src_file.is_file():
                    continue

                dest_file = GLOBAL_ASSET_STORE / src_file.relative_to(src_dir)
                if dest_file.exists():
                    print(f"Warning: Asset collision! skipping: {dest_file} (source: {src_file})")
                    continue

                # Copy file to global asset store
                dest_file.parent.mkdir(parents=True, exist_ok=True)
                print(f"Copying {src_file} to {dest_file}")
                shutil.copy2(str(src_file), str(dest_file))

        # Strip compiler directory attributes from the XML
        for attr_name in dir_attrs:
            compiler.attrib.pop(attr_name, None)

    # Write the modified XML to new path
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
    ROBOTS_DIR.mkdir(parents=True, exist_ok=True)
    GLOBAL_ASSET_STORE.mkdir(parents=True, exist_ok=True)

    all_assets = dict()
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

    # Normalize MJCF and URDF assets
    normalized_assets = dict()
    for key, record in all_assets.items():
        match_substring = record["match_substring"]
        orig_path = Path(record["path"])

        if match_substring == "URDF_PATH" and orig_path.suffix.lower() == ".urdf":
            # Convert URDF to MJCF, then normalize
            print(f"Converting URDF: {orig_path.name}")
            mjcf_path = convert_urdf_to_mjcf(urdf_path=orig_path)
            if (normalized_path := normalize_mjcf(mjcf_path=mjcf_path)) is not None:
                normalized_assets[key] = {"path": str(normalized_path), "match_substring": match_substring}

        elif match_substring == "MJCF_PATH":
            # Normalize MJCF directly
            print(f"Normalizing MJCF: {orig_path.name}")
            if (normalized_path := normalize_mjcf(mjcf_path=orig_path)) is not None:
                normalized_assets[key] = {"path": str(normalized_path), "match_substring": match_substring}
        else:
            # Keep MESH_PATHS and other types as-is
            # TODO: Should I be copying these? Investigate the mesh paths
            normalized_assets[key] = record

    return dict(sorted(normalized_assets.items()))


def load_asset_catalog(force_rebuild: bool = False) -> dict[str, dict[str, str]]:
    """Load the cached asset catalog, building and saving it if needed."""

    if not force_rebuild and CATALOG_PATH.exists():
        with CATALOG_PATH.open(mode="r") as f:
            return json.load(fp=f)

    catalog = _build_catalog()
    with CATALOG_PATH.open(mode="w") as f:
        json.dump(obj=catalog, fp=f, indent=2, sort_keys=True)
    return catalog


if __name__ == "__main__":
    catalog = load_asset_catalog(force_rebuild=True)
    # print(catalog)
