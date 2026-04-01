import axios from 'axios'
import type {
  AtlassianProject,
  AtlassianSpace,
  AtlassianUser,
  MeetingMinutes,
  ParseResult,
  PublishResult,
} from '../types'

const BASE = import.meta.env.VITE_API_URL ?? ''
const api = axios.create({ baseURL: `${BASE}/api` })

export async function parseFile(file: File): Promise<ParseResult> {
  const form = new FormData()
  form.append('file', file)
  const { data } = await api.post<ParseResult>('/parse', form)
  return data
}

export async function processTranscript(
  rawText: string,
  speakerMap: Record<string, string>,
  meetingDate: string,
): Promise<MeetingMinutes> {
  const { data } = await api.post<MeetingMinutes>('/process', {
    raw_text: rawText,
    speaker_map: speakerMap,
    meeting_date: meetingDate,
  })
  return data
}

export async function getConfluenceSpaces(
  domain: string,
  email: string,
  token: string,
): Promise<AtlassianSpace[]> {
  const { data } = await api.get<{ spaces: AtlassianSpace[] }>('/confluence/spaces', {
    params: { domain, email, token },
  })
  return data.spaces
}

export async function getJiraProjects(
  domain: string,
  email: string,
  token: string,
): Promise<AtlassianProject[]> {
  const { data } = await api.get<{ projects: AtlassianProject[] }>('/jira/projects', {
    params: { domain, email, token },
  })
  return data.projects
}

export async function getJiraUsers(
  domain: string,
  email: string,
  token: string,
  projectKey: string,
): Promise<AtlassianUser[]> {
  const { data } = await api.get<{ users: AtlassianUser[] }>('/jira/users', {
    params: { domain, email, token, project_key: projectKey },
  })
  return data.users
}

export async function publish(payload: object): Promise<PublishResult> {
  const { data } = await api.post<PublishResult>('/publish', payload)
  return data
}
