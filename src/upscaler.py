import torch
import numpy as np
from PIL import Image
from pathlib import Path
from basicsr.archs.rrdbnet_arch import RRDBNet
from realesrgan import RealESRGANer

class ImageUpscaler:
    def __init__(self, model_path: str, scale: int = 4):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.scale = scale
        self.model_path = Path(model_path)

        # Force half=False on both GPU and CPU (matches your working config)
        self.half = False
        self.tile = 128 if self.device.type == 'cuda' else 0

        self.model = self._load_model()

    def _load_model(self):
        state_dict = torch.load(self.model_path, map_location=self.device)
        if 'params_ema' in state_dict:
            state_dict = state_dict['params_ema']

        model = RRDBNet(
            num_in_ch=3,
            num_out_ch=3,
            num_feat=64,
            num_block=23,
            num_grow_ch=32,
            scale=self.scale
        )
        model.load_state_dict(state_dict, strict=True)
        model.eval()
        model.to(self.device)

        self.upsampler = RealESRGANer(
            scale=self.scale,
            model_path=str(self.model_path),
            model=model,
            tile=self.tile,
            pre_pad=0,
            half=self.half,
            device=self.device
        )
        return model

    def upscale_image(self, input_path: str, output_path: str):
        img = Image.open(input_path).convert('RGB')
        img_np = np.array(img, dtype=np.uint8)  # ensure uint8

        output, _ = self.upsampler.enhance(img_np, outscale=self.scale)
        Image.fromarray(output).save(output_path)
        print(f"Upscaled {input_path} -> {output_path} using device {self.device}")
