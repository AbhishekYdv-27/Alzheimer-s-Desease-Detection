import { useState, useRef, useCallback, useEffect } from 'react'
import { analysisApi, modelsApi, portalApi } from '@/services/api'
import { useAuth } from '@/context/useAuth'
import { ModelInfo } from '@/types'
import { Upload, Image, X, Loader2, Brain, AlertCircle, CheckCircle, BarChart3 } from 'lucide-react'

interface PredictionResult {
  predicted_class: string
  predicted_class_index: number
  class_probabilities: Record<string, number>
  confidence: number
  model_name: string
  model_version: string
  explanation_available: boolean
  timestamp: string
  error_code: string | null
  error_message: string | null
}

export default function AnalysisPage() {
  const { user } = useAuth()
  const [patients, setPatients] = useState<{ id: string; name: string; email: string }[]>([])
  const [selectedPatientId, setSelectedPatientId] = useState('')
  const [models, setModels] = useState<ModelInfo[]>([])
  const [selectedModel, setSelectedModel] = useState<string>('ResNet50')
  const [image, setImage] = useState<File | null>(null)
  const [imagePreview, setImagePreview] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [isDragging, setIsDragging] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<PredictionResult | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    const loadModels = async () => {
      try {
        const [modelsData, statusData] = await Promise.all([
          modelsApi.getAll(),
          modelsApi.getStatus(),
        ])
        const availableNames = new Set(
          statusData.models.filter((model) => model.available).map((model) => model.model_name),
        )
        setModels(modelsData.filter((model) => availableNames.has(model.model_name)))
      } catch (err) {
        console.error('Failed to load models:', err)
      }
    }
    loadModels()
  }, [])

  useEffect(() => {
    if (user?.role === 'doctor') {
      portalApi.doctorPatients().then(setPatients).catch(() => setPatients([]))
    }
  }, [user?.role])

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }, [])

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
  }, [])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)

    const file = e.dataTransfer.files[0]
    if (file && file.type.startsWith('image/')) {
      handleFile(file)
    }
  }, [])

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      handleFile(file)
    }
  }

  const handleFile = (file: File) => {
    if (!file.type.startsWith('image/')) {
      setError('Please select an image file')
      return
    }
    setImage(file)
    setError(null)
    setResult(null)
    const reader = new FileReader()
    reader.onload = (e) => {
      setImagePreview(e.target?.result as string)
    }
    reader.readAsDataURL(file)
  }

  const clearImage = () => {
    setImage(null)
    setImagePreview(null)
    setResult(null)
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  const analyzeImage = async () => {
    if (!image || !selectedModel) return

    setIsLoading(true)
    setError(null)

    try {
      const predictionResult = await analysisApi.predict(image, selectedModel)
      if (predictionResult.error_code) {
        setError(predictionResult.error_message || 'Analysis failed')
        return
      }
      setResult(predictionResult)

      if (user && predictionResult.predicted_class && (user.role !== 'doctor' || selectedPatientId)) {
        try {
          await analysisApi.saveRecord({
            user_id: user.role === 'doctor' ? selectedPatientId : user.id,
            image_name: image.name,
            model_name: selectedModel,
            predicted_class: predictionResult.predicted_class,
            confidence: predictionResult.confidence,
            status: 'completed',
            model_version: predictionResult.model_version,
            class_probabilities: predictionResult.class_probabilities,
            explanation_available: predictionResult.explanation_available,
          })
        } catch (saveErr) {
          console.error('Failed to save analysis record:', saveErr)
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Analysis failed')
    } finally {
      setIsLoading(false)
    }
  }

  const isModelReady = models.some((m) => m.model_name === selectedModel)

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold">AI Analysis</h1>
        <p className="mt-1 text-muted-foreground">
          Upload MRI images for AI-powered analysis
        </p>
      </div>

      {user?.role === 'doctor' && (
        <div className="rounded-xl border border-border/40 bg-card p-6">
          <h2 className="font-semibold">Patient for this analysis</h2>
          <p className="mt-1 text-sm text-muted-foreground">Only patients with an active appointment relationship are available.</p>
          <select value={selectedPatientId} onChange={(e) => setSelectedPatientId(e.target.value)} className="mt-4 w-full rounded-lg border border-border/40 bg-background px-4 py-2.5 text-sm">
            <option value="">Select an authorized patient</option>
            {patients.map((patient) => <option key={patient.id} value={patient.id}>{patient.name} ({patient.email})</option>)}
          </select>
        </div>
      )}

      {/* Model Selection */}
      <div className="rounded-xl border border-border/40 bg-card p-6">
        <h2 className="font-semibold">Select Model</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          Choose an AI model for analysis
        </p>

        <div className="mt-4 grid gap-3 md:grid-cols-3">
          {models.length > 0 ? (
            models.map((model) => (
              <button
                key={model.model_name}
                onClick={() => setSelectedModel(model.model_name)}
                className={`flex items-center gap-3 rounded-lg border p-4 text-left transition-all ${
                  selectedModel === model.model_name
                    ? 'border-primary bg-primary/5'
                    : 'border-border/40 hover:border-primary/30'
                }`}
              >
                <Brain className="h-5 w-5 text-primary" />
                <div>
                  <p className="font-medium">{model.model_name}</p>
                  <p className="text-xs text-muted-foreground">
                    {model.architecture} - {model.num_classes} classes
                  </p>
                </div>
                {selectedModel === model.model_name && (
                  <CheckCircle className="ml-auto h-4 w-4 text-primary" />
                )}
              </button>
            ))
          ) : (
            <div className="col-span-3 flex items-center gap-2 rounded-lg bg-orange-500/10 px-4 py-3 text-sm text-orange-600">
              <AlertCircle className="h-4 w-4" />
              No inference-ready models available
            </div>
          )}
        </div>

        {models.length > 0 && (
          <div className="mt-4 rounded-lg bg-green-500/10 px-4 py-3 text-sm text-green-600">
            Model ready for inference
          </div>
        )}
      </div>

      {/* Image Upload */}
      <div className="rounded-xl border border-border/40 bg-card p-6">
        <h2 className="font-semibold">Upload Image</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          Drag and drop or browse for MRI images
        </p>

        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
          className={`mt-4 flex flex-col items-center justify-center rounded-lg border-2 border-dashed p-8 transition-colors cursor-pointer ${
            isDragging
              ? 'border-primary bg-primary/5'
              : 'border-border/40 hover:border-primary/30'
          }`}
        >
          {imagePreview ? (
            <div className="relative">
              <img
                src={imagePreview}
                alt="Preview"
                className="max-h-64 rounded-lg object-contain"
              />
              <button
                onClick={(e) => {
                  e.stopPropagation()
                  clearImage()
                }}
                className="absolute -right-2 -top-2 flex h-8 w-8 items-center justify-center rounded-full bg-destructive text-destructive-foreground shadow-lg"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
          ) : (
            <>
              <Upload className="h-12 w-12 text-muted-foreground" />
              <p className="mt-4 font-medium">Drop your image here</p>
              <p className="mt-1 text-sm text-muted-foreground">
                or click to browse
              </p>
              <p className="mt-2 text-xs text-muted-foreground">
                Supports: JPEG, PNG, BMP, TIFF
              </p>
            </>
          )}
        </div>

        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          onChange={handleFileSelect}
          className="hidden"
        />

        {error && (
          <div className="mt-4 rounded-lg border border-destructive/50 bg-destructive/10 px-4 py-3 text-sm text-destructive">
            {error}
          </div>
        )}
      </div>

      {/* Analyze Button */}
      <button
        onClick={analyzeImage}
        disabled={!image || !selectedModel || isLoading || !isModelReady || (user?.role === 'doctor' && !selectedPatientId)}
        className="flex w-full items-center justify-center gap-2 rounded-lg bg-primary px-6 py-3 font-semibold text-primary-foreground transition-colors hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {isLoading ? (
          <>
            <Loader2 className="h-5 w-5 animate-spin" />
            Analyzing...
          </>
        ) : (
          <>
            <Image className="h-5 w-5" />
            Analyze Image
          </>
        )}
      </button>

      {/* Results */}
      {result && !result.error_code && (
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

          {/* Class Probabilities */}
          {result.class_probabilities && (
            <div className="mt-6">
              <h3 className="flex items-center gap-2 font-semibold">
                <BarChart3 className="h-5 w-5 text-primary" />
                Softmax Scores (Not Calibrated)
              </h3>
              <div className="mt-4 space-y-3">
                {Object.entries(result.class_probabilities).map(([cls, prob]) => (
                  <div key={cls}>
                    <div className="flex justify-between text-sm">
                      <span>{cls}</span>
                      <span className="font-medium">{(prob * 100).toFixed(2)}%</span>
                    </div>
                    <div className="mt-1 h-2 w-full rounded-full bg-secondary">
                      <div
                        className="h-2 rounded-full bg-primary transition-all"
                        style={{ width: `${prob * 100}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Disclaimer */}
      <div className="rounded-lg border border-orange-500/30 bg-orange-500/10 p-4">
        <p className="text-xs text-orange-600 dark:text-orange-400">
          <strong>Disclaimer:</strong> This platform is for research purposes only.
          AI predictions should never replace professional medical diagnosis.
        </p>
      </div>
    </div>
  )
}