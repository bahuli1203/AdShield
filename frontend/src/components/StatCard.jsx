import { motion } from 'framer-motion'

const riskConfig = {
  SAFE:      { label: '✅ SAFE',      cls: 'badge-safe' },
  BORDERLINE:{ label: '⚠️ BORDERLINE', cls: 'badge-borderline' },
  VIOLATION: { label: '🔴 VIOLATION',  cls: 'badge-violation' },
  'HIGH RISK':{ label: '🚨 HIGH RISK', cls: 'badge-highrisk' },
}

export function RiskBadge({ risk }) {
  const cfg = riskConfig[risk] ?? riskConfig['SAFE']
  return <span className={cfg.cls}>{cfg.label}</span>
}

export default function StatCard({ title, value, sub, icon: Icon, accent = 'slate', delay = 0 }) {
  const accentMap = {
    slate:  'bg-slate-100 text-slate-500',
    red:    'bg-red-50 text-red-500',
    orange: 'bg-orange-50 text-orange-500',
    green:  'bg-emerald-50 text-emerald-500',
    amber:  'bg-amber-50 text-amber-500',
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay }}
      className="card p-5 hover:shadow-card-hover transition-shadow duration-200"
    >
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">{title}</p>
          <p className="text-3xl font-bold text-slate-900 mt-1">{value}</p>
          {sub && <p className="text-xs text-slate-500 mt-1">{sub}</p>}
        </div>
        {Icon && (
          <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${accentMap[accent]}`}>
            <Icon size={18} strokeWidth={2} />
          </div>
        )}
      </div>
    </motion.div>
  )
}
