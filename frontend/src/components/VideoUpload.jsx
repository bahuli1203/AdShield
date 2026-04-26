import { useState, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Upload, Link, Play, CheckCircle, Loader2, AlertCircle } from 'lucide-react'

const API = ''  // Vite proxy forwards /analyse → http://localhost:8000

const LOADING_STEPS = [
  'Uploading video…',
  'Extracting frames…',
  'Running YOLO-World object detection…',
  'Running CLIP scene classification…',
  'Running NudeNet NSFW check…',
  'Running MediaPipe pose recognition…',
  'Statistical anomaly analysis…',
  'Generating report…',
]

export default function VideoUpload({ onResult, settings, modules }) {
  const [mode, setMode]       = useState('file')
  const [file, setFile]       = useState(null)
  const [url, setUrl]         = useState('')
  const [cookiesBrowser, setCookiesBrowser] = useState('')
  const [dragging, setDragging] = useState(false)
  const [loading, setLoading] = useState(false)
  const [stepIdx, setStepIdx] = useState(0)
  const [done, setDone]       = useState(false)
  const [error, setError]     = useState(null)

  const handleFile = (f) => {
    if (f) { setFile(f); setDone(false); setError(null) }
  }

  const onDrop = useCallback((e) => {
    e.preventDefault(); setDragging(false)
    handleFile(e.dataTransfer.files[0])
  }, [])

  const runAnalysis = async () => {
    setLoading(true); setStepIdx(0); setError(null)

    // Animate steps while waiting for API
    let stepTimer = 0
    const stepIntervals = LOADING_STEPS.map((_, i) =>
      setTimeout(() => setStepIdx(i), i * 2500)
    )

    try {
      const form = new FormData()
      if (mode === 'file' && file)  form.append('file', file)
      if (mode === 'url' && url)    form.append('url', url)
      if (cookiesBrowser)           form.append('cookies_browser', cookiesBrowser)

      form.append('frame_sample_rate',   settings?.frameSampleRate ?? 1)
      form.append('violation_threshold', settings?.violationThreshold ?? 0.45)
      form.append('use_object',  modules?.objectDetection   ?? true)
      form.append('use_nsfw',    modules?.nsfwDetection     ?? true)
      form.append('use_scene',   modules?.sceneClassification ?? true)
      form.append('use_motion',  modules?.motionAnalysis    ?? true)
      form.append('use_action',  modules?.actionRecognition ?? true)
      form.append('use_anomaly', modules?.anomalyDetection  ?? true)
      form.append('mask_faces',  modules?.blurFaces         ?? true)

      const res = await fetch(`${API}/analyse`, { method: 'POST', body: form })
      if (!res.ok) {
        const err = await res.json()
        throw new Error(err.detail ?? `Server error ${res.status}`)
      }

      const data = await res.json()
      stepIntervals.forEach(clearTimeout)
      setStepIdx(LOADING_STEPS.length - 1)
      await new Promise(r => setTimeout(r, 400))
      setDone(true)
      onResult(data)
    } catch (err) {
      stepIntervals.forEach(clearTimeout)
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  // Fallback: demo mode when API is not running
  const runDemo = async () => {
    setLoading(true); setError(null)
    for (let i = 0; i < LOADING_STEPS.length; i++) {
      setStepIdx(i)
      await new Promise(r => setTimeout(r, 600))
    }
    const { dummyResult } = await import('../data/dummyData.js')
    setLoading(false); setDone(true)
    onResult(dummyResult)
  }

  const canAnalyze = (mode === 'file' && file) || (mode === 'url' && url.trim())

  return (
    <div className="space-y-4">
      {/* Mode Toggle */}
      <div className="flex gap-2">
        {[{ key:'file', label:'📁 Upload File' }, { key:'url', label:'🔗 YouTube URL' }].map(m => (
          <button key={m.key} onClick={() => setMode(m.key)}
            className={`px-4 py-2 rounded-xl text-sm font-medium transition-all border ${
              mode === m.key ? 'text-white border-transparent' : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50'
            }`}
            style={mode === m.key ? {backgroundColor: '#4285F4', borderColor: '#4285F4'} : {}}>
            {m.label}
          </button>
        ))}
      </div>

      <AnimatePresence mode="wait">
        {mode === 'file' ? (
          <motion.div key="file" initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -8 }}
            onDragOver={e => { e.preventDefault(); setDragging(true) }}
            onDragLeave={() => setDragging(false)}
            onDrop={onDrop}
            onClick={() => document.getElementById('video-input').click()}
            className={`border-2 border-dashed rounded-2xl p-10 text-center cursor-pointer transition-all duration-200 ${
              dragging ? 'bg-blue-50' : file ? 'border-emerald-300 bg-emerald-50' : 'border-slate-200 bg-slate-50'
            }`}
            style={dragging ? {borderColor: '#4285F4'} : (!file ? {borderColor: undefined} : undefined)}
            onMouseEnter={e => { if (!dragging && !file) { e.currentTarget.style.borderColor='#4285F4'; e.currentTarget.style.backgroundColor='rgba(66,133,244,0.03)' } }}
            onMouseLeave={e => { if (!dragging && !file) { e.currentTarget.style.borderColor=''; e.currentTarget.style.backgroundColor='' } }}>
            <input id="video-input" type="file" accept="video/*" className="hidden" onChange={e => handleFile(e.target.files[0])} />
            <div className="flex flex-col items-center gap-3">
              {file ? (
                <>
                  <div className="w-12 h-12 rounded-xl bg-emerald-100 flex items-center justify-center">
                    <CheckCircle size={24} className="text-emerald-600" />
                  </div>
                  <div>
                    <p className="font-semibold text-emerald-700">{file.name}</p>
                    <p className="text-xs text-emerald-500 mt-0.5">{(file.size / (1024*1024)).toFixed(1)} MB — Ready</p>
                  </div>
                </>
              ) : (
                <>
                  <div className="w-12 h-12 rounded-xl bg-slate-100 flex items-center justify-center">
                    <Upload size={22} className="text-slate-400" />
                  </div>
                  <div>
                    <p className="font-semibold text-slate-700">Drag & drop your video here</p>
                    <p className="text-xs text-slate-400 mt-0.5">MP4, MOV, AVI, MKV — up to 500 MB</p>
                  </div>
                  <span className="px-3 py-1.5 text-xs font-medium border rounded-lg" style={{color: '#4285F4', backgroundColor: '#e8f0fe', borderColor: '#c5d9fb'}}>Browse file</span>
                </>
              )}
            </div>
          </motion.div>
        ) : (
          <motion.div key="url" initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -8 }} className="space-y-3">
            <div className="flex items-center gap-2 px-4 py-3 bg-white border border-slate-200 rounded-xl transition-all" style={{}} onFocus={e=>e.currentTarget.style.borderColor='#4285F4'} onBlur={e=>e.currentTarget.style.borderColor='#e2e8f0'}>
              <Link size={15} className="text-slate-400 shrink-0" />
              <input type="url" value={url} onChange={e => { setUrl(e.target.value); setError(null) }}
                placeholder="https://www.youtube.com/watch?v=…"
                className="flex-1 text-sm text-slate-700 bg-transparent outline-none placeholder-slate-400" />
            </div>
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-slate-600 pl-1">Cookie Source (for age-restricted videos)</label>
              <select value={cookiesBrowser} onChange={e => setCookiesBrowser(e.target.value)}
                className="w-full px-3 py-2 text-sm bg-white border border-slate-200 rounded-lg text-slate-700 outline-none transition-all hover:border-slate-300 focus:border-blue-400">
                <option value="">None (default)</option>
                <option value="chrome">Chrome</option>
                <option value="firefox">Firefox</option>
                <option value="edge">Edge</option>
                <option value="safari">Safari</option>
              </select>
              <p className="text-xs text-slate-400 pl-1">Select your browser if you're logged into YouTube to bypass age restrictions</p>
            </div>
            <p className="text-xs text-slate-400 pl-1">Supports YouTube, Instagram, TikTok, X/Twitter</p>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Error */}
      <AnimatePresence>
        {error && (
          <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} exit={{ opacity: 0, height: 0 }}
            className="flex items-start gap-2 p-3 bg-red-50 border border-red-100 rounded-xl text-xs text-red-700">
            <AlertCircle size={14} className="shrink-0 mt-0.5" />
            <div>
              <p className="font-semibold">Analysis failed</p>
              <p className="whitespace-pre-wrap">{error}</p>
              {error.includes('Sign in') || error.includes('age') ? (
                <p className="mt-2 text-xs">💡 Try selecting your browser in the Cookie Source dropdown above</p>
              ) : (
                <button onClick={runDemo} className="mt-1.5 underline font-medium">Run demo with sample data →</button>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Loading steps */}
      <AnimatePresence>
        {loading && (
          <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} exit={{ opacity: 0, height: 0 }}
            className="card p-5 overflow-hidden">
            <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">Analysis Progress</p>
            <div className="space-y-2">
              {LOADING_STEPS.map((step, i) => (
                <motion.div key={step} initial={{ opacity: 0, x: -10 }} animate={{ opacity: i <= stepIdx ? 1 : 0.3, x: 0 }}
                  transition={{ delay: i * 0.05 }} className="flex items-center gap-2.5">
                  {i < stepIdx
                    ? <CheckCircle size={14} className="text-emerald-500 shrink-0" />
                    : i === stepIdx
                    ? <Loader2 size={14} className="animate-spin shrink-0" style={{color: '#4285F4'}} />
                      : <div className="w-3.5 h-3.5 rounded-full border-2 border-slate-200 shrink-0" />}
                  <span className={`text-sm ${i <= stepIdx ? 'text-slate-700 font-medium' : 'text-slate-400'}`}>{step}</span>
                </motion.div>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Buttons */}
      <div className="flex gap-2">
        <motion.button
          onClick={runAnalysis}
          disabled={!canAnalyze || loading}
          whileTap={{ scale: 0.97 }}
          className="flex-1 btn-primary h-12 text-base disabled:opacity-50 disabled:cursor-not-allowed">
          {loading ? <><Loader2 size={18} className="animate-spin" /> Analysing…</>
            : done  ? <><CheckCircle size={18} /> Re-run Analysis</>
                    : <><Play size={18} /> Start Analysis</>}
        </motion.button>

        <motion.button onClick={runDemo} disabled={loading} whileTap={{ scale: 0.97 }}
          className="px-4 h-12 text-sm font-medium border border-slate-200 rounded-xl text-slate-600 hover:bg-slate-50 disabled:opacity-50 transition-colors">
          Demo
        </motion.button>
      </div>
    </div>
  )
}
