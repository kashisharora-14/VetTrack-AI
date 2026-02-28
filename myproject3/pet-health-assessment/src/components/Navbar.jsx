import { PawPrint, Bell, ShieldCheck, UserCircle } from 'lucide-react'

const Navbar = () => {
  return (
    <header className="sticky top-0 z-30 border-b border-slate-200 bg-white/95 backdrop-blur">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3 md:px-6">
        <div className="flex items-center gap-3">
          <span className="grid h-10 w-10 place-items-center rounded-xl bg-brand-50 text-brand-600">
            <PawPrint size={20} />
          </span>
          <div>
            <p className="text-lg font-extrabold tracking-tight text-slate-900">VetTrack AI</p>
            <p className="text-xs text-slate-500">AI-Powered Health Assessment</p>
          </div>
        </div>

        <nav className="hidden items-center gap-2 md:flex">
          <button className="chip"><ShieldCheck size={16} /> Assessment</button>
          <button className="chip"><Bell size={16} /> Alerts</button>
          <button className="chip"><UserCircle size={16} /> Profile</button>
        </nav>
      </div>
    </header>
  )
}

export default Navbar
