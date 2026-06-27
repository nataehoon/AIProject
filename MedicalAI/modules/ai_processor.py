import matplotlib.pyplot as plt
import base64
import io
import requests
import json
from config import VLM_MODEL, LLM_MODEL, OLLAMA_VLM_API_URL, OLLAMA_LLM_API_URL

def run_llm_generator(chatMessage):
    llm_payload = {
        "model": LLM_MODEL,
        "message": [
            {
                "role": "system",
                "content": ""
            },
            {
                "role": "user",
                "content": ""
            }
        ],
        "temperature": 0.0,
        "options": {"num_predict": 2048}
    }
    pass

def run_vlm_inference_generator(patient_info):
    """UI단에서 토스해준 pixel_buffers와 환자 정보를 전달받아 Ollama VLM과 패킷을 맺고 스트림 제너레이터를 리턴"""

    pixel_buffers = patient_info["pixel_buffer"]
    description = ""
    images_payload_array = []
    for target_modality in ["CR", "MR"]:
        total_slices = len(pixel_buffers[target_modality])

        if total_slices == 0:
            raise ValueError("전송받은 픽셀 버퍼 내에 슬라이스가 존재하지 않습니다.")

        if total_slices > 5:
            target_indices = [int(total_slices * fraction) for fraction in [0.2, 0.4, 0.6, 0.8]]
        else:
            target_indices = list(range(total_slices))

        for slice_idx in target_indices:
            try:
                safe_idx = min(slice_idx, total_slices -1)
                matrix_np = pixel_buffers[target_modality][safe_idx]

                if isinstance(matrix_np, (int, float)) or matrix_np is None:
                    print(f"[{target_modality}] 슬라이스 {safe_idx}번 데이터 유효성 실효: 스칼라 타입이 발견되어 스킵합니다.")
                    continue

                plt.figure(figsize=[5, 5])
                plt.imshow(matrix_np, cmap=plt.cm.bone)
                plt.axis('off')

                memory_stream = io.BytesIO()

                plt.savefig(memory_stream, format='png', bbox_inches='tight', dpi=40)
                plt.close()

                base64_encoded = base64.b64encode(memory_stream.getvalue()).decode('utf-8')
                images_payload_array.append(base64_encoded)

                if target_modality == "CR":
                    description += "일반 엑스레이 (CR) 전경 영상입니다. 전체적인 골격 정렬 및 탈구 소견을 판독하세요."
                elif target_modality == "MR":
                    description += f"자기공명영상 (MRI) 단면 볼륨 중 ({slice_idx}/{total_slices}) 정밀 단면 레이어 입니다. 회전근개 힘줄 상태를 교차 분석 하세요."
            except Exception as e:
                print(f"[target_modality] 슬라이스 {slice_idx} 랜더링 예외 발생: {e}")
                if 'plt' in locals() or 'plt' in globals():
                    plt.close()

    if images_payload_array:
        llm_payload = {
            "model": VLM_MODEL,
            "messages": [
                {
                    "role": "user",
                    "content": (
                        "[IMPORTANT INSTRUCTION]: 당신은 한국어 의료 전문의입니다. 반드시 한국어로만 답변하고, 생각 과정(reasoning)이나 영어 혼잣말은 절대 출력하지 말고 최종 소견서 서식만 출력하세요.\n\n"
                        f"[환자 의료 메타데이터 컨텍스트]\n"
                        f"- 환자명: {patient_info['patient_name']} | ID: {patient_info['patient_id']}\n"
                        f"- 검사 일자: {patient_info['study_date']}\n\n"
                        f"[종합 방사선학적 정밀 판독 지시서]\n"
                        f"{description}\n"
                        "위 인덱스별 영상을 상호 연동하여 종합 소견서 초안을 한국어로 상세히 구성해 주세요."
                    ),
                    "images": images_payload_array
                }
            ],
            "temperature": 0.0,
            "options": {"num_predict": 2048}
        }

        response = requests.post(OLLAMA_VLM_API_URL, json=llm_payload, stream=True, timeout=300)
        response.raise_for_status()

        reasoning_text = ""
        for index, chunk in enumerate(response.iter_lines()):
            if chunk:
                decoded_line = chunk.decode('utf-8').strip()

                if decoded_line.startswith("data:"):
                    data_content = decoded_line[5:].strip()
                    #print(f"{index}__{reasoning_text}")

                    if data_content == "[DONE]":
                        print(reasoning_text)
                        break

                    try:
                        chunk_json = json.loads(data_content)
                        chunk_text = chunk_json.get("choices", [{}])[0].get("delta", {}).get("content", "")
                        reasoning_text += chunk_json.get("choices", [{}])[0].get("delta", {}).get("reasoning", "")

                        if chunk_text:
                            yield chunk_text
                            
                    except Exception as e:
                        print(f"[스트림 파싱 예외 발생]: {e}")

    