/**
 * App.jsx
 * ========
 * Root component. Manages global state:
 *   - uploaded documents list
 *   - selected documents for chat (multi-doc support)
 *   - chat history per session
 *
 * Layout: fixed sidebar (documents) + main chat area
 */

import { useState, useCallback } from 'react'
import Sidebar from './components/Sidebar'
import ChatPanel from './components/ChatPanel'
import Header from './components/Header'

export default function App() {
  // All documents uploaded in this session (fetched from backend)
  const [documents, setDocuments] = useState([])

  // doc_ids selected for the current chat query (empty = search all)
  const [selectedDocIds, setSelectedDocIds] = useState([])

  // Full conversation history [{role, content}, ...]
  const [chatHistory, setChatHistory] = useState([])

  // Whether the sidebar is collapsed on mobile
  const [sidebarOpen, setSidebarOpen] = useState(true)

  // Called by Sidebar when a new doc is successfully uploaded
  const handleDocumentUploaded = useCallback((newDoc) => {
    setDocuments((prev) => [newDoc, ...prev])
    // Auto-select the newly uploaded document
    setSelectedDocIds((prev) =>
      prev.includes(newDoc.doc_id) ? prev : [...prev, newDoc.doc_id]
    )
  }, [])

  // Called by Sidebar when documents are loaded from backend on mount
  const handleDocumentsLoaded = useCallback((docs) => {
    setDocuments(docs)
  }, [])

  // Toggle doc selection for filtered chat
  const handleToggleDoc = useCallback((docId) => {
    setSelectedDocIds((prev) =>
      prev.includes(docId) ? prev.filter((id) => id !== docId) : [...prev, docId]
    )
  }, [])

  // Called when a document is deleted
  const handleDocumentDeleted = useCallback((docId) => {
    setDocuments((prev) => prev.filter((d) => d.doc_id !== docId))
    setSelectedDocIds((prev) => prev.filter((id) => id !== docId))
  }, [])

  // Add a message pair (user + assistant) to chat history
  const handleAddToHistory = useCallback((userMsg, assistantMsg) => {
    setChatHistory((prev) => [
      ...prev,
      { role: 'user', content: userMsg },
      { role: 'assistant', content: assistantMsg },
    ])
  }, [])

  const handleClearChat = useCallback(() => {
    setChatHistory([])
  }, [])

  return (
    <div className="flex flex-col h-screen bg-ink-950 overflow-hidden">
      {/* ── Top header bar ── */}
      <Header
        sidebarOpen={sidebarOpen}
        onToggleSidebar={() => setSidebarOpen((o) => !o)}
        docCount={documents.length}
      />

      <div className="flex flex-1 overflow-hidden">
        {/* ── Left sidebar: document manager ── */}
        <Sidebar
          open={sidebarOpen}
          documents={documents}
          selectedDocIds={selectedDocIds}
          onDocumentUploaded={handleDocumentUploaded}
          onDocumentsLoaded={handleDocumentsLoaded}
          onToggleDoc={handleToggleDoc}
          onDocumentDeleted={handleDocumentDeleted}
        />

        {/* ── Right: chat area ── */}
        <ChatPanel
          selectedDocIds={selectedDocIds}
          chatHistory={chatHistory}
          onAddToHistory={handleAddToHistory}
          onClearChat={handleClearChat}
          hasDocuments={documents.length > 0}
        />
      </div>
    </div>
  )
}
