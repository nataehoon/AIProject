import matplotlib.pyplot as plt
import base64
import io
import requests
import json
from config import VLM_MODEL, LLM_MODEL, OLLAMA_VLM_API_URL, OLLAMA_LLM_API_URL, VLM_NUM_PREDICT, LLM_NUM_PREDICT, VLM_NUM_CTX, LLM_NUM_CTX
from models.ai_payload import OllamaPayload
from typing import List, Dict
from modules.sentence_transformer import get_vector_data
from services.rag_service import RAGService

def query_vector_db(query_text: str) -> str:
    raw_data = []
    raw_data.append(query_text)

    v_list = get_vector_data(raw_data)
    v_data = v_list[0]

    return RAGService.get_rag_data(v_data)

def run_llm_generator(chatMessage: List[Dict[str, str]]):
    llm_payload = OllamaPayload(
        model=LLM_MODEL,
        messages=chatMessage,
        temperature=0.0,
        options={"num_predict": LLM_NUM_PREDICT}
    ).model_dump()

    print(llm_payload)

    response = requests.post(OLLAMA_LLM_API_URL, json=llm_payload, stream=True, timeout=300)
    response.raise_for_status()
    
    reasoning_text = ""
    finish_text = ""
    for index, chunk in enumerate(response.iter_lines()):
        if chunk:
            decoded_line = chunk.decode('utf-8').strip()

            if decoded_line.startswith("data:"):
                data_content = decoded_line[5:].strip()
                print(f"{index}__{decoded_line}")

                if data_content == "[DONE]":
                    print(finish_text)
                    break

                try:
                    chunk_json = json.loads(data_content)
                    chunk_text = chunk_json.get("choices", [{}])[0].get("delta", {}).get("content", "")
                    reasoning_text += chunk_json.get("choices", [{}])[0].get("delta", {}).get("reasoning", "")
                    finish_text += chunk_json.get("choices", [{}])[0].get("delta", {}).get("finish_reason", "")

                    if chunk_text:
                        yield chunk_text
                        
                except Exception as e:
                    print(f"[스트림 파싱 예외 발생]: {e}")

