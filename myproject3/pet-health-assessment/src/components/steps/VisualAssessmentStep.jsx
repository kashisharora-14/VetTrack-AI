import { useMemo } from 'react'
import { motion } from 'framer-motion'
import { UploadCloud, Lightbulb, Image as ImageIcon } from 'lucide-react'

const tips = [
  'Use good natural or bright indoor lighting',
  'Keep the camera focused on the affected area',
  'Frame the full area with minimal blur',
]

const VisualAssessmentStep = ({ imageFile, onImageChange, onNext }) => {
  const preview = useMemo(() => (imageFile ? URL.createObjectURL(imageFile) : null), [imageFile])

  const handleDrop = (e) => {
    e.preventDefault()
    const file = e.dataTransfer.files?.[0]
    if (file && file.type.startsWith('image/')) onImageChange(file)
  }

  return (
    <div className="assessment-card">
      <h2 className="text-2xl font-extrabold tracking-tight">Step 1: Visual Assessment</h2>
      <p className="mt-1 text-sm text-slate-500">Upload a clear photo to improve symptom understanding.</p>

      <motion.label
        whileHover={{ scale: 1.01 }}
        onDragOver={(e) => e.preventDefault()}
        onDrop={handleDrop}
        className="mt-6 flex min-h-56 cursor-pointer flex-col items-center justify-center rounded-2xl border-2 border-dashed border-slate-300 bg-slate-50 p-6 text-center"
      >
        {preview ? (
          <img src={preview} alt="preview" className="h-48 w-full rounded-xl object-cover" />
        ) : (
          <>
            <UploadCloud className="mb-3 text-slate-500" size={34} />
            <p className="font-semibold text-slate-700">Drag & drop or click to upload</p>
            <p className="mt-1 text-sm text-slate-500">PNG, JPG, WEBP</p>
          </>
        )}
        <input
          type="file"
          accept="image/*"
          className="hidden"
          onChange={(e) => onImageChange(e.target.files?.[0] || null)}
        />
      </motion.label>

      <div className="mt-6 rounded-2xl border border-slate-200 bg-white p-4">
        <p className="mb-3 flex items-center gap-2 text-sm font-semibold text-slate-700">
          <Lightbulb size={16} className="text-amber-500" /> Tips for better analysis
        </p>
        <ul className="space-y-2 text-sm text-slate-600">
          {tips.map((tip) => (
            <li key={tip} className="flex items-start gap-2">
              <ImageIcon size={14} className="mt-0.5 text-brand-500" /> {tip}
            </li>
          ))}
        </ul>
      </div>

      <div className="mt-6 flex justify-end">
        <button
          onClick={onNext}
          disabled={!imageFile}
          className="rounded-xl bg-brand-600 px-5 py-3 text-sm font-semibold text-white transition hover:bg-brand-500 disabled:cursor-not-allowed disabled:bg-slate-300"
        >
          Analyze & Continue
        </button>
      </div>
    </div>
  )
}

export default VisualAssessmentStep
