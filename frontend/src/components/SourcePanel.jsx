/**
 * components/SourcePanel.jsx
 * ===========================
 * Displays the document chunks that were retrieved and used to answer
 * the user's question — the "source highlighting" feature.
 *
 * Each source card shows:
 *   - Filename + page number
 *   - Relevance score (cosine similarity)
 *   - Chunk text (truncated with expand toggle)
 */

import { useState } from 'react'
import { FileText, ChevronDown, ChevronUp } from 'lucide-react'
import clsx from 'clsx'

// Score → colour mapping for visual relevance indication
function scoreColor(score) {
  if (score >= 0.75) return 'text-emerald-400 bg-emerald-400/10 border-emerald-400/20'
  if (score >= 0.5)  return 'text-amber-400  bg-amber-400/10  border-amber-400/20'
  return 'text-slate-400 bg-slate-400/10 border-slate-600/20'
}

function ScoreBadge({ score }) {
  return (
    <span className={clsx(
      'text-xs font-mono px-1.5 py-0.5 rounded border font-medium',
      scoreColor(score)
    )}>
      {(score * 100).toFixed(0)}%
    </span>
  )
}

const PREVIEW_LENGTH = 220

function SourceCard({ source, index }) {
  const [expanded, setExpanded] = useState(false)
  const isLong = source.page_content.length > PREVIEW_LENGTH
  const displayText = expanded || !isLong
    ? source.page_content
    : source.page_content.slice(0, PREVIEW_LENGTH) + '…'

  return (
    <div className="rounded-lg border border-ink-700 bg-ink-900/60 overflow-hidden animate-slide-in"
      style={{ animationDelay: `${index * 60}ms` }}>
      {/* Card header */}
      <div className="flex items-center justify-between gap-2 px-3 py-2 border-b border-ink-700/60 bg-ink-800/40">
        <div className="flex items-center gap-2 min-w-0">
          <FileText size={12} className="text-slate-500 flex-shrink-0" />
          <span className="text-xs font-medium text-slate-300 truncate">
            {source.filename}
          </span>
          {source.page_number && source.page_number !== -1 && (
            <span className="text-xs text-slate-600 flex-shrink-0">
              p.{source.page_number}
            </span>
          )}
        </div>
        <div className="flex items-center gap-2 flex-shrink-0">
          <span className="text-xs text-slate-700">relevance</span>
          <ScoreBadge score={source.score} />
        </div>
      </div>

      {/* Chunk text */}
      <div className="px-3 py-2.5">
        <p className="font-mono text-xs text-slate-400 leading-relaxed whitespace-pre-wrap break-words">
          {displayText}
        </p>
        {isLong && (
          <button
            onClick={() => setExpanded((e) => !e)}
            className="flex items-center gap-1 text-xs text-slate-600 hover:text-amber-400 mt-2 transition-colors"
          >
            {expanded ? (
              <><ChevronUp size={11} /> Show less</>
            ) : (
              <><ChevronDown size={11} /> Show more</>
            )}
          </button>
        )}
      </div>
    </div>
  )
}

export default function SourcePanel({ sources }) {
  return (
    <div className="mt-2 space-y-2">
      <p className="text-xs font-display font-semibold text-slate-600 uppercase tracking-wider">
        Retrieved chunks
      </p>
      {sources.map((source, i) => (
        <SourceCard key={source.chunk_id} source={source} index={i} />
      ))}
    </div>
  )
}
