import { useEffect, useState, useRef } from 'react'
import { AlertCircle, Image as ImageIcon, Info, Upload, Loader2, CheckCircle } from 'lucide-react'
import { analysisApi, modelsApi } from '@/services/api'

interface ExplainResult {
  success: boolean
  predicted_class: string
  predicted_class_index: number
  confidence: number
  model_name: string
  model_version: string
  heatmap_url: string | null
  overlay_url: string | null
  explanation_available: boolean
  error_code: string | null
  error_message: string | null
}

export default function ExplainabilityPage() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [previewUrl, setPreviewUrl] = useState<string | null>(null)
  const [result, setResult] = useState<ExplainResult | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [modelAvailable, setModelAvailable] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    modelsApi.getStatus()
      .then(({ models }) => setModelAvailable(
        models.some((model) => model.model_name === 'ResNet50' && model.available),
      ))
      .catch(() => setModelAvailable(false))
  }, [])

  useEffect(() => () => {
    if (result?.heatmap_url) URL.revokeObjectURL(result.heatmap_url)
    if (result?.overlay_url) URL.revokeObjectURL(result.overlay_url)
  }, [result])

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      setSelectedFile(file)
      setPreviewUrl(URL.createObjectURL(file))
      setResult(null)
      setError(null)
    }
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    const file = e.dataTransfer.files?.[0]
    if (file && file.type.startsWith('image/')) {
      setSelectedFile(file)
      setPreviewUrl(URL.createObjectURL(file))
      setResult(null)
      setError(null)
    }
  }

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
  }

  const handleExplain = async () => {
    if (!selectedFile) return

    setIsLoading(true)
    setError(null)

    try {
      const response = await analysisApi.explain(selectedFile, 'ResNet50', '1.0')
      if (!response.success) {
        setError(response.error_message || 'Explanation failed')
        setResult(null)
        return
      }
      setResult(response)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Explanation failed')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold">Explainability</h1>
        <p className="mt-1 text-muted-foreground">
          Understand AI model decisions through Grad-CAM visualizations
        </p>
      </div>

      {/* Info Card */}
      <div className="rounded-xl border border-border/40 bg-card p-6">
        <div className="flex items-start gap-4">
          <Info className="h-5 w-5 text-primary mt-0.5" />
          <div>
            <h3 className="font-semibold">How Grad-CAM Works</h3>
            <p className="mt-2 text-sm text-muted-foreground">
              Grad-CAM (Gradient-weighted Class Activation Mapping) highlights regions of the MRI image that contributed most to the model&apos;s prediction. Red regions indicate high importance, while blue regions indicate low importance.
            </p>
          </div>
        </div>
      </div>

      {/* Image Upload */}
      <div className="rounded-xl border border-border/40 bg-card p-6">
        <h3 className="font-semibold">Upload MRI Image</h3>
        <p className="mt-1 text-sm text-muted-foreground">
          Upload an MRI brain scan to generate Grad-CAM explanation
        </p>

        <div
          className="mt-4 flex flex-col items-center justify-center rounded-lg border-2 border-dashed border-border/40 bg-secondary/30 p-8 cursor-pointer hover:bg-secondary/40 transition-colors"
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          onClick={() => fileInputRef.current?.click()}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            onChange={handleFileSelect}
            className="hidden"
          />
          {previewUrl ? (
            <img
              src={previewUrl}
              alt="Preview"
              className="max-h-64 rounded-lg object-contain"
            />
          ) : (
            <>
              <Upload className="h-12 w-12 text-muted-foreground" />
              <p className="mt-2 text-sm text-muted-foreground">
                Click or drag image to upload
              </p>
            </>
          )}
        </div>

        {selectedFile && (
          <div className="mt-4 flex items-center justify-between">
            <p className="text-sm text-muted-foreground">
              Selected: {selectedFile.name}
            </p>
            <button
              onClick={handleExplain}
              disabled={isLoading}
              className="flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
            >
              {isLoading ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Generating...
                </>
              ) : (
                <>
                  <ImageIcon className="h-4 w-4" />
                  Generate Explanation
                </>
              )}
            </button>
          </div>
        )}
      </div>

      {/* Error Display */}
      {error && (
        <div className="rounded-xl border border-red-500/30 bg-red-500/10 p-4">
          <div className="flex items-center gap-2 text-red-600">
            <AlertCircle className="h-5 w-5" />
            <p className="font-medium">{error}</p>
          </div>
        </div>
      )}

      {/* Results */}
      {result && result.success && (
        <>
          {/* Prediction Result */}
          <div className="rounded-xl border border-border/40 bg-card p-6">
            <div className="flex items-center gap-4">
              <div className="flex h-12 w-12 items-center justify-center rounded-full bg-green-500/10">
                <CheckCircle className="h-6 w-6 text-green-500" />
              </div>
              <div>
                <h2 className="text-lg font-semibold">Prediction: {result.predicted_class}</h2>
                <p className="text-sm text-muted-foreground">
                  Top-class softmax score: {(result.confidence * 100).toFixed(2)}% (uncalibrated) | Model: {result.model_name} v{result.model_version}
                </p>
              </div>
            </div>
          </div>

          {/* Grad-CAM Visualizations */}
          <div className="grid gap-6 md:grid-cols-2">
            {/* Heatmap */}
            {result.heatmap_url && (
              <div className="rounded-xl border border-border/40 bg-card p-6">
                <h3 className="font-semibold">Grad-CAM Heatmap</h3>
                <p className="mt-1 text-sm text-muted-foreground">
                  Highlights important regions for the prediction
                </p>
                <div className="mt-4 flex items-center justify-center rounded-lg bg-secondary/30 p-4">
                  <img
                    src={result.heatmap_url}
                    alt="Grad-CAM Heatmap"
                    className="max-h-64 rounded-lg object-contain"
                  />
                </div>
              </div>
            )}

            {/* Overlay */}
            {result.overlay_url && (
              <div className="rounded-xl border border-border/40 bg-card p-6">
                <h3 className="font-semibold">MRI + Heatmap Overlay</h3>
                <p className="mt-1 text-sm text-muted-foreground">
                  Original image with Grad-CAM overlay
                </p>
                <div className="mt-4 flex items-center justify-center rounded-lg bg-secondary/30 p-4">
                  <img
                    src={result.overlay_url}
                    alt="MRI + Grad-CAM Overlay"
                    className="max-h-64 rounded-lg object-contain"
                  />
                </div>
              </div>
            )}
          </div>

          {/* Legend */}
          <div className="rounded-xl border border-border/40 bg-card p-6">
            <h3 className="font-semibold">Heatmap Legend</h3>
            <div className="mt-4 flex items-center justify-center gap-8">
              <div className="flex items-center gap-2">
                <div className="h-4 w-4 rounded bg-red-500" />
                <span className="text-xs text-muted-foreground">High importance (Red)</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="h-4 w-4 rounded bg-yellow-500" />
                <span className="text-xs text-muted-foreground">Medium importance (Yellow)</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="h-4 w-4 rounded bg-blue-500" />
                <span className="text-xs text-muted-foreground">Low importance (Blue)</span>
              </div>
            </div>
          </div>
        </>
      )}

      {/* Configured Model */}
      <div className="rounded-xl border border-border/40 bg-card p-6">
        <h3 className="font-semibold">Configured Model</h3>
        <div className="mt-4 space-y-3">
          <div className="flex items-center justify-between rounded-lg border border-border/40 bg-secondary/30 p-3">
            <span className="font-medium">ResNet50</span>
            <span className={`rounded px-2 py-0.5 text-xs font-medium ${modelAvailable ? 'bg-green-500/10 text-green-600' : 'bg-orange-500/10 text-orange-600'}`}>
              {modelAvailable ? 'Checkpoint ready' : 'Unavailable'}
            </span>
          </div>
        </div>
      </div>

      {/* Disclaimer */}
      <div className="rounded-lg border border-orange-500/30 bg-orange-500/10 p-4">
        <p className="text-xs text-orange-600 dark:text-orange-400">
          <strong>Disclaimer:</strong> AI visualizations show which regions influenced
          the model&apos;s prediction, but do not represent actual medical findings.
          This platform is for research purposes only.
        </p>
      </div>
    </div>
  )
}