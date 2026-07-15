import matplotlib.pyplot as plt
import base64
import io
import requests
import json
import config
from models.ai_payload import OllamaPayload
from typing import List, Dict, Any

def run_router_llm(chatMessage: List[Dict[str, str]]):
    llm_payload = OllamaPayload(
        model=config.ROUTER_MODEL,
        messages=chatMessage,
        temperature=config.DEFAULT_TEMPERATURE,
        think=config.ROUTER_THINK,
        stream=True,
        options={"num_predict": config.ROUTER_NUM_PREDICT, "num_ctx": config.ROUTER_NUM_CTX}
    ).model_dump()

    response = requests.post(config.ROUTER_LLM_API_URL, json=llm_payload, stream=True, timeout=300)
    response.raise_for_status()

    result_text = ""
    for chunk in response.iter_lines():
        if chunk:
            decoded_line = chunk.decode('utf-8').strip()

            if decoded_line.startswith("data:"):
                data_content = decoded_line[5:].strip()

                if data_content == "[DONE]":
                    break

                try:
                    chunk_json = json.loads(data_content)
                    result_text += chunk_json.get("choices", [{}])[0].get("delta", {}).get("content", "")
                except Exception as e:
                    print(f"[스트림 파싱 예외 발생]: {e}")

    return result_text

def run_llm_generator(chatMessage: List[Dict[str, str]]):
    llm_payload = OllamaPayload(
        model=config.LLM_MODEL,
        messages=chatMessage,
        temperature=config.DEFAULT_TEMPERATURE,
        think=config.LLM_THINK,
        stream=True,
        options={"num_predict": config.LLM_NUM_PREDICT, "num_ctx": config.LLM_NUM_CTX}
    ).model_dump()

    response = requests.post(config.OLLAMA_LLM_API_URL, json=llm_payload, stream=True, timeout=300)
    response.raise_for_status()
    
    reasoning_text = ""
    finish_text = ""
    for index, chunk in enumerate(response.iter_lines()):
        if chunk:
            decoded_line = chunk.decode('utf-8').strip()

            if decoded_line.startswith("data:"):
                data_content = decoded_line[5:].strip()

                if data_content == "[DONE]":
                    break

                try:
                    chunk_json = json.loads(data_content)
                    chunk_text = chunk_json.get("choices", [{}])[0].get("delta", {}).get("content", "")
                    reasoning_text += chunk_json.get("choices", [{}])[0].get("delta", {}).get("reasoning", "")
                    finish_text += chunk_json.get("finish_reason", "")

                    if chunk_text:
                        yield chunk_text
                        
                except Exception as e:
                    print(f"[스트림 파싱 예외 발생]: {e}")

def run_vlm_generator(chatMessage: List[Dict[str, Any]], response_format: Dict[str, Any] | None = None):
    vlm_payload = OllamaPayload(
            model=config.VLM_MODEL,
            messages=chatMessage,
            temperature=config.DEFAULT_TEMPERATURE,
            think=config.VLM_THINK,
            stream=True,
            options={"num_predict": config.VLM_NUM_PREDICT, "num_ctx": config.VLM_NUM_CTX}
        ).model_dump()

    if response_format is not None:
        vlm_payload["format"] = response_format

    vlm_response = requests.post(config.OLLAMA_VLM_API_URL, json=vlm_payload, stream=True, timeout=300)
    vlm_response.raise_for_status()

    vlm_text = ""
    reasoning = ""
    for chunk in vlm_response.iter_lines():
        if chunk:
            decoded_line = chunk.decode('utf-8').strip()

            if decoded_line.startswith("data:"):
                data_content = decoded_line[5:].strip()

                if data_content == "[DONE]":
                    break

                try:
                    chunk_json = json.loads(data_content)
                    chunk_text = chunk_json.get("choices", [{}])[0].get("delta", {}).get("content", "")
                    vlm_text += chunk_text
                    reasoning += chunk_json.get("choices", [{}])[0].get("delta", {}).get("reasoning", "")

                    if chunk_text:
                        yield chunk_text
                    
                except Exception as e:
                    print(f"[스트림 파싱 예외 발생]: {e}")
    