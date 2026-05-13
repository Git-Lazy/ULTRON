import torch
from torch import nn


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
        return self.steps(x)