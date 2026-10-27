import { Brain, Layers, Microscope, BarChart3, Thermometer } from 'lucide-react'

const technologies = [
  {
    category: 'AI Models',
    items: [
      {
        name: 'ResNet50',
        description: 'Configured four-output classifier. Checkpoint availability depends on the deployment artifact.',
        status: 'CONFIGURED',
        classes: 4,
      },
      {
        name: 'Swin Transformer',
        description: 'Architecture code only; not part of the active configured inference path.',
        status: 'RESEARCH CODE',
        classes: 4,
      },
      {
        name: 'U-Net',
        description: 'Experimental segmentation architecture; no trained checkpoint or active segmentation path is verified.',
        status: 'EXPERIMENTAL',
        purpose: 'Experimental',
      },
    ],
  },
  {
    category: 'Explainability',
    items: [
      {
        name: 'Grad-CAM',
        description: 'Implemented and smoke-tested with the configured ResNet50 checkpoint on synthetic input; hosted availability is unverified.',
        status: 'LOCAL SMOKE TEST',
      },
    ],
  },
  {
    category: 'Uncertainty',
    items: [
      {
        name: 'MC Dropout',
        description: 'Research code exists; this is not used by the active prediction endpoint.',
        status: 'NOT ACTIVE',
      },
      {
        name: 'Ensemble Methods',
        description: 'No ensemble inference or reliability evaluation is verified.',
        status: 'NOT VERIFIED',
      },
    ],
  },
  {
    category: 'Calibration',
    items: [
      {
        name: 'Temperature Scaling',
        description: 'Calibration has not been verified on labeled data.',
        status: 'NOT VERIFIED',
      },
      {
        name: 'ECE/MCE',
        description: 'No labeled test dataset is available to produce calibration metrics.',
        status: 'NOT VERIFIED',
      },
    ],
  },
]

export default function TechnologyPage() {
  return (
    <div className="py-16">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mx-auto max-w-3xl text-center">
          <h1 className="text-4xl font-bold tracking-tight sm:text-5xl">
            Technology Stack
          </h1>
          <p className="mt-4 text-lg text-muted-foreground">
            Cutting-edge AI technologies designed for Alzheimer's research analysis.
          </p>
        </div>

        {/* Technology Categories */}
        <div className="mt-16 space-y-16">
          {technologies.map((tech) => (
            <div key={tech.category}>
              <h2 className="flex items-center gap-2 text-xl font-semibold">
                {tech.category === 'AI Models' && <Brain className="h-5 w-5 text-primary" />}
                {tech.category === 'Explainability' && <Microscope className="h-5 w-5 text-primary" />}
                {tech.category === 'Uncertainty' && <BarChart3 className="h-5 w-5 text-primary" />}
                {tech.category === 'Calibration' && <Thermometer className="h-5 w-5 text-primary" />}
                {tech.category}
              </h2>

              <div className="mt-6 grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                {tech.items.map((item) => (
                  <div
                    key={item.name}
                    className="rounded-xl border border-border/40 bg-card p-5"
                  >
                    <div className="flex items-start justify-between">
                      <h3 className="font-medium">{item.name}</h3>
                      <span
                        className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                          item.status === 'CONFIGURED' || item.status === 'LOCAL SMOKE TEST'
                            ? 'bg-primary/10 text-primary'
                            : 'bg-secondary text-muted-foreground'
                        }`}
                      >
                        {item.status}
                      </span>
                    </div>

                    <p className="mt-2 text-sm text-muted-foreground">
                      {item.description}
                    </p>

                    {'classes' in item && (
                      <div className="mt-3 text-xs text-muted-foreground">
                        Classes: {item.classes}
                      </div>
                    )}

                    {'purpose' in item && (
                      <div className="mt-3 text-xs text-muted-foreground">
                        Purpose: {item.purpose}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>

        {/* Architecture Overview */}
        <div className="mt-16 rounded-xl border border-border/40 bg-card p-8">
          <h2 className="flex items-center gap-2 text-xl font-semibold">
            <Layers className="h-5 w-5 text-primary" />
            Architecture Overview
          </h2>

          <div className="mt-6 grid gap-6 md:grid-cols-2">
            <div>
              <h3 className="font-medium">Backend Stack</h3>
              <ul className="mt-3 space-y-2 text-sm text-muted-foreground">
                <li>• FastAPI - High-performance web framework</li>
                <li>• PyTorch - Deep learning framework</li>
                <li>• SQLite - Database for users and records</li>
                <li>• JWT - Secure authentication</li>
              </ul>
            </div>
            <div>
              <h3 className="font-medium">Frontend Stack</h3>
              <ul className="mt-3 space-y-2 text-sm text-muted-foreground">
                <li>• React 18 - User interface library</li>
                <li>• TypeScript - Type-safe development</li>
                <li>• Tailwind CSS - Utility-first styling</li>
                <li>• React Router - Client-side routing</li>
              </ul>
            </div>
          </div>
        </div>

        {/* Note */}
        <div className="mt-8 rounded-lg border border-orange-500/30 bg-orange-500/10 p-4">
          <p className="text-sm text-orange-600 dark:text-orange-400">
            <strong>Research limitation:</strong> The active local inference path is a
            four-output ResNet50 classifier. A local checkpoint is present but is not
            included in the Git deployment tree. No authorized labeled MRI dataset is
            bundled, so model performance and clinical validity have not been established.
            U-Net segmentation and CLAHE are not part of the verified inference path.
          </p>
        </div>
      </div>
    </div>
  )
}
