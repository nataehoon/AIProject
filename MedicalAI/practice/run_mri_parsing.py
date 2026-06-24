import os
import pydicom
import numpy as np
import matplotlib.pyplot as plt
import io
import base64
import requests
import json

raw_pixel_buffers = {
    "CR": [],
    "MR": []
}

current_patient_id = "Unkown"
current_patient_name = "Unkown"
current_study_date = "Unkown"
modality = "Unkown"

print("==================================================")
print("1단계: DICOM 디렉터리 순회 및 생 메모리 적재 개시")
print("==================================================")

dicomdir_path = "../rawData/MRI(강선애, F70)/DICOMDIR"

if not os.path.exists(dicomdir_path):
    print(f"에러: 해당 경로에 DICOMDIR 파일이 없습니다: {dicomdir_path}")
    exit()

dcmdir = pydicom.dcmread(dicomdir_path)
dcmdir.charsets = ['cp949']
base_dir = os.path.dirname(dicomdir_path)

for record in dcmdir.DirectoryRecordSequence:
    rec_type = record.DirectoryRecordType

    if rec_type == "PATIENT":
        current_patient_id = record.get("PatientID", "Unkown")
                
        # 1. pydicom의 디코딩 캐시를 우회하기 위해, 데이터 엘리먼트 자체를 가져옵니다.
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
                current_patient_name = raw_bytes.decode('cp949', errors='replace').strip()
            except Exception:
                # 최후의 보루: 디코딩 실패 시 원래 값 유지
                current_patient_name = str(name_element.value)
        else:
            current_patient_name = "Unknown"

        current_patient_id = str(record.get("PatientID", "Unknown"))
        print(f"환자명: {current_patient_name} | ID: {current_patient_id}")

    elif rec_type == "STUDY":
        current_study_date = record.get("StudyDate", "Unkown")
    elif rec_type == "SERIES":
        modality = record.get("Modality", "Unkown")

    elif rec_type == "IMAGE":
        if "ReferencedFileID" in record:
            referenced_file_id = list(record.ReferencedFileID)
            actual_file_path = os.path.join(base_dir, *referenced_file_id)

            try:
                slice_data = pydicom.dcmread(actual_file_path)

                if hasattr(slice_data, "pixel_array"):
                    img_matrix = slice_data.pixel_array

                    if isinstance(img_matrix, np.ndarray) and img_matrix.ndim >= 2:
                        actual_modality = getattr(slice_data, "Modality", modality)
                        
                        if actual_modality in raw_pixel_buffers:
                            raw_pixel_buffers[actual_modality].append(img_matrix)
                else:
                    continue
            except Exception as e:
                print(f"픽셀 추출 실패 ({actual_file_path}): {e}")


print(f"✅ 수집 완료 -> [CR 수집량]: {len(raw_pixel_buffers['CR'])}장, [MR 수집량]: {len(raw_pixel_buffers['MR'])}장")

print("\n==========================================")
print("2단계: 가변 데이터 볼륨 샘플링 및 임베딩 처리 엔진 가동")
print("==========================================")

images_dict = {
    "CR": [],
    "MR": []
}
images_payload_array = []
global_description = ""
global_image_index = 0

for target_modality in ["CR", "MR"]:
    total_slices = len(raw_pixel_buffers[target_modality])

    if total_slices == 0:
        continue

    if total_slices > 5:
        target_indices = [int(total_slices * fraction) for fraction in [0.2, 0.4, 0.6, 0.8]]
    else:
        target_indices = list(range(total_slices))

    for slice_idx in target_indices:
        try:
            safe_idx = min(slice_idx, total_slices - 1)
            matrix_np = raw_pixel_buffers[target_modality][safe_idx]

            if isinstance(matrix_np, (int, float)) or matrix_np is None:
                print(f" [{target_modality}] 슬라이스 {safe_idx}번 데이터 유효성 실효: 스칼라 타입이 발견되어 스킵합니다.")
                continue

            plt.figure(figsize=(5, 5))
            plt.imshow(matrix_np, cmap=plt.cm.bone)
            plt.axis('off')

            memory_stream = io.BytesIO()

            plt.savefig(memory_stream, format='png', bbox_inches='tight', dpi=40)
            plt.close()

            base64_encoded = base64.b64encode(memory_stream.getvalue()).decode('utf-8')
            images_payload_array.append(base64_encoded)
            #images_dict[target_modality].append(base64_encoded)

            global_image_index += 1

            if target_modality == "CR":
                global_description += f"** {global_image_index}번째 인덱스 **: 일반 엑스레이 (CR) 전경 영상입니다. 전체적인 골격 정렬 및 탈구 소견을 판독하세요."
            elif target_modality == "MR":
                global_description += f"** {global_image_index}번째 인덱스 **: 자기공명영상 (MRI) 단면 볼륨 중 ({slice_idx}/{total_slices}) 정밀 단면 레이어 입니다. 회전근개 힘줄 상태를 교차 분석 하세요."

        except Exception as e:
            print(f"[{target_modality}] 슬라이스 {slice_idx} 렌더링 예외 발생: {e}")
            if 'plt' in locals() or 'plt' in globals():
                plt.close()

