import pydicom
import os
import io
import base64
import matplotlib

matplotlib.use('Agg')

import matplotlib.pyplot as plt
import requests
import json
import httpx

dicomdir_path = "../rawData/MRI(강선애, F70)/DICOMDIR"

# matplotlib.rcParams['font.family'] = 'Malgun Gothic'
# matplotlib.rcParams['axes.unicode_minus'] = False

if not os.path.exists(dicomdir_path):
    print(f"에러: 해당 경로에 DICOMDIR 파일이 없습니다: {dicomdir_path}")
    exit()

pydicom.config.settings.reading_validation_mode = pydicom.config.WARN

dcmdir = pydicom.dcmread(dicomdir_path)
dcmdir.charsets = ['cp949']
base_dir = os.path.dirname(dicomdir_path)

# output_base_dir = "./result"
# os.makedirs(output_base_dir, exist_ok=True)

print("==========================================")
print("원본 의료 데이터베이스 연결 성공")
print("==========================================")

extracted_image = {
    "CR": None,
    "MR": None
}

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

        print(f"환자명: {current_patient_name} | ID: {record.PatientID}")

    elif rec_type == "STUDY":
        current_study_date = record.get("StudyDate", "Unknown")
        study_desc = record.get("StudyDescription", "No Description")
        print(f"   --> [검사] 날짜: {current_study_date} | 부위: {study_desc}")

    elif rec_type == "SERIES":
        current_series_number = record.get("SeriesNumber", "Unkown")
        modality = record.get("Modality", "Unkown")
        series_desc = record.get("SeriesDescription", "No Description")
        print(f"[시리즈] 번호: {current_series_number} | 장비: {modality}({series_desc})")

    elif rec_type == "IMAGE":
        if "ReferencedFileID" in record:
            referenced_file_id = list(record.ReferencedFileID)
            actual_file_path = os.path.join(base_dir, *referenced_file_id)

            print(f"   --> [이미지 매핑 확인] 파일 위치: {actual_file_path}")
            print("   --> 첫 번째 슬라이스 단면 시각화를 구동합니다...")

            image_id = referenced_file_id[-1]

            try:
                slice_data = pydicom.dcmread(actual_file_path)
                mri_matrix = slice_data.pixel_array

                plt.figure(figsize=(6, 6))
                plt.imshow(mri_matrix, cmap=plt.cm.bone)
                # plt.title(f"Patient: {current_patient_name}")
                plt.axis('off')

                # filename = f"{current_patient_name}_Ser{current_series_number}_{image_id}.png"
                # full_output_path = os.path.join(output_base_dir, filename)
                # plt.savefig(full_output_path, bbox_inches='tight')
                # print(f"[성공] 프로젝트 폴더에 '{full_output_path}' 파일이 생성되었습니다!")

                memory_stream = io.BytesIO()

                plt.savefig(memory_stream, format='png', bbox_inches='tight', dpi=60)
                plt.close()

                raw_image_bytes = memory_stream.getvalue()

                base64_encoded = base64.b64encode(raw_image_bytes).decode('utf-8')
                extracted_image[modality] = base64_encoded

                print("[성공] 메모리 단에서 LLM 송신용 데이터 직렬화 완료!")
                # print(f"       --> 데이터 타입: {type(base64_encoded)}")
                # print(f"       --> 가공된 텍스트 길이: {len(base64_encoded)} 글자")
                # print(f"       --> LLM 송신용 샘플 스니펫 (앞 50글자): {base64_encoded[:50]}...")

                # llm_payload = {
                #     "model": "qwen3-vl:8b",
                #     "messages": [
                #         {
                #             "role": "user",
                #             "content": [
                #                 {
                #                     "type": "text",
                #                     "text": (
                #                         f"📊 [환자 및 의료 영상 메타데이터 컨텍스트]\n"
                #                         f"- 환자명 (Patient Name): {current_patient_name}\n"
                #                         f"- 환자 ID (Patient ID): {current_patient_id}\n"
                #                         f"- 검사 일자 (Study Date): {current_study_date}\n"
                #                         f"- 촬영 부위 (Study Description): {study_desc}\n"
                #                         f"- 촬영 장비 (Modality): {modality}\n"
                #                         f"- 시퀀스 세부 정보 (Series Description): {series_desc}\n\n"
                                        
                #                         f"❓ [전문의 분석 및 판독 지시서]\n"
                #                         f"당신은 대학병원 방사선과 전문의 가상 어시스턴트입니다.\n"
                #                         f"위 환자의 메타데이터 컨텍스트와 첨부된 고해상도 흑백 의료 영상을 종합적으로 분석하여,\n"
                #                         f"다음 요구사항에 맞춰 전문적인 '의료 영상 소견 초안(Medical Report Draft)'을 작성하세요.\n\n"
                                        
                #                         f"1. 영상의 종류(CR/MR 등)와 해부학적 촬영 부위가 메타데이터와 일치하는지 교차 검증하세요.\n"
                #                         f"2. 관절면의 정렬 상태, 골밀도 대조, 혹은 골절(Fracture)이나 탈구(Dislocation) 가능성이 보이는지 육안 소견을 기술하세요.\n"
                #                         f"3. 임상적으로 유의미하게 관찰되는 이상 징후가 없다면 '특이 소견 없음'으로 명시하고, 정밀 판독이 필요한 부위가 있다면 제언하세요.\n\n"
                #                         f"⚠️ 주의: 반드시 한국어로 가독성 있게 서식을 나누어 출력하세요."
                #                     )
                #                 },
                #                 {
                #                     "type": "image_url",
                #                     "image_url":{
                #                         "url": base64_encoded
                #                     }
                #                 }
                #             ]
                #         }
                #     ],
                #     "temperature":0.0
                # }

                llm_payload = {
                    "model": "qwen3-vl:8b",
                    "messages": [
                        {
                            "role": "user",
                            # [코드 설명]: content에는 텍스트 지시서만 순수 문자열 형태로 직렬화하여 할당합니다.
                            "content": (
                                f"📊 [환자 및 의료 영상 메타데이터 컨텍스트]\n"
                                f"- 환자명 (Patient Name): {current_patient_name}\n"
                                f"- 환자 ID (Patient ID): {current_patient_id}\n"
                                f"- 검사 일자 (Study Date): {current_study_date}\n"
                                f"- 촬영 부위 (Study Description): {study_desc}\n"
                                f"- 촬영 장비 (Modality): {modality}\n"
                                f"- 시퀀스 세부 정보 (Series Description): {series_desc}\n\n"
                                
                                f"❓ [전문의 분석 및 판독 지시서]\n"
                                f"당신은 대학병원 방사선과 전문의 가상 어시스턴트입니다.\n"
                                f"위 환자의 메타데이터 컨텍스트와 첨부된 고해상도 흑백 의료 영상을 종합적으로 분석하여,\n"
                                f"다음 요구사항에 맞춰 전문적인 '의료 영상 소견 초안(Medical Report Draft)'을 작성하세요.\n\n"
                                
                                f"1. 영상의 종류(CR/MR 등)와 해부학적 촬영 부위가 메타데이터와 일치하는지 교차 검증하세요.\n"
                                f"2. 관절면의 정렬 상태, 골밀도 대조, 혹은 골절(Fracture)이나 탈구(Dislocation) 가능성이 보이는지 육안 소견을 기술하세요.\n"
                                f"3. 임상적으로 유의미하게 관찰되는 이상 징후가 없다면 '특이 소견 없음'으로 명시하고, 정밀 판독이 필요한 부위가 있다면 제언하세요.\n\n"
                                f"⚠️ 주의: 반드시 한국어로 가독성 있게 서식을 나누어 출력하세요."
                            ),
                            # 🌟 [핵심]: image_url 객체를 지우고, messages[0] 내부에 'images' 리스트 필드를 개설하여 순수 Base64 스트링을 탑재합니다.
                            "images": [base64_encoded]
                        }
                    ],
                    "temperature": 0.0
                }

                target_url = "https://overrate-comprised-outfield.ngrok-free.dev/v1/chat/completions"
                headers = {"Content-Type": "application/json"}

                print(f"[API 송신] ngrok 터널을 통해 Qwen3-vl:8b 서버로 의료 데이터 송신 중...")
                print(f"      --> 목적지: {target_url}")

                with httpx.Client(timeout=180.0) as client:
                    with client.stream("POST", target_url, headers=headers, json=llm_payload) as response:
                        response.raise_for_status()

                        for line in response.iter_lines():
                            if line:
                                decoded_line = line.strip()

                                if decoded_line.startswith("data:"):
                                    data_content = decoded_line[5:].strip()

                                    if data_content == "[DONE]":
                                        break

                                    try:
                                        chunk_json = json.loads(data_content)
                                        chunk_text = chunk_json.get("choices", [{}])[0].get("delta", {}).get("content", "")

                                        print(chunk_text, end="", flush=True)
                                    except Exception:
                                        pass
                print("\n=========================================\n")
                
                break
            except Exception as e:
                print(f"이미지 로드 실패: {e}. 다음 파일로 넘어갑니다.")
                break

print("\n=========================================")
print("🏁 [성공] 모든 의료 영상의 행렬 변환 및 이미지 추출 완료!")
print("=========================================")