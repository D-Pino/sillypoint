import argparse

import mujoco
import mujoco.viewer


def main() -> None:
    parser = argparse.ArgumentParser(description="Launch a MuJoCo viewer for an existing XML scene file.")
    parser.add_argument(
        "xml_path",
        help="Path to a MuJoCo XML file to load and visualize.",
    )
    args = parser.parse_args()

    model = mujoco.MjModel.from_xml_path(filename=args.xml_path)
    data = mujoco.MjData(model)
    mujoco.viewer.launch(model=model, data=data)


if __name__ == "__main__":
    main()
