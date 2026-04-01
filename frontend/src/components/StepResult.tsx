import type { WizardState } from '../types'

interface Props {
  state: WizardState
  onReset: () => void
}

export default function StepResult({ state, onReset }: Props) {
  const r = state.publishResult
  if (!r) return null

  return (
    <div className="step-card">
      <div className="result-header">
        <div className="result-icon">🎉</div>
        <h2>게시 완료!</h2>
      </div>

      {/* Confluence */}
      <div className="result-section">
        <h3>📄 Confluence 회의록</h3>
        <a href={r.confluence_page.url} target="_blank" rel="noreferrer" className="result-link">
          {r.confluence_page.title}
          <span className="ext-icon">↗</span>
        </a>
      </div>

      {/* 생성된 Jira 이슈 */}
      {r.created_jira_issues.length > 0 && (
        <div className="result-section">
          <h3>🎯 생성된 Jira 이슈 ({r.created_jira_issues.length}건)</h3>
          <div className="issue-list">
            {r.created_jira_issues.map(issue => (
              <a key={issue.key} href={issue.url} target="_blank" rel="noreferrer" className="issue-chip">
                <span className="issue-key">{issue.key}</span>
                <span className="issue-summary">{issue.summary}</span>
                <span className="ext-icon">↗</span>
              </a>
            ))}
          </div>
        </div>
      )}

      {/* 댓글 추가된 이슈 */}
      {r.commented_issues.length > 0 && (
        <div className="result-section">
          <h3>💬 댓글 추가된 이슈 ({r.commented_issues.length}건)</h3>
          <div className="issue-list">
            {r.commented_issues.map(issue => (
              <a key={issue.key} href={issue.url} target="_blank" rel="noreferrer" className="issue-chip">
                <span className="issue-key">{issue.key}</span>
                <span className="ext-icon">↗</span>
              </a>
            ))}
          </div>
        </div>
      )}

      {/* 오류 */}
      {r.errors.length > 0 && (
        <div className="result-section error-section">
          <h3>⚠️ 일부 오류 발생</h3>
          <ul>
            {r.errors.map((e, i) => <li key={i}>{e}</li>)}
          </ul>
        </div>
      )}

      <div className="btn-row center">
        <button className="btn-primary" onClick={onReset}>새 회의록 작성</button>
      </div>
    </div>
  )
}
