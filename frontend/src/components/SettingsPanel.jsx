import { motion } from 'framer-motion'

function Slider({ label, min, max, step, value, onChange, format }) {
  const pct = ((value - min) / (max - min)) * 100
  return (
    <div className="space-y-2">
      <div className="flex justify-between items-center">
        <p className="text-sm font-medium text-slate-700">{label}</p>
        <span className="text-sm font-bold text-blue-600 bg-blue-50 px-2.5 py-0.5 rounded-lg border border-blue-100">
          {format ? format(value) : value}
        </span>
      </div>
      <div className="relative h-2 bg-slate-100 rounded-full">
        <div
          className="absolute top-0 left-0 h-full bg-gradient-to-r from-blue-400 to-blue-600 rounded-full transition-all"
          style={{ width: `${pct}%` }}
        />
        <input
          type="range"
          min={min} max={max} step={step} value={value}
          onChange={e => onChange(Number(e.target.value))}
          className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
        />
      </div>
      <div className="flex justify-between text-[10px] text-slate-400 font-medium">
        <span>{format ? format(min) : min}</span>
        <span>{format ? format(max) : max}</span>
      </div>
    </div>
  )
}

export default function SettingsPanel({ settings, onChange }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, delay: 0.1 }}
      className="card p-5 space-y-6"
    >
      <div>
        <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-4">⚙️ Settings</p>
        <div className="space-y-6">
          <Slider
            label="Frame Sample Rate"
            min={0.5} max={5} step={0.5}
            value={settings.frameSampleRate}
            onChange={v => onChange({ ...settings, frameSampleRate: v })}
            format={v => `${v}s`}
          />
          <Slider
            label="Violation Threshold"
            min={0.2} max={0.8} step={0.05}
            value={settings.violationThreshold}
            onChange={v => onChange({ ...settings, violationThreshold: v })}
            format={v => v.toFixed(2)}
          />
        </div>
      </div>

      {/* Threshold guide */}
      <div className="bg-slate-50 rounded-xl p-3 space-y-1.5 border border-slate-100">
        <p className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider">Threshold Guide</p>
        {[
          { label: '≥ 0.75', risk: 'HIGH RISK', color: 'text-red-600' },
          { label: '≥ 0.45', risk: 'VIOLATION', color: 'text-orange-600' },
          { label: '≥ 0.30', risk: 'BORDERLINE', color: 'text-amber-600' },
          { label: '< 0.30', risk: 'SAFE', color: 'text-emerald-600' },
        ].map(r => (
          <div key={r.risk} className="flex justify-between text-xs">
            <span className="text-slate-500">{r.label}</span>
            <span className={`font-semibold ${r.color}`}>{r.risk}</span>
          </div>
        ))}
      </div>
    </motion.div>
  )
}
