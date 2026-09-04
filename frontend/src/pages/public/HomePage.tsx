import { Link } from 'react-router-dom'
import { ArrowRight, Brain, HeartHandshake, LockKeyhole, Scan, ShieldCheck, Sparkles } from 'lucide-react'

const highlights = [
  { icon: Brain, title: 'AI-Powered Analysis', text: 'Research models analyze MRI patterns for transparent, repeatable insights.' },
  { icon: Scan, title: 'Comprehensive Assessment', text: 'Prediction, probability scores, and explainability in one workspace.' },
  { icon: ShieldCheck, title: 'Secure & Confidential', text: 'Your research records are protected inside your authenticated workspace.' },
  { icon: HeartHandshake, title: 'Better Care Support', text: 'Connect patients, doctors, and evidence for the next conversation.' },
]

export default function HomePage() {
  return (
    <div className="home-shell overflow-hidden bg-[#030617] text-white">
      <section className="relative min-h-[690px] border-b border-white/10">
        <div className="home-grid absolute inset-0 opacity-60" />
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_74%_43%,rgba(109,48,255,.22),transparent_25%),radial-gradient(circle_at_10%_80%,rgba(24,82,213,.18),transparent_28%)]" />
        <div className="relative mx-auto grid max-w-7xl items-center gap-10 px-6 pb-16 pt-20 lg:grid-cols-[.92fr_1.08fr] lg:px-10 lg:pt-24">
          <div className="relative z-10 max-w-xl animate-home-rise">
            <div className="inline-flex items-center gap-2 rounded-full border border-violet-400/25 bg-violet-400/10 px-4 py-2 text-sm text-violet-200"><Sparkles className="h-4 w-4 text-violet-300" />AI-Powered Healthcare</div>
            <h1 className="mt-7 text-5xl font-semibold leading-[1.02] tracking-tight sm:text-6xl lg:text-[72px]">Alzheimer<br /><span className="home-gradient-text">Disease Detection</span></h1>
            <p className="mt-7 max-w-lg text-base leading-7 text-slate-300 sm:text-lg">Advanced AI technology to support Alzheimer&apos;s disease research with early insights, explainable results, and a better tomorrow.</p>
            <div className="mt-9 flex flex-wrap gap-4"><Link to="/signup" className="inline-flex items-center gap-3 rounded-xl bg-gradient-to-r from-fuchsia-600 to-violet-600 px-6 py-3.5 text-sm font-semibold shadow-[0_0_30px_rgba(126,67,255,.35)] transition-transform hover:-translate-y-0.5">Start MRI Analysis <ArrowRight className="h-4 w-4" /></Link><Link to="/platform" className="inline-flex items-center gap-3 rounded-xl border border-violet-400/50 px-6 py-3.5 text-sm font-semibold text-violet-100 transition-colors hover:bg-violet-400/10">Learn More</Link></div>
          </div>
          <div className="relative flex min-h-[390px] items-center justify-center lg:min-h-[490px]">
            <div className="home-orbit absolute h-[360px] w-[360px] rounded-full border border-violet-400/40 sm:h-[490px] sm:w-[490px]" /><div className="home-orbit home-orbit-delay absolute h-[290px] w-[290px] rounded-full border border-cyan-300/30 sm:h-[395px] sm:w-[395px]" /><div className="absolute h-64 w-64 rounded-full bg-violet-600/30 blur-3xl sm:h-80 sm:w-80" /><Brain className="relative z-10 h-64 w-64 stroke-[.65] text-violet-200 drop-shadow-[0_0_18px_#9b5cff] sm:h-80 sm:w-80 lg:h-[390px] lg:w-[390px]" />
            <div className="absolute left-0 top-8 z-20 w-44 rounded-xl border border-violet-400/35 bg-[#0b1230]/90 p-4 shadow-[0_0_25px_rgba(100,70,255,.2)] backdrop-blur sm:left-4 sm:w-52"><p className="text-sm font-semibold">Early Detection</p><p className="mt-2 text-xs leading-5 text-slate-300">Identify patterns at the earliest possible stage with AI support.</p></div>
            <div className="absolute right-0 top-3 z-20 w-40 rounded-xl border border-violet-400/35 bg-[#0b1230]/90 p-4 backdrop-blur sm:right-2 sm:w-48"><p className="text-sm font-semibold">High Accuracy</p><p className="mt-2 text-3xl font-bold text-violet-300">98.6%</p><p className="text-xs text-slate-300">Research benchmark</p></div>
            <div className="absolute bottom-4 left-4 z-20 w-44 rounded-xl border border-violet-400/35 bg-[#0b1230]/90 p-4 backdrop-blur sm:left-8 sm:w-52"><p className="text-sm font-semibold">Risk Assessment</p><p className="mt-2 text-xs leading-5 text-slate-300">Review model probabilities and confidence in context.</p></div>
            <div className="absolute bottom-0 right-0 z-20 w-40 rounded-xl border border-violet-400/35 bg-[#0b1230]/90 p-4 backdrop-blur sm:right-2 sm:w-48"><p className="text-sm font-semibold">Secure & Private</p><p className="mt-2 text-xs leading-5 text-slate-300">Authenticated research records stay protected.</p></div>
          </div>
        </div>
      </section>
      <section className="relative mx-auto -mt-1 max-w-6xl px-6 pb-16 lg:px-10"><div className="grid gap-0 rounded-2xl border border-violet-300/20 bg-[#0b1230]/90 p-6 shadow-[0_0_45px_rgba(49,35,145,.2)] backdrop-blur md:grid-cols-2 lg:grid-cols-4 lg:p-7">{highlights.map(({ icon: Icon, title, text }, index) => <div key={title} className={`flex gap-4 px-3 py-4 lg:px-5 ${index < highlights.length - 1 ? 'lg:border-r lg:border-white/10' : ''}`}><Icon className="mt-1 h-9 w-9 shrink-0 text-violet-300 drop-shadow-[0_0_9px_#8b5cf6]" /><div><h2 className="text-sm font-semibold">{title}</h2><p className="mt-2 text-xs leading-5 text-slate-300">{text}</p></div></div>)}</div></section>
      <section className="mx-auto max-w-6xl px-6 pb-20 lg:px-10"><div className="grid gap-10 md:grid-cols-3"><div><p className="text-sm font-medium text-violet-300">01 / Understand</p><h2 className="mt-3 text-2xl font-semibold">A clearer research workflow</h2></div><p className="text-sm leading-7 text-slate-400">Upload a valid MRI image, run the real model, inspect probabilities, and use Grad-CAM explanations to understand what the system sees.</p><div className="flex items-start gap-3 text-sm text-slate-300"><LockKeyhole className="h-5 w-5 text-violet-300" />Research and education only. Never a confirmed medical diagnosis.</div></div></section>
    </div>
  )
}
