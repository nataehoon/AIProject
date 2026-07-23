import pydicom
import numpy as np
import torch
import torch.nn as nn
import zipfile
import io
from pydicom.errors import InvalidDicomError
import matplotlib.pyplot as plt

DICOM_FILE_PATH = "../../rawData/MRI.zip"

with zipfile.ZipFile(DICOM_FILE_PATH, "r") as archive:
    for file_info in archive.infolist():
        normalized_path = file_info.filename.replace("\\", "/").upper()

        if normalized_path.endswith("DICOMDIR"):
            continue

        file_bytes = archive.read(file_info.filename)

        try:
            ds = pydicom.dcmread(io.BytesIO(file_bytes), force=False)
        except InvalidDicomError:
            continue

pixel_array = ds.pixel_array.astype(np.float32)

pixel_array = (pixel_array - pixel_array.min() / (pixel_array.max() - pixel_array.min() + 1e-8))

image_tensor = torch.from_numpy(pixel_array)
image_tensor = image_tensor.unsqueeze(0).unsqueeze(0)

print(image_tensor.shape)

conv = nn.Conv2d(in_channels=1, out_channels=768, kernel_size=16, stride=16)
x = conv(image_tensor)
print(x.shape)

x = x.flatten(2)
print(x.shape)

x = x.transpose(1,2)
print(x.shape)

pos_embed = nn.Parameter(torch.randn(1, 1024, 768))
print(pos_embed.shape)

x = x+pos_embed
print(x.shape)

encoder_layer = nn.TransformerEncoderLayer(
    d_model=768,
    nhead=12,
    dim_feedforward=3072,
    batch_first=True
)

encoder = nn.TransformerEncoder(encoder_layer,
    num_layers=12)
x = encoder(x)

x = x.mean(dim=1)

classifier = nn.Linear(768, 2)

logits = classifier(x)

print(logits.shape)
