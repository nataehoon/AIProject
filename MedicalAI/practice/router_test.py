from services.chat_service import ChatService
import time
import json

user_prompt = [
    "오늘 기분이 어때?",
    "우산을 챙기는게 좋을까?",
    "무릎이 시린데 날씨랑 연관이 있는건가?",
    "어깨가 아픈데 어느 병원을 가는게 좋을까?",
    "아침에 기버터 한스쿱 먹는게 건강에 좋아?",
    "최근 무릎 십자인대 수술을 했는데 재활은 언제부터 시작하는게 좋을까?",
    "공복시 혈당이 150이 나왔는데 나쁜거야?",
    "어제 발목을 접질러서 부었는데 수영해도 될까?",
    "사무직인데 장시간 일하면 두통이 생기는데 원인이 뭐야?",
    "타이레놀 먹었는데 저녁에 회식이라 술 마셔도 돼?",
    "일을 오래하면 손끝이 저리고 손목이 아파 왜그런거야?",
    "팔꿈치가 착색돼서 까매지는건 왜그러는거야?"
]

summary_prompt = "오늘은 구름이 많고 흐립니다. 오후에 태풍 영향으로 장맛비가 내릴 예정입니다."
assistant_prompt = "오늘은 구름이 많고 흐립니다. 오후에 태풍 영향으로 장맛비가 내릴 예정입니다."

CONTEXT_LABEL = {
    "new_topic": "새 주제",
    "continuation": "연속 질문"
}

RETRIEVAL_LABEL = {
    True: "RAG",
    False: "None-RAG"
}


for index, test in enumerate(user_prompt):
    recent_chatMessage = [{"role": "assistant", "content": assistant_prompt}, {"role": "user", "content": test}]
    start = time.perf_counter()
    result = ChatService.run_rout(recent_chatMessage, summary_prompt)
    end = time.perf_counter()

    json_data = json.loads(result)
    context_relation = json_data.get("context_relation")
    retrieval = json_data.get("retrieval_required")
    sources = ", ".join(json_data.get("sources"))
    body_part = ", ".join(json_data.get("body_part"))
    reasoning_level = json_data.get("reasoning_level")
    route = json_data.get("route")

    print_text = f"[{index+1}. {test} | {CONTEXT_LABEL[context_relation]} | {RETRIEVAL_LABEL[retrieval]} | {body_part} | {sources} | {reasoning_level} | {route} | 소요 시간: {end-start:.3f}s]"
    print(print_text)