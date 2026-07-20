import matplotlib.pyplot as plt
import base64
import io
import requests
import json
import config
from models.ai_payload import AI_Payload
from typing import List, Dict, Any

def run_router_llm(chatMessage: List[Dict[str, str]]):
    llm_payload = AI_Payload(
        model=config.ROUTER_MODEL,
        messages=chatMessage,
        temperature=config.DEFAULT_TEMPERATURE,
        think=config.ROUTER_THINK,
        stream=True,
        num_predict=config.ROUTER_NUM_PREDICT,
        num_ctx=config.ROUTER_NUM_CTX,
        max_tokens=config.ROUTER_MAX_TOKEN
    ).model_dump()

    response = requests.post(config.ROUTER_LLM_API_URL, json=llm_payload, stream=True, timeout=300)
    response.raise_for_status()

    result_text = ""
    for chunk in response.iter_content(decode_unicode=True):
        if chunk:
            try:
                result_text += chunk
            except Exception as e:
                print(f"[스트림 파싱 예외 발생]: {e}")

    result_text = result_text.strip()

    if result_text.startswith("```json"):
        result_text = result_text[7:]

    if result_text.startswith("```"):
        result_text = result_text[3:]

    if result_text.endswith("```"):
        result_text = result_text[:-3]

    return result_text

def run_llm_generator(chatMessage: List[Dict[str, str]]):
    llm_payload = AI_Payload(
        model=config.LLM_MODEL,
        messages=chatMessage,
        temperature=config.DEFAULT_TEMPERATURE,
        think=config.LLM_THINK,
        stream=True,
        num_predict=config.LLM_NUM_PREDICT,
        num_ctx=config.LLM_NUM_CTX,
        max_tokens=config.LLM_MAX_TOKEN
    ).model_dump()

    response = requests.post(config.LLM_API_URL, json=llm_payload, stream=True, timeout=300)
    response.raise_for_status()
    
    for index, chunk in enumerate(response.iter_content(decode_unicode=True)):
        if chunk:
            try:
                yield chunk
                    
            except Exception as e:
                print(f"[스트림 파싱 예외 발생]: {e}")

def run_vlm_generator(chatMessage: List[Dict[str, Any]], response_format: Dict[str, Any] | None = None):
    vlm_payload = AI_Payload(
            model=config.VLM_MODEL,
            messages=chatMessage,
            temperature=config.DEFAULT_TEMPERATURE,
            think=config.VLM_THINK,
            stream=True,
            num_predict=config.VLM_NUM_PREDICT,
            num_ctx=config.VLM_NUM_CTX,
            max_tokens=config.VLM_MAX_TOKEN
        ).model_dump()

    if response_format is not None:
        vlm_payload["format"] = response_format

    vlm_response = requests.post(config.VLM_API_URL, json=vlm_payload, stream=True, timeout=300)
    vlm_response.raise_for_status()

    for chunk in vlm_response.iter_content(decode_unicode=True):
        if chunk:
            try:
                yield chunk
                
            except Exception as e:
                print(f"[스트림 파싱 예외 발생]: {e}")
    