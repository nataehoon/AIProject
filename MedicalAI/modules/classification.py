import io
import numpy as np
import pydicom
from pydicom.dataset import Dataset
from PIL import Image
from typing import Any
import copy
from modules.ai_processor import classification_api

def _select_largest_series(series_map: dict[str, list[Dataset]]):
    if not series_map:
        raise ValueError("선택할 DICOM 시리즈가 없습니다.")

    selected_uid, selected_series = max(series_map.items(), key=lambda item: len(item[1]))

    return selected_series

def MRI_classification(series_map: dict[str, list[Dataset]]):
    image_info: list[dict[str, Any]] = []
    for index, (uid, datasets) in enumerate(series_map.items()):
        selected_series = datasets[0]
        if getattr(selected_series, "Modality", "") != "MR":
            continue

        image_buffers = []
        for series in datasets:
            pixel_array = series.pixel_array.astype(np.float32)
            normalized = (pixel_array - pixel_array.min()) / (pixel_array.max() - pixel_array.min() +1e-8)

            image_uint8 = (normalized * 255).astype(np.uint8)

            image = Image.fromarray(image_uint8)
            image = image.convert("RGB")

            image_buffer = io.BytesIO()
            image.save(image_buffer, "PNG")
            image_buffer.seek(0)
            image_buffers.append(image_buffer)

        image_info.append({
            "modality": getattr(selected_series, "Modality", ""),
            "image_count": len(image_buffers),
            "description": str(getattr(selected_series, "SeriesDescription", "")),
            "image_buffers": image_buffers,
            "result": [],
            "image_buffer": []
        })

    metadata_list = copy.deepcopy(image_info)

    classification_result = classification_api(image_info)
    classification_result = [x for x in classification_result if x["result"]]

    for index, result in enumerate(classification_result):
        data = next(target for target in metadata_list if target.get("description") == result.get("description"))

        slice_number = int(result.get("result")[index].get("slice_number"))
        image_buffers = data.get("image_buffers")
        result["image_buffer"].append(data.get("image_buffers")[slice_number])

    return classification_result

# series_info = _describe_series(series_map)
# print(series_info)

# selected_series = _select_largest_series(series_map)

# print(f"{len(selected_series)}")
# print(f"설명: {getattr(selected_series[0], "SeriesDescription", None)}")

# pixel_array = selected_series[0].pixel_array.astype(np.float32)

# normalized = (pixel_array - pixel_array.min()) / (pixel_array.max() - pixel_array.min() + 1e-8)
# print(normalized)

# image_uint8 = (normalized * 255).astype(np.uint8)
# print(image_uint8)

# image = Image.fromarray(image_uint8)
# image = image.convert("RGB")

# image_buffer = io.BytesIO()
# image.save(image_buffer, format="PNG")
# image_buffer.seek(0)

# print("image size:", image.size)
# print("image mode:", image.mode)
# print("png bytes:", len(image_buffer.getvalue()))

# classification_result = send_image_data(image_buffer)
# print(f"")