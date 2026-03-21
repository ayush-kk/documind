/**
 * components/Header.jsx
 * ======================
 * Top navigation bar with branding and sidebar toggle.
 */

import { PanelLeftOpen, PanelLeftClose, Brain } from 'lucide-react'
import clsx from 'clsx'

export default function Header({ sidebarOpen, onToggleSidebar, docCount }) {
  return (
    <header className="flex items-center justify-between h-14 px-4 border-b border-ink-800 bg-ink-900/80 backdrop-blur-sm flex-shrink-0 z-10">
      {/* Brand */}
      <div className="flex items-center gap-3">
        <button
          onClick={onToggleSidebar}
          className="p-1.5 rounded-md text-slate-400 hover:text-amber-400 hover:bg-ink-800 transition-colors"
          aria-label="Toggle sidebar"
        >
          {sidebarOpen
            ? <PanelLeftClose size={18} />
            : <PanelLeftOpen size={18} />}
        </button>

        {/* Logo mark */}
        <div className="flex items-center gap-2">
          <div className="relative w-7 h-7 flex items-center justify-center">
            <div className="absolute inset-0 bg-amber-400/20 rounded-lg" />
            <Brain size={15} className="text-amber-400 relative z-10" />
          </div>
          <span className="font-display font-700 text-base tracking-tight text-slate-100">
            Docu<span className="text-amber-400">Mind</span>
          </span>
        </div>
      </div>

      {/* Right side metadata */}
      <div className="flex items-center gap-3 text-xs text-slate-500">
        {docCount > 0 && (
          <span className="flex items-center gap-1.5 bg-ink-800 px-2.5 py-1 rounded-full border border-ink-700">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
            {docCount} document{docCount !== 1 ? 's' : ''} loaded
          </span>
        )}
        <span className="hidden sm:block text-slate-600 font-mono text-xs">RAG · Groq · ChromaDB</span>
      </div>
    </header>
  )
}
