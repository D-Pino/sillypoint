from lerobot.policies.smolvla.modeling_smolvla import SmolVLAPolicy
from lerobot.datasets.lerobot_dataset import LeRobotDataset
import torch


def main():
    print("Loading model...")
    policy = SmolVLAPolicy.from_pretrained("lerobot/smolvla_base")
    policy.eval()  # Sets model to evaluation mode
    print("Model loaded.")

    print("Loading dataset...")
    dataset = LeRobotDataset("lerobot/svla_so101_pickplace")
    print(f"Dataset loaded with {len(dataset)} samples loaded.")

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
