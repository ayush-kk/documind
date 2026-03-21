/**
 * services/api.js
 * ================
 * Axios-based API client for the DocuMind FastAPI backend.
 *
 * All backend calls are centralised here so the rest of the app
 * never hard-codes URLs or handles raw HTTP errors.
 */

import axios from 'axios'

// Base URL — falls back to relative '/api' so the Vite proxy works locally.
// Set VITE_API_URL in your .env.local (or Vercel env vars) for production.
const BASE_URL = import.meta.env.VITE_API_URL || ''

const client = axios.create({
  baseURL: BASE_URL,
  timeout: 60_000, // 60 s — LLM generation can take a moment
  headers: { 'Content-Type': 'application/json' },
})

// Global response interceptor — unwrap data, surface errors cleanly
client.interceptors.response.use(
  (response) => response.data,
  (error) => {
    const message =
      error.response?.data?.detail ||
      error.message ||
      'An unexpected error occurred'
    return Promise.reject(new Error(message))
  }
)

// ─────────────────────────────────────────────────────────────────
// Documents API
// ─────────────────────────────────────────────────────────────────

/**
 * Upload a single document file.
 * @param {File} file - The file object from the browser
 * @param {Function} onProgress - Optional upload progress callback (0–100)
 * @returns {Promise<{doc_id, filename, num_chunks, message}>}
 */
export async function uploadDocument(file, onProgress) {
  const formData = new FormData()
  formData.append('file', file)

  return client.post('/api/upload/', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    onUploadProgress: (evt) => {
      if (onProgress && evt.total) {
        onProgress(Math.round((evt.loaded / evt.total) * 100))
      }
    },
  })
}

/**
 * Fetch all uploaded documents.
 * @returns {Promise<{documents: DocumentMeta[], total: number}>}
 */
export async function listDocuments() {
  return client.get('/api/documents/')
}

/**
 * Delete a document and its embeddings.
 * @param {string} docId - Document UUID
 */
export async function deleteDocument(docId) {
  return client.delete(`/api/documents/${docId}`)
}

// ─────────────────────────────────────────────────────────────────
// Chat API
// ─────────────────────────────────────────────────────────────────

/**
 * Send a question to the RAG pipeline.
 *
 * @param {Object} params
 * @param {string}   params.question  - User's question
 * @param {string[]} params.docIds    - Optional doc_id filter list
 * @param {Array}    params.history   - [{role, content}] conversation history
 * @param {number}   params.topK      - Number of chunks to retrieve
 * @returns {Promise<ChatResponse>}   - {answer, sources, model_used, tokens_used}
 */
export async function askQuestion({ question, docIds = [], history = [], topK = 4 }) {
  return client.post('/api/chat/ask', {
    question,
    doc_ids: docIds,
    history,
    top_k: topK,
  })
}

/**
 * Health check — verifies the backend is reachable.
 * @returns {Promise<{status, service, version}>}
 */
export async function healthCheck() {
  return client.get('/health')
}
