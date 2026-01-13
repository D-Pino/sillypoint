from lerobot.policies.smolvla.modeling_smolvla import SmolVLAPolicy
from lerobot.policies.smolvla.configuration_smolvla import SmolVLAConfig
from lerobot.datasets.lerobot_dataset import LeRobotDataset
from lerobot.utils.constants import OBS_LANGUAGE_TOKENS, OBS_LANGUAGE_ATTENTION_MASK
import torch


def main():
    device = "cpu"
    print(f"Using device: {device}")

    # Load dataset
    print("Loading dataset...")
    dataset = LeRobotDataset(repo_id="lerobot/svla_so101_pickplace")
    print("Dataset loaded.\n")

    # Load model
    print("Loading SmolVLA model...")
    config = SmolVLAConfig.from_pretrained(pretrained_name_or_path="lerobot/smolvla_base")
    policy = SmolVLAPolicy.from_pretrained("lerobot/smolvla_base", config=config)
    policy.to(device)
    policy.eval()
    print("Model loaded.\n")

    # Get tokenizer from model
    tokenizer = policy.model.vlm_with_expert.processor.tokenizer

    # Model overview
    print("=" * 60)
    print("MODEL OVERVIEW")
    print("=" * 60)
    print(f"Policy type: {type(policy).__name__}")
    print(f"Config type: {type(policy.config).__name__}")

    print("\n--- Config ---")
    print(f"  chunk_size: {policy.config.chunk_size}")
    print(f"  n_obs_steps: {policy.config.n_obs_steps}")
    print(f"  n_action_steps: {policy.config.n_action_steps}")
    print(f"  max_state_dim: {policy.config.max_state_dim}")
    print(f"  max_action_dim: {policy.config.max_action_dim}")
    print(f"  num_vlm_layers: {policy.config.num_vlm_layers}")
    print(f"  vlm_model_name: {policy.config.vlm_model_name}")

    total_params = sum(p.numel() for p in policy.parameters())
    trainable_params = sum(p.numel() for p in policy.parameters() if p.requires_grad)
    print("\n--- Parameters ---")
    print(f"  Total: {total_params:,}")
    print(f"  Trainable: {trainable_params:,}")

    # Run inference
    print("\n" + "=" * 60)
    print("INFERENCE")
    print("=" * 60)

    num_samples = 5
    for i in range(num_samples):
        sample = dataset[i]

        # Add batch dimension to tensors
        batch = {
            k: v.unsqueeze(0) if isinstance(v, torch.Tensor) else v
            for k, v in sample.items()
        }

        # Get instruction from 'task' field
        instruction = sample.get("task", "pick up the object")
        tokens = tokenizer(
            instruction,
            return_tensors="pt",
            padding="max_length",
            max_length=config.tokenizer_max_length,
            truncation=True,
        )
        batch[OBS_LANGUAGE_TOKENS] = tokens["input_ids"]
        batch[OBS_LANGUAGE_ATTENTION_MASK] = tokens["attention_mask"].bool()

        with torch.no_grad():
            prediction = policy.select_action(batch=batch)

        print(f"\nSample {i + 1}/{num_samples}:")
        print(f"  Instruction: {instruction}")
        print(f"  Predicted action shape: {prediction.shape}")
        print(f"  Predicted action: {prediction}")


if __name__ == "__main__":
    main()
