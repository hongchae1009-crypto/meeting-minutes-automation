"""
Confluence REST API v2 클라이언트
회의록 페이지 생성 및 Jira 링크 연동
"""
import os
import requests
from requests.auth import HTTPBasicAuth
from dataclasses import dataclass


@dataclass
class ConfluencePage:
    id: str
    title: str
    url: str
    space_key: str


class ConfluenceClient:
    def __init__(self, domain: str, email: str, api_token: str):
        """
        domain: yourcompany.atlassian.net
        email: Atlassian 계정 이메일
        api_token: https://id.atlassian.com/manage-profile/security/api-tokens
        """
        self.base_url = f"https://{domain}/wiki/api/v2"
        self.auth = HTTPBasicAuth(email, api_token)
        self.headers = {"Accept": "application/json", "Content-Type": "application/json"}
        self.domain = domain

    def _req(self, method: str, path: str, **kwargs) -> dict:
        resp = requests.request(
            method,
            f"{self.base_url}{path}",
            auth=self.auth,
            headers=self.headers,
            **kwargs,
        )
        resp.raise_for_status()
        return resp.json() if resp.text else {}

    # ── 스페이스 ──────────────────────────────────────────────────────────────

    def get_spaces(self) -> list[dict]:
        """접근 가능한 Confluence 스페이스 목록"""
        data = self._req("GET", "/spaces", params={"limit": 50})
        return [{"key": s["key"], "name": s["name"], "id": s["id"]}
                for s in data.get("results", [])]

    # ── 페이지 ──────────────────────────────────────────────────────────────

    def get_pages_in_space(self, space_key: str) -> list[dict]:
        """스페이스 내 최상위 페이지 목록 (부모 페이지 선택용)"""
        data = self._req(
            "GET", "/pages",
            params={"spaceKey": space_key, "depth": "root", "limit": 50},
        )
        return [{"id": p["id"], "title": p["title"]} for p in data.get("results", [])]

    def create_page(
        self,
        space_key: str,
        title: str,
        body_html: str,
        parent_id: str | None = None,
    ) -> ConfluencePage:
        """HTML 본문으로 Confluence 페이지 생성"""
        payload: dict = {
            "spaceId": self._get_space_id(space_key),
            "status": "current",
            "title": title,
            "body": {
                "representation": "storage",
                "value": body_html,
            },
        }
        if parent_id:
            payload["parentId"] = parent_id

        data = self._req("POST", "/pages", json=payload)
        page_id = data["id"]
        page_url = f"https://{self.domain}/wiki/spaces/{space_key}/pages/{page_id}"
        return ConfluencePage(id=page_id, title=title, url=page_url, space_key=space_key)

    def _get_space_id(self, space_key: str) -> str:
        data = self._req("GET", "/spaces", params={"keys": space_key, "limit": 1})
        results = data.get("results", [])
        if not results:
            raise ValueError(f"스페이스를 찾을 수 없습니다: {space_key}")
        return results[0]["id"]

    # ── Jira 원격 링크 ────────────────────────────────────────────────────────

    def add_jira_link_to_page(self, page_id: str, jira_issue_key: str, jira_domain: str, issue_title: str):
        """Confluence 페이지에 Jira 이슈 원격 링크 추가 (v1 API 사용)"""
        url = f"https://{self.domain}/wiki/rest/api/content/{page_id}/child/attachment"
        # Confluence v1 remote links endpoint
        link_url = f"https://{self.domain}/wiki/rest/api/content/{page_id}/remotelinks" if False else None

        # Jira Smart Link 방식: 페이지 본문에 인라인으로 처리하므로
        # 여기서는 metadata용 레이블 추가로 대체
        try:
            requests.post(
                f"https://{self.domain}/wiki/rest/api/content/{page_id}/label",
                auth=self.auth,
                headers=self.headers,
                json=[{"prefix": "global", "name": f"jira-{jira_issue_key.lower()}"}],
            )
        except Exception:
            pass  # 레이블 추가 실패는 무시


# ── 회의록 HTML 생성 ──────────────────────────────────────────────────────────

def build_confluence_html(
    minutes: dict,
    meeting_date: str,
    attendees: list[str],
    action_items_with_jira: list[dict],
) -> str:
    """회의록 dict를 Confluence Storage Format HTML로 변환"""

    # 요약
    summary_html = f"<p>{minutes.get('summary', '')}</p>"

    # 주요 논의
    discussions = minutes.get("discussions", [])
    disc_html = ""
    for d in discussions:
        disc_html += f"<h3>{d.get('topic', '')}</h3><p>{d.get('content', '')}</p>"

    # 결정사항
    decisions = minutes.get("decisions", [])
    dec_html = "".join(f"<li>{d}</li>" for d in decisions)
    dec_html = f"<ul>{dec_html}</ul>" if dec_html else "<p>없음</p>"

    # 액션 아이템 테이블
    rows = ""
    for ai in action_items_with_jira:
        jira_key = ai.get("jira_issue_key", "")
        jira_cell = f'<a href="{ai.get("jira_url", "")}">{jira_key}</a>' if jira_key else "-"
        badge = "✅" if ai.get("confidence") == "확실" else "⚠️"
        rows += (
            f"<tr>"
            f"<td>{ai.get('assignee', '미정')}</td>"
            f"<td>{badge} {ai.get('task', '')}</td>"
            f"<td>{ai.get('deadline', '미정')}</td>"
            f"<td>{jira_cell}</td>"
            f"</tr>"
        )
    action_table = f"""
<table>
  <thead>
    <tr><th>담당자</th><th>업무 내용</th><th>기한</th><th>Jira</th></tr>
  </thead>
  <tbody>{rows}</tbody>
</table>""" if rows else "<p>없음</p>"

    # 참석자
    attendees_str = ", ".join(attendees) if attendees else "미정"

    html = f"""
<ac:structured-macro ac:name="info">
  <ac:rich-text-body>
    <p><strong>회의 일시:</strong> {meeting_date} &nbsp;|&nbsp;
       <strong>참석자:</strong> {attendees_str}</p>
  </ac:rich-text-body>
</ac:structured-macro>

<h2>회의 요약</h2>
{summary_html}

<h2>주요 논의 내용</h2>
{disc_html if disc_html else '<p>없음</p>'}

<h2>결정사항</h2>
{dec_html}

<h2>액션 아이템</h2>
{action_table}

<h2>다음 회의</h2>
<p>{minutes.get('next_meeting', '미정')}</p>
"""
    return html
