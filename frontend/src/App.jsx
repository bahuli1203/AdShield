import { useState } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import Sidebar from './components/Sidebar'
import VideoUpload from './components/VideoUpload'
import SettingsPanel from './components/SettingsPanel'
import AIModules from './components/AIModules'
import Dashboard from './components/Dashboard'
import FrameGrid from './components/FrameGrid'
import { defaultModules, defaultSettings } from './data/dummyData'

export default function App() {
  const [activePage, setActivePage] = useState('upload')
  const [result, setResult]         = useState(null)
  const [modules, setModules]       = useState(defaultModules)
  const [settings, setSettings]     = useState(defaultSettings)

  const handleResult = (data) => {
    setResult(data)
    setActivePage('dashboard')
  }

  return (
    <div className="min-h-screen bg-slate-50">
      <Sidebar activePage={activePage} setActivePage={setActivePage} />

      {/* Main content */}
      <div className="ml-64 min-h-screen">
        {/* Top bar */}
        <header className="sticky top-0 z-30 bg-white/80 backdrop-blur border-b border-slate-100 px-8 py-3.5 flex items-center justify-between">
          <div>
            <h1 className="font-bold text-slate-900 text-base capitalize">
              {activePage === 'upload'    ? '📤 Upload & Analyse'   :
               activePage === 'dashboard' ? '📊 Results Dashboard'  :
                                           '🔎 Frame Inspector'}
            </h1>
            <p className="text-xs text-slate-400 mt-0.5">AdShield · Google Ads Policy Violation Detector</p>
          </div>
          {result && (
            <span className="text-xs bg-emerald-50 text-emerald-700 border border-emerald-200 px-3 py-1 rounded-full font-semibold">
              ✅ Analysis complete
            </span>
          )}
        </header>

        {/* Page content */}
        <main className="p-8">
          <AnimatePresence mode="wait">
            {/* UPLOAD PAGE */}
            {activePage === 'upload' && (
              <motion.div
                key="upload"
                initial={{ opacity: 0, y: 16 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -8 }}
                transition={{ duration: 0.25 }}
                className="max-w-5xl mx-auto grid grid-cols-1 lg:grid-cols-3 gap-6"
              >
                {/* Left: Upload */}
                <div className="lg:col-span-2 space-y-5">
                  <div className="card p-6">
                    <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-4">📤 Video Source</p>
                    <VideoUpload onResult={handleResult} settings={settings} modules={modules} />
                  </div>
                </div>
                {/* Right: Settings + Modules */}
                <div className="space-y-4">
                  <SettingsPanel settings={settings} onChange={setSettings} />
                  <AIModules modules={modules} onChange={setModules} />
                </div>
              </motion.div>
            )}

            {/* DASHBOARD PAGE */}
            {activePage === 'dashboard' && (
              <motion.div
                key="dashboard"
                initial={{ opacity: 0, y: 16 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -8 }}
                transition={{ duration: 0.25 }}
                className="max-w-6xl mx-auto"
              >
                <Dashboard result={result} />
              </motion.div>
            )}

            {/* FRAME INSPECTOR */}
            {activePage === 'inspector' && (
              <motion.div
                key="inspector"
                initial={{ opacity: 0, y: 16 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -8 }}
                transition={{ duration: 0.25 }}
                className="max-w-6xl mx-auto space-y-5"
              >
                <div className="card p-5">
                  <p className="font-semibold text-slate-900 mb-1">Frame Inspector</p>
                  <p className="text-xs text-slate-400">Browse all frames from the latest analysis and inspect bounding box detections</p>
                </div>
                {result ? (
                  <div className="card p-5">
                    <FrameGrid frames={result.frames} showAll={true} />
                  </div>
                ) : (
                  <div className="card p-12 text-center">
                    <p className="text-2xl mb-2">🔎</p>
                    <p className="font-semibold text-slate-600">No analysis data</p>
                    <p className="text-xs text-slate-400 mt-1">Run an analysis first to inspect frames</p>
                  </div>
                )}
              </motion.div>
            )}
          </AnimatePresence>
        </main>
      </div>
    </div>
  )
}
