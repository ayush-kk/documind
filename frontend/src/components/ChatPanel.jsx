/**
 * components/ChatPanel.jsx
 * =========================
 * Main chat interface:
 *   - Scrollable message history
 *   - Input bar with submit
 *   - Loading / typing indicator
 *   - Source chunk display per AI message
 */

import { useState, useRef, useEffect, useCallback } from 'react'
import { Send, Trash2, BrainCircuit, ChevronDown, ChevronUp } from 'lucide-react'
import clsx from 'clsx'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { askQuestion } from '../services/api'
import SourcePanel from './SourcePanel'

export default function ChatPanel({
  selectedDocIds,
  chatHistory,
  onAddToHistory,
  onClearChat,
  hasDocuments,
}) {
  // Local UI messages (includes loading state)
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState(null)

  const bottomRef = useRef(null)
  const inputRef = useRef(null)

  // Auto-scroll to latest message
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // Focus input on mount
  useEffect(() => {
    inputRef.current?.focus()
  }, [])

  const handleSubmit = useCallback(async () => {
    const question = input.trim()
    if (!question || isLoading) return

    setInput('')
    setError(null)

    // Optimistically add user message
    const userMsg = { role: 'user', content: question, id: Date.now() }
    setMessages((prev) => [...prev, userMsg])
    setIsLoading(true)

    // Add a placeholder "thinking" message
    const thinkingId = Date.now() + 1
    setMessages((prev) => [
      ...prev,
      { role: 'assistant', content: null, id: thinkingId, loading: true },
    ])

    try {
      const response = await askQuestion({
        question,
        docIds: selectedDocIds,
        history: chatHistory,
        topK: 4,
      })

      // Replace thinking placeholder with real answer
      setMessages((prev) =>
        prev.map((m) =>
          m.id === thinkingId
            ? {
                ...m,
                loading: false,
                content: response.answer,
                sources: response.sources,
                model: response.model_used,
                tokens: response.tokens_used,
              }
            : m
        )
      )

      // Persist to global history for multi-turn context
      onAddToHistory(question, response.answer)
    } catch (err) {
      setMessages((prev) => prev.filter((m) => m.id !== thinkingId))
      setError(err.message || 'Something went wrong. Please try again.')
    } finally {
      setIsLoading(false)
    }
  }, [input, isLoading, selectedDocIds, chatHistory, onAddToHistory])

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit()
    }
  }

  const handleClear = () => {
    setMessages([])
    setError(null)
    onClearChat()
  }

  // ── Empty state ──────────────────────────────────────────────
  const isEmpty = messages.length === 0

  return (
    <main className="flex flex-col flex-1 min-w-0 overflow-hidden">
      {/* ── Toolbar ── */}
      <div className="flex items-center justify-between px-4 py-2 border-b border-ink-800 flex-shrink-0">
        <div className="flex items-center gap-2 text-xs text-slate-500">
          {selectedDocIds.length > 0
            ? <span className="text-amber-400/80">{selectedDocIds.length} doc{selectedDocIds.length !== 1 ? 's' : ''} selected</span>
            : <span>All documents in scope</span>
          }
        </div>
        {messages.length > 0 && (
          <button
            onClick={handleClear}
            className="flex items-center gap-1.5 text-xs text-slate-600 hover:text-red-400 transition-colors"
          >
            <Trash2 size={12} />
            Clear chat
          </button>
        )}
      </div>

      {/* ── Messages ── */}
      <div className="flex-1 overflow-y-auto px-4 py-6 space-y-6">
        {isEmpty && (
          <EmptyState hasDocuments={hasDocuments} />
        )}

        {messages.map((msg) => (
          <Message key={msg.id} msg={msg} />
        ))}

        {/* Error banner */}
        {error && (
          <div className="flex justify-center">
            <div className="text-xs text-red-400 bg-red-400/10 border border-red-400/20 rounded-lg px-4 py-2.5 max-w-lg text-center">
              {error}
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* ── Input bar ── */}
      <div className="flex-shrink-0 border-t border-ink-800 p-4">
        <div className={clsx(
          'flex items-end gap-3 rounded-xl border bg-ink-800/60 px-4 py-3 transition-all',
          'focus-within:border-amber-500/50 focus-within:bg-ink-800',
          'border-ink-700'
        )}>
          <textarea
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={
              hasDocuments
                ? 'Ask anything about your documents…'
                : 'Upload a document first, then ask questions…'
            }
            disabled={isLoading || !hasDocuments}
            rows={1}
            className={clsx(
              'flex-1 bg-transparent text-sm text-slate-200 placeholder-slate-600',
              'resize-none outline-none leading-relaxed',
              'min-h-[24px] max-h-32',
              (!hasDocuments || isLoading) && 'cursor-not-allowed opacity-50'
            )}
            style={{ fieldSizing: 'content' }}
          />

          <button
            onClick={handleSubmit}
            disabled={!input.trim() || isLoading || !hasDocuments}
            className={clsx(
              'flex-shrink-0 w-8 h-8 rounded-lg flex items-center justify-center transition-all',
              input.trim() && !isLoading && hasDocuments
                ? 'bg-amber-400 text-ink-950 hover:bg-amber-300 shadow-lg shadow-amber-400/20'
                : 'bg-ink-700 text-slate-600 cursor-not-allowed'
            )}
          >
            <Send size={14} />
          </button>
        </div>
        <p className="text-xs text-slate-700 mt-2 text-center">
          Powered by Groq · LLaMA 3.1 · ChromaDB
        </p>
      </div>
    </main>
  )
}

