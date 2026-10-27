import { useEffect, useState, useCallback } from 'react'
import { CalendarDays, Check, Clock3, X, RefreshCw } from 'lucide-react'
import { useAuth } from '@/context/useAuth'
import { portalApi } from '@/services/api'

type Appointment = { id: string; appointment_at: string; reason: string; status: string; patient_name?: string; doctor_name?: string }

const statusStyles: Record<string, string> = {
  pending: 'bg-amber-500/10 text-amber-700 dark:text-amber-300',
  approved: 'bg-emerald-500/10 text-emerald-700 dark:text-emerald-300',
  rejected: 'bg-destructive/10 text-destructive',
  completed: 'bg-primary/10 text-primary',
  cancelled: 'bg-secondary text-muted-foreground',
}

function AppointmentSkeleton() {
  return <div className="space-y-3" aria-label="Loading appointments">{[1, 2].map(item => <div key={item} className="rounded-xl border border-border/40 bg-card p-5"><div className="portal-skeleton h-4 w-40" /><div className="portal-skeleton mt-3 h-3 w-56" /><div className="portal-skeleton mt-5 h-3 w-full" /></div>)}</div>
}

export default function AppointmentsPage() {
  const { user } = useAuth()
  const [items, setItems] = useState<Appointment[]>([])
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)
  const [updating, setUpdating] = useState('')

  const load = useCallback(async () => {
    setLoading(true)
    setError('')
    try { setItems(user?.role === 'doctor' ? await portalApi.doctorAppointments() : await portalApi.myAppointments()) }
    catch (e) { setError(e instanceof Error ? e.message : 'We could not load appointments. Please try again.') }
    finally { setLoading(false) }
  }, [user?.role])

  useEffect(() => { load() }, [load])

  const update = async (id: string, status: string) => {
    setUpdating(id)
    setError('')
    try { await portalApi.updateAppointment(id, status); await load() }
    catch (e) { setError(e instanceof Error ? e.message : 'We could not update this appointment. Please try again.') }
    finally { setUpdating('') }
  }

  return <div className="portal-page animate-fade-in space-y-6">
    <header className="flex flex-wrap items-end justify-between gap-4">
      <div><p className="text-sm font-medium text-primary">Care coordination</p><h1 className="mt-1 text-2xl font-bold tracking-tight">{user?.role === 'doctor' ? 'Appointment management' : 'My appointments'}</h1><p className="mt-2 max-w-2xl text-sm text-muted-foreground">Keep track of upcoming visits, requests, and care-team decisions in one place.</p></div>
      <button aria-label="Refresh appointments" onClick={load} disabled={loading} className="flex items-center gap-2 rounded-lg border border-border/60 px-3 py-2 text-sm font-medium transition-colors hover:bg-secondary disabled:opacity-50"><RefreshCw className={loading ? 'h-4 w-4 animate-spin' : 'h-4 w-4'} />Refresh</button>
    </header>
    {error && <div role="alert" className="flex items-start gap-3 rounded-lg border border-destructive/30 bg-destructive/5 px-4 py-3 text-sm text-destructive"><X className="mt-0.5 h-4 w-4 shrink-0" /><span>{error}</span></div>}
    {loading ? <AppointmentSkeleton /> : items.length === 0 ? <div className="rounded-xl border border-dashed border-border/70 bg-card p-12 text-center"><CalendarDays className="mx-auto h-10 w-10 text-muted-foreground/60" /><h2 className="mt-4 font-semibold">No appointments yet</h2><p className="mx-auto mt-2 max-w-sm text-sm text-muted-foreground">{user?.role === 'doctor' ? 'New patient requests will appear here.' : 'Find a doctor to request your first consultation.'}</p></div> : <div className="space-y-3">{items.map(item => <article key={item.id} className="rounded-xl border border-border/50 bg-card p-5 shadow-sm transition-shadow hover:shadow-md"><div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between"><div><p className="font-semibold">{user?.role === 'doctor' ? item.patient_name : `Dr. ${item.doctor_name}`}</p><p className="mt-2 flex items-center gap-2 text-sm text-muted-foreground"><Clock3 className="h-4 w-4" />{new Date(item.appointment_at).toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' })}</p></div><span className={`w-fit rounded-full px-3 py-1 text-xs font-semibold capitalize ${statusStyles[item.status] || statusStyles.cancelled}`}>{item.status}</span></div>{item.reason && <p className="mt-4 border-t border-border/40 pt-4 text-sm text-muted-foreground"><span className="font-medium text-foreground">Reason:</span> {item.reason}</p>}{user?.role === 'doctor' && item.status === 'pending' && <div className="mt-4 flex flex-wrap gap-2 border-t border-border/40 pt-4"><button onClick={() => update(item.id, 'approved')} disabled={updating === item.id} className="flex items-center gap-2 rounded-lg bg-primary px-3 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"><Check className="h-4 w-4" />Approve</button><button onClick={() => update(item.id, 'rejected')} disabled={updating === item.id} className="flex items-center gap-2 rounded-lg border border-border/60 px-3 py-2 text-sm font-medium hover:bg-secondary disabled:opacity-50"><X className="h-4 w-4" />Reject</button></div>}</article>)}</div>}
  </div>
}
