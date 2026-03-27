import json
import os
from openai import OpenAI
from dotenv import load_dotenv
import streamlit as st

load_dotenv()
client = OpenAI()


st.set_page_config(
    page_title="5살 체하딤 양치시키기",
    page_icon="🪥",
    layout="centered"
)

def get_system_prompt():
    return """
당신은 5살 아이 '체하딤'입니다.

지금은 자기 전 양치 시간입니다.
하지만 당신은 양치가 싫어서 도망다니고 있습니다.

[캐릭터 설정]
- 치약이 맵다고 느낍니다
- 노는 걸 더 좋아합니다
- 공감해주면 마음이 약해집니다
- 강압적으로 말하면 더 반항합니다
- 반드시 5살 아이처럼 짧고 귀엽고 서툰 말투를 사용하세요
- 너무 어른스럽고 논리적인 말투는 사용하지 마세요

[좋은 말투 예시]
- "시러! 치카치카 안 해!"
- "조금만 할래…"
- "매워…"
- "같이 하면 할래"
- "아아~ 해써!"
- "헤헤 나 잘했지!"

[나쁜 말투 예시]
- "알겠어. 양치를 시작할게."
- "고마워. 이제 해볼게."
- "양치를 하는 것이 좋겠어."

[상태 설명]
- stubbornness (고집): 0~100
- trust (신뢰): 0~100
- brushing_progress (양치 진행도): 0~100
- stage (단계):
    - "runaway"     : 도망 중
    - "bathroom"    : 화장실 옴
    - "toothbrush"  : 칫솔 잡음
    - "open_mouth"  : 입 벌림
    - "brushing"    : 닦는 중
    - "rinse"       : 헹구기

[반응 규칙]
1. 논리적 설명("양치 안 하면 충치 생겨") → 효과 약함, 고집 약간 증가
2. 강압적 말투("빨리 와", "안 하면 혼난다") → 고집 크게 증가, 신뢰 감소
3. 공감("무서웠구나", "같이 하자") → 신뢰 증가
4. 놀이/상상("충치 괴물 잡자", "사자처럼 아~") → 신뢰 + 진행도 증가
5. 칭찬과 보상 예고 → 진행도 증가 가능
6. 상태 변화는 이전 상태를 반영해서 자연스럽게 이어가세요

[출력 규칙]
- 반드시 JSON 객체 하나로만 응답하세요
- 설명문, 해설, 마크다운, 코드블록은 쓰지 마세요
- response는 반드시 아이의 실제 대사처럼 짧게 작성하세요

[출력 형식]
{
  "stubbornness": 0~100 사이의 정수,
  "trust": 0~100 사이의 정수,
  "brushing_progress": 0~100 사이의 정수,
  "stage": "runaway 또는 bathroom 또는 toothbrush 또는 open_mouth 또는 brushing 또는 rinse",
  "response": "5살 체하딤의 짧고 귀엽고 서툰 말투 대사"
}
"""


def init_game():
    system_prompt = get_system_prompt()

    st.session_state.messages = [
        {"role": "system", "content": system_prompt},
        {
            "role": "assistant",
            "content": json.dumps(
                {
                    "stubbornness": 60,
                    "trust": 20,
                    "brushing_progress": 0,
                    "stage": "runaway",
                    "response": "시러!! 치카치카 안 해!! 나 도망갈 거야!!"
                },
                ensure_ascii=False
            )
        }
    ]

    st.session_state.chat_log = [
        {"role": "assistant", "content": "시러!! 치카치카 안 해!! 나 도망갈 거야!!"}
    ]

    st.session_state.stubbornness = 60
    st.session_state.trust = 20
    st.session_state.progress = 0
    st.session_state.stage = "runaway"
    st.session_state.turn = 0
    st.session_state.max_turns = 10
    st.session_state.game_over = False
    st.session_state.result_text = ""


def get_child_response(messages):
    response = client.chat.completions.create(
        model="ft:gpt-3.5-turbo-0125:personal:stubborn-child:DNND59Dw",
        messages=messages,
        response_format={"type": "json_object"},
        temperature=0.7
    )

    return json.loads(response.choices[0].message.content)


def adjust_progress(stage, progress):
    if stage == "runaway":
        return 0
    elif stage == "bathroom":
        return max(progress, 5)
    elif stage == "toothbrush":
        return max(progress, 15)
    elif stage == "open_mouth":
        return max(progress, 30)
    elif stage == "brushing":
        return max(progress, 50)
    elif stage == "rinse":
        return max(progress, 90)
    return progress


