import { useEffect, useState } from 'react'
import { portalApi } from '@/services/api'
import { Search, MapPin, Calendar, Clock, X } from 'lucide-react'

type Doctor = { id: string; name: string; specialization: string; qualifications: string; experience_years: number; clinic_name: string; city: string; state: string }
type Slot = { id: string; slot_at: string; duration_minutes: number; is_available: number }

export default function FindDoctorsPage() {
  const [doctors, setDoctors] = useState<Doctor[]>([])
  const [city, setCity] = useState('')
  const [specialization, setSpecialization] = useState('')
  const [selected, setSelected] = useState<Doctor | null>(null)
  const [date, setDate] = useState('')
  const [slots, setSlots] = useState<Slot[]>([])
  const [slotId, setSlotId] = useState('')
  const [reason, setReason] = useState('')
  const [message, setMessage] = useState('')
  const [loading, setLoading] = useState(true)

  const load = async () => { setLoading(true); try { setDoctors(await portalApi.doctors(city, specialization)) } catch (e) { setMessage(e instanceof Error ? e.message : 'Unable to load doctors') } finally { setLoading(false) } }
  useEffect(() => { load() }, [])
  const openBooking = async (doctor: Doctor) => { setSelected(doctor); setDate(''); setSlotId(''); setSlots([]); try { setSlots(await portalApi.availability(doctor.id)) } catch { setMessage('Unable to load availability') } }
  const selectDate = async (value: string) => { setDate(value); setSlotId(''); if (selected && value) setSlots(await portalApi.availability(selected.id, value)) }
  const book = async () => { const slot = slots.find(item => item.id === slotId); if (!selected || !slot) return; try { await portalApi.bookAppointment(selected.id, slot.slot_at, reason, slotId); setMessage('Appointment request submitted'); setSelected(null); setReason(''); setSlotId('') } catch (e) { setMessage(e instanceof Error ? e.message : 'Unable to book appointment') } }
  const dates = [...new Set(slots.filter(slot => slot.is_available).map(slot => slot.slot_at.slice(0, 10)))]

  return <div className="space-y-6"><div><h1 className="text-2xl font-bold">Find a Doctor</h1><p className="mt-1 text-muted-foreground">Choose a care professional and reserve an available time.</p></div><div className="flex flex-wrap gap-3"><input value={city} onChange={e => setCity(e.target.value)} placeholder="City" className="rounded-lg border border-border/40 bg-background px-4 py-2.5 text-sm" /><input value={specialization} onChange={e => setSpecialization(e.target.value)} placeholder="Specialization" className="rounded-lg border border-border/40 bg-background px-4 py-2.5 text-sm" /><button onClick={load} className="flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm text-primary-foreground"><Search className="h-4 w-4" />Search</button></div>{message && <p className="text-sm text-muted-foreground">{message}</p>}{loading ? <p>Loading doctors...</p> : doctors.length === 0 ? <div className="rounded-xl border border-border/40 bg-card p-10 text-center">No registered doctor profiles match your search.</div> : <div className="grid gap-4 md:grid-cols-2">{doctors.map(doctor => <div key={doctor.id} className="rounded-xl border border-border/40 bg-card p-5"><h2 className="font-semibold">{doctor.name}</h2><p className="mt-1 text-sm text-primary">{doctor.specialization || 'Specialization not provided'}</p><p className="mt-3 text-sm">{doctor.qualifications || 'Qualifications not provided'}</p><p className="mt-2 flex items-center gap-1 text-sm text-muted-foreground"><MapPin className="h-4 w-4" />{doctor.city || 'Location not provided'}{doctor.state && `, ${doctor.state}`}</p><p className="mt-1 text-sm text-muted-foreground">{doctor.experience_years} years experience · {doctor.clinic_name || 'Clinic not provided'}</p><button onClick={() => openBooking(doctor)} className="mt-4 flex items-center gap-2 rounded-lg bg-primary px-3 py-2 text-sm text-primary-foreground"><Calendar className="h-4 w-4" />View availability</button></div>)}</div>}
    {selected && <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4" role="presentation">
      <div role="dialog" aria-modal="true" aria-labelledby="booking-title" className="max-h-[90vh] w-full max-w-lg overflow-y-auto rounded-xl border border-border/40 bg-card p-6 shadow-xl">
        <div className="flex items-start justify-between gap-4"><div><h2 id="booking-title" className="text-lg font-semibold">Book with {selected.name}</h2><p className="text-sm text-muted-foreground">Select a date and an open time slot.</p></div><button aria-label="Close booking" onClick={() => setSelected(null)}><X className="h-5 w-5" /></button></div>
        {dates.length === 0 ? <p className="mt-6 rounded-lg bg-secondary p-4 text-sm text-muted-foreground">This doctor has not published any upcoming availability.</p> : <>
          <label className="mt-5 block text-sm font-medium">Available date<select aria-label="Available date" value={date} onChange={e => selectDate(e.target.value)} className="mt-1 w-full rounded-lg border border-border/40 bg-background px-3 py-2.5 text-sm"><option value="">Choose a date</option>{dates.map(item => <option key={item} value={item}>{new Date(`${item}T12:00`).toLocaleDateString(undefined, { weekday: 'long', month: 'short', day: 'numeric' })}</option>)}</select></label>
          {date && <div className="mt-4 grid grid-cols-2 gap-2">{slots.filter(slot => slot.is_available).map(slot => <button key={slot.id} onClick={() => setSlotId(slot.id)} aria-pressed={slotId === slot.id} className={`flex items-center justify-center gap-2 rounded-lg border px-3 py-2 text-sm ${slotId === slot.id ? 'border-primary bg-primary/10 text-primary' : 'border-border/40'}`}><Clock className="h-4 w-4" />{new Date(slot.slot_at).toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' })}</button>)}</div>}
          <textarea aria-label="Reason for visit" value={reason} onChange={e => setReason(e.target.value)} placeholder="Reason for visit (optional)" className="mt-4 min-h-20 w-full rounded-lg border border-border/40 bg-background px-3 py-2.5 text-sm" />
          <button disabled={!slotId} onClick={book} className="mt-4 w-full rounded-lg bg-primary px-4 py-2.5 text-sm text-primary-foreground disabled:opacity-50">Request appointment</button>
        </>}
      </div>
    </div>}
  </div>
}
