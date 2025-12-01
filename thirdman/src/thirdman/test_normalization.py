#!/usr/bin/env python3
"""Test script to regenerate the asset catalog and verify normalized MJCFs."""

from pathlib import Path
import mujoco
from asset_catalog import load_asset_catalog


def main():
    print("Regenerating asset catalog with normalization...")
    catalog = load_asset_catalog()
    
    print(f"\nTotal assets in catalog: {len(catalog)}")
    
    # Count by type
    mjcf_count = sum(1 for r in catalog.values() if r["match_substring"] == "MJCF_PATH")
    urdf_count = sum(1 for r in catalog.values() if r["match_substring"] == "URDF_PATH")
    mesh_count = sum(1 for r in catalog.values() if r["match_substring"] == "MESH_PATHS")
    
    print(f"  MJCF_PATH: {mjcf_count}")
    print(f"  URDF_PATH: {urdf_count}")
    print(f"  MESH_PATHS: {mesh_count}")
    
    # Test loading a few normalized MJCFs
    print("\nTesting normalized MJCFs...")
    test_count = 0
    success_count = 0
    
    for name, record in catalog.items():
        if record["match_substring"] in ("MJCF_PATH", "URDF_PATH"):
            if test_count >= 5:  # Test first 5
                break
            
            test_count += 1
            mjcf_path = Path(record["path"])  # Paths are now absolute
            
            print(f"\n  Testing: {name}")
            print(f"    Path: {mjcf_path}")
            
            if not mjcf_path.exists():
                print(f"    ERROR: File does not exist!")
                continue
            
            try:
                model = mujoco.MjModel.from_xml_path(filename=str(mjcf_path))
                print(f"    ✓ Successfully loaded! ({model.nbody} bodies, {model.ngeom} geoms)")
                success_count += 1
            except Exception as e:
                print(f"    ERROR: {e}")
    
    print(f"\n\nSummary: {success_count}/{test_count} test MJCFs loaded successfully")
    
    # Show some example catalog entries
    print("\n\nExample catalog entries:")
    for i, (name, record) in enumerate(catalog.items()):
        if i >= 5:
            break
        print(f"  {name}")
        print(f"    path: {record['path']}")
        print(f"    type: {record['match_substring']}")


if __name__ == "__main__":
    main()

