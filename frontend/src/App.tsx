import { useState } from 'react'
import { publish } from './api/client'
import StepUpload from './components/StepUpload'
import StepSpeakerMap from './components/StepSpeakerMap'
import StepPreview from './components/StepPreview'
import StepPublish from './components/StepPublish'
import StepResult from './components/StepResult'
import type { WizardState } from './types'

const STEPS = ['파일 업로드', '화자 매핑', 'AI 처리', '게시 설정', '완료']

const INITIAL_STATE: WizardState = {
  rawText: '',
  speakers: [],
  fileName: '',
  speakerMap: {},
  meetingDate: new Date().toISOString().split('T')[0],
  attendees: '',
  minutes: null,
  confluenceDomain: '',
  confluenceEmail: '',
  confluenceToken: '',
  confluenceSpaceKey: '',
  confluenceParentId: '',
  jiraDomain: '',
  jiraEmail: '',
  jiraToken: '',
  jiraProjectKey: '',
  jiraIssueType: 'Task',
  jiraUserMap: {},
  existingIssueKeys: '',
  publishResult: null,
}

export default function App() {
  const [step, setStep] = useState(0)
  const [state, setState] = useState<WizardState>(INITIAL_STATE)
  const [publishing, setPublishing] = useState(false)
  const [publishError, setPublishError] = useState('')

  async function handlePublish() {
    if (!state.minutes) return
    setPublishing(true)
    setPublishError('')
    try {
      const result = await publish({
        minutes: state.minutes,
        meeting_title: state.minutes.title,
        meeting_date: state.meetingDate,
        attendees: state.attendees.split(',').map(s => s.trim()).filter(Boolean),
        confluence_domain: state.confluenceDomain,
        confluence_email: state.confluenceEmail,
        confluence_token: state.confluenceToken,
        confluence_space_key: state.confluenceSpaceKey,
        confluence_parent_id: state.confluenceParentId || null,
        jira_domain: state.jiraDomain,
        jira_email: state.jiraEmail,
        jira_token: state.jiraToken,
        jira_project_key: state.jiraProjectKey,
        jira_issue_type: state.jiraIssueType,
        jira_user_map: state.jiraUserMap,
        existing_issue_keys: state.existingIssueKeys
          .split(',').map(s => s.trim()).filter(Boolean),
      })
      setState(s => ({ ...s, publishResult: result }))
      setStep(4)
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : '게시에 실패했습니다.'
      setPublishError(msg)
    } finally {
      setPublishing(false)
    }
  }

  function reset() {
    setState(INITIAL_STATE)
    setStep(0)
    setPublishError('')
  }

  return (
    <div className="app">
      {/* 헤더 */}
      <header className="app-header">
        <div className="header-inner">
          <h1>🎙 AI 회의록 자동화</h1>
          <p>전사 텍스트 → Confluence 회의록 + Jira 이슈 자동 생성</p>
        </div>
      </header>

      {/* 단계 표시 */}
      <div className="stepper">
        {STEPS.map((label, i) => (
          <div key={i} className={`step-item ${i === step ? 'active' : ''} ${i < step ? 'done' : ''}`}>
            <div className="step-circle">{i < step ? '✓' : i + 1}</div>
            <div className="step-label">{label}</div>
            {i < STEPS.length - 1 && <div className="step-line" />}
          </div>
        ))}
      </div>

      {/* 게시 중 오버레이 */}
      {publishing && (
        <div className="overlay">
          <div className="overlay-box">
            <div className="spinner large" />
            <p>Confluence와 Jira에 게시하는 중...</p>
          </div>
        </div>
      )}

      {/* 게시 오류 */}
      {publishError && (
        <div className="global-error">
          ⚠️ {publishError}
          <button onClick={() => setPublishError('')}>✕</button>
        </div>
      )}

      {/* 단계별 컴포넌트 */}
      <main className="app-main">
        {step === 0 && (
          <StepUpload state={state} setState={setState} onNext={() => setStep(1)} />
        )}
        {step === 1 && (
          <StepSpeakerMap state={state} setState={setState}
            onNext={() => setStep(2)} onBack={() => setStep(0)} />
        )}
        {step === 2 && (
          <StepPreview state={state} setState={setState}
            onNext={() => setStep(3)} onBack={() => { setState(s => ({ ...s, minutes: null })); setStep(1) }} />
        )}
        {step === 3 && (
          <StepPublish state={state} setState={setState}
            onPublish={handlePublish} onBack={() => setStep(2)} />
        )}
        {step === 4 && (
          <StepResult state={state} onReset={reset} />
        )}
      </main>
    </div>
  )
}
