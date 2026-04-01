import type { WizardState } from '../types'

interface Props {
  state: WizardState
  setState: React.Dispatch<React.SetStateAction<WizardState>>
  onNext: () => void
  onBack: () => void
}

export default function StepSpeakerMap({ state, setState, onNext, onBack }: Props) {
  function setName(speakerId: string, name: string) {
    setState(s => ({
      ...s,
      speakerMap: { ...s.speakerMap, [speakerId]: name },
    }))
  }

  const allMapped = state.speakers.every(id => state.speakerMap[id]?.trim())

  return (
    <div className="step-card">
      <h2>Step 2 — 화자 이름 매핑</h2>
      <p className="step-desc">
        전사 텍스트에서 감지된 화자에게 실제 이름을 지정하세요.
        이름이 없으면 "화자 N"으로 표시됩니다.
      </p>

      <div className="speaker-list">
        {state.speakers.map(id => (
          <div key={id} className="speaker-row">
            <div className="speaker-badge">화자 {id}</div>
            <input
              type="text"
              placeholder={`화자 ${id} 이름 입력`}
              value={state.speakerMap[id] || ''}
              onChange={e => setName(id, e.target.value)}
              onKeyDown={e => e.key === 'Enter' && onNext()}
            />
          </div>
        ))}
      </div>

      {!allMapped && (
        <p className="warn-msg">⚠️ 일부 화자에 이름이 없습니다. 빈 화자는 "화자 N"으로 처리됩니다.</p>
      )}

      {/* 미리보기 */}
      <details className="preview-collapse">
        <summary>전사 미리보기 (처음 10개 발화)</summary>
        <pre className="transcript-preview">{state.rawText.slice(0, 1000)}...</pre>
      </details>

      <div className="btn-row">
        <button className="btn-secondary" onClick={onBack}>← 이전</button>
        <button className="btn-primary" onClick={onNext}>AI 처리 시작 →</button>
      </div>
    </div>
  )
}
