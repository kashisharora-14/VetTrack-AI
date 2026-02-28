import { useEffect, useMemo, useState } from 'react'
import { motion } from 'framer-motion'
import Navbar from './components/Navbar'
import AnimalFoodPlanManager from './components/AnimalFoodPlanManager'
import VisualAssessmentStep from './components/steps/VisualAssessmentStep'
import BehaviorAssessmentStep from './components/steps/BehaviorAssessmentStep'
import ProcessingStep from './components/steps/ProcessingStep'
import ResultsStep from './components/steps/ResultsStep'
import { statusMessages } from './data/mockData'

const buildResult = (metrics, selectedObservations) => {
  const riskRaw = (10 - metrics.energy) * 3 + (10 - metrics.appetite) * 3 + (10 - metrics.mood) * 2 + selectedObservations.length * 2
  const score = Math.max(8, Math.min(96, Math.round(riskRaw)))
  const level = score < 34 ? 'low' : score < 67 ? 'moderate' : 'high'

  return {
    score,
    level,
    summary:
      level === 'high'
        ? 'The model flags a high-risk cluster based on low vitality signals and symptom intensity. Prompt veterinary evaluation is recommended.'
        : level === 'moderate'
          ? 'The model indicates moderate concern with mixed behavior changes. Monitor closely and consult a veterinarian if symptoms persist.'
          : 'The model indicates low immediate risk. Continue watchful care and maintain hydration, appetite monitoring, and routine observation.',
    observations: selectedObservations.length
      ? selectedObservations.slice(0, 4)
      : ['Image quality acceptable for analysis', 'No extreme emergency signature detected', 'Behavior baseline partly stable'],
    actions: [
      'Track hydration and appetite every 6-8 hours',
      'Recheck symptoms after rest and hydration support',
      'Schedule vet follow-up if no improvement in 24 hours',
    ],
    vets: [
      { name: 'CityCare Veterinary Clinic', distance: '1.8 km', availability: 'Open now' },
      { name: 'Paws & Whiskers Animal Hospital', distance: '3.1 km', availability: 'Available in 30 mins' },
      { name: 'Greenfield Pet Emergency', distance: '4.2 km', availability: '24/7 emergency' },
    ],
  }
}

const App = () => {
  const [step, setStep] = useState(1)
  const [imageFile, setImageFile] = useState(null)
  const [metrics, setMetrics] = useState({ energy: 6, appetite: 6, mood: 6 })
  const [observations, setObservations] = useState([])
  const [progress, setProgress] = useState(0)
  const [statusIndex, setStatusIndex] = useState(0)

  const result = useMemo(() => buildResult(metrics, observations), [metrics, observations])

  useEffect(() => {
    if (step !== 3) return

    setProgress(0)
    setStatusIndex(0)

    const statusTimer = setInterval(() => {
      setStatusIndex((prev) => (prev + 1) % statusMessages.length)
    }, 2000)

    const progressTimer = setInterval(() => {
      setProgress((prev) => {
        const next = Math.min(prev + 5, 100)
        if (next >= 100) {
          clearInterval(progressTimer)
          setTimeout(() => setStep(4), 450)
        }
        return next
      })
    }, 220)

    return () => {
      clearInterval(statusTimer)
      clearInterval(progressTimer)
    }
  }, [step])

  const resetAll = () => {
    setStep(1)
    setImageFile(null)
    setMetrics({ energy: 6, appetite: 6, mood: 6 })
    setObservations([])
    setProgress(0)
    setStatusIndex(0)
  }

  return (
    <div className="min-h-screen">
      <Navbar />

      <main className="mx-auto max-w-6xl px-4 py-8 md:px-6">
        <AnimalFoodPlanManager />

        <motion.section
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.35 }}
        >
          {step === 1 && (
            <VisualAssessmentStep
              imageFile={imageFile}
              onImageChange={setImageFile}
              onNext={() => setStep(2)}
            />
          )}

          {step === 2 && (
            <BehaviorAssessmentStep
              values={metrics}
              setValues={setMetrics}
              observations={observations}
              setObservations={setObservations}
              onBack={() => setStep(1)}
              onNext={() => setStep(3)}
            />
          )}

          {step === 3 && <ProcessingStep progress={progress} status={statusMessages[statusIndex]} />}

          {step === 4 && <ResultsStep result={result} onRestart={resetAll} />}
        </motion.section>
      </main>
    </div>
  )
}

export default App
