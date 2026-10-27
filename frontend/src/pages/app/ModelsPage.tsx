import { useState, useEffect } from 'react'
import { modelsApi } from '@/services/api'
import { ModelInfo } from '@/types'
import { Brain, AlertCircle, Clock } from 'lucide-react'

export default function ModelsPage() {
  const [models, setModels] = useState<ModelInfo[]>([])
  const [availability, setAvailability] = useState<Record<string, boolean>>({})
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    const loadModels = async () => {
      try {
        const [data, statusData] = await Promise.all([
          modelsApi.getAll(),
          modelsApi.getStatus(),
        ])
        setModels(data)
        setAvailability(Object.fromEntries(
          statusData.models.map((model) => [model.model_name, model.available]),
        ))
      } catch (error) {
        console.error('Failed to load models:', error)
      } finally {
        setIsLoading(false)
      }
    }
    loadModels()
  }, [])

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold">Models</h1>
        <p className="mt-1 text-muted-foreground">
          Explore and manage AI model architectures
        </p>
      </div>

      {/* Models Grid */}
      {isLoading ? (
        <div className="flex items-center justify-center py-16">
          <Clock className="h-6 w-6 animate-spin text-muted-foreground" />
          <span className="ml-2 text-muted-foreground">Loading models...</span>
        </div>
      ) : models.length === 0 ? (
        <div className="flex flex-col items-center justify-center rounded-xl border border-border/40 bg-card py-16">
          <div className="flex h-20 w-20 items-center justify-center rounded-full bg-secondary">
            <AlertCircle className="h-10 w-10 text-muted-foreground" />
          </div>
          <p className="mt-4 font-medium">No models available</p>
          <p className="mt-1 text-sm text-muted-foreground">
            Model architectures will appear here once registered
          </p>
        </div>
      ) : (
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {models.map((model) => (
            <div
              key={model.model_name}
              className="group rounded-xl border border-border/40 bg-card p-6 transition-all hover:border-primary/30 hover:shadow-lg hover:shadow-primary/5"
            >
              <div className="flex items-start justify-between">
                <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-primary/10">
                  <Brain className="h-6 w-6 text-primary" />
                </div>
                <span
                  className={`rounded-full px-3 py-1 text-xs font-medium ${
                    availability[model.model_name]
                      ? 'bg-green-500/10 text-green-600'
                      : 'bg-orange-500/10 text-orange-600'
                  }`}
                >
                  {availability[model.model_name] ? 'Checkpoint ready' : 'Unavailable'}
                </span>
              </div>

              <h3 className="mt-4 font-semibold">{model.model_name}</h3>
              <p className="mt-1 text-sm text-muted-foreground">
                {model.architecture}
              </p>

              <div className="mt-4 space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">Version</span>
                  <span className="font-medium">{model.model_version}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">Classes</span>
                  <span className="font-medium">{model.num_classes}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">Experiment ID</span>
                  <span className="font-medium">
                    {model.experiment_id || 'N/A'}
                  </span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">Training provenance</span>
                  <span className="font-medium">
                    {model.training_status === 'UNVERIFIED' ? 'Not verified' : model.training_status}
                  </span>
                </div>
              </div>

              {/* Classes */}
              <div className="mt-4">
                <p className="text-xs font-medium text-muted-foreground">
                  Classes
                </p>
                <div className="mt-2 flex flex-wrap gap-1">
                  {model.class_names.map((cls) => (
                    <span
                      key={cls}
                      className="rounded bg-secondary px-2 py-0.5 text-xs text-secondary-foreground"
                    >
                      {cls}
                    </span>
                  ))}
                </div>
              </div>

              {/* Metrics */}
              {Object.keys(model.metrics).length > 0 && (
                <div className="mt-4 border-t border-border/40 pt-4">
                  <p className="text-xs font-medium text-muted-foreground">
                    Registered metrics (unverified)
                  </p>
                  <div className="mt-2 grid grid-cols-2 gap-2">
                    {Object.entries(model.metrics).slice(0, 4).map(([key, value]) => (
                      <div key={key} className="rounded bg-secondary/50 px-2 py-1">
                        <p className="text-xs text-muted-foreground">{key}</p>
                        <p className="text-sm font-medium">
                          {typeof value === 'number' ? value.toFixed(4) : value}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {Object.keys(model.metrics).length === 0 && (
                <div className="mt-4 border-t border-border/40 pt-4">
                  <p className="text-xs text-muted-foreground">
                    Metrics: NOT AVAILABLE
                  </p>
                </div>
              )}

            </div>
          ))}
        </div>
      )}

      {/* Disclaimer */}
      <div className="rounded-lg border border-orange-500/30 bg-orange-500/10 p-4">
        <p className="text-xs text-orange-600 dark:text-orange-400">
          <strong>Research note:</strong> Checkpoint availability is checked at runtime.
          Registered metrics have not been independently validated and are not clinical
          performance claims. Other architectures may remain research infrastructure only.
        </p>
      </div>
    </div>
  )
}
