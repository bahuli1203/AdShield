import { motion } from 'framer-motion'
import {
  ResponsiveContainer, LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, ReferenceLine
} from 'recharts'

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null
  const score = payload[0]?.value
  const risk = score >= 0.75 ? 'HIGH RISK' : score >= 0.45 ? 'VIOLATION' : score >= 0.3 ? 'BORDERLINE' : 'SAFE'
  const color = score >= 0.75 ? '#dc2626' : score >= 0.45 ? '#ea580c' : score >= 0.3 ? '#d97706' : '#059669'
  return (
    <div className="bg-white border border-slate-200 rounded-xl shadow-lg px-3 py-2 text-xs">
      <p className="font-semibold text-slate-600">Frame @ {label}s</p>
      <p className="font-bold mt-0.5" style={{ color }}>Score: {(score * 100).toFixed(0)}% — {risk}</p>
    </div>
  )
}

export default function ViolationChart({ data }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: 0.25 }}
      className="card p-5"
    >
      <div className="flex items-center justify-between mb-4">
        <div>
          <p className="font-semibold text-slate-900">Violation Score Timeline</p>
          <p className="text-xs text-slate-400 mt-0.5">Each point = 1 frame · Horizontal lines = risk thresholds</p>
        </div>
        <div className="flex items-center gap-3 text-[10px] font-medium">
          <span className="flex items-center gap-1"><span className="w-5 h-0.5 bg-red-700 inline-block rounded" style={{borderTop:'2px dashed #b91c1c'}} />High Risk</span>
          <span className="flex items-center gap-1"><span className="w-5 h-0.5 bg-orange-500 inline-block rounded" style={{borderTop:'2px dashed #ea580c'}} />Violation</span>
          <span className="flex items-center gap-1"><span className="w-5 h-0.5 bg-amber-400 inline-block rounded" style={{borderTop:'2px dashed #d97706'}} />Borderline</span>
        </div>
      </div>

      <ResponsiveContainer width="100%" height={220}>
        <LineChart data={data} margin={{ top: 4, right: 8, left: -20, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
          <XAxis
            dataKey="time"
            tick={{ fontSize: 10, fill: '#94a3b8' }}
            axisLine={{ stroke: '#e2e8f0' }}
            tickLine={false}
            label={{ value: 'Time (s)', position: 'insideBottomRight', offset: 0, fontSize: 10, fill: '#94a3b8' }}
          />
          <YAxis
            domain={[0, 1]}
            tick={{ fontSize: 10, fill: '#94a3b8' }}
            axisLine={{ stroke: '#e2e8f0' }}
            tickLine={false}
            tickFormatter={v => `${(v * 100).toFixed(0)}%`}
          />
          <Tooltip content={<CustomTooltip />} />
          <ReferenceLine y={0.75} stroke="#b91c1c" strokeDasharray="5 4" strokeWidth={1.5} />
          <ReferenceLine y={0.45} stroke="#ea580c" strokeDasharray="5 4" strokeWidth={1.5} />
          <ReferenceLine y={0.30} stroke="#d97706" strokeDasharray="5 4" strokeWidth={1.5} />
          <Line
            type="monotone"
            dataKey="score"
            stroke="#dc2626"
            strokeWidth={2.5}
            dot={(props) => {
              const { cx, cy, payload } = props
              const s = payload.score
              const fill = s >= 0.75 ? '#b91c1c' : s >= 0.45 ? '#ea580c' : s >= 0.3 ? '#d97706' : '#10b981'
              return <circle key={`dot-${payload.time}`} cx={cx} cy={cy} r={4} fill={fill} stroke="#fff" strokeWidth={1.5} />
            }}
            activeDot={{ r: 6, stroke: '#fff', strokeWidth: 2 }}
            animationDuration={1200}
            animationEasing="ease-out"
          />
        </LineChart>
      </ResponsiveContainer>
    </motion.div>
  )
}
