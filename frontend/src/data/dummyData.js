// Realistic dummy data matching the AdShield backend response structure
export const dummyResult = {
  overallRisk: 'VIOLATION',
  finalScore: 0.71,
  framesAnalyzed: 13,
  flaggedFrames: 4,
  summary: 'Analysis detected policy violations including firearm objects and high-risk scene context across 4 frames.',

  signals: {
    objectHit: true,
    nsfwHit: false,
    sceneHit: true,
    motionHit: true,
    actionHit: false,
    anomalyHit: true,
  },

  // X = seconds, Y = violation score 0–1
  timeline: [
    { time: 1,  score: 0.05, timestamp: '0:01' },
    { time: 2,  score: 0.08, timestamp: '0:02' },
    { time: 3,  score: 0.62, timestamp: '0:03' },
    { time: 4,  score: 0.78, timestamp: '0:04' },
    { time: 5,  score: 0.74, timestamp: '0:05' },
    { time: 6,  score: 0.19, timestamp: '0:06' },
    { time: 7,  score: 0.11, timestamp: '0:07' },
    { time: 8,  score: 0.07, timestamp: '0:08' },
    { time: 9,  score: 0.55, timestamp: '0:09' },
    { time: 10, score: 0.47, timestamp: '0:10' },
    { time: 11, score: 0.14, timestamp: '0:11' },
    { time: 12, score: 0.09, timestamp: '0:12' },
    { time: 13, score: 0.06, timestamp: '0:13' },
  ],

  flaggedSegments: [
    {
      start: '0:03',
      end: '0:05',
      duration: '2.0s',
      peakScore: 0.78,
      risk: 'HIGH RISK',
      reasons: 'CRITICAL object: handgun (67%) | Scene context: weapons & violence (71%)',
    },
    {
      start: '0:09',
      end: '0:10',
      duration: '1.0s',
      peakScore: 0.55,
      risk: 'VIOLATION',
      reasons: 'CRITICAL object: knife (52%) | High-motion anomaly (magnitude 8.3)',
    },
  ],

  frames: [
    {
      index: 2,
      timestamp: '0:03',
      finalScore: 0.62,
      riskLevel: 'VIOLATION',
      severity: 'critical',
      label: 'CRITICAL: handgun 67%',
      color: '#dc2626',
    },
    {
      index: 3,
      timestamp: '0:04',
      finalScore: 0.78,
      riskLevel: 'HIGH RISK',
      severity: 'critical',
      label: 'CRITICAL: handgun 71%',
      color: '#dc2626',
    },
    {
      index: 4,
      timestamp: '0:05',
      finalScore: 0.74,
      riskLevel: 'HIGH RISK',
      severity: 'critical',
      label: 'HIGH RISK: cigarette 42%',
      color: '#ea580c',
    },
    {
      index: 8,
      timestamp: '0:09',
      finalScore: 0.55,
      riskLevel: 'VIOLATION',
      severity: 'high_risk',
      label: 'CRITICAL: knife 52%',
      color: '#b91c1c',
    },
  ],
}

export const defaultModules = {
  objectDetection: true,
  nsfwDetection: true,
  sceneClassification: true,
  motionAnalysis: true,
  actionRecognition: true,
  anomalyDetection: true,
}

export const defaultSettings = {
  frameSampleRate: 1,
  violationThreshold: 0.45,
}
