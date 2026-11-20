const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'

class ApiError extends Error {
  constructor(message, status, data) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.data = data
  }
}

async function handleResponse(response) {
  const contentType = response.headers.get('content-type')
  
  if (contentType && contentType.includes('application/pdf')) {
    if (!response.ok) {
      throw new ApiError('PDF download failed', response.status, null)
    }
    return response.blob()
  }

  const data = await response.json()

  if (!response.ok) {
    throw new ApiError(
      data.error?.message || data.message || 'Request failed',
      response.status,
      data
    )
  }

  return data
}

export const api = {
  async get(endpoint) {
    const response = await fetch(`${API_BASE}${endpoint}`, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
    })
    return handleResponse(response)
  },

  async post(endpoint, body) {
    const response = await fetch(`${API_BASE}${endpoint}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })
    return handleResponse(response)
  },

  async postFormData(endpoint, formData) {
    const response = await fetch(`${API_BASE}${endpoint}`, {
      method: 'POST',
      body: formData,
    })
    return handleResponse(response)
  },

  async delete(endpoint) {
    const response = await fetch(`${API_BASE}${endpoint}`, {
      method: 'DELETE',
      headers: { 'Content-Type': 'application/json' },
    })
    return handleResponse(response)
  },
}

export const healthApi = {
  async check() {
    const result = await api.get('/health')
    return result.data?.status || result.status
  },
}

export const sessionApi = {
  async create(payload) {
    const result = await api.post('/sessions', payload)
    return result.data
  },

  async list() {
    const result = await api.get('/sessions')
    return result.data
  },

  async get(sessionId) {
    const result = await api.get(`/sessions/${sessionId}`)
    return result.data
  },

  async analyze(sessionId) {
    const result = await api.post(`/sessions/${sessionId}/analyze`)
    return result.data
  },

  async uploadArtifact(sessionId, file, artifactType) {
    const formData = new FormData()
    formData.append('files', file)
    formData.append('artifact_types', artifactType)
    const result = await api.postFormData(`/ingest/${sessionId}`, formData)
    return result.data
  },

  async listArtifacts(sessionId) {
    const result = await api.get(`/ingest/${sessionId}/status`)
    return result.data
  },

  async submitClarification(sessionId, questionId, answer) {
    const result = await api.post(`/sessions/${sessionId}/clarify`, {
      question_id: questionId,
      answer,
    })
    return result.data
  },

  async getProvenance(sessionId) {
    const result = await api.get(`/sessions/${sessionId}/provenance`)
    return result.data
  },

  async downloadMemo(sessionId) {
    const blob = await api.get(`/sessions/${sessionId}/memo`)
    return blob
  },
}

export function createWebSocket(sessionId) {
  const WS_BASE = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000'
  return new WebSocket(`${WS_BASE}/ws/${sessionId}`)
}

// Convenience wrappers for processing screen
api.runAnalysis = async (sessionId) => {
  return sessionApi.analyze(sessionId)
}

api.wsUrl = (sessionId) => {
  const WS_BASE = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000'
  return `${WS_BASE}/ws/${sessionId}`
}

api.getSession = async (sessionId) => {
  return sessionApi.get(sessionId)
}

api.submitClarification = async (sessionId, payload) => {
  const result = await api.post(`/sessions/${sessionId}/clarify`, {
    question_id:      payload.question_id,
    clarification_id: payload.clarification_id,
    answer:           payload.answer,
    response:         payload.response ?? payload.answer,
    response_label:   payload.response_label || 'user_explanation',
  })
  return result.data
}

// Create session convenience wrapper
api.createSession = async (payload) => {
  const result = await api.post('/sessions', payload)
  return result.data
}

// Alias for analyzeSession
api.analyzeSession = async (sessionId) => {
  return sessionApi.analyze(sessionId)
}

// Get all sessions (for dashboard)
api.getSessions = async () => {
  return sessionApi.list()
}

export { ApiError }
