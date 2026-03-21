/**
 * components/Sidebar.jsx
 * =======================
 * Left panel: document upload drop zone + document list with selection.
 *
 * On mount, fetches existing documents from the backend.
 * Supports drag-and-drop + click-to-browse upload.
 * Each document can be selected/deselected to scope chat queries.
 */

import { useCallback, useEffect, useRef, useState } from 'react'
import { useDropzone } from 'react-dropzone'
import {
  FileText, Trash2, Upload, CheckSquare, Square,
  Loader2, AlertCircle, FileType, CheckCircle, RefreshCw
} from 'lucide-react'
import clsx from 'clsx'
import { uploadDocument, listDocuments, deleteDocument } from '../services/api'

const ACCEPTED_TYPES = {
  'application/pdf': ['.pdf'],
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
  'text/plain': ['.txt'],
}

// Human-readable file sizes
function formatBytes(bytes) {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 ** 2) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / 1024 ** 2).toFixed(1)} MB`
}

export default function Sidebar({
  open,
  documents,
  selectedDocIds,
  onDocumentUploaded,
  onDocumentsLoaded,
  onToggleDoc,
  onDocumentDeleted,
}) {
  const [uploading, setUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [uploadError, setUploadError] = useState(null)
  const [uploadSuccess, setUploadSuccess] = useState(null)
  const [loadingDocs, setLoadingDocs] = useState(true)
  const [deletingId, setDeletingId] = useState(null)
  const successTimer = useRef(null)

  // Load documents from backend on mount
  useEffect(() => {
    async function load() {
      try {
        const res = await listDocuments()
        onDocumentsLoaded(res.documents || [])
      } catch {
        // silently fail — backend may not be running yet locally
      } finally {
        setLoadingDocs(false)
      }
    }
    load()
  }, [onDocumentsLoaded])

  // Handle file drop / selection
  const onDrop = useCallback(async (acceptedFiles) => {
    if (!acceptedFiles.length) return
    const file = acceptedFiles[0]
    setUploading(true)
    setUploadError(null)
    setUploadSuccess(null)
    setUploadProgress(0)

    try {
      const result = await uploadDocument(file, setUploadProgress)
      onDocumentUploaded(result)
      setUploadSuccess(`"${result.filename}" ingested (${result.num_chunks} chunks)`)
      // Auto-clear success banner after 4 s
      clearTimeout(successTimer.current)
      successTimer.current = setTimeout(() => setUploadSuccess(null), 4000)
    } catch (err) {
      setUploadError(err.message || 'Upload failed')
    } finally {
      setUploading(false)
      setUploadProgress(0)
    }
  }, [onDocumentUploaded])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: ACCEPTED_TYPES,
    maxFiles: 1,
    maxSize: 20 * 1024 * 1024,
    disabled: uploading,
  })

  const handleDelete = async (e, docId) => {
    e.stopPropagation()
    if (!confirm('Remove this document and its embeddings?')) return
    setDeletingId(docId)
    try {
      await deleteDocument(docId)
      onDocumentDeleted(docId)
    } catch (err) {
      alert('Delete failed: ' + err.message)
    } finally {
      setDeletingId(null)
    }
  }

  // File type icon colour
  const docIconColor = (filename) => {
    if (filename?.endsWith('.pdf')) return 'text-red-400'
    if (filename?.endsWith('.docx')) return 'text-blue-400'
    return 'text-slate-400'
  }

  if (!open) return null

  return (
    <aside className="w-72 flex-shrink-0 flex flex-col border-r border-ink-800 bg-ink-900/50 overflow-hidden">
      {/* ── Section header ── */}
      <div className="px-4 pt-4 pb-3 border-b border-ink-800">
        <p className="font-display font-semibold text-sm text-slate-200 tracking-wide uppercase">
          Documents
        </p>
        <p className="text-xs text-slate-500 mt-0.5">Upload PDF, DOCX, or TXT</p>
      </div>

      {/* ── Drop zone ── */}
      <div className="p-3">
        <div
          {...getRootProps()}
          className={clsx(
            'relative rounded-xl border-2 border-dashed border-ink-700 p-4 cursor-pointer',
            'flex flex-col items-center justify-center gap-2 text-center',
            'transition-all duration-200 group',
            isDragActive
              ? 'border-amber-400 bg-amber-400/5 dropzone-active'
              : 'hover:border-ink-600 hover:bg-ink-800/40',
            uploading && 'pointer-events-none opacity-60'
          )}
        >
          <input {...getInputProps()} />

          {uploading ? (
            <>
              <Loader2 size={22} className="text-amber-400 animate-spin" />
              <p className="text-xs text-slate-400">Uploading… {uploadProgress}%</p>
              {/* Progress bar */}
              <div className="w-full bg-ink-800 rounded-full h-1 mt-1">
                <div
                  className="bg-amber-400 h-1 rounded-full transition-all duration-300"
                  style={{ width: `${uploadProgress}%` }}
                />
              </div>
            </>
          ) : isDragActive ? (
            <>
              <Upload size={22} className="text-amber-400" />
              <p className="text-xs text-amber-300 font-medium">Drop to upload</p>
            </>
          ) : (
            <>
              <div className="w-9 h-9 rounded-lg bg-ink-800 group-hover:bg-ink-700 flex items-center justify-center transition-colors">
                <Upload size={16} className="text-slate-400 group-hover:text-amber-400 transition-colors" />
              </div>
              <div>
                <p className="text-xs font-medium text-slate-300">
                  Drop file or <span className="text-amber-400 underline underline-offset-2">browse</span>
                </p>
                <p className="text-xs text-slate-600 mt-0.5">PDF · DOCX · TXT · Max 20 MB</p>
              </div>
            </>
          )}
        </div>

        {/* Upload feedback banners */}
        {uploadError && (
          <div className="mt-2 flex items-start gap-2 text-xs text-red-400 bg-red-400/10 border border-red-400/20 rounded-lg p-2.5">
            <AlertCircle size={13} className="flex-shrink-0 mt-0.5" />
            <span>{uploadError}</span>
          </div>
        )}
        {uploadSuccess && (
          <div className="mt-2 flex items-start gap-2 text-xs text-emerald-400 bg-emerald-400/10 border border-emerald-400/20 rounded-lg p-2.5 animate-fade-up">
            <CheckCircle size={13} className="flex-shrink-0 mt-0.5" />
            <span>{uploadSuccess}</span>
          </div>
        )}
      </div>

      {/* ── Document list ── */}
      <div className="flex-1 overflow-y-auto px-3 pb-3 space-y-1.5">
        {loadingDocs ? (
          <div className="flex items-center justify-center py-8 gap-2 text-slate-600 text-xs">
            <Loader2 size={14} className="animate-spin" />
            Loading…
          </div>
        ) : documents.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-10 text-center gap-2">
            <FileType size={28} className="text-ink-700" />
            <p className="text-xs text-slate-600">No documents yet.</p>
            <p className="text-xs text-slate-700">Upload one above to get started.</p>
          </div>
        ) : (
          documents.map((doc) => {
            const isSelected = selectedDocIds.includes(doc.doc_id)
            const isDeleting = deletingId === doc.doc_id

            return (
              <div
                key={doc.doc_id}
                onClick={() => onToggleDoc(doc.doc_id)}
                className={clsx(
                  'flex items-start gap-2.5 rounded-lg p-2.5 cursor-pointer group',
                  'border transition-all duration-150',
                  isSelected
                    ? 'border-amber-500/40 bg-amber-400/5 hover:bg-amber-400/8'
                    : 'border-transparent bg-ink-800/40 hover:bg-ink-800 hover:border-ink-700'
                )}
              >
                {/* Selection checkbox */}
                <div className="mt-0.5 flex-shrink-0">
                  {isSelected
                    ? <CheckSquare size={14} className="text-amber-400" />
                    : <Square size={14} className="text-slate-600 group-hover:text-slate-500" />
                  }
                </div>

                {/* File icon */}
                <FileText size={14} className={clsx('mt-0.5 flex-shrink-0', docIconColor(doc.filename))} />

                {/* Details */}
                <div className="flex-1 min-w-0">
                  <p className="text-xs font-medium text-slate-200 truncate leading-tight">
                    {doc.filename}
                  </p>
                  <p className="text-xs text-slate-600 mt-0.5">
                    {doc.num_chunks} chunks · {formatBytes(doc.size_bytes)}
                  </p>
                </div>

                {/* Delete button */}
                <button
                  onClick={(e) => handleDelete(e, doc.doc_id)}
                  disabled={isDeleting}
                  className="flex-shrink-0 opacity-0 group-hover:opacity-100 p-1 rounded hover:bg-red-400/10 text-slate-600 hover:text-red-400 transition-all"
                  aria-label="Delete document"
                >
                  {isDeleting
                    ? <Loader2 size={12} className="animate-spin" />
                    : <Trash2 size={12} />
                  }
                </button>
              </div>
            )
          })
        )}
      </div>

      {/* ── Footer: filter note ── */}
      {documents.length > 0 && (
        <div className="px-4 py-2.5 border-t border-ink-800">
          <p className="text-xs text-slate-600 leading-relaxed">
            {selectedDocIds.length === 0
              ? 'Searching all documents'
              : `Filtering to ${selectedDocIds.length} selected`
            }
          </p>
        </div>
      )}
    </aside>
  )
}