def check_game_result():
    if st.session_state.stubbornness >= 100:
        st.session_state.game_over = True
        st.session_state.result_text = "💥 GAME OVER: 체하딤이 울음 폭발했어..."
    elif st.session_state.progress >= 100:
        st.session_state.game_over = True
        st.session_state.result_text = "🎉 SUCCESS: 체하딤 양치 완료!!"


if "messages" not in st.session_state:
    init_game()

st.title("🪥 5살 체하딤 양치시키기 ! ")
st.caption("10턴 안에 체하딤의 양치를 완료해보자!")

with st.expander("🎮 게임 설명 보기"):
    st.markdown("""
### 🎮 게임 설명

👶 체하딤은 양치가 너무 싫은 5살 아이입니다.  
당신은 체하딤을 설득해서 **양치를 끝까지 완료**해야 합니다.

---

### 🎯 목표
- 총 **10턴 안에 양치 진행도 100% 달성**
- 성공하면 🎉, 실패하면 😭

---

### 📊 상태 지표
- 😡 **고집 (stubbornness)**: 높을수록 말 안 들음 (100이면 폭발 💥)
- 🤝 **신뢰 (trust)**: 높을수록 설득 잘 됨
- 🪥 **진행도 (progress)**: 100이 되면 양치 성공

---

### 🧭 진행 단계
- 🏃 도망 중
- 🚿 화장실 옴
- 🪥 칫솔 잡음 
- 😮 입 벌림
- 🧼 닦는 중
- 💦 헹구기

---

### 💡 공략 팁
- ❌ 강압적 말투 → 고집 상승
- ⭕ 공감 & 칭찬 → 신뢰 상승
- 🎭 놀이 & 상상 → 진행도 상승

👉 5살 체하딤의 마음을 잘 읽어야 성공할 수 있습니다!
""")

col1, col2 = st.columns([3, 1])

with col2:
    if st.button("다시 시작"):
        init_game()
        st.rerun()

st.subheader("현재 상태")

c1, c2, c3 = st.columns(3)

with c1:
    st.metric("😡 고집", st.session_state.stubbornness)
    st.progress(st.session_state.stubbornness / 100)

with c2:
    st.metric("🤝 신뢰", st.session_state.trust)
    st.progress(st.session_state.trust / 100)

with c3:
    st.metric("🪥 진행도", st.session_state.progress)
    st.progress(st.session_state.progress / 100)

stage_map = {
    "runaway": "도망 중",
    "bathroom": "화장실 옴",
    "toothbrush": "칫솔 잡음",
    "open_mouth": "입 벌림",
    "brushing": "닦는 중",
    "rinse": "헹구기"
}

st.info(
    f"📍 현재 단계: {stage_map.get(st.session_state.stage, st.session_state.stage)} | "
    f"턴: {st.session_state.turn}/{st.session_state.max_turns}"
)

st.subheader("대화")

for msg in st.session_state.chat_log:
    with st.chat_message("assistant" if msg["role"] == "assistant" else "user"):
        st.write(msg["content"])

if st.session_state.game_over:
    st.success(st.session_state.result_text)

elif st.session_state.turn >= st.session_state.max_turns:
    st.warning("⏳ TIME OVER: 결국 양치 실패...")
    st.session_state.game_over = True

else:
    user_input = st.chat_input("체하딤에게 뭐라고 말할까?")

    if user_input:
        st.session_state.turn += 1

        st.session_state.chat_log.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.write(user_input)

        st.session_state.messages.append({"role": "user", "content": user_input})

        try:
            result = get_child_response(st.session_state.messages)

            stage = result["stage"]
            progress = result["brushing_progress"]
            progress = adjust_progress(stage, progress)

            st.session_state.stubbornness = result["stubbornness"]
            st.session_state.trust = result["trust"]
            st.session_state.progress = progress
            st.session_state.stage = stage

            child_reply = result["response"]
            result["brushing_progress"] = progress

            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": json.dumps(result, ensure_ascii=False)
                }
            )

            st.session_state.chat_log.append({"role": "assistant", "content": child_reply})

            with st.chat_message("assistant"):
                st.write(child_reply)

            check_game_result()

            if (not st.session_state.game_over) and st.session_state.turn >= st.session_state.max_turns:
                st.warning("⏳ TIME OVER: 결국 양치 실패...")
                st.session_state.game_over = True

            st.rerun()

        except Exception as e:
            st.error(f"오류가 발생했어: {e}")