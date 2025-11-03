import torch

original_load = torch.load


def load_with_weights_only_false(*args, **kwargs):
    kwargs.setdefault("weights_only", False)
    return original_load(*args, **kwargs)


torch.load = load_with_weights_only_false


from autogluon.multimodal import MultiModalPredictor


train_path = "/home/pino/github/sillypoint/firstslip/data/defect_detect/originals/_annotations.coco.json"

predictor = MultiModalPredictor(problem_type="object_detection", sample_data_path=train_path)

predictor.fit(train_path)

predictor.fit_summary(verbosity=3)
