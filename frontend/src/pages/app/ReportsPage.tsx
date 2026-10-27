import { useEffect, useState } from 'react'
import { useAuth } from '@/context/useAuth'
import { analysisApi } from '@/services/api'
import { AnalysisRecord } from '@/types'
import { FileText, Download, Clock, Brain, AlertCircle, CheckCircle, XCircle, BarChart3 } from 'lucide-react'

export default function ReportsPage() {
  const { user } = useAuth()
  const [records, setRecords] = useState<AnalysisRecord[]>([])
  const [selectedId, setSelectedId] = useState('')
  const [isLoading, setIsLoading] = useState(true)
  const [isDownloading, setIsDownloading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const loadRecords = async () => {
      if (!user?.id) { setIsLoading(false); return }
      try {
        const data = await analysisApi.getRecords(user.id)
        setRecords(data)
        if (data.length > 0) setSelectedId(data[0].id)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unable to load analysis reports')
      } finally { setIsLoading(false) }
    }
    loadRecords()
  }, [user?.id])

  const selectedRecord = records.find((record) => record.id === selectedId)
  const formatDate = (dateStr: string) => new Date(dateStr).toLocaleString('en-US', { dateStyle: 'long', timeStyle: 'short' })

  const downloadReport = async () => {
    if (!selectedRecord) return
    setIsDownloading(true)
    setError(null)
    try {
      const blob = await analysisApi.downloadReport(selectedRecord.id)
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `analysis-report-${selectedRecord.id}.html`
      link.click()
      URL.revokeObjectURL(url)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Report download failed')
    } finally { setIsDownloading(false) }
  }

  if (isLoading) return <div className="flex items-center justify-center py-16"><div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" /><span className="ml-3 text-muted-foreground">Loading reports...</span></div>

  return (
    <div className="space-y-6 animate-fade-in">
      <div><h1 className="text-2xl font-bold">Reports</h1><p className="mt-1 text-muted-foreground">Review and export reports from your saved analyses</p></div>
      {error && <div className="rounded-lg border border-red-500/30 bg-red-500/10 p-3 text-sm text-red-600">{error}</div>}

      {records.length === 0 ? (
        <div className="rounded-xl border border-border/40 bg-card p-12 text-center">
          <FileText className="mx-auto h-12 w-12 text-muted-foreground" />
          <p className="mt-4 font-medium">No analysis records available</p>
          <p className="mt-1 text-sm text-muted-foreground">Complete an analysis to generate a report from real prediction data.</p>
          <a href="/analysis" className="mt-4 inline-flex rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground">Start Analysis</a>
        </div>
      ) : (
        <>
          <div className="rounded-xl border border-border/40 bg-card p-6">
            <label htmlFor="report-record" className="block text-sm font-medium">Analysis record</label>
            <select id="report-record" value={selectedId} onChange={(event) => setSelectedId(event.target.value)} className="mt-2 w-full rounded-lg border border-border/40 bg-background px-4 py-2.5 text-sm">
              {records.map((record) => <option key={record.id} value={record.id}>{record.predicted_class || 'Incomplete analysis'} | {formatDate(record.created_at)} | {record.image_name}</option>)}
            </select>
          </div>

          {selectedRecord && <div className="rounded-xl border border-border/40 bg-card p-6">
            <div className="flex flex-wrap items-start justify-between gap-4">
              <div><h2 className="text-xl font-semibold">AI-Assisted Analysis Report</h2><p className="mt-1 text-sm text-muted-foreground">Research output for {selectedRecord.image_name}</p></div>
              <button onClick={downloadReport} disabled={isDownloading} className="flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground disabled:opacity-50">{isDownloading ? 'Preparing...' : 'Download HTML Report'}<Download className="h-4 w-4" /></button>
            </div>
            <div className="mt-6 grid gap-4 sm:grid-cols-2">
              <div><p className="text-xs text-muted-foreground">Predicted class</p><p className="mt-1 font-semibold">{selectedRecord.predicted_class || 'Not available'}</p></div>
              <div><p className="text-xs text-muted-foreground">Confidence</p><p className="mt-1 font-semibold">{selectedRecord.confidence == null ? 'Not available' : `${(selectedRecord.confidence * 100).toFixed(2)}%`}</p></div>
              <div><p className="text-xs text-muted-foreground">Analysis date</p><p className="mt-1 flex items-center gap-1 text-sm"><Clock className="h-4 w-4" />{formatDate(selectedRecord.created_at)}</p></div>
              <div><p className="text-xs text-muted-foreground">Model</p><p className="mt-1 flex items-center gap-1 text-sm"><Brain className="h-4 w-4" />{selectedRecord.model_name} v{selectedRecord.model_version}</p></div>
              <div><p className="text-xs text-muted-foreground">Record status</p><p className="mt-1 flex items-center gap-1 text-sm">{selectedRecord.status === 'completed' ? <CheckCircle className="h-4 w-4 text-green-500" /> : selectedRecord.status === 'failed' ? <XCircle className="h-4 w-4 text-red-500" /> : <AlertCircle className="h-4 w-4 text-yellow-500" />}{selectedRecord.status}</p></div>
              <div><p className="text-xs text-muted-foreground">Grad-CAM explanation</p><p className="mt-1 text-sm">{selectedRecord.explanation_available ? 'Available' : 'Not generated for this analysis'}</p></div>
            </div>
            {selectedRecord.class_probabilities && <div className="mt-8"><h3 className="flex items-center gap-2 font-semibold"><BarChart3 className="h-5 w-5 text-primary" />Class probabilities</h3><div className="mt-4 space-y-3">{Object.entries(selectedRecord.class_probabilities).map(([label, value]) => <div key={label}><div className="flex justify-between text-sm"><span>{label}</span><span>{(value * 100).toFixed(2)}%</span></div><div className="mt-1 h-2 rounded-full bg-secondary"><div className="h-2 rounded-full bg-primary" style={{ width: `${value * 100}%` }} /></div></div>)}</div></div>}
            <p className="mt-8 rounded-lg border border-orange-500/30 bg-orange-500/10 p-4 text-xs text-orange-600 dark:text-orange-400"><strong>Research disclaimer:</strong> This is an AI-assisted research or demonstration output, not a professional medical diagnosis or treatment recommendation.</p>
          </div>}
        </>
      )}
    </div>
  )
}
