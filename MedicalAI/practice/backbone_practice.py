import pydicom
import zipfile
import io
from pydicom.dataset import Dataset
from collections import defaultdict
import numpy as np
import matplotlib.pyplot as plt
import torch
import torch.nn as nn
from torchvision.models import resnet18, ResNet18_Weights
from PIL import Image

DICOM_FILE_PATH = "../../rawData/MRI.zip"

def _group_by_series(datasets: list[Dataset]):
    series_map: dict[str, list[Dataset]] = defaultdict(list)

    for ds in datasets:
        series_uid = str(getattr(ds, "SeriesInstanceUID", "UNKNOWN_SERIES"))
        series_map[series_uid].append(ds)

    return dict(series_map)

def _describe_series(series_map: dict[str, list[Dataset]]):
    result: list[dict] = []

    for uid, datasets in series_map.items():
        first = datasets[0]
        if not getattr(first, "Modality", "") == "CR":
            result.append(
                {
                    "series_uid": uid,
                    "series_number": getattr(first, "SeriesNumber", None),
                    "description": str(getattr(first, "SeriesDescription", "")),
                    "protocol": str(getattr(first, "protocolName", "")),
                    "modality": str(getattr(first, "Modality", "")),
                    "body_part": str(getattr(first, "BodyPartExamined", "")),
                    "slice_count": len(datasets),
                    "rows": getattr(first, "Rows", None),
                    "Columns": getattr(first, "Columns", None),
                    "pixel_spacing": list(getattr(first, "PixelSpacing", [])),
                    "slice_thinkness": getattr(first, "SliceThickness", None)
                }
            )

    return result

def _select_largest_series(series_map: dict[str, list[Dataset]]):
    if not series_map:
        raise ValueError("선택할 DICOM 시리즈가 없습니다.")

    selected_uid, selected_series = max(series_map.items(), key=lambda item: len(item[1]))

    return selected_uid, selected_series

def _calculate_slice_position(ds: Dataset):
    if hasattr(ds, "ImageOrientationPatient") and hasattr(ds, "ImagePositionPatient"):
        orientation = np.asarray(ds.ImageOrientationPatient, dtype=np.float64)
        position = np.asarray(ds.ImagePositionPatient, dtype=np.float64)

        # print(f"orientation: {orientation}\nposition: {position}")
        # print(f"orientation.shape: {orientation.shape}\nposition.shape: {position.shape}")

        if orientation.shape == (6,) and position.shape == (3,):
            row_direction = orientation[:3]
            column_direction = orientation[3:]
            # print(f"row_direction: {row_direction}")
            # print(f"column_direction: {column_direction}")

            slice_normal = np.cross(row_direction, column_direction)
            # print(f"slice_normal: {slice_normal}")

            # print(f"dot: {float(np.dot(position, slice_normal))}")
            return float(np.dot(position, slice_normal))

    if hasattr(ds, "SliceLocation"):
        return float(ds.SliceLocation)
    if hasattr(ds, "InstanceNumber"):
        return float(ds.InstanceNumber)

    return 0.0

def _sort_dicom_slices(datasets: list[Dataset]):
    return sorted(datasets, key=_calculate_slice_position)

datasets: list[Dataset] = []
with zipfile.ZipFile(DICOM_FILE_PATH, "r") as archive:
    for file_info in archive.infolist():
        if file_info.is_dir():
            continue

        try:
            raw_bytes = archive.read(file_info.filename)
            ds = pydicom.dcmread(io.BytesIO(raw_bytes), force=False)

            if "PixelData" not in ds:
                continue

            datasets.append(ds)

        except (pydicom.errors.InvalidDicomError, EOFError, ValueError):
            continue

if not datasets:
    raise ValueError("ZPI 파일에서 PixelData를 가진 DICOM을 찾지 못했습니다.")

print(len(datasets))

series_map = _group_by_series(datasets)
print(len(series_map))

series_info = _describe_series(series_map)

for item in series_info:
    print(item)

# selected_uid, selected_series = _select_largest_series(series_map)

# print(f"선택 UID: {selected_uid}")
# print(f"슬라이스 수: {len(selected_series)}")
# print(f"설명: {getattr(selected_series[0], "SeriesDescription", None)}")

# sorted_series = _sort_dicom_slices(selected_series)

# for index, ds in enumerate(sorted_series[:5]):
#     print(index, _calculate_slice_position(ds), getattr(ds, "InstanceNumber", None))

# pixel_array = sorted_series[0].pixel_array
# print(type(pixel_array))
# print(pixel_array.shape)
# print(pixel_array.dtype)

# slices = []
# for ds in sorted_series:
#     pixel_array = ds.pixel_array.astype(np.float32)

#     slope = float(getattr(ds, "RescaleSlope", 1.0))
#     intercept = float(getattr(ds, "RescaleIntercept", 0.0))

#     pixel_array = pixel_array * slope + intercept

#     slices.append(pixel_array)

# print(len(slices))
# print(slices[0].shape)

# volume = np.stack(slices, axis=0)
# print("shape:", volume.shape)
# print("dtype:", volume.dtype)
# print("min:", volume.min())
# print("max:", volume.max())
# print("mean:", volume.mean())

# middle_index = volume.shape[0] //2
# print("middle_index:", middle_index)

# device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# image = volume[middle_index]
# image = image.astype(np.float32)
# image = (image - image.min()) / (image.max() - image.min() + 1e-8)
# image = (image * 255).astype(np.uint8)

# pil_image = Image.fromarray(image, mode="L").convert("RGB")

# weights = ResNet18_Weights.DEFAULT
# preprocess = weights.transforms()

# model = resnet18(weights=weights)

# input_features = model.fc.in_features
# model.fc = nn.Linear(input_features, 2)
# model = model.to(device)

# model.eval()

# input_tensor = preprocess(pil_image).unsqueeze(0).to(device)

# with torch.no_grad():
#     logits = model(input_tensor)
#     probabilities = torch.softmax(logits, dim=1)

# class_index = probabilities.argmax(dim=1).item()
# confidence = probabilities[0, class_index].item()
# class_name = weights.meta["categories"][class_index]

# print("input shape:", input_tensor.shape)
# print("prediction:", class_name)
# print("confidence:", confidence)

# plt.imshow(volume[middle_index], cmap="gray")
# plt.title(f"Slice {middle_index}")
# plt.axis('off')
# plt.savefig("mri")

# print(ds.PixelSpacing)
# print(ds.SliceThickness)

# volume = (volume - volume.min()) / (volume.max() - volume.min() + 1e-8)
# tensor = torch.from_numpy(volume)
# tensor = tensor.unsqueeze(0).unsqueeze(0)
# print(tensor.shape)
