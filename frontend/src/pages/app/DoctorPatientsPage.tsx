import { useEffect, useState } from 'react'
import { portalApi } from '@/services/api'

type Patient = { id: string; name: string; email: string }
export default function DoctorPatientsPage() {
  const [patients, setPatients] = useState<Patient[]>([])
  const [selected, setSelected] = useState('')
  const [content, setContent] = useState('')
  const [followUp, setFollowUp] = useState('')
  const [message, setMessage] = useState('')
  useEffect(() => { portalApi.doctorPatients().then(setPatients).catch(e => setMessage(e instanceof Error ? e.message : 'Unable to load patients')) }, [])
  const save = async () => { if (!selected || !content.trim()) return; try { await portalApi.createDoctorNote(selected, content, followUp); setMessage('Doctor note saved for the patient'); setContent(''); setFollowUp('') } catch (e) { setMessage(e instanceof Error ? e.message : 'Unable to save note') } }
  return <div className="space-y-6"><div><h1 className="text-2xl font-bold">Patients and Notes</h1><p className="mt-1 text-muted-foreground">Patients appear after a pending, approved, or completed appointment. Notes are shared with that patient.</p></div>{message && <p className="text-sm text-muted-foreground">{message}</p>}{patients.length === 0 ? <div className="rounded-xl border border-border/40 bg-card p-10 text-center">No connected patients yet.</div> : <div className="grid gap-4 md:grid-cols-2">{patients.map(patient => <button key={patient.id} onClick={() => setSelected(patient.id)} className={`rounded-xl border p-5 text-left ${selected === patient.id ? 'border-primary bg-primary/5' : 'border-border/40 bg-card'}`}><p className="font-medium">{patient.name}</p><p className="mt-1 text-sm text-muted-foreground">{patient.email}</p></button>)}</div>}{selected && <div className="rounded-xl border border-border/40 bg-card p-6"><h2 className="font-semibold">Add professional note</h2><textarea value={content} onChange={e => setContent(e.target.value)} placeholder="Enter your observation or note" className="mt-4 min-h-28 w-full rounded-lg border border-border/40 bg-background px-4 py-2.5 text-sm" /><textarea value={followUp} onChange={e => setFollowUp(e.target.value)} placeholder="Follow-up plan (optional)" className="mt-3 min-h-20 w-full rounded-lg border border-border/40 bg-background px-4 py-2.5 text-sm" /><button onClick={save} disabled={!content.trim()} className="mt-3 rounded-lg bg-primary px-4 py-2 text-sm text-primary-foreground disabled:opacity-50">Save note</button></div>}</div>
}