def run_vlm_inference_generator(patient_info):
    """UI단에서 토스해준 pixel_buffers와 환자 정보를 전달받아 Ollama VLM과 패킷을 맺고 스트림 제너레이터를 리턴"""

    pixel_buffers = patient_info["pixel_buffer"]
    description = ""
    images_payload_array = []
    yield {"status": "파일 전처리를 시작합니다..."}
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
                    description += "This is a general X-ray (CR) view. Please evaluate the overall skeletal alignment and check for signs of dislocation."
                elif target_modality == "MR":
                    description += f"This is a specific cross-sectional layer ({slice_idx}/{total_slices}) from the MRI volume. Please cross-analyze the condition of the rotator cuff tendons."
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
                        "[IMPORTANT INSTRUCTION]: You are a professional radiologist. Do not output any chain-of-thought, reasoning process, or internal monologues. Output ONLY the final formal medical report structure.\n\n"
                        f"[Patient Medical Metadata Context]\n"
                        f"- Patient Name: {patient_info['patient_name']} | ID: {patient_info['patient_id']}\n"
                        f"- Study Date: {patient_info['study_date']}\n\n"
                        f"[Comprehensive Radiological Interpretation Directive]\n"
                        f"{description}\n\n"
                        "Cross-reference and integrate the images from each index above to compose a detailed draft of the comprehensive medical report."
                    ),
                    "images": images_payload_array
                }
            ],
            "temperature": 0.0,
            "options": {"num_predict": VLM_NUM_PREDICT, "num_ctx": VLM_NUM_CTX}
        }

        yield {"status": "파일 전처리를 완료하여 AI(VLM)에게 전송합니다..."}
        vlm_response = requests.post(OLLAMA_VLM_API_URL, json=llm_payload, stream=True, timeout=300)
        vlm_response.raise_for_status()

        vlm_text = ""
        reasoning = ""
        for chunk in vlm_response.iter_lines():
            if chunk:
                decoded_line = chunk.decode('utf-8').strip()

                if decoded_line.startswith("data:"):
                    data_content = decoded_line[5:].strip()
                    print(data_content)

                    if data_content == "[DONE]":
                        break

                    try:
                        chunk_json = json.loads(data_content)
                        vlm_text += chunk_json.get("choices", [{}])[0].get("delta", {}).get("content", "")
                        reasoning += chunk_json.get("choices", [{}])[0].get("delta", {}).get("reasoning", "")
                            
                    except Exception as e:
                        print(f"[스트림 파싱 예외 발생]: {e}")

        if not vlm_text:
            yield {"status": f"vlm_text데이터 추출 실패: {reasoning}"}
        else:
            yield {"status": "AI에게 받은 데이터를 RAG를 사용하여 재검증 합니다..."}
            retrieved_knowledge = query_vector_db(vlm_text)

            yield {"status": "RAG검증을 완료 하였습니다. AI(LLM)에게 전송합니다..."}
            verification_prompt = (
                "You are a Senior Radiologist and a Medical Report Validation AI.\n"
                "Thoroughly verify and correct the provided [VLM Draft Interpretation] to ensure it perfectly aligns with the given [Medical Guideline Reference Standard].\n\n"
                "[Medical Guideline Reference Standard]\n"
                f"{retrieved_knowledge}\n\n"
                "[Patient Metadata]\n"
                f"- Patient Name: {patient_info['patient_name']} | ID: {patient_info['patient_id']}\n\n"
                "[VLM Draft Interpretation]\n"
                f"{vlm_text}\n\n"
                "[Action Guidelines]\n"
                "1. If the draft deviates from the reference standard, contains medical distortions (hallucinations), or shows logical contradictions, correct them strictly based on the reference standard.\n"
                "2. Filter out any fictional disease names or diagnoses not explicitly stated in the reference standard that are based on excessive speculation.\n"
                "3. The final output must be formatted as a structured 'Final Comprehensive Medical Report' including the patient metadata.\n"
                "4. Exclude all validation processes, justifications, or introductory remarks. Output ONLY the body of the 'Final Medical Report'."
                )

            chatMessage = [{"role": "user", "content": verification_prompt}]

            llm_payload = OllamaPayload(
                    model=LLM_MODEL,
                    messages=chatMessage,
                    temperature=0.0,
                    options={"num_predict": LLM_NUM_PREDICT, "num_ctx": LLM_NUM_CTX}
                ).model_dump()

            response = requests.post(OLLAMA_LLM_API_URL, json=llm_payload, stream=True, timeout=300)
            response.raise_for_status()

            result_text = ""
            for llm_chunk in response.iter_lines():
                if llm_chunk:
                    llm_decoded_line = llm_chunk.decode('utf-8').strip()

                    if llm_decoded_line.startswith("data:"):
                        llm_data_content = llm_decoded_line[5:].strip()

                        if llm_data_content == "[DONE]":
                            break

                        try:
                            llm_chunk_json = json.loads(llm_data_content)
                            result_text += llm_chunk_json.get("choices", [{}])[0].get("delta", {}).get("content", "")

                        except Exception as e:
                            print(f"[스트림 파싱 예외 발생]: {e}")

            yield result_text
        # reasoning_text = ""
        # finish_text = ""
        # for index, chunk in enumerate(response.iter_lines()):
        #     if chunk:
        #         decoded_line = chunk.decode('utf-8').strip()

        #         if decoded_line.startswith("data:"):
        #             data_content = decoded_line[5:].strip()
        #             print(f"{index}__{decoded_line}")

        #             if data_content == "[DONE]":
        #                 print(finish_text)
        #                 break

        #             try:
        #                 chunk_json = json.loads(data_content)
        #                 chunk_text = chunk_json.get("choices", [{}])[0].get("delta", {}).get("content", "")
        #                 reasoning_text += chunk_json.get("choices", [{}])[0].get("delta", {}).get("reasoning", "")
        #                 finish_text += chunk_json.get("choices", [{}])[0].get("delta", {}).get("finish_reason", "")

        #                 if chunk_text:
        #                     yield chunk_text
                            
        #             except Exception as e:
        #                 print(f"[스트림 파싱 예외 발생]: {e}")

    