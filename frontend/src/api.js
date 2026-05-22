// FastAPI 백엔드 호출 래퍼. 개발 시 Vite 프록시가 /api → :8000 로 전달.
const BASE = '/api'

export async function fetchStatus() {
  const res = await fetch(`${BASE}/status`)
  if (!res.ok) throw new Error('상태 조회 실패')
  return res.json()
}

export async function generateSpeech(text, language) {
  const res = await fetch(`${BASE}/generate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text, language }),
  })
  const data = await res.json().catch(() => ({}))
  if (!res.ok) {
    throw new Error(data.detail || '음성 생성에 실패했습니다.')
  }
  return data // { filename }
}

export function audioUrl(filename) {
  return `${BASE}/audio/${encodeURIComponent(filename)}`
}
