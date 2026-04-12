import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { RiskBadge } from './StatCard'

const PAGE_SIZE = 12

export default function FrameGrid({ frames, showAll = false }) {
  const [page, setPage]       = useState(0)
  const [selected, setSelected] = useState(null)
  const [imgErrors, setImgErrors] = useState({})

  if (!frames?.length) {
    return (
      <div className="card p-12 text-center">
        <p className="text-3xl mb-2">🖼️</p>
        <p className="font-semibold text-slate-700">No frames to display</p>
        <p className="text-xs text-slate-400 mt-1">Run an analysis to see extracted frames here</p>
      </div>
    )
  }

  // For dashboard, show only flagged. For inspector, show all paginated
  const displayFrames = showAll ? frames : frames.filter(f => f.riskLevel !== 'SAFE').slice(0, 6)
  const paged = showAll ? displayFrames.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE) : displayFrames
  const totalPages = Math.ceil(displayFrames.length / PAGE_SIZE)

  const scoreColor = (s) =>
    s >= 0.75 ? '#b91c1c' : s >= 0.45 ? '#ea580c' : s >= 0.3 ? '#d97706' : '#059669'

  const handleImgError = (idx, useAnnotated) => {
    setImgErrors(prev => ({ ...prev, [idx]: true }))
  }

  return (
    <>
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <p className="font-semibold text-slate-900">
            {showAll ? 'All Extracted Frames' : 'Most Concerning Frames'}
          </p>
          <p className="text-xs text-slate-400 mt-0.5">
            {showAll
              ? `${displayFrames.length} frames · page ${page + 1}/${totalPages}`
              : `Top ${displayFrames.length} frames by violation score`}
          </p>
        </div>
        {showAll && totalPages > 1 && (
          <div className="flex items-center gap-2">
            <button
              disabled={page === 0}
              onClick={() => setPage(p => p - 1)}
              className="px-3 py-1.5 text-xs font-medium rounded-lg border border-slate-200 disabled:opacity-40 hover:bg-slate-50 transition-colors"
            >← Prev</button>
            <span className="text-xs text-slate-500">{page + 1} / {totalPages}</span>
            <button
              disabled={page >= totalPages - 1}
              onClick={() => setPage(p => p + 1)}
              className="px-3 py-1.5 text-xs font-medium rounded-lg border border-slate-200 disabled:opacity-40 hover:bg-slate-50 transition-colors"
            >Next →</button>
          </div>
        )}
      </div>

      {/* Grid */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
        {paged.map((frame, i) => {
          const imgSrc = frame.annotatedUrl || frame.frameUrl
          const fallbackSrc = frame.frameUrl
          const hasError = imgErrors[frame.index]
          return (
            <motion.div
              key={`${frame.index}-${page}`}
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: i * 0.04 }}
              whileHover={{ scale: 1.03, y: -3 }}
              onClick={() => setSelected(frame)}
              className="group relative rounded-xl overflow-hidden border border-slate-200 cursor-pointer bg-slate-100"
              style={{ boxShadow: '0 1px 4px rgba(0,0,0,0.07)' }}
            >
              {/* Frame Image */}
              <div className="relative aspect-video bg-slate-100 overflow-hidden">
                {imgSrc && !hasError ? (
                  <img
                    src={imgSrc}
                    alt={`Frame @ ${frame.timestamp}`}
                    className="w-full h-full object-cover"
                    onError={() => handleImgError(frame.index)}
                    loading="lazy"
                  />
                ) : fallbackSrc && !hasError ? (
                  <img
                    src={fallbackSrc}
                    alt={`Frame @ ${frame.timestamp}`}
                    className="w-full h-full object-cover"
                    onError={() => handleImgError(frame.index)}
                    loading="lazy"
                  />
                ) : (
                  /* Placeholder if no real image or error */
                  <div className="w-full h-full flex flex-col items-center justify-center gap-1 bg-gradient-to-br from-slate-100 to-slate-50">
                    <span className="text-2xl">
                      {frame.riskLevel === 'HIGH RISK' ? '🚨' : frame.riskLevel === 'VIOLATION' ? '🔴' : frame.riskLevel === 'BORDERLINE' ? '⚠️' : '✅'}
                    </span>
                    <span className="text-[10px] text-slate-400">No image</span>
                  </div>
                )}

                {/* Score chip */}
                <div className="absolute top-1.5 left-1.5">
                  <span
                    className="text-[10px] font-bold px-1.5 py-0.5 rounded-md text-white shadow-sm"
                    style={{ background: scoreColor(frame.finalScore) }}
                  >
                    {(frame.finalScore * 100).toFixed(0)}%
                  </span>
                </div>

                {/* Detection label */}
                {frame.label && (
                  <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/70 to-transparent px-2 py-1.5">
                    <p className="text-[10px] text-white font-medium truncate">{frame.label}</p>
                  </div>
                )}

                {/* Hover glow ring */}
                <div className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none ring-2 ring-red-400/50 rounded-xl" />
              </div>

              {/* Info bar */}
              <div className="bg-white px-2.5 py-1.5 border-t border-slate-100 flex items-center justify-between">
                <span className="font-mono text-[10px] text-slate-400">⏱ {frame.timestamp}</span>
                <RiskBadge risk={frame.riskLevel} />
              </div>
            </motion.div>
          )
        })}
      </div>

      {/* Lightbox modal */}
      <AnimatePresence>
        {selected && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-6"
            onClick={() => setSelected(null)}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              className="bg-white rounded-2xl shadow-2xl max-w-2xl w-full overflow-hidden"
              onClick={e => e.stopPropagation()}
            >
              {/* Image */}
              <div className="bg-slate-900 aspect-video flex items-center justify-center">
                {(selected.annotatedUrl || selected.frameUrl) && !imgErrors[selected.index] ? (
                  <img
                    src={selected.annotatedUrl || selected.frameUrl}
                    alt={`Frame @ ${selected.timestamp}`}
                    className="max-h-full max-w-full object-contain"
                  />
                ) : (
                  <div className="text-white text-center">
                    <p className="text-4xl mb-2">🖼️</p>
                    <p className="text-sm opacity-60">Image not available</p>
                  </div>
                )}
              </div>

              {/* Details */}
              <div className="p-5">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-sm text-slate-500">⏱ {selected.timestamp}</span>
                    <RiskBadge risk={selected.riskLevel} />
                  </div>
                  <span
                    className="text-sm font-bold px-2.5 py-0.5 rounded-lg text-white"
                    style={{ background: scoreColor(selected.finalScore) }}
                  >
                    {(selected.finalScore * 100).toFixed(0)}% risk
                  </span>
                </div>

                {selected.violationReasons?.length > 0 && (
                  <div className="space-y-1">
                    <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Violation Reasons</p>
                    {selected.violationReasons.map((r, i) => (
                      <p key={i} className="text-xs text-slate-700 bg-slate-50 rounded-lg px-3 py-1.5 border border-slate-100">{r}</p>
                    ))}
                  </div>
                )}

                <button
                  onClick={() => setSelected(null)}
                  className="mt-4 w-full py-2 text-sm font-medium text-slate-600 border border-slate-200 rounded-xl hover:bg-slate-50 transition-colors"
                >
                  Close
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  )
}
