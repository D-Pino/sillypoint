import argparse
from pathlib import Path

import mujoco
import mujoco.viewer


def main() -> None:
    parser = argparse.ArgumentParser(description="Launch a MuJoCo viewer for an existing XML scene file.")
    parser.add_argument(
        "xml_path",
        help="Path to a MuJoCo <mujoco>...</mujoco> XML file to load and visualize.",
    )
    args = parser.parse_args()

    xml_path = Path(args.xml_path)
    if not xml_path.is_file():
        raise SystemExit(f"XML file not found: {xml_path}")

    model = mujoco.MjModel.from_xml_path(filename=str(xml_path))
    data = mujoco.MjData(model)
    mujoco.viewer.launch(model=model, data=data)


if __name__ == "__main__":
    main()


