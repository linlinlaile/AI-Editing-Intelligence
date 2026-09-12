"""One pinned CPU classifier. Weights must already exist; no network paths."""
import hashlib
from importlib.metadata import version
from io import BytesIO
from pathlib import Path

from aei.ports.vision_model import Prediction
from aei.adapters.vision.images import decode_image

MODEL_NAME = "torchvision/resnet18"
WEIGHT_REVISION = "IMAGENET1K_V1"
WEIGHT_SHA256 = "f37072fd47e89c5e827621c5baffa7500819f7896bbacec160b1a16c560e07ec"
PRODUCER_REF = f"{MODEL_NAME}@{WEIGHT_REVISION}:sha256:{WEIGHT_SHA256}:torchvision-0.23.0:rgb-cpu-v1"
TAXONOMY = "imagenet-1k:torchvision-0.23.0"


class ResNet18VisionModel:
    producer_ref = PRODUCER_REF
    taxonomy = TAXONOMY

    def __init__(self, weights_path: str | Path):
        # Read once so hash verification and deserialization use the same bytes.
        weights = Path(weights_path).read_bytes()
        if hashlib.sha256(weights).hexdigest() != WEIGHT_SHA256:
            raise ValueError("ResNet18 weight SHA-256 does not match pinned revision")
        for package, expected in (("torch", "2.8.0"), ("torchvision", "0.23.0")):
            if version(package).split("+")[0] != expected:
                raise RuntimeError(f"{package}=={expected} is required by this producer revision")
        import torch
        from torchvision.models import ResNet18_Weights, resnet18

        self._torch = torch
        # weights=None is essential: torchvision must never fetch pretrained weights.
        self._network = resnet18(weights=None)
        self._network.load_state_dict(torch.load(BytesIO(weights), map_location="cpu", weights_only=True))
        self._network.eval()
        self._preprocess = ResNet18_Weights.IMAGENET1K_V1.transforms()
        self._labels = tuple(ResNet18_Weights.IMAGENET1K_V1.meta["categories"])

    def predict(self, image_bytes: bytes) -> Prediction:
        with decode_image(image_bytes) as image:
            batch = self._preprocess(image).unsqueeze(0)
        with self._torch.inference_mode():
            probabilities = self._network(batch).softmax(dim=1)[0]
            score, class_id = probabilities.max(dim=0)
        index = int(class_id.item())
        return Prediction(self._labels[index], index, float(score.item()))
