import { Shield, LayoutDashboard, Upload, Search, ChevronRight } from 'lucide-react'
import { motion } from 'framer-motion'

const navItems = [
  { id: 'upload',    icon: Upload,          label: 'Upload & Analyse' },
  { id: 'dashboard', icon: LayoutDashboard, label: 'Results Dashboard' },
  { id: 'inspector', icon: Search,          label: 'Frame Inspector' },
]

export default function Sidebar({ activePage, setActivePage }) {
  return (
    <aside className="fixed left-0 top-0 h-full w-64 bg-white border-r border-slate-100 shadow-sm flex flex-col z-40">
      {/* Logo */}
      <div className="px-6 py-5 border-b border-slate-100">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl flex items-center justify-center shadow-sm" style={{background: 'linear-gradient(135deg, #4285F4 0%, #1a73e8 100%)'}}>
            <Shield size={18} className="text-white" strokeWidth={2.5} />
          </div>
          <div>
            <p className="font-bold text-slate-900 text-base leading-tight tracking-tight">AdShield</p>
            <p className="text-[10px] text-slate-400 font-medium leading-tight">Google Ads Policy Detector</p>
          </div>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 px-3 py-4 space-y-0.5">
        <p className="px-3 text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-2">Navigation</p>
        {navItems.map(({ id, icon: Icon, label }) => {
          const active = activePage === id
          return (
            <motion.button
              key={id}
              onClick={() => setActivePage(id)}
              whileHover={{ x: 2 }}
              whileTap={{ scale: 0.98 }}
              className={`w-full flex items-center justify-between px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-150 group ${
                active
                  ? 'text-blue-700'
                  : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
              }`}
              style={active ? {backgroundColor: '#e8f0fe'} : {}}
            >
              <span className="flex items-center gap-2.5">
                <Icon
                  size={16}
                  strokeWidth={active ? 2.5 : 2}
                  style={active ? {color: '#4285F4'} : {}}
                  className={active ? '' : 'text-slate-400 group-hover:text-slate-600'}
                />
                {label}
              </span>
              {active && <ChevronRight size={14} style={{color: '#4285F4'}} />}
            </motion.button>
          )
        })}
      </nav>

      {/* Footer */}
      <div className="px-4 py-4 border-t border-slate-100">
        <div className="rounded-xl p-3 border" style={{background: 'linear-gradient(135deg, #e8f0fe 0%, #fce8e6 50%, #fef9e0 100%)', borderColor: '#dadce0'}}>
          <p className="text-xs font-semibold" style={{color: '#1a73e8'}}>5 AI Models Active</p>
          <p className="text-[10px] mt-0.5" style={{color: '#4285F4'}}>YOLO-World · CLIP · NudeNet · MediaPipe · Whisper</p>
        </div>
      </div>
    </aside>
  )
}
