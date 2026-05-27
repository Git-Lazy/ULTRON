from torch.nn import functional as FootPics
from torch import nn
from torch import tensor, zeros, save
from torchvision import transforms
import numpy
from PIL import Image
import torchvision.transforms.functional as F
import os
from fastapi import FastAPI, File, UploadFile, responses
import torch
import io
from typing import List


class ResizeWithPad:
    def __init__(self, target_size):
        self.target_size = target_size  # e.g. 224

    def __call__(self, img):
        _, w, h = img.shape  # PIL uses (width, height)
        scale = self.target_size / max(w, h)

        # Resize proportionally
        new_w = int(w * scale)
        new_h = int(h * scale)
        img = F.resize(img, (new_h, new_w))

        # Calculate padding to reach target_size x target_size
        pad_left   = (self.target_size - new_w) // 2
        pad_right  = self.target_size - new_w - pad_left
        pad_top    = (self.target_size - new_h) // 2
        pad_bottom = self.target_size - new_h - pad_top

        img = F.pad(img, (pad_left, pad_top, pad_right, pad_bottom), fill=0)
        return img


class Model(nn.Module):
    def __init__(self, embedding_dim=256):
        super(Model, self).__init__()

        def conv_block(in_ch, out_ch, pool=True):
            layers = [
                nn.Conv2d(in_ch, out_ch, kernel_size=3, padding=1),
                nn.BatchNorm2d(out_ch),
                nn.ReLU(inplace=True),
                nn.Conv2d(out_ch, out_ch, kernel_size=3, padding=1),
                nn.BatchNorm2d(out_ch),
                nn.ReLU(inplace=True),
            ]
            if pool:
                layers.append(nn.MaxPool2d(2, 2))
            return layers

        steps = []
        steps += conv_block(3,   32)   # → 32 × 64 × 64
        steps += conv_block(32,  64)   # → 64 × 32 × 32
        steps += conv_block(64,  128)  # → 128 × 16 × 16
        steps += conv_block(128, 256)  # → 256 × 8 × 8
        steps += [
            nn.AdaptiveAvgPool2d((4, 4)),  # → 256 × 4 × 4 (more robust than Flatten raw)
            nn.Flatten(),
            nn.Linear(256 * 4 * 4, 512),
            nn.ReLU(inplace=True),
            nn.Dropout(0.3),
            nn.Linear(512, embedding_dim),
        ]

        self.steps = nn.Sequential(*steps)

    def forward(self, x):
        return FootPics.normalize(self.steps(x), p=2, dim=1)



app = FastAPI()
model = Model()
model.load_state_dict(torch.load("../modelTraining/models/gen2/new_data_new_new.pth"))
model.eval()

transform = transforms.Compose([
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5]),
    ResizeWithPad(128),
])

@app.post("/predict_one")
async def predict(file: UploadFile = File(...)):
    try:
        if not file.content_type.startswith("image/"):
            raise ValueError("Invalid file type")
        print("file content type: ", file.content_type)
        content = await file.read()
        print("got content:")
        image = Image.open(io.BytesIO(content)).convert("RGB")
        print("opened image:")
        image = transform(image)
        print("transformed image:")
        print(image.shape)
        input_tensor = torch.zeros(1, 3, 128, 128)
        input_tensor[0] = image
        embedding = model(input_tensor)[0]
        print("got embedding:")
        return embedding.tolist()
    except Exception as e:
        print(e)
        return responses.JSONResponse(status_code=500, content={"error": str(e)})

@app.post("/predict_many")
async def predict(files: List[UploadFile] = File(...)):
    try:
        input_vectors = torch.zeros((len(files), 3, 128, 128))
        for i, file in enumerate(files):
            if not file.content_type.startswith("image/"):
                raise ValueError("Invalid file type")
            content = await file.read()
            image = Image.open(io.BytesIO(content)).convert("RGB")
            image = transform(image)
            input_vectors[i] = image
        print("input shape: ", input_vectors.shape)
        embedding = model(input_vectors)
        print("got embedding:")
        return embedding.tolist()
    except Exception as e:
        print(e)
        return responses.JSONResponse(status_code=500, content={"error": str(e)})