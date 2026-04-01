"""
FastAPI 백엔드 서버
회의록 자동화 시스템의 모든 API 엔드포인트
"""
import os
from datetime import datetime
from typing import Annotated

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from claude_processor import MeetingMinutes, minutes_to_dict, process_transcript
from confluence_client import ConfluenceClient, build_confluence_html
from jira_client import JiraClient
from text_parser import get_speakers, parse_transcript, read_transcript_bytes, utterances_to_text

load_dotenv(override=True)

app = FastAPI(title="회의록 자동화 API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── 헬퍼 ─────────────────────────────────────────────────────────────────────

def _get_confluence(domain: str, email: str, token: str) -> ConfluenceClient:
    return ConfluenceClient(domain=domain, email=email, api_token=token)

def _get_jira(domain: str, email: str, token: str) -> JiraClient:
    return JiraClient(domain=domain, email=email, api_token=token)


# ── 요청/응답 스키마 ──────────────────────────────────────────────────────────

class AtlassianCreds(BaseModel):
    domain: str        # yourcompany.atlassian.net
    email: str
    api_token: str


class PublishRequest(BaseModel):
    minutes: dict                         # MeetingMinutes dict
    meeting_title: str
    meeting_date: str
    attendees: list[str]
    # Confluence
    confluence_domain: str
    confluence_email: str
    confluence_token: str
    confluence_space_key: str
    confluence_parent_id: str | None = None
    # Jira
    jira_domain: str
    jira_email: str
    jira_token: str
    jira_project_key: str
    jira_issue_type: str = "Task"
    jira_user_map: dict[str, str] = {}    # assignee 이름 → accountId
    # 기존 이슈에 댓글 추가
    existing_issue_keys: list[str] = []


# ── 1. 파일 파싱 ──────────────────────────────────────────────────────────────

@app.post("/api/parse")
async def parse_file(file: UploadFile = File(...)):
    """전사 텍스트 파일 업로드 → 화자 목록 + 미리보기 반환"""
    try:
        raw_bytes = await file.read()
        text = read_transcript_bytes(raw_bytes)
        utterances = parse_transcript(text)
        speakers = get_speakers(utterances)
        preview = utterances_to_text(utterances[:10])  # 처음 10개 발화 미리보기
        return {
            "speakers": speakers,
            "total_utterances": len(utterances),
            "preview": preview,
            "raw_text": text,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ── 2. Claude 처리 ────────────────────────────────────────────────────────────

class ProcessRequest(BaseModel):
    raw_text: str
    speaker_map: dict[str, str]   # {"1": "홍길동", "2": "김철수"}
    meeting_date: str


@app.post("/api/process")
async def process(req: ProcessRequest):
    """전사 텍스트 + 화자 매핑 → AI API 처리 → 구조화된 회의록 반환"""
    try:
        utterances = parse_transcript(req.raw_text, req.speaker_map)
        transcript_text = utterances_to_text(utterances)

        minutes = process_transcript(
            transcript_text=transcript_text,
            meeting_date=req.meeting_date,
        )
        return minutes_to_dict(minutes)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── 3. Confluence 스페이스 목록 ───────────────────────────────────────────────

@app.get("/api/confluence/spaces")
async def confluence_spaces(domain: str, email: str, token: str):
    try:
        client = _get_confluence(domain, email, token)
        return {"spaces": client.get_spaces()}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/confluence/pages")
async def confluence_pages(domain: str, email: str, token: str, space_key: str):
    try:
        client = _get_confluence(domain, email, token)
        return {"pages": client.get_pages_in_space(space_key)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ── 4. Jira 프로젝트 / 사용자 목록 ───────────────────────────────────────────

@app.get("/api/jira/projects")
async def jira_projects(domain: str, email: str, token: str):
    try:
        client = _get_jira(domain, email, token)
        return {"projects": client.get_projects()}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/jira/users")
async def jira_users(domain: str, email: str, token: str, project_key: str):
    try:
        client = _get_jira(domain, email, token)
        return {"users": client.get_users(project_key)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ── 5. 게시 (Confluence + Jira) ───────────────────────────────────────────────

@app.post("/api/publish")
async def publish(req: PublishRequest):
    """Confluence 회의록 페이지 생성 + Jira 이슈 생성 + 기존 이슈 댓글 추가"""
    confluence = _get_confluence(req.confluence_domain, req.confluence_email, req.confluence_token)
    jira = _get_jira(req.jira_domain, req.jira_email, req.jira_token)

    minutes = req.minutes
    action_items = minutes.get("action_items", [])
    created_issues: list[dict] = []
    errors: list[str] = []

    # Step 1: Jira 이슈 먼저 생성 (Confluence 페이지에 링크 삽입용)
    for ai in action_items:
        if not ai.get("task"):
            continue
        try:
            assignee_id = req.jira_user_map.get(ai.get("assignee", ""))
            issue = jira.create_issue(
                project_key=req.jira_project_key,
                summary=ai["task"],
                description=f"회의 출처: {req.meeting_title} ({req.meeting_date})\n원본 발화: {ai.get('source_text', '')}",
                issue_type=req.jira_issue_type,
                assignee_account_id=assignee_id or None,
                due_date=ai.get("deadline"),
            )
            ai["jira_issue_key"] = issue.key
            ai["jira_url"] = issue.url
            created_issues.append({"key": issue.key, "url": issue.url, "summary": issue.summary})
        except Exception as e:
            errors.append(f"Jira 이슈 생성 실패 ({ai.get('task', '')}): {str(e)}")

    # Step 2: Confluence 페이지 생성
    try:
        html_body = build_confluence_html(
            minutes=minutes,
            meeting_date=req.meeting_date,
            attendees=req.attendees,
            action_items_with_jira=action_items,
        )
        page = confluence.create_page(
            space_key=req.confluence_space_key,
            title=req.meeting_title,
            body_html=html_body,
            parent_id=req.confluence_parent_id,
        )
        confluence_page_url = page.url
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Confluence 페이지 생성 실패: {str(e)}")

    # Step 3: Jira 이슈에 Confluence 링크 추가
    for issue_dict in created_issues:
        try:
            jira.add_confluence_link(issue_dict["key"], confluence_page_url, req.meeting_title)
        except Exception:
            pass

    # Step 4: 기존 이슈에 댓글 추가
    commented_issues: list[dict] = []
    for issue_key in req.existing_issue_keys:
        if not issue_key.strip():
            continue
        try:
            jira.add_comment(
                issue_key=issue_key.strip(),
                meeting_title=req.meeting_title,
                meeting_date=req.meeting_date,
                summary=minutes.get("summary", ""),
                confluence_page_url=confluence_page_url,
            )
            commented_issues.append({"key": issue_key.strip(), "url": f"https://{req.jira_domain}/browse/{issue_key.strip()}"})
        except Exception as e:
            errors.append(f"댓글 추가 실패 ({issue_key}): {str(e)}")

    return {
        "confluence_page": {"url": confluence_page_url, "title": req.meeting_title},
        "created_jira_issues": created_issues,
        "commented_issues": commented_issues,
        "errors": errors,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
