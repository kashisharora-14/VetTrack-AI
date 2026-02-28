import { Download, Save, Share2, Stethoscope } from 'lucide-react'

const riskLevelStyle = {
  low: 'bg-emerald-50 text-emerald-700 border-emerald-200',
  moderate: 'bg-amber-50 text-amber-700 border-amber-200',
  high: 'bg-rose-50 text-rose-700 border-rose-200',
}

const CircularScore = ({ score }) => {
  const r = 54
  const c = 2 * Math.PI * r
  const offset = c - (score / 100) * c

  return (
    <div className="relative grid h-40 w-40 place-items-center">
      <svg width="140" height="140" className="-rotate-90">
        <circle cx="70" cy="70" r={r} stroke="#e2e8f0" strokeWidth="10" fill="none" />
        <circle
          cx="70"
          cy="70"
          r={r}
          stroke="#2563eb"
          strokeWidth="10"
          fill="none"
          strokeDasharray={c}
          strokeDashoffset={offset}
          strokeLinecap="round"
        />
      </svg>
      <div className="absolute text-center">
        <p className="text-3xl font-extrabold">{score}</p>
        <p className="text-xs text-slate-500">Risk Score</p>
      </div>
    </div>
  )
}

const ResultsStep = ({ result, onRestart }) => {
  return (
    <div className="space-y-6">
      <div className="assessment-card">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <h2 className="text-2xl font-extrabold tracking-tight">Step 4: Diagnostic Results</h2>
            <p className="mt-1 text-sm text-slate-500">AI-powered summary for owner decision support.</p>
          </div>
          <button onClick={onRestart} className="rounded-xl border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-600 hover:bg-slate-100">Start New Assessment</button>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="assessment-card flex flex-col items-center justify-center lg:col-span-1">
          <CircularScore score={result.score} />
          <span className={`mt-4 rounded-full border px-3 py-1 text-xs font-semibold ${riskLevelStyle[result.level]}`}>{result.level.toUpperCase()} RISK</span>
        </div>

        <div className="assessment-card lg:col-span-2">
          <h3 className="text-lg font-bold">AI Summary</h3>
          <p className="mt-2 text-sm text-slate-600">{result.summary}</p>

          <div className="mt-5 grid gap-4 sm:grid-cols-2">
            <section className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
              <h4 className="text-sm font-bold text-slate-800">Key Observations</h4>
              <ul className="mt-2 space-y-1 text-sm text-slate-600">
                {result.observations.map((item) => (
                  <li key={item}>- {item}</li>
                ))}
              </ul>
            </section>
            <section className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
              <h4 className="text-sm font-bold text-slate-800">Recommended Actions</h4>
              <ul className="mt-2 space-y-1 text-sm text-slate-600">
                {result.actions.map((item) => (
                  <li key={item}>- {item}</li>
                ))}
              </ul>
            </section>
          </div>
        </div>
      </div>

      <div className="assessment-card">
        <h3 className="text-lg font-bold">Nearby Veterinarians</h3>
        <div className="mt-4 grid gap-3 md:grid-cols-3">
          {result.vets.map((vet) => (
            <article key={vet.name} className="rounded-xl border border-slate-200 bg-white p-4">
              <h4 className="font-semibold text-slate-800">{vet.name}</h4>
              <p className="mt-1 text-sm text-slate-500">{vet.distance}</p>
              <p className="text-sm text-slate-500">{vet.availability}</p>
            </article>
          ))}
        </div>
      </div>

      <div className="assessment-card">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex flex-wrap gap-2">
            <button className="chip"><Save size={16} /> Save</button>
            <button className="chip"><Share2 size={16} /> Share</button>
            <button className="chip"><Download size={16} /> Export</button>
          </div>
          <button className="inline-flex items-center gap-2 rounded-xl bg-brand-600 px-5 py-3 text-sm font-semibold text-white hover:bg-brand-500">
            <Stethoscope size={16} /> Consult Now
          </button>
        </div>
      </div>
    </div>
  )
}

export default ResultsStep