if images_payload_array:
    llm_payload = {
        "model": "qwen3-vl:8b",
                "messages": [
                    {
                        "role": "user",
                        "content": (
                            "[IMPORTANT INSTRUCTION]: 당신은 한국어 의료 전문의입니다. 반드시 한국어로만 답변하고, 생각 과정(reasoning)이나 영어 혼잣말은 절대 출력하지 말고 최종 소견서 서식만 출력하세요.\n\n"
                            f"[환자 의료 메타데이터 컨텍스트]\n"
                            f"- 환자명: {current_patient_name} | ID: {current_patient_id}\n"
                            f"- 검사 일자: {current_study_date}\n\n"
                            f"[종합 방사선학적 정밀 판독 지시서]\n"
                            f"{global_description}\n"
                            "위 인덱스별 영상을 상호 연동하여 종합 소견서 초안을 한국어로 상세히 구성해 주세요."
                        ),
                        "images": images_payload_array
                    }
                ],
                "temperature": 0.0
    }

    print(global_description)

    target_url = "https://overrate-comprised-outfield.ngrok-free.dev/v1/chat/completions"
    headers = {"Content-Type": "application/json"}

    try:
        print(f"[종합 API 전송] 정제 완료된 멀티모달 프레임 팩 전송 중 (총 {len(images_payload_array)})장...")
        response = requests.post(target_url, headers=headers, json=llm_payload, stream=True, timeout=300)
        response.raise_for_status()

        print("\n=========================================")
        print("하이브리드 볼륨 연동 정밀 판독 결과 출력")
        print("=========================================")

        for line in response.iter_lines():
            if line:
                decoded_line = line.decode('utf-8').strip()
                if decoded_line.startswith("data:"):
                    data_content = decoded_line[5:].strip()
                    if data_content == "[DONE]": break
                    try:
                        chunk_json = json.loads(data_content)
                        chunk_text = chunk_json.get("choices", [{}])[0].get("delta", {}).get("content", "")
                        print(chunk_text, end="", flush=True)
                    except Exception as e: print(e)
        print("\n=========================================\n")

    except Exception as e:
        print(f"네트워크 통신 실패: {e}")
else:
    print("전송 실패: 메모리 버퍼에 적재된 의료 영상이 존재하지 않습니다.")

# for modality_payload in images_dict:
#     if modality == "CR":
#         description = "일반 엑스레이 (CR) 전경 영상입니다. 전체적인 골격 정렬 및 탈구 소견을 판독하세요."
#     elif modality == "MR":
#         description = "자기공명영상 (MRI) 단면 볼륨 정밀 단면 레이어 입니다. 회전근개 힘줄 상태를 교차 분석 하세요."

#     llm_payload = {
#         "model": "qwen3-vl:8b",
#                 "messages": [
#                     {
#                         "role": "user",
#                         "content": (
#                             "[IMPORTANT INSTRUCTION]: 당신은 한국어 의료 전문의입니다. 반드시 한국어로만 답변하고, 생각 과정(reasoning)이나 영어 혼잣말은 절대 출력하지 말고 최종 소견서 서식만 출력하세요.\n\n"
#                             f"[환자 의료 메타데이터 컨텍스트]\n"
#                             f"- 환자명: {current_patient_name} | ID: {current_patient_id}\n"
#                             f"- 검사 일자: {current_study_date}\n\n"
#                             f"[종합 방사선학적 정밀 판독 지시서]\n"
#                             f"{description}\n"
#                             "위 인덱스별 영상을 상호 연동하여 종합 소견서 초안을 한국어로 상세히 구성해 주세요."
#                         ),
#                         "images": images_dict[modality_payload]
#                     }
#                 ],
#                 "temperature": 0.0
#     }

#     target_url = "https://overrate-comprised-outfield.ngrok-free.dev/v1/chat/completions"
#     headers = {"Content-Type": "application/json"}

#     try:
#         print(f"[종합 API 전송] 정제 완료된 멀티모달 프레임 팩 전송 중 ([{modality_payload}] 총 {len(images_dict[modality_payload])})장...")
#         response = requests.post(target_url, headers=headers, json=llm_payload, stream=True, timeout=300)
#         response.raise_for_status()

#         print("\n=========================================")
#         print("하이브리드 볼륨 연동 정밀 판독 결과 출력")
#         print("=========================================")

#         for line in response.iter_lines():
#             if line:
#                 decoded_line = line.decode('utf-8').strip()
#                 if decoded_line.startswith("data:"):
#                     data_content = decoded_line[5:].strip()
#                     if data_content == "[DONE]": break
#                     try:
#                         chunk_json = json.loads(data_content)
#                         chunk_text = chunk_json.get("choices", [{}])[0].get("delta", {}).get("content", "")
#                         print(chunk_text, end="", flush=True)
#                     except Exception : pass
#         print("\n=========================================\n")

#     except Exception as e:
#         print(f"네트워크 통신 실패: {e}")
# else:
#     print("전송 실패: 메모리 버퍼에 적재된 의료 영상이 존재하지 않습니다.")