import { symptomObservations } from '../../data/mockData'

const insightFromMetrics = ({ energy, appetite, mood }) => {
  const riskBase = (10 - energy) + (10 - appetite) + (10 - mood)
  if (riskBase >= 20) return 'AI context: Significant behavioral decline detected. Prioritize same-day veterinary review.'
  if (riskBase >= 13) return 'AI context: Moderate concern pattern. Monitor closely and consider a vet consultation within 24 hours.'
  return 'AI context: Mild behavioral changes. Continue monitoring with hydration and routine checks.'
}

const BehaviorAssessmentStep = ({ values, setValues, observations, setObservations, onBack, onNext }) => {
  const toggleObservation = (item) => {
    setObservations((prev) =>
      prev.includes(item) ? prev.filter((x) => x !== item) : [...prev, item]
    )
  }

  return (
    <div className="grid gap-6 lg:grid-cols-3">
      <div className="assessment-card lg:col-span-2">
        <h2 className="text-2xl font-extrabold tracking-tight">Step 2: Behavior Assessment</h2>
        <p className="mt-1 text-sm text-slate-500">Capture subtle behavior shifts for higher diagnostic confidence.</p>

        <div className="mt-6 space-y-5">
          {[
            { label: 'Energy Level', key: 'energy' },
            { label: 'Appetite & Thirst', key: 'appetite' },
            { label: 'Mood & Sociability', key: 'mood' },
          ].map((s) => (
            <div key={s.key}>
              <div className="mb-2 flex items-center justify-between text-sm font-semibold text-slate-700">
                <span>{s.label}</span>
                <span className="rounded-full bg-slate-100 px-3 py-1 text-xs text-slate-600">{values[s.key]}/10</span>
              </div>
              <input
                type="range"
                min="1"
                max="10"
                value={values[s.key]}
                onChange={(e) => setValues((v) => ({ ...v, [s.key]: Number(e.target.value) }))}
                className="w-full accent-blue-600"
              />
            </div>
          ))}
        </div>

        <div className="mt-6">
          <h3 className="text-sm font-semibold text-slate-700">Additional Observations</h3>
          <div className="mt-3 grid gap-2 sm:grid-cols-2">
            {symptomObservations.map((item) => (
              <label key={item} className="flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-600">
                <input
                  type="checkbox"
                  checked={observations.includes(item)}
                  onChange={() => toggleObservation(item)}
                  className="accent-blue-600"
                />
                {item}
              </label>
            ))}
          </div>
        </div>

        <div className="mt-8 flex justify-between">
          <button onClick={onBack} className="rounded-xl border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-600 hover:bg-slate-100">Back</button>
          <button onClick={onNext} className="rounded-xl bg-brand-600 px-5 py-3 text-sm font-semibold text-white hover:bg-brand-500">Continue</button>
        </div>
      </div>

      <aside className="assessment-card h-fit">
        <h3 className="text-sm font-bold uppercase tracking-wide text-slate-500">AI Context</h3>
        <p className="mt-3 text-sm text-slate-700">{insightFromMetrics(values)}</p>
      </aside>
    </div>
  )
}

export default BehaviorAssessmentStep
