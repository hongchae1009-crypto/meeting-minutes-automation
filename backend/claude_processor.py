"""
AI API를 사용하여 전사 텍스트에서 구조화된 회의록을 생성합니다.
Gemini 또는 Claude API 지원 (GEMINI_API_KEY 있으면 Gemini 우선 사용)
"""
import json
import os
from dataclasses import dataclass, asdict
from typing import Literal


@dataclass
class ActionItem:
    id: str
    assignee: str
    task: str
    deadline: str
    confidence: Literal["확실", "추정"]
    timestamp: str
    source_text: str
    jira_issue_key: str = ""


@dataclass
class ReviewItem:
    timestamp: str
    speaker: str
    text: str
    reason: str


@dataclass
class MeetingMinutes:
    title: str
    summary: str
    discussions: list[dict]
    decisions: list[str]
    action_items: list[ActionItem]
    review_items: list[ReviewItem]
    next_meeting: str


SYSTEM_PROMPT = """당신은 회의록 작성 전문가입니다. 전사된 회의 내용을 분석하여 구조화된 회의록을 JSON 형식으로 작성합니다.

규칙:
1. 업무 관련 내용만 포함합니다 (프로젝트, 일정, 결정사항, 기술 논의)
2. 잡담, 감탄사, 순수 사교적 발화는 제외합니다
3. 판단이 불명확한 발화는 review_items에 포함합니다
4. 비선형적으로 논의된 동일 주제는 하나의 섹션으로 통합합니다
5. 액션 아이템의 담당자가 불명확한 경우 assignee를 "미정"으로 표시합니다
6. 기한이 언급되지 않은 경우 deadline을 "미정"으로 표시합니다
7. 확실한 지시사항(~해주세요, ~해야 합니다 등)은 confidence를 "확실"로,
   암묵적·추정 할 일(~할 것 같다, ~하면 좋겠다 등)은 "추정"으로 표시합니다

출력 형식 (반드시 유효한 JSON만 출력, 다른 텍스트 없이):
{
  "title": "회의 제목 (내용 기반 자동 생성)",
  "summary": "2~3문장 회의 요약",
  "discussions": [
    {"topic": "논의 주제", "content": "논의 내용 요약"}
  ],
  "decisions": ["결정사항 1", "결정사항 2"],
  "action_items": [
    {
      "id": "ai_1",
      "assignee": "담당자 이름 또는 미정",
      "task": "수행할 업무 내용",
      "deadline": "YYYY-MM-DD 또는 미정",
      "confidence": "확실 또는 추정",
      "timestamp": "MM:SS",
      "source_text": "원본 발화 내용 (20자 이내로 요약)"
    }
  ],
  "review_items": [
    {
      "timestamp": "MM:SS",
      "speaker": "화자 이름",
      "text": "발화 내용",
      "reason": "잡담인지 업무 발화인지 불명확한 이유"
    }
  ],
  "next_meeting": "다음 회의 일정 (언급된 경우) 또는 미정"
}"""


def _extract_json(raw: str) -> dict:
    """마크다운 코드블록 제거 후 JSON 파싱"""
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    if raw.endswith("```"):
        raw = raw.rsplit("```", 1)[0]
    return json.loads(raw.strip())


def _call_gemini(transcript_text: str, meeting_date: str) -> str:
    """Gemini REST API 직접 호출"""
    import requests
    api_key = os.environ["GEMINI_API_KEY"]
    prompt = f"""다음은 {meeting_date} 회의의 전사 텍스트입니다. 구조화된 회의록을 JSON으로 작성해주세요.

[전사 텍스트]
{transcript_text}

반드시 유효한 JSON만 출력하세요."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    payload = {
        "contents": [{"parts": [{"text": SYSTEM_PROMPT + "\n\n" + prompt}]}],
        "generationConfig": {
            "temperature": 0.2,
            "thinkingConfig": {"thinkingBudget": 0},
        },
    }
    resp = requests.post(url, json=payload, timeout=120)
    if not resp.ok:
        raise ValueError(f"Gemini API error {resp.status_code}: {resp.text}")
    data = resp.json()
    return data["candidates"][0]["content"]["parts"][0]["text"]


def _call_claude(transcript_text: str, meeting_date: str) -> str:
    """Claude API 호출"""
    import anthropic
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    prompt = f"""다음은 {meeting_date} 회의의 전사 텍스트입니다. 구조화된 회의록을 JSON으로 작성해주세요.

[전사 텍스트]
{transcript_text}

반드시 유효한 JSON만 출력하세요."""
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text


def process_transcript(
    transcript_text: str,
    meeting_date: str,
    client=None,
    model: str = "",
) -> MeetingMinutes:
    """
    전사 텍스트를 AI API로 처리하여 구조화된 회의록 반환
    GEMINI_API_KEY 있으면 Gemini 사용, 없으면 Claude 사용
    """
    if os.environ.get("GEMINI_API_KEY"):
        raw = _call_gemini(transcript_text, meeting_date)
    else:
        raw = _call_claude(transcript_text, meeting_date)

    data = _extract_json(raw)

    action_items = [
        ActionItem(
            id=item.get("id", f"ai_{i}"),
            assignee=item.get("assignee", "미정"),
            task=item.get("task", ""),
            deadline=item.get("deadline", "미정"),
            confidence=item.get("confidence", "추정"),
            timestamp=item.get("timestamp", ""),
            source_text=item.get("source_text", ""),
        )
        for i, item in enumerate(data.get("action_items", []))
    ]

    review_items = [
        ReviewItem(
            timestamp=item.get("timestamp", ""),
            speaker=item.get("speaker", ""),
            text=item.get("text", ""),
            reason=item.get("reason", ""),
        )
        for item in data.get("review_items", [])
    ]

    return MeetingMinutes(
        title=data.get("title", f"{meeting_date} 회의"),
        summary=data.get("summary", ""),
        discussions=data.get("discussions", []),
        decisions=data.get("decisions", []),
        action_items=action_items,
        review_items=review_items,
        next_meeting=data.get("next_meeting", "미정"),
    )


def minutes_to_dict(minutes: MeetingMinutes) -> dict:
    return {
        "title": minutes.title,
        "summary": minutes.summary,
        "discussions": minutes.discussions,
        "decisions": minutes.decisions,
        "action_items": [asdict(ai) for ai in minutes.action_items],
        "review_items": [asdict(ri) for ri in minutes.review_items],
        "next_meeting": minutes.next_meeting,
    }
