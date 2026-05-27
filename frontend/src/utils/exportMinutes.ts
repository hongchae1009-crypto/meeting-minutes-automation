import type { MeetingMinutes } from '../types'

/** MeetingMinutes를 사람이 읽기 좋은 Markdown으로 변환 */
export function minutesToMarkdown(m: MeetingMinutes, meetingDate: string, attendees: string): string {
  const lines: string[] = []

  lines.push(`# ${m.title}`)
  lines.push('')
  if (meetingDate) lines.push(`**일시**: ${meetingDate}`)
  if (attendees) lines.push(`**참석자**: ${attendees}`)
  lines.push('')

  lines.push('## 📋 회의 요약')
  lines.push(m.summary || '_없음_')
  lines.push('')

  lines.push('## 💬 주요 논의 내용')
  if (m.discussions.length === 0) {
    lines.push('_없음_')
  } else {
    m.discussions.forEach(d => {
      lines.push(`### ${d.topic}`)
      lines.push(d.content)
      lines.push('')
    })
  }
  lines.push('')

  lines.push('## ✅ 결정사항')
  if (m.decisions.length === 0) {
    lines.push('_없음_')
  } else {
    m.decisions.forEach(d => lines.push(`- ${d}`))
  }
  lines.push('')

  lines.push('## 📌 액션 아이템')
  if (m.action_items.length === 0) {
    lines.push('_없음_')
  } else {
    lines.push('| 신뢰도 | 담당자 | 업무 | 기한 | 시간 |')
    lines.push('|---|---|---|---|---|')
    m.action_items.forEach(ai => {
      const conf = ai.confidence === '확실' ? '✅ 확실' : '⚠️ 추정'
      const task = ai.task.replace(/\|/g, '\\|')
      lines.push(`| ${conf} | ${ai.assignee} | ${task} | ${ai.deadline} | ${ai.timestamp || '-'} |`)
    })
  }
  lines.push('')

  if (m.next_meeting) {
    lines.push('## 🗓️ 다음 회의')
    lines.push(m.next_meeting)
    lines.push('')
  }

  if (m.review_items.length > 0) {
    lines.push(`## ⚠️ 검토 필요 항목 (${m.review_items.length}건)`)
    m.review_items.forEach(ri => {
      lines.push(`- **[${ri.timestamp}] ${ri.speaker}**: ${ri.text}`)
      lines.push(`  - _이유_: ${ri.reason}`)
    })
    lines.push('')
  }

  return lines.join('\n')
}

/** 파일명에 못 쓰는 문자를 _ 로 치환 */
function safeFilename(name: string): string {
  return name.replace(/[\\/:*?"<>|]/g, '_').slice(0, 80) || '회의록'
}

/** Blob을 다운로드 트리거 */
function downloadBlob(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  setTimeout(() => URL.revokeObjectURL(url), 1000)
}

export function downloadMarkdown(m: MeetingMinutes, meetingDate: string, attendees: string): void {
  const md = minutesToMarkdown(m, meetingDate, attendees)
  const blob = new Blob([md], { type: 'text/markdown;charset=utf-8' })
  downloadBlob(blob, `${safeFilename(m.title)}.md`)
}

export function downloadJson(m: MeetingMinutes, meetingDate: string, attendees: string): void {
  const payload = { meeting_date: meetingDate, attendees, ...m }
  const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json;charset=utf-8' })
  downloadBlob(blob, `${safeFilename(m.title)}.json`)
}

export async function copyMarkdownToClipboard(
  m: MeetingMinutes,
  meetingDate: string,
  attendees: string,
): Promise<void> {
  const md = minutesToMarkdown(m, meetingDate, attendees)
  await navigator.clipboard.writeText(md)
}
