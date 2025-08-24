import torch
import numpy as np
from PIL import Image
from pathlib import Path
from basicsr.archs.rrdbnet_arch import RRDBNet
from realesrgan import RealESRGANer

class ImageUpscaler:
    def __init__(self, model_path: str, device_mode: str = 'auto', scale: int = 4):
        """
        Initializes the upscaler with robust settings.

        Args:
            model_path (str): The path to the .pth model file.
            device_mode (str): The device to run on ('auto', 'cpu', 'cuda').
            scale (int): The upscale factor of the model.
        """
        self.scale = scale
        self.model_path = Path(model_path)
        self.device = self._get_device(device_mode)

        # CRITICAL: Hardcode half=False to prevent corrupted black image outputs on some GPUs.
        self.half = False
        # Use tiling on CUDA to manage memory usage.
        self.tile = 128 if self.device.type == 'cuda' else 0

        self.model = self._load_model()
        self.upsampler = self._initialize_upsampler()
        print(f"ImageUpscaler initialized on device: '{self.device}' with tiling={self.tile}, half_precision={self.half}")

    def _get_device(self, device_mode):
        """Determines the correct torch device to use based on user setting."""
        if device_mode == 'cpu':
            return torch.device('cpu')
        if device_mode == 'cuda':
            if not torch.cuda.is_available():
                print("Warning: CUDA selected but not available. Falling back to CPU.")
                return torch.device('cpu')
            return torch.device('cuda')
        # Default 'auto' behavior
        return torch.device('cuda' if torch.cuda.is_available() else 'cpu')

    def _load_model(self):
        """Loads the model state dictionary."""
        state_dict = torch.load(self.model_path, map_location='cpu')
        if 'params_ema' in state_dict:
            state_dict = state_dict['params_ema']

        model = RRDBNet(
            num_in_ch=3, num_out_ch=3, num_feat=64,
            num_block=23, num_grow_ch=32, scale=self.scale
        )
        model.load_state_dict(state_dict, strict=True)
        model.eval()
        return model.to(self.device)

    def _initialize_upsampler(self):
        """Initializes the RealESRGANer with the loaded model and settings."""
        return RealESRGANer(
            scale=self.scale,
            model_path=str(self.model_path),
            model=self.model,
            tile=self.tile,
            pre_pad=0,
            half=self.half,
            device=self.device
        )

    def upscale_image(self, input_path: str, output_path: str):
        """Upscales an image using PIL and saves the result."""
        try:
            img = Image.open(input_path).convert('RGB')
            img_np = np.array(img, dtype=np.uint8)

            output, _ = self.upsampler.enhance(img_np, outscale=self.scale)
            Image.fromarray(output).save(output_path)
        except Exception as e:
            print(f"Error processing {input_path}: {e}")
            # As a fallback, copy the original file to prevent the job from getting stuck
            import shutil
            shutil.copy(input_path, output_path)