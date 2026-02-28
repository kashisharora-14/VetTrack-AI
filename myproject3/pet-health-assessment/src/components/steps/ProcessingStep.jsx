import { motion } from 'framer-motion'
import { Brain } from 'lucide-react'

const ProcessingStep = ({ progress, status }) => {
  return (
    <div className="assessment-card text-center">
      <h2 className="text-2xl font-extrabold tracking-tight">Step 3: AI Processing</h2>
      <p className="mt-1 text-sm text-slate-500">Analyzing image, behavior, and symptom context.</p>

      <div className="relative mx-auto mt-12 h-60 w-60">
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 12, repeat: Infinity, ease: 'linear' }}
          className="absolute inset-0 rounded-full border border-dashed border-slate-300"
        />
        {[0, 90, 180, 270].map((deg) => (
          <motion.span
            key={deg}
            animate={{ rotate: [deg, deg + 360] }}
            transition={{ duration: 8, repeat: Infinity, ease: 'linear' }}
            className="absolute left-1/2 top-1/2 h-3 w-3 rounded-full bg-brand-400"
            style={{ transformOrigin: '0 85px' }}
          />
        ))}
        <motion.div
          animate={{ scale: [1, 1.08, 1] }}
          transition={{ duration: 2, repeat: Infinity }}
          className="absolute inset-0 m-auto grid h-24 w-24 place-items-center rounded-3xl bg-brand-50 text-brand-600 shadow"
        >
          <Brain size={42} />
        </motion.div>
      </div>

      <p className="mt-8 text-sm font-semibold text-slate-700">{status}</p>
      <div className="mx-auto mt-4 h-3 max-w-xl rounded-full bg-slate-100">
        <div className="h-3 rounded-full bg-brand-600 transition-all duration-300" style={{ width: `${progress}%` }} />
      </div>
      <p className="mt-2 text-xs text-slate-500">{progress}% complete</p>
    </div>
  )
}

export default ProcessingStep
