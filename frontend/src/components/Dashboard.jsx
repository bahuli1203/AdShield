import { motion } from 'framer-motion'
import { ScanLine, AlertTriangle, Shield, Activity } from 'lucide-react'
import StatCard, { RiskBadge } from './StatCard'
import ViolationChart from './ViolationChart'
import FlaggedTable from './FlaggedTable'
import FrameGrid from './FrameGrid'

function SignalTag({ label, active }) {
  return (
    <span className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs font-semibold border transition-all ${
      active
        ? 'border-blue-200'
        : 'bg-slate-50 text-slate-400 border-slate-100 opacity-50'
    }`}
    style={active ? {backgroundColor: '#e8f0fe', color: '#1a73e8'} : {}}>
      {active ? '🔵' : '⚪'} {label}
    </span>
  )
}

export default function Dashboard({ result }) {
  if (!result) {
    return (
      <div className="h-full flex flex-col items-center justify-center text-center py-24 gap-4">
        <div className="w-16 h-16 rounded-2xl bg-slate-100 flex items-center justify-center">
          <Activity size={28} className="text-slate-300" />
        </div>
        <div>
          <p className="font-semibold text-slate-500">No analysis results yet</p>
          <p className="text-sm text-slate-400 mt-1">Upload a video and run analysis to see the dashboard</p>
        </div>
      </div>
    )
  }

  const { overallRisk, finalScore, framesAnalyzed, flaggedFrames, signals, timeline, flaggedSegments, frames } = result

  const riskBg = overallRisk === 'HIGH RISK'  ? 'from-red-50 to-rose-50 border-red-200' :
                 overallRisk === 'VIOLATION'   ? 'from-orange-50 to-amber-50 border-orange-200' :
                 overallRisk === 'BORDERLINE'  ? 'from-amber-50 to-yellow-50 border-amber-200' :
                                                 'from-emerald-50 to-green-50 border-emerald-200'

  return (
    <div className="space-y-5">
      {/* Overall Risk Banner */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className={`card p-5 border bg-gradient-to-r ${riskBg}`}
      >
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">Overall Verdict</p>
            <div className="flex items-center gap-3">
              <RiskBadge risk={overallRisk} />
              <span className="font-bold text-2xl text-slate-900">{(finalScore * 100).toFixed(0)}%</span>
              <span className="text-sm text-slate-500">risk score</span>
            </div>
          </div>
          <div className="flex flex-wrap gap-2">
            <SignalTag label="Object Hit"  active={signals.objectHit} />
            <SignalTag label="NSFW Hit"    active={signals.nsfwHit} />
            <SignalTag label="Scene Hit"   active={signals.sceneHit} />
            <SignalTag label="Motion Hit"  active={signals.motionHit} />
            <SignalTag label="Action Hit"  active={signals.actionHit} />
            <SignalTag label="Anomaly Hit" active={signals.anomalyHit} />
          </div>
        </div>
      </motion.div>

      {/* Stat Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard title="Frames Analysed" value={framesAnalyzed}     icon={ScanLine}      accent="slate" delay={0}    />
        <StatCard title="Flagged Frames"  value={flaggedFrames}      icon={AlertTriangle} accent="red"   delay={0.05} sub={`${Math.round(flaggedFrames/framesAnalyzed*100)}% of total`} />
        <StatCard title="Segments Found"  value={flaggedSegments.length} icon={Shield}   accent="orange" delay={0.1} />
        <StatCard title="Risk Score"      value={`${(finalScore*100).toFixed(0)}%`} icon={Activity} accent={overallRisk === 'SAFE' ? 'green' : 'red'} delay={0.15} />
      </div>

      {/* Timeline */}
      <ViolationChart data={timeline} />

      {/* Flagged Segments Table */}
      <div>
        <FlaggedTable segments={flaggedSegments} />
      </div>

      {/* Frame Grid — flagged only */}
      <FrameGrid frames={frames} showAll={false} />
    </div>
  )
}
