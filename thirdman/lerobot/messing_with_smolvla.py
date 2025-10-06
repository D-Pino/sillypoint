from lerobot.policies.factory import make_policy
from lerobot.policies.smolvla.configuration_smolvla import SmolVLAConfig
from lerobot.datasets.lerobot_dataset import LeRobotDataset
import torch


def main():

    # Can't get GPU working for some reason, dataset won't load tensors onto it
    # device = "cuda" if torch.cuda.is_available() else "cpu"
    device = "cpu"
    torch.set_default_device(device)
    print(f"Using device: {device}")

    # Load dataset
    print("Loading dataset...")
    dataset = LeRobotDataset("lerobot/svla_so101_pickplace")
    print("Dataset loaded")

    # I had to manually find the downloaded config file in the cache and remove the "type" field
    # TODO: Find the correct way to load this model
    print("Loading model...")
    svla_config = SmolVLAConfig.from_pretrained("lerobot/smolvla_base")
    policy = make_policy(cfg=svla_config, ds_meta=dataset.meta)
    policy.eval()  # Sets model to evaluation mode
    print("Model loaded.")

    num_samples = 10
    for i in range(num_samples):
        sample = dataset[i]

        # # Prepare observation for model ?
        # obs = {}

        # # Add image (use whichever camera is available)
        # if "observation.images.up" in sample:
        #     obs["observation.images.up"] = sample["observation.images.up"].unsqueeze(0)
        #     print(f"  Image shape: {obs['observation.images.up'].shape}")
        # elif "observation.images.side" in sample:
        #     obs["observation.images.side"] = sample["observation.images.side"].unsqueeze(0)
        #     print(f"  Image shape: {obs['observation.images.side'].shape}")

        # # Add state
        # obs["observation.state"] = sample["observation.state"].unsqueeze(0)

        # # Add instruction (use the task or a default)
        # obs["instruction"] = sample["task"] if isinstance(sample["task"], str) else "pick up the cube"

        with torch.no_grad():
            prediction = policy.select_action(sample)

        print(f"Sample {i + 1}/{num_samples}:")

        print(f"  Instruction: {sample['instruction']}")
        print(f"  Predicted Action: {prediction}")
        print("-" * 50)


if __name__ == "__main__":
    main()
