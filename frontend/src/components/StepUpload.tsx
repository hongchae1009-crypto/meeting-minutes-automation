import { useRef, useState } from 'react'
import { parseFile } from '../api/client'
import type { WizardState } from '../types'

interface Props {
  state: WizardState
  setState: React.Dispatch<React.SetStateAction<WizardState>>
  onNext: () => void
}

export default function StepUpload({ state, setState, onNext }: Props) {
  const [dragging, setDragging] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const inputRef = useRef<HTMLInputElement>(null)

  async function handleFile(file: File) {
    if (!file.name.endsWith('.txt')) {
      setError('.txt 파일만 업로드 가능합니다.')
      return
    }
    setLoading(true)
    setError('')
    try {
      const result = await parseFile(file)
      setState(s => ({
        ...s,
        rawText: result.raw_text,
        speakers: result.speakers,
        fileName: file.name,
      }))
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : '파일 파싱에 실패했습니다.'
      setError(msg)
    } finally {
      setLoading(false)
    }
  }

  function onDrop(e: React.DragEvent) {
    e.preventDefault()
    setDragging(false)
    const file = e.dataTransfer.files[0]
    if (file) handleFile(file)
  }

  const today = new Date().toISOString().split('T')[0]

  return (
    <div className="step-card">
      <h2>Step 1 — 전사 파일 업로드</h2>
      <p className="step-desc">AI 전사 도구로 생성된 .txt 파일을 업로드하세요.</p>

      {/* 드래그 앤 드롭 영역 */}
      <div
        className={`drop-zone ${dragging ? 'dragging' : ''} ${state.fileName ? 'uploaded' : ''}`}
        onDragOver={e => { e.preventDefault(); setDragging(true) }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
        onClick={() => inputRef.current?.click()}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".txt"
          style={{ display: 'none' }}
          onChange={e => e.target.files?.[0] && handleFile(e.target.files[0])}
        />
        {loading ? (
          <div className="spinner-wrap"><div className="spinner" /><p>파일 분석 중...</p></div>
        ) : state.fileName ? (
          <div>
            <div className="upload-icon">✅</div>
            <p className="upload-filename">{state.fileName}</p>
            <p className="upload-sub">화자 {state.speakers.length}명 감지됨 · 클릭하여 변경</p>
          </div>
        ) : (
          <div>
            <div className="upload-icon">📄</div>
            <p>파일을 여기에 드래그하거나 클릭하여 선택</p>
            <p className="upload-sub">AI 전사 .txt 파일 (UTF-16 지원)</p>
          </div>
        )}
      </div>

      {error && <p className="error-msg">{error}</p>}

      {/* 회의 기본 정보 */}
      {state.fileName && (
        <div className="form-section">
          <div className="form-row">
            <label>회의 날짜</label>
            <input
              type="date"
              value={state.meetingDate || today}
              onChange={e => setState(s => ({ ...s, meetingDate: e.target.value }))}
            />
          </div>
          <div className="form-row">
            <label>참석자 <span className="hint">(쉼표로 구분)</span></label>
            <input
              type="text"
              placeholder="홍길동, 김철수, 박영희"
              value={state.attendees}
              onChange={e => setState(s => ({ ...s, attendees: e.target.value }))}
            />
          </div>
        </div>
      )}

      <div className="btn-row">
        <button
          className="btn-primary"
          disabled={!state.fileName || !state.meetingDate}
          onClick={onNext}
        >
          다음 →
        </button>
      </div>
    </div>
  )
}
