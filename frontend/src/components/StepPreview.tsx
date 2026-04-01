import { useEffect, useState } from 'react'
import { processTranscript } from '../api/client'
import type { ActionItem, MeetingMinutes, WizardState } from '../types'

interface Props {
  state: WizardState
  setState: React.Dispatch<React.SetStateAction<WizardState>>
  onNext: () => void
  onBack: () => void
}

export default function StepPreview({ state, setState, onNext, onBack }: Props) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [showReview, setShowReview] = useState(false)

  useEffect(() => {
    if (!state.minutes) {
      runProcess()
    }
  }, [])

  async function runProcess() {
    setLoading(true)
    setError('')
    try {
      const minutes = await processTranscript(
        state.rawText,
        state.speakerMap,
        state.meetingDate,
      )
      setState(s => ({ ...s, minutes }))
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : 'AI 처리에 실패했습니다.'
      setError(msg)
    } finally {
      setLoading(false)
    }
  }

  function updateActionItem(idx: number, field: keyof ActionItem, value: string) {
    if (!state.minutes) return
    const updated: MeetingMinutes = {
      ...state.minutes,
      action_items: state.minutes.action_items.map((ai, i) =>
        i === idx ? { ...ai, [field]: value } : ai,
      ),
    }
    setState(s => ({ ...s, minutes: updated }))
  }

  function addActionItem() {
    if (!state.minutes) return
    const newItem: ActionItem = {
      id: `manual_${Date.now()}`,
      assignee: '미정',
      task: '',
      deadline: '미정',
      confidence: '확실',
      timestamp: '',
      source_text: '수동 추가',
    }
    setState(s => ({
      ...s,
      minutes: s.minutes
        ? { ...s.minutes, action_items: [...s.minutes.action_items, newItem] }
        : s.minutes,
    }))
  }

  function removeActionItem(idx: number) {
    if (!state.minutes) return
    setState(s => ({
      ...s,
      minutes: s.minutes
        ? { ...s.minutes, action_items: s.minutes.action_items.filter((_, i) => i !== idx) }
        : s.minutes,
    }))
  }

  function updateTitle(title: string) {
    if (!state.minutes) return
    setState(s => ({ ...s, minutes: s.minutes ? { ...s.minutes, title } : s.minutes }))
  }

  if (loading) {
    return (
      <div className="step-card center">
        <div className="spinner large" />
        <p className="loading-text">Claude AI가 회의 내용을 분석 중입니다...</p>
        <p className="loading-sub">비선형 주제 통합·잡담 필터링·액션 아이템 추출 중</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="step-card">
        <p className="error-msg">{error}</p>
        <div className="btn-row">
          <button className="btn-secondary" onClick={onBack}>← 이전</button>
          <button className="btn-primary" onClick={runProcess}>다시 시도</button>
        </div>
      </div>
    )
  }

  const m = state.minutes
  if (!m) return null

  return (
    <div className="step-card wide">
      <div className="preview-header">
        <h2>Step 3 — 회의록 미리보기 · 편집</h2>
        <button className="btn-ghost" onClick={runProcess}>↺ 재생성</button>
      </div>

      {/* 제목 */}
      <div className="form-row">
        <label>회의록 제목</label>
        <input
          type="text"
          value={m.title}
          onChange={e => updateTitle(e.target.value)}
          className="title-input"
        />
      </div>

      {/* 요약 */}
      <section className="preview-section">
        <h3>📋 회의 요약</h3>
        <p>{m.summary}</p>
      </section>

      {/* 주요 논의 */}
      <section className="preview-section">
        <h3>💬 주요 논의 내용</h3>
        {m.discussions.map((d, i) => (
          <div key={i} className="discussion-item">
            <strong>{d.topic}</strong>
            <p>{d.content}</p>
          </div>
        ))}
      </section>

      {/* 결정사항 */}
      <section className="preview-section">
        <h3>✅ 결정사항</h3>
        {m.decisions.length > 0 ? (
          <ul>{m.decisions.map((d, i) => <li key={i}>{d}</li>)}</ul>
        ) : (
          <p className="empty-msg">없음</p>
        )}
      </section>

      {/* 액션 아이템 */}
      <section className="preview-section">
        <div className="section-header">
          <h3>📌 액션 아이템</h3>
          <button className="btn-small" onClick={addActionItem}>+ 추가</button>
        </div>
        <div className="action-table-wrap">
          <table className="action-table">
            <thead>
              <tr>
                <th>신뢰도</th><th>담당자</th><th>업무 내용</th><th>기한</th><th>원본</th><th></th>
              </tr>
            </thead>
            <tbody>
              {m.action_items.map((ai, i) => (
                <tr key={ai.id}>
                  <td>
                    <span className={`badge ${ai.confidence === '확실' ? 'badge-sure' : 'badge-guess'}`}>
                      {ai.confidence === '확실' ? '✅ 확실' : '⚠️ 추정'}
                    </span>
                  </td>
                  <td>
                    <input
                      value={ai.assignee}
                      onChange={e => updateActionItem(i, 'assignee', e.target.value)}
                      className="cell-input"
                    />
                  </td>
                  <td>
                    <input
                      value={ai.task}
                      onChange={e => updateActionItem(i, 'task', e.target.value)}
                      className="cell-input wide-cell"
                    />
                  </td>
                  <td>
                    <input
                      value={ai.deadline}
                      onChange={e => updateActionItem(i, 'deadline', e.target.value)}
                      className="cell-input"
                      placeholder="YYYY-MM-DD"
                    />
                  </td>
                  <td>
                    <span className="timestamp-tag" title={ai.source_text}>
                      {ai.timestamp || '-'}
                    </span>
                  </td>
                  <td>
                    <button className="btn-del" onClick={() => removeActionItem(i)}>✕</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* 검토 필요 항목 */}
      {m.review_items.length > 0 && (
        <section className="preview-section review-section">
          <button className="review-toggle" onClick={() => setShowReview(!showReview)}>
            ⚠️ 검토 필요 항목 ({m.review_items.length}건) {showReview ? '▲' : '▼'}
          </button>
          {showReview && (
            <table className="action-table">
              <thead>
                <tr><th>시간</th><th>화자</th><th>발화 내용</th><th>검토 이유</th></tr>
              </thead>
              <tbody>
                {m.review_items.map((ri, i) => (
                  <tr key={i}>
                    <td><span className="timestamp-tag">{ri.timestamp}</span></td>
                    <td>{ri.speaker}</td>
                    <td>{ri.text}</td>
                    <td className="review-reason">{ri.reason}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </section>
      )}

      <div className="btn-row">
        <button className="btn-secondary" onClick={onBack}>← 이전</button>
        <button className="btn-primary" onClick={onNext}>게시 설정 →</button>
      </div>
    </div>
  )
}
