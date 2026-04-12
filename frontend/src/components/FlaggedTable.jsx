import { motion } from 'framer-motion'
import { RiskBadge } from './StatCard'

export default function FlaggedTable({ segments }) {
  if (!segments?.length) {
    return (
      <div className="card p-8 text-center">
        <p className="text-2xl mb-2">✅</p>
        <p className="font-semibold text-slate-700">No Flagged Segments</p>
        <p className="text-xs text-slate-400 mt-1">All frames fall below the violation threshold</p>
      </div>
    )
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay: 0.3 }}
      className="card overflow-hidden"
    >
      <div className="px-5 py-4 border-b border-slate-100">
        <p className="font-semibold text-slate-900">Flagged Segments</p>
        <p className="text-xs text-slate-400 mt-0.5">{segments.length} segment{segments.length !== 1 ? 's' : ''} require attention</p>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-slate-50 border-b border-slate-100">
              {['Start', 'End', 'Duration', 'Peak Score', 'Risk', 'Reasons'].map(h => (
                <th key={h} className="px-4 py-2.5 text-left text-[10px] font-semibold text-slate-500 uppercase tracking-wider">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {segments.map((seg, i) => {
              const score = seg.peakScore
              const scoreColor = score >= 0.75 ? 'text-red-700 bg-red-50' : score >= 0.45 ? 'text-orange-700 bg-orange-50' : 'text-amber-700 bg-amber-50'
              return (
                <motion.tr
                  key={i}
                  initial={{ opacity: 0, x: -8 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: i * 0.08 }}
                  className="border-b border-slate-50 hover:bg-slate-50 transition-colors"
                >
                  <td className="px-4 py-3 font-mono text-xs text-slate-700">{seg.start}</td>
                  <td className="px-4 py-3 font-mono text-xs text-slate-700">{seg.end}</td>
                  <td className="px-4 py-3 text-xs text-slate-500">{seg.duration}</td>
                  <td className="px-4 py-3">
                    <span className={`text-xs font-bold px-2 py-0.5 rounded-lg ${scoreColor}`}>
                      {(score * 100).toFixed(0)}%
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <RiskBadge risk={seg.risk} />
                  </td>
                  <td className="px-4 py-3 text-xs text-slate-500 max-w-xs truncate" title={seg.reasons}>
                    {seg.reasons}
                  </td>
                </motion.tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </motion.div>
  )
}
