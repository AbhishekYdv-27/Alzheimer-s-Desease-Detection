import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { portalApi } from '@/services/api'

type Appointment = { id: string; appointment_at: string; patient_name?: string; status: string }
export default function DoctorDashboardPage() {
  const [appointments, setAppointments] = useState<Appointment[]>([])
  useEffect(() => { portalApi.doctorAppointments().then(setAppointments).catch(() => setAppointments([])) }, [])
  const pending = appointments.filter(item => item.status === 'pending').length
  return <div className="space-y-6"><div><h1 className="text-2xl font-bold">Doctor Dashboard</h1><p className="mt-1 text-muted-foreground">Manage patient relationships, appointment requests, and research analyses.</p></div><div className="grid gap-4 md:grid-cols-3"><div className="rounded-xl border border-border/40 bg-card p-5"><p className="text-sm text-muted-foreground">Pending requests</p><p className="mt-2 text-3xl font-bold text-primary">{pending}</p></div><div className="rounded-xl border border-border/40 bg-card p-5"><p className="text-sm text-muted-foreground">Appointments</p><p className="mt-2 text-3xl font-bold">{appointments.length}</p></div><div className="rounded-xl border border-border/40 bg-card p-5"><p className="text-sm text-muted-foreground">Portal role</p><p className="mt-2 text-xl font-semibold">Doctor</p></div></div><div className="rounded-xl border border-border/40 bg-card p-6"><h2 className="font-semibold">Next steps</h2><div className="mt-4 flex flex-wrap gap-3"><Link to="/doctor/profile" className="rounded-lg bg-primary px-4 py-2 text-sm text-primary-foreground">Complete doctor profile</Link><Link to="/doctor/appointments" className="rounded-lg border border-border px-4 py-2 text-sm">Review appointments</Link><Link to="/doctor/patients" className="rounded-lg border border-border px-4 py-2 text-sm">View patients</Link></div></div></div>
}
