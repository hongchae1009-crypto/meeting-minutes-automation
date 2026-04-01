"""
Jira REST API v3 클라이언트
액션 아이템 → Jira 이슈 생성, 기존 이슈 댓글 추가, Confluence 링크
"""
import requests
from requests.auth import HTTPBasicAuth
from dataclasses import dataclass


@dataclass
class JiraIssue:
    key: str       # "RD-178"
    id: str
    url: str
    summary: str


class JiraClient:
    def __init__(self, domain: str, email: str, api_token: str):
        """
        domain: yourcompany.atlassian.net
        email: Atlassian 계정 이메일
        api_token: Atlassian API 토큰
        """
        self.base_url = f"https://{domain}/rest/api/3"
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

    # ── 프로젝트 / 사용자 조회 ─────────────────────────────────────────────────

    def get_projects(self) -> list[dict]:
        """접근 가능한 Jira 프로젝트 목록"""
        data = self._req("GET", "/project/search", params={"maxResults": 50})
        return [
            {"key": p["key"], "name": p["name"], "id": p["id"]}
            for p in data.get("values", [])
        ]

    def get_users(self, project_key: str) -> list[dict]:
        """프로젝트에서 이슈를 할당받을 수 있는 사용자 목록"""
        data = self._req(
            "GET", "/user/assignable/search",
            params={"project": project_key, "maxResults": 50},
        )
        return [
            {"accountId": u["accountId"], "displayName": u.get("displayName", ""), "email": u.get("emailAddress", "")}
            for u in data
        ]

    def get_issue_types(self, project_key: str) -> list[dict]:
        """프로젝트의 이슈 유형 목록"""
        data = self._req("GET", f"/project/{project_key}")
        return [
            {"id": it["id"], "name": it["name"]}
            for it in data.get("issueTypes", [])
        ]

    # ── 이슈 생성 ─────────────────────────────────────────────────────────────

    def create_issue(
        self,
        project_key: str,
        summary: str,
        description: str,
        issue_type: str = "Task",
        assignee_account_id: str | None = None,
        due_date: str | None = None,          # "YYYY-MM-DD"
        confluence_page_url: str | None = None,
    ) -> JiraIssue:
        """Jira 이슈 생성"""

        # ADF(Atlassian Document Format) 설명 본문
        desc_content = [
            {
                "type": "paragraph",
                "content": [{"type": "text", "text": description}],
            }
        ]
        if confluence_page_url:
            desc_content.append({
                "type": "paragraph",
                "content": [
                    {"type": "text", "text": "📄 회의록: "},
                    {
                        "type": "inlineCard",
                        "attrs": {"url": confluence_page_url},
                    },
                ],
            })

        fields: dict = {
            "project": {"key": project_key},
            "summary": summary,
            "issuetype": {"name": issue_type},
            "description": {
                "type": "doc",
                "version": 1,
                "content": desc_content,
            },
        }
        if assignee_account_id:
            fields["assignee"] = {"accountId": assignee_account_id}
        if due_date and due_date != "미정":
            fields["duedate"] = due_date

        data = self._req("POST", "/issue", json={"fields": fields})
        issue_key = data["key"]
        issue_id = data["id"]
        issue_url = f"https://{self.domain}/browse/{issue_key}"
        return JiraIssue(key=issue_key, id=issue_id, url=issue_url, summary=summary)

    # ── 댓글 추가 ─────────────────────────────────────────────────────────────

    def add_comment(
        self,
        issue_key: str,
        meeting_title: str,
        meeting_date: str,
        summary: str,
        confluence_page_url: str | None = None,
    ) -> dict:
        """기존 Jira 이슈에 회의 내용 댓글 추가"""

        content = [
            {
                "type": "paragraph",
                "content": [
                    {"type": "text", "text": f"🗓 ", "marks": []},
                    {"type": "text", "text": f"{meeting_date} 회의에서 논의됨", "marks": [{"type": "strong"}]},
                ],
            },
            {
                "type": "paragraph",
                "content": [{"type": "text", "text": f"회의명: {meeting_title}"}],
            },
            {
                "type": "paragraph",
                "content": [{"type": "text", "text": summary}],
            },
        ]
        if confluence_page_url:
            content.append({
                "type": "paragraph",
                "content": [
                    {"type": "text", "text": "📄 전체 회의록: "},
                    {"type": "inlineCard", "attrs": {"url": confluence_page_url}},
                ],
            })

        return self._req(
            "POST", f"/issue/{issue_key}/comment",
            json={"body": {"type": "doc", "version": 1, "content": content}},
        )

    # ── Confluence 원격 링크 ──────────────────────────────────────────────────

    def add_confluence_link(self, issue_key: str, confluence_page_url: str, page_title: str):
        """Jira 이슈에 Confluence 페이지 원격 링크 추가"""
        try:
            self._req(
                "POST", f"/issue/{issue_key}/remotelink",
                json={
                    "globalId": f"confluence-{confluence_page_url}",
                    "object": {
                        "url": confluence_page_url,
                        "title": page_title,
                        "icon": {
                            "url16x16": "https://confluence.atlassian.com/favicon.ico",
                            "title": "Confluence",
                        },
                    },
                },
            )
        except Exception:
            pass  # 원격 링크 실패는 무시 (권한 문제일 수 있음)
