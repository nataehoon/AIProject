import pydicom
import numpy as np
import torch
import torch.nn as nn
import zipfile
import io
import os
from pydicom.errors import InvalidDicomError
import matplotlib.pyplot as plt

DICOM_FILE_PATH = "../../rawData/MRI.zip"
with zipfile.ZipFile(DICOM_FILE_PATH, "r") as archive:
    for index, file_info in enumerate(archive.infolist()):
        normalized_path = file_info.filename.replace("\\", "/").upper()

        if normalized_path.endswith("DICOMDIR"):
            continue

        file_bytes = archive.read(file_info.filename)

        try:
            ds = pydicom.dcmread(io.BytesIO(file_bytes), force=False)
        except InvalidDicomError:
            continue

        # print(f"{index}. ds: {file_info.filename}")
            

pixel_array = ds.pixel_array
# print(f"pre pixel_array: {pixel_array}")
pixel_array = ds.pixel_array.astype(np.float32)
# print(f"first pixel_array: {pixel_array}")
# print(f"min pixel_array: {pixel_array.min()}")
# print(f"max pixel_array: {pixel_array.max()}")
# print(f"1 pixel_array: {pixel_array - pixel_array.min()}")
# print(f"2 pixel_array: {pixel_array.max() - pixel_array.min() + 1e-8}")
pixel_array = (pixel_array - pixel_array.min()) / (pixel_array.max() - pixel_array.min() + 1e-8)
# print(f"second pixel_array: {pixel_array}")
# print("normalized min:", pixel_array.min())
# print("normalized max:", pixel_array.max())

image_tensor = torch.from_numpy(pixel_array)
# print(f"first image_tensor: {image_tensor}")
# print(image_tensor.shape)
image_tensor = image_tensor.unsqueeze(0).unsqueeze(0)
# print(f"second image_tensor: {image_tensor}")

print(image_tensor.shape)

conv = nn.Conv2d(in_channels=1,out_channels=8,kernel_size=3,padding=1)
# print(f"conv: {conv}")
pool = nn.MaxPool2d(kernel_size=2, stride=2)
fc = nn.Linear(in_features=524288, out_features=2)

feature_map = conv(image_tensor)
# print(feature_map)
feature_map = torch.relu(feature_map)
# print(feature_map.shape)
feature_map = pool(feature_map)
feature_map = torch.flatten(feature_map, start_dim=1)
feature_map = fc(feature_map)
print(feature_map.shape)

# feature_map = feature_map.detach().numpy()
# print(feature_map)

# plt.figure(figsize=(6,6))
# plt.imshow(feature_map[0, 0], cmap="gray")
# plt.imshow(feature_map[0, 0].detach().numpy(), cmap="gray")
# plt.axis('off')
# plt.savefig("mri.png", dpi=200)

