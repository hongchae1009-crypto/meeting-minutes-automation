"""
전사 텍스트 파일 파서
화자 N (MM:SS) 형식의 AI 전사 결과물을 파싱합니다.
"""
import re
from dataclasses import dataclass
from typing import Optional


@dataclass
class Utterance:
    speaker_id: str       # "1", "2", "3" 등
    speaker_name: str     # 매핑 후 실제 이름 ("홍길동" 등), 기본값은 "화자 N"
    timestamp: str        # "00:01"
    timestamp_seconds: int
    text: str


def parse_transcript(raw_text: str, speaker_map: dict[str, str] | None = None) -> list[Utterance]:
    """
    전사 텍스트를 파싱하여 Utterance 목록 반환
    speaker_map: {"1": "홍길동", "2": "김철수"} 형태
    """
    utterances: list[Utterance] = []
    speaker_map = speaker_map or {}

    # 화자 블록 패턴: "화자  N  (MM:SS)" 또는 "화자 N (MM:SS)"
    pattern = re.compile(
        r'화자\s+(\d+)\s+\((\d{2}:\d{2}(?::\d{2})?)\)\s*(.*?)(?=화자\s+\d+\s+\(|$)',
        re.DOTALL
    )

    for match in pattern.finditer(raw_text):
        speaker_id = match.group(1).strip()
        timestamp = match.group(2).strip()
        text = match.group(3).strip()

        # 빈 발화 제거
        if not text:
            continue

        # 타임스탬프 → 초 변환
        parts = timestamp.split(":")
        if len(parts) == 2:
            ts_seconds = int(parts[0]) * 60 + int(parts[1])
        else:
            ts_seconds = int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])

        # 화자 이름 결정
        speaker_name = speaker_map.get(speaker_id, f"화자 {speaker_id}")

        utterances.append(Utterance(
            speaker_id=speaker_id,
            speaker_name=speaker_name,
            timestamp=timestamp,
            timestamp_seconds=ts_seconds,
            text=text,
        ))

    return utterances


def read_transcript_file(file_path: str) -> str:
    """파일 인코딩 자동 감지 후 읽기 (UTF-16 BE/LE, UTF-8 순서로 시도)"""
    encodings = ["utf-16", "utf-16-be", "utf-16-le", "utf-8", "cp949"]
    for enc in encodings:
        try:
            with open(file_path, "r", encoding=enc) as f:
                content = f.read()
            if "화자" in content:
                return content
        except (UnicodeDecodeError, UnicodeError):
            continue
    raise ValueError(f"파일을 읽을 수 없습니다: {file_path}")


def read_transcript_bytes(file_bytes: bytes) -> str:
    """업로드된 바이트 데이터에서 전사 텍스트 읽기"""
    encodings = ["utf-16", "utf-16-be", "utf-16-le", "utf-8", "cp949"]
    for enc in encodings:
        try:
            content = file_bytes.decode(enc)
            if "화자" in content:
                return content
        except (UnicodeDecodeError, UnicodeError):
            continue
    raise ValueError("지원하지 않는 파일 인코딩입니다.")


def get_speakers(utterances: list[Utterance]) -> list[str]:
    """발화 목록에서 등장하는 화자 ID 목록 반환 (순서 유지)"""
    seen = set()
    result = []
    for u in utterances:
        if u.speaker_id not in seen:
            seen.add(u.speaker_id)
            result.append(u.speaker_id)
    return result


def utterances_to_text(utterances: list[Utterance]) -> str:
    """Utterance 목록을 Claude 처리용 텍스트로 변환"""
    lines = []
    for u in utterances:
        lines.append(f"[{u.timestamp}] {u.speaker_name}: {u.text}")
    return "\n".join(lines)
