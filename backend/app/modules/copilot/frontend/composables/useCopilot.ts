// Copilot chat state — a single shared session per browser tab (useState
// keeps it SSR-safe and shared between the drawer and the /copilot page).

import type { ApiResponse } from '~~/app/types'

export interface ToolUiMessage {
  kind: 'tool'
  callId: string
  name: string
  status: 'running' | 'done' | 'failed'
}

export interface ConfirmUiMessage {
  kind: 'confirmation'
  callId: string
  name: string
  args: Record<string, unknown>
  resolved?: 'confirm' | 'reject'
}

export interface TextUiMessage {
  kind: 'text'
  role: 'user' | 'assistant'
  text: string
  streaming?: boolean
}

export type CopilotUiMessage = TextUiMessage | ToolUiMessage | ConfirmUiMessage

interface PendingConfirmation {
  callId: string
  name: string
  args: Record<string, unknown>
}

export function useCopilot() {
  const api = useApi()
  const route = useRoute()
  const { stream } = useCopilotStream()

  const open = useState<boolean>('copilot:open', () => false)
  const conversationId = useState<string | null>('copilot:conversation', () => null)
  const messages = useState<CopilotUiMessage[]>('copilot:messages', () => [])
  const busy = useState<boolean>('copilot:busy', () => false)
  const pending = useState<PendingConfirmation | null>('copilot:pending', () => null)

  function toggle() {
    open.value = !open.value
  }

  function captureContext(): Record<string, unknown> {
    const ctx: Record<string, unknown> = { screen: route.path }
    const patientId = route.params.id
    if (typeof patientId === 'string' && route.path.startsWith('/patients/')) {
      ctx.patient_id = patientId
    }
    return ctx
  }

  async function ensureSession(): Promise<void> {
    if (conversationId.value) return
    const res = await api.post<ApiResponse<{ id: string }>>('/api/v1/copilot/sessions', {
      context: captureContext()
    })
    conversationId.value = res.data.id
  }

  function lastStreamingAssistant(): TextUiMessage | null {
    const last = messages.value[messages.value.length - 1]
    if (last && last.kind === 'text' && last.role === 'assistant' && last.streaming) return last
    return null
  }

  function handle(event: string, data: Record<string, unknown>): void {
    if (event === 'token') {
      const current = lastStreamingAssistant()
      if (current) current.text += String(data.text ?? '')
      else messages.value.push({ kind: 'text', role: 'assistant', text: String(data.text ?? ''), streaming: true })
    } else if (event === 'tool_call') {
      messages.value.push({ kind: 'tool', callId: String(data.call_id), name: String(data.name), status: 'running' })
    } else if (event === 'tool_result') {
      const tool = [...messages.value].reverse().find(
        (m): m is ToolUiMessage => m.kind === 'tool' && m.callId === data.call_id
      )
      if (tool) tool.status = data.ok ? 'done' : 'failed'
    } else if (event === 'confirmation_required') {
      const c: ConfirmUiMessage = {
        kind: 'confirmation',
        callId: String(data.call_id),
        name: String(data.name),
        args: (data.arguments as Record<string, unknown>) ?? {}
      }
      messages.value.push(c)
      pending.value = { callId: c.callId, name: c.name, args: c.args }
    } else if (event === 'done') {
      const current = lastStreamingAssistant()
      if (current) current.streaming = false
    } else if (event === 'budget_exceeded') {
      messages.value.push({ kind: 'text', role: 'assistant', text: '⚠️ budget', streaming: false })
    } else if (event === 'error') {
      messages.value.push({ kind: 'text', role: 'assistant', text: `⚠️ ${data.detail ?? ''}`, streaming: false })
    }
  }

  async function send(text: string): Promise<void> {
    if (busy.value) return
    await ensureSession()
    messages.value.push({ kind: 'text', role: 'user', text })
    busy.value = true
    await stream(
      `/api/v1/copilot/sessions/${conversationId.value}/messages`,
      { content: text },
      { onEvent: handle, onError: (m) => handle('error', { detail: m }) }
    )
    busy.value = false
  }

  async function confirm(callId: string, decision: 'confirm' | 'reject'): Promise<void> {
    if (busy.value) return
    const card = messages.value.find(
      (m): m is ConfirmUiMessage => m.kind === 'confirmation' && m.callId === callId
    )
    if (card) card.resolved = decision
    pending.value = null
    busy.value = true
    await stream(
      `/api/v1/copilot/sessions/${conversationId.value}/confirmations/${callId}`,
      { decision },
      { onEvent: handle, onError: (m) => handle('error', { detail: m }) }
    )
    busy.value = false
  }

  function reset(): void {
    conversationId.value = null
    messages.value = []
    pending.value = null
  }

  return { open, messages, busy, pending, toggle, send, confirm, reset }
}
