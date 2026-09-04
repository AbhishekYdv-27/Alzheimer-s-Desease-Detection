import { Brain, Layers, Microscope, BarChart3, Thermometer } from 'lucide-react'

const technologies = [
  {
    category: 'AI Models',
    items: [
      {
        name: 'ResNet50',
        description: 'Deep residual network for image classification with 50 layers.',
        status: 'IMPLEMENTED',
        trained: false,
        classes: 4,
      },
      {
        name: 'Swin Transformer',
        description: 'Hierarchical vision transformer with shifted windows.',
        status: 'IMPLEMENTED',
        trained: false,
        classes: 4,
      },
      {
        name: 'U-Net',
        description: 'Encoder-decoder architecture for segmentation research.',
        status: 'IMPLEMENTED',
        trained: false,
        purpose: 'Experimental',
      },
    ],
  },
  {
    category: 'Explainability',
    items: [
      {
        name: 'Grad-CAM',
        description: 'Gradient-weighted Class Activation Mapping for CNN visualizations.',
        status: 'IMPLEMENTED',
        compatible: ['ResNet50', 'Swin Transformer'],
      },
    ],
  },
  {
    category: 'Uncertainty',
    items: [
      {
        name: 'MC Dropout',
        description: 'Monte Carlo Dropout for uncertainty quantification.',
        status: 'IMPLEMENTED',
      },
      {
        name: 'Ensemble Methods',
        description: 'Multi-model ensemble for improved reliability.',
        status: 'READY',
      },
    ],
  },
  {
    category: 'Calibration',
    items: [
      {
        name: 'Temperature Scaling',
        description: 'Post-training calibration for probability estimates.',
        status: 'IMPLEMENTED',
      },
      {
        name: 'ECE/MCE',
        description: 'Expected and Maximum Calibration Error metrics.',
        status: 'IMPLEMENTED',
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
                          item.status === 'IMPLEMENTED'
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

                    {'trained' in item && (
                      <div className="mt-3 flex items-center gap-2 text-xs">
                        <span
                          className={`flex h-2 w-2 rounded-full ${
                            item.trained ? 'bg-green-500' : 'bg-orange-500'
                          }`}
                        />
                        <span className="text-muted-foreground">
                          {item.trained ? 'Trained' : 'NOT TRAINED'}
                        </span>
                      </div>
                    )}

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
            <strong>Note:</strong> While the model architectures are fully implemented,
            they have not been trained on a dataset yet. Predictions will become available
            once trained models are integrated into the platform.
          </p>
        </div>
      </div>
    </div>
  )
}
