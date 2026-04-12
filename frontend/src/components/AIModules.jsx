import { motion } from 'framer-motion'
import { Target, ShieldOff, Film, Waves, PersonStanding, BarChart3, Eye } from 'lucide-react'

const MODULES = [
  { key: 'objectDetection',    icon: Target,          label: 'Object Detection',      sub: 'YOLO-World: guns, knives, syringes' },
  { key: 'nsfwDetection',      icon: ShieldOff,       label: 'NSFW Content Detection', sub: 'NudeNet explicit content filter' },
  { key: 'sceneClassification',icon: Film,            label: 'Scene Classification',  sub: 'CLIP zero-shot scene understanding' },
  { key: 'motionAnalysis',     icon: Waves,           label: 'Optical Flow Motion',   sub: 'Detects violent/chaotic motion' },
  { key: 'actionRecognition',  icon: PersonStanding,  label: 'Action Recognition',    sub: 'MediaPipe combat pose detection' },
  { key: 'anomalyDetection',   icon: BarChart3,       label: 'Anomaly Detection',     sub: 'Z-score statistical spike detection' },
]

function Toggle({ enabled, onToggle }) {
  return (
    <motion.button
      onClick={onToggle}
      className={`toggle-track ${enabled ? 'bg-blue-500' : 'bg-slate-200'}`}
      whileTap={{ scale: 0.95 }}
    >
      <motion.span
        className="toggle-thumb"
        animate={{ x: enabled ? 16 : 0 }}
        transition={{ type: 'spring', stiffness: 500, damping: 30 }}
      />
    </motion.button>
  )
}

export default function AIModules({ modules, onChange }) {
  const toggle = (key) => onChange({ ...modules, [key]: !modules[key] })
  const activeCount = Object.values(modules).filter(Boolean).length

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, delay: 0.2 }}
      className="card p-5"
    >
      <div className="flex items-center justify-between mb-4">
        <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">🤖 AI Modules</p>
        <span className="text-xs font-semibold text-blue-600 bg-blue-50 px-2 py-0.5 rounded-lg border border-blue-100">
          {activeCount}/{MODULES.length} active
        </span>
      </div>

      <div className="space-y-1">
        {MODULES.map(({ key, icon: Icon, label, sub }, i) => (
          <motion.div
            key={key}
            initial={{ opacity: 0, x: -8 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: i * 0.05 }}
            className="flex items-center justify-between p-2.5 rounded-xl hover:bg-slate-50 transition-colors group"
          >
            <div className="flex items-center gap-2.5">
              <div className={`w-7 h-7 rounded-lg flex items-center justify-center transition-colors ${
                modules[key] ? 'bg-blue-50 text-blue-600' : 'bg-slate-100 text-slate-400'
              }`}>
                <Icon size={13} strokeWidth={2.5} />
              </div>
              <div>
                <p className={`text-xs font-semibold transition-colors ${modules[key] ? 'text-slate-800' : 'text-slate-400'}`}>
                  {label}
                </p>
                <p className="text-[10px] text-slate-400 leading-tight">{sub}</p>
              </div>
            </div>
            <Toggle enabled={modules[key]} onToggle={() => toggle(key)} />
          </motion.div>
        ))}
      </div>
    </motion.div>
  )
}
