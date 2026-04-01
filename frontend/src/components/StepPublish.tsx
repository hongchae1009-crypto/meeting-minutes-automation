import { useEffect, useState } from 'react'
import { getConfluenceSpaces, getJiraProjects, getJiraUsers } from '../api/client'
import type { AtlassianProject, AtlassianSpace, AtlassianUser, WizardState } from '../types'

interface Props {
  state: WizardState
  setState: React.Dispatch<React.SetStateAction<WizardState>>
  onPublish: () => void
  onBack: () => void
}

export default function StepPublish({ state, setState, onPublish, onBack }: Props) {
  const [spaces, setSpaces] = useState<AtlassianSpace[]>([])
  const [projects, setProjects] = useState<AtlassianProject[]>([])
  const [jiraUsers, setJiraUsers] = useState<AtlassianUser[]>([])
  const [loadingSpaces, setLoadingSpaces] = useState(false)
  const [loadingProjects, setLoadingProjects] = useState(false)
  const [loadingUsers, setLoadingUsers] = useState(false)
  const [credError, setCredError] = useState('')

  const s = state

  function set(field: keyof WizardState, value: string) {
    setState(prev => ({ ...prev, [field]: value }))
  }

  async function fetchSpaces() {
    if (!s.confluenceDomain || !s.confluenceEmail || !s.confluenceToken) return
    setLoadingSpaces(true)
    setCredError('')
    try {
      const data = await getConfluenceSpaces(s.confluenceDomain, s.confluenceEmail, s.confluenceToken)
      setSpaces(data)
    } catch {
      setCredError('Confluence 인증 실패. 도메인·이메일·토큰을 확인하세요.')
    } finally {
      setLoadingSpaces(false)
    }
  }

  async function fetchProjects() {
    if (!s.jiraDomain || !s.jiraEmail || !s.jiraToken) return
    setLoadingProjects(true)
    setCredError('')
    try {
      const data = await getJiraProjects(s.jiraDomain, s.jiraEmail, s.jiraToken)
      setProjects(data)
    } catch {
      setCredError('Jira 인증 실패. 도메인·이메일·토큰을 확인하세요.')
    } finally {
      setLoadingProjects(false)
    }
  }

  async function fetchUsers() {
    if (!s.jiraDomain || !s.jiraEmail || !s.jiraToken || !s.jiraProjectKey) return
    setLoadingUsers(true)
    try {
      const data = await getJiraUsers(s.jiraDomain, s.jiraEmail, s.jiraToken, s.jiraProjectKey)
      setJiraUsers(data)
    } finally {
      setLoadingUsers(false)
    }
  }

  useEffect(() => { if (s.jiraProjectKey) fetchUsers() }, [s.jiraProjectKey])

  // 액션 아이템의 고유 담당자 목록
  const assignees = [...new Set(
    (state.minutes?.action_items ?? [])
      .map(ai => ai.assignee)
      .filter(a => a && a !== '미정')
  )]

  function setUserMap(assigneeName: string, accountId: string) {
    setState(prev => ({
      ...prev,
      jiraUserMap: { ...prev.jiraUserMap, [assigneeName]: accountId },
    }))
  }

  const canPublish =
    s.confluenceDomain && s.confluenceEmail && s.confluenceToken && s.confluenceSpaceKey &&
    s.jiraDomain && s.jiraEmail && s.jiraToken && s.jiraProjectKey

  return (
    <div className="step-card">
      <h2>Step 4 — 게시 설정</h2>

      {credError && <p className="error-msg">{credError}</p>}

      {/* Confluence */}
      <div className="publish-section">
        <h3>📄 Confluence 설정</h3>
        <div className="form-row">
          <label>도메인</label>
          <input placeholder="yourcompany.atlassian.net"
            value={s.confluenceDomain}
            onChange={e => set('confluenceDomain', e.target.value)}
            onBlur={fetchSpaces}
          />
        </div>
        <div className="form-row">
          <label>이메일</label>
          <input type="email" placeholder="your@email.com"
            value={s.confluenceEmail} onChange={e => set('confluenceEmail', e.target.value)} />
        </div>
        <div className="form-row">
          <label>API 토큰 <a className="link-hint" href="https://id.atlassian.com/manage-profile/security/api-tokens" target="_blank" rel="noreferrer">발급</a></label>
          <input type="password" placeholder="Atlassian API 토큰"
            value={s.confluenceToken}
            onChange={e => set('confluenceToken', e.target.value)}
            onBlur={fetchSpaces}
          />
        </div>
        <div className="form-row">
          <label>스페이스 {loadingSpaces && <span className="loading-dot">···</span>}</label>
          {spaces.length > 0 ? (
            <select value={s.confluenceSpaceKey} onChange={e => set('confluenceSpaceKey', e.target.value)}>
              <option value="">스페이스 선택</option>
              {spaces.map(sp => <option key={sp.key} value={sp.key}>{sp.name} ({sp.key})</option>)}
            </select>
          ) : (
            <input placeholder="스페이스 키 직접 입력 (예: RD)"
              value={s.confluenceSpaceKey} onChange={e => set('confluenceSpaceKey', e.target.value)} />
          )}
        </div>
      </div>

      {/* Jira */}
      <div className="publish-section">
        <h3>🎯 Jira 설정</h3>
        <div className="form-row">
          <label>도메인</label>
          <input placeholder="yourcompany.atlassian.net"
            value={s.jiraDomain}
            onChange={e => set('jiraDomain', e.target.value)}
            onBlur={fetchProjects}
          />
        </div>
        <div className="form-row">
          <label>이메일</label>
          <input type="email" placeholder="your@email.com"
            value={s.jiraEmail} onChange={e => set('jiraEmail', e.target.value)} />
        </div>
        <div className="form-row">
          <label>API 토큰</label>
          <input type="password" placeholder="Atlassian API 토큰"
            value={s.jiraToken}
            onChange={e => set('jiraToken', e.target.value)}
            onBlur={fetchProjects}
          />
        </div>
        <div className="form-row">
          <label>프로젝트 {loadingProjects && <span className="loading-dot">···</span>}</label>
          {projects.length > 0 ? (
            <select value={s.jiraProjectKey} onChange={e => set('jiraProjectKey', e.target.value)}>
              <option value="">프로젝트 선택</option>
              {projects.map(p => <option key={p.key} value={p.key}>{p.name} ({p.key})</option>)}
            </select>
          ) : (
            <input placeholder="프로젝트 키 직접 입력 (예: RD)"
              value={s.jiraProjectKey} onChange={e => set('jiraProjectKey', e.target.value)} />
          )}
        </div>
        <div className="form-row">
          <label>이슈 유형</label>
          <select value={s.jiraIssueType} onChange={e => set('jiraIssueType', e.target.value)}>
            <option value="Task">Task</option>
            <option value="Story">Story</option>
            <option value="Sub-task">Sub-task</option>
          </select>
        </div>

        {/* 담당자 매핑 */}
        {assignees.length > 0 && (
          <div className="user-map-section">
            <h4>담당자 매핑 {loadingUsers && <span className="loading-dot">···</span>}</h4>
            <p className="hint">액션 아이템 담당자를 Jira 계정에 연결합니다.</p>
            {assignees.map(name => (
              <div key={name} className="form-row">
                <label>{name}</label>
                {jiraUsers.length > 0 ? (
                  <select value={s.jiraUserMap[name] || ''} onChange={e => setUserMap(name, e.target.value)}>
                    <option value="">할당 안 함</option>
                    {jiraUsers.map(u => (
                      <option key={u.accountId} value={u.accountId}>{u.displayName}</option>
                    ))}
                  </select>
                ) : (
                  <input placeholder="accountId 직접 입력"
                    value={s.jiraUserMap[name] || ''}
                    onChange={e => setUserMap(name, e.target.value)}
                  />
                )}
              </div>
            ))}
          </div>
        )}

        {/* 기존 이슈에 댓글 */}
        <div className="form-row">
          <label>기존 이슈 댓글 추가 <span className="hint">(쉼표로 구분)</span></label>
          <input placeholder="RD-142, RD-155"
            value={s.existingIssueKeys}
            onChange={e => set('existingIssueKeys', e.target.value)}
          />
        </div>
      </div>

      <div className="btn-row">
        <button className="btn-secondary" onClick={onBack}>← 이전</button>
        <button className="btn-publish" disabled={!canPublish} onClick={onPublish}>
          🚀 Confluence + Jira에 게시
        </button>
      </div>
    </div>
  )
}
