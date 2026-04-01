export interface ActionItem {
  id: string
  assignee: string
  task: string
  deadline: string
  confidence: '확실' | '추정'
  timestamp: string
  source_text: string
  jira_issue_key?: string
  jira_url?: string
}

export interface ReviewItem {
  timestamp: string
  speaker: string
  text: string
  reason: string
}

export interface Discussion {
  topic: string
  content: string
}

export interface MeetingMinutes {
  title: string
  summary: string
  discussions: Discussion[]
  decisions: string[]
  action_items: ActionItem[]
  review_items: ReviewItem[]
  next_meeting: string
}

export interface ParseResult {
  speakers: string[]
  total_utterances: number
  preview: string
  raw_text: string
}

export interface AtlassianSpace {
  key: string
  name: string
  id: string
}

export interface AtlassianProject {
  key: string
  name: string
  id: string
}

export interface AtlassianUser {
  accountId: string
  displayName: string
  email: string
}

export interface PublishResult {
  confluence_page: { url: string; title: string }
  created_jira_issues: { key: string; url: string; summary: string }[]
  commented_issues: { key: string; url: string }[]
  errors: string[]
}

// 마법사 단계별 데이터
export interface WizardState {
  // Step 1
  rawText: string
  speakers: string[]
  fileName: string
  // Step 2
  speakerMap: Record<string, string>  // { "1": "홍길동" }
  meetingDate: string
  attendees: string
  // Step 3
  minutes: MeetingMinutes | null
  // Step 4
  confluenceDomain: string
  confluenceEmail: string
  confluenceToken: string
  confluenceSpaceKey: string
  confluenceParentId: string
  jiraDomain: string
  jiraEmail: string
  jiraToken: string
  jiraProjectKey: string
  jiraIssueType: string
  jiraUserMap: Record<string, string>   // assignee 이름 → accountId
  existingIssueKeys: string
  // Step 5
  publishResult: PublishResult | null
}
