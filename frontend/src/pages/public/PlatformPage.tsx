import { Link } from 'react-router-dom'
import { Database, Brain, Lightbulb, BarChart3, Scan, Shield, ArrowRight } from 'lucide-react'

const features = [
  {
    icon: Database,
    title: 'Data Pipeline',
    description: 'Comprehensive preprocessing pipeline with image validation, format checking, and quality assessment.',
    status: 'Ready',
  },
  {
    icon: Brain,
    title: 'AI Models',
    description: 'Multiple architectures including ResNet50 and Swin Transformer for pattern recognition.',
    status: 'Implemented',
  },
  {
    icon: Lightbulb,
    title: 'Explainability',
    description: 'Grad-CAM visualizations to understand what features drive model predictions.',
    status: 'Available',
  },
  {
    icon: BarChart3,
    title: 'Model Evaluation',
    description: 'Comprehensive metrics including precision, recall, F1, ROC-AUC, and calibration analysis.',
    status: 'Ready',
  },
  {
    icon: Scan,
    title: 'Uncertainty Estimation',
    description: 'Monte Carlo Dropout and ensemble methods for confidence intervals.',
    status: 'Implemented',
  },
  {
    icon: Shield,
    title: 'Model Calibration',
    description: 'Temperature scaling for reliable probability estimates and calibration curves.',
    status: 'Available',
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