// ── Sub-components ────────────────────────────────────────────────────────────

function EmptyState({ hasDocuments }) {
  const suggestions = [
    'Summarize the key findings in this document',
    'What are the main conclusions?',
    'List all the action items mentioned',
    'Explain the methodology used',
  ]

  return (
    <div className="flex flex-col items-center justify-center h-full min-h-[400px] gap-6 text-center px-6">
      {/* Icon */}
      <div className="relative">
        <div className="w-16 h-16 rounded-2xl bg-ink-800 border border-ink-700 flex items-center justify-center">
          <BrainCircuit size={28} className="text-amber-400" />
        </div>
        <div className="absolute -inset-2 rounded-3xl bg-amber-400/5 -z-10" />
      </div>

      <div>
        <h2 className="font-display font-bold text-xl text-slate-200 tracking-tight">
          Ask anything about your documents
        </h2>
        <p className="text-sm text-slate-500 mt-2 max-w-sm">
          {hasDocuments
            ? 'Your documents are loaded. Try one of the prompts below or write your own.'
            : 'Upload a PDF, DOCX, or TXT file from the sidebar to get started.'
          }
        </p>
      </div>

      {hasDocuments && (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 w-full max-w-lg">
          {suggestions.map((s) => (
            <div
              key={s}
              className="text-left text-xs text-slate-400 bg-ink-800/60 border border-ink-700 rounded-lg px-3 py-2.5 hover:border-amber-500/30 hover:text-slate-300 cursor-default transition-colors"
            >
              "{s}"
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

function Message({ msg }) {
  const isUser = msg.role === 'user'
  const [sourcesOpen, setSourcesOpen] = useState(false)

  return (
    <div className={clsx('flex gap-3 animate-fade-up', isUser && 'flex-row-reverse')}>
      {/* Avatar */}
      <div className={clsx(
        'w-7 h-7 rounded-lg flex-shrink-0 flex items-center justify-center text-xs font-display font-bold mt-0.5',
        isUser
          ? 'bg-amber-400/20 text-amber-400 border border-amber-400/30'
          : 'bg-ink-800 text-slate-400 border border-ink-700'
      )}>
        {isUser ? 'U' : <BrainCircuit size={13} />}
      </div>

      {/* Bubble */}
      <div className={clsx('flex flex-col gap-2 max-w-2xl', isUser && 'items-end')}>
        <div className={clsx(
          'rounded-xl px-4 py-3 text-sm leading-relaxed',
          isUser
            ? 'bg-amber-400/10 border border-amber-400/20 text-slate-200'
            : 'bg-ink-800/70 border border-ink-700 text-slate-300'
        )}>
          {msg.loading ? (
            <TypingIndicator />
          ) : (
            <div className="prose-documind">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {msg.content}
              </ReactMarkdown>
            </div>
          )}
        </div>

        {/* Source chunks toggle */}
        {!isUser && !msg.loading && msg.sources && msg.sources.length > 0 && (
          <div className="w-full">
            <button
              onClick={() => setSourcesOpen((o) => !o)}
              className="flex items-center gap-1.5 text-xs text-slate-600 hover:text-amber-400 transition-colors"
            >
              {sourcesOpen ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
              {msg.sources.length} source chunk{msg.sources.length !== 1 ? 's' : ''} used
              {msg.tokens && (
                <span className="ml-2 text-slate-700 font-mono">
                  {msg.tokens} tokens
                </span>
              )}
            </button>
            {sourcesOpen && <SourcePanel sources={msg.sources} />}
          </div>
        )}
      </div>
    </div>
  )
}

function TypingIndicator() {
  return (
    <div className="flex items-center gap-1.5 h-5">
      {[0, 1, 2].map((i) => (
        <span
          key={i}
          className="w-1.5 h-1.5 rounded-full bg-amber-400/60 animate-pulse-dot"
          style={{ animationDelay: `${i * 0.2}s` }}
        />
      ))}
    </div>
  )
}
