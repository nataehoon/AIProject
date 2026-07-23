import pydicom
import io
import zipfile
import numpy as np
from pydicom.dataset import Dataset
from collections import defaultdict
import modules.classification as classification

def _group_by_series(datasets: list[Dataset]):
    series_map: dict[str, list[Dataset]] = defaultdict(list)

    for ds in datasets:
        series_uid = str(getattr(ds, "SeriesInstanceUID", "UNKNOWN_SERIES"))
        series_map[series_uid].append(ds)

    return dict(series_map)

def dicom_research_process(uploaded_zip):
    uploaded_zip.seek(0)
    datasets: list[Dataset] = []
    with zipfile.ZipFile(uploaded_zip, "r") as archive:
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
        raise ValueError("ZIP 파일에서 PixelData를 가진 DICOM을 찾지 못했습니다.")

    series_map = _group_by_series(datasets)

    MRI_Classification_result = classification.MRI_classification(series_map)
    print(MRI_Classification_result)

def process_dicom_zip(uploaded_zip):
    """[함수 설명]: 업로드 컴포넌트가 전달한 파일 바이트 스트림을 pydicom 라이브러리를 통해 읽어 환자 메타데이터를 추출합니다."""

    try:
        pixel_buffers = {
            "CR": [],
            "MR": []
        }
        zip_file_map = {}
        dicomdir_bytes = None

        uploaded_zip.seek(0)
        with zipfile.ZipFile(io.BytesIO(uploaded_zip.read())) as archive:
            for file_info in archive.infolist():
                normalized_path = file_info.filename.replace("\\", "/").upper()

                if normalized_path.endswith("DICOMDIR"):
                    dicomdir_bytes = archive.read(file_info.filename)
                else:
                    zip_file_map[normalized_path] = archive.read(file_info.filename)

        if not dicomdir_bytes:
            return {"success": False, "error": "ZIP 압축 내부에 'DICOMDIR 색인 파일이 존재하지 않습니다."}
        
        dcm = pydicom.dcmread(io.BytesIO(dicomdir_bytes))

        for record in dcm.DirectoryRecordSequence:
            rec_type = record.DirectoryRecordType

            if rec_type == "PATIENT":
                name_element = record.get(0x00100010) # PatientName 공식 DICOM 태그 번호
                        
                if name_element is not None:
                    # [원리 설명]: name_element.value에 이미 깨진 문자열이 들어있더라도, 
                    # pydicom 내부 버퍼 레벨(_value)에는 최초 파일에서 읽은 순수 바이트(Bytes) 배열이 보존되어 있을 수 있습니다.
                    raw_bytes = getattr(name_element, '_value', None)
                    
                    # 만약 버퍼가 비어있다면, 이미 깨져버린 문자열을 아스키 바이트로 역강제 변환(latin1)하여 원본 옥텟을 복구합니다.
                    if not isinstance(raw_bytes, bytes):
                        raw_bytes = str(name_element.value).encode('latin1', errors='ignore')
                    
                    try:
                        # [코드 설명]: 복구된 순수 바이트 배열을 한국어 완성형(cp949) 및 확장형 규격으로 정밀 디코딩합니다.
                        # 혹시 모를 공백이나 의료 영상 특유의 컴포넌트 구분자(^) 뒤의 쓰레기 값을 제거합니다.
                        patient_name = raw_bytes.decode('cp949', errors='replace').strip()
                    except Exception:
                        # 최후의 보루: 디코딩 실패 시 원래 값 유지
                        patient_name = str(name_element.value)
                else:
                    patient_name = "Unknown"

                patient_id = str(record.get("PatientID", "Unknown")).strip()

            elif rec_type == "STUDY":
                study_date = str(record.get("StudyDate", "Unknown")).strip()

            elif rec_type == "SERIES":
                modality = record.get("Modality", "Unknown").upper().strip()
                body_part = record.get("BodyPartExamined", "Unknown").upper().strip()

            elif rec_type == "IMAGE":
                if "ReferencedFileID" in record:
                    target_zip_key = "/".join(list(record.ReferencedFileID)).upper()
                    matched_key = next((k for k in zip_file_map.keys() if k.endswith(target_zip_key)), None)

                    if matched_key:
                        try:
                            slice_data = pydicom.dcmread(io.BytesIO(zip_file_map[matched_key]))
                            if hasattr(slice_data, "pixel_array"):
                                img_matrix = slice_data.pixel_array
                                if isinstance(img_matrix, np.ndarray) and img_matrix.ndim >= 2:
                                    pixel_buffers[modality].append(img_matrix)
                        except Exception:
                            continue


        return {
            "success": True,
            "patient_name": patient_name,
            "patient_id": patient_id,
            "study_date": study_date,
            "body_part": body_part,
            "pixel_buffer": pixel_buffers
        }
    except Exception as e:
        return{
            "success":False,
            "error":str(e)
        }