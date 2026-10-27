import { Link } from 'react-router-dom'
import { Database, Brain, Lightbulb, BarChart3, Scan, Shield, ArrowRight } from 'lucide-react'

const features = [
  {
    icon: Database,
    title: 'Data Pipeline',
    description: 'Supported image formats are decoded and validated before resize and normalization. No labeled MRI dataset is bundled.',
    status: 'Implemented',
  },
  {
    icon: Brain,
    title: 'AI Models',
    description: 'A four-output ResNet50 classifier is configured. Other architectures remain research code, not active inference.',
    status: 'Deployment-dependent',
  },
  {
    icon: Lightbulb,
    title: 'Explainability',
    description: 'Grad-CAM code is implemented; availability depends on a compatible checkpoint and writable host storage.',
    status: 'Deployment-dependent',
  },
  {
    icon: BarChart3,
    title: 'Model Evaluation',
    description: 'Performance has not been validated against an authorized labeled test dataset.',
    status: 'Not verified',
  },
  {
    icon: Scan,
    title: 'Uncertainty Estimation',
    description: 'The active API returns class probabilities; uncertainty intervals are not part of the verified workflow.',
    status: 'Not active',
  },
  {
    icon: Shield,
    title: 'Model Calibration',
    description: 'No calibration evaluation on labeled data is available.',
    status: 'Not verified',
  },
]

export default function PlatformPage() {
  return (
    <div className="py-16">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mx-auto max-w-3xl text-center">
          <h1 className="text-4xl font-bold tracking-tight sm:text-5xl">
            Research Platform
          </h1>
          <p className="mt-4 text-lg text-muted-foreground">
            A comprehensive AI platform designed for researchers studying Alzheimer's
            disease through machine learning analysis.
          </p>
        </div>

        {/* Features Grid */}
        <div className="mt-16 grid gap-8 md:grid-cols-2 lg:grid-cols-3">
          {features.map((feature) => {
            const Icon = feature.icon
            return (
              <div
                key={feature.title}
                className="group relative overflow-hidden rounded-xl border border-border/40 bg-card p-6 transition-all hover:border-primary/30 hover:shadow-lg hover:shadow-primary/5"
              >
                <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-primary/10 transition-colors group-hover:bg-primary/20">
                  <Icon className="h-6 w-6 text-primary" />
                </div>

                <div className="mt-4">
                  <div className="flex items-center justify-between">
                    <h3 className="font-semibold">{feature.title}</h3>
                    <span className="rounded-full bg-primary/10 px-2 py-0.5 text-xs font-medium text-primary">
                      {feature.status}
                    </span>
                  </div>
                  <p className="mt-2 text-sm text-muted-foreground">
                    {feature.description}
                  </p>
                </div>
              </div>
            )
          })}
        </div>

        {/* Workflow */}
        <div className="mt-24">
          <h2 className="text-center text-2xl font-bold">Research Workflow</h2>

          <div className="mt-8 grid gap-4 md:grid-cols-5">
            {['Upload', 'Validate', 'Analyze', 'Interpret', 'Report'].map((step, i) => (
              <div key={step} className="relative">
                <div className="flex flex-col items-center">
                  <div className="flex h-12 w-12 items-center justify-center rounded-full border-2 border-primary bg-primary/10 text-sm font-bold text-primary">
                    {i + 1}
                  </div>
                  <p className="mt-2 text-sm font-medium">{step}</p>
                </div>
                {i < 4 && (
                  <div className="absolute left-[calc(50%+24px)] top-6 hidden h-px w-[calc(100%-48px)] bg-border/40 md:block" />
                )}
              </div>
            ))}
          </div>
        </div>

        {/* CTA */}
        <div className="mt-16 text-center">
          <Link
            to="/signup"
            className="inline-flex items-center gap-2 rounded-lg bg-primary px-6 py-3 text-sm font-semibold text-primary-foreground transition-colors hover:bg-primary/90"
          >
            Start Researching
            <ArrowRight className="h-4 w-4" />
          </Link>
        </div>
      </div>
    </div>
  )
}
