import { FlaskConical, AlertTriangle, Microscope, BookOpen, FileWarning } from 'lucide-react'

export default function ResearchPage() {
  return (
    <div className="py-16">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mx-auto max-w-3xl text-center">
          <h1 className="text-4xl font-bold tracking-tight sm:text-5xl">
            Research Platform
          </h1>
          <p className="mt-4 text-lg text-muted-foreground">
            An explainable AI platform designed for researchers studying Alzheimer's
            disease through machine learning.
          </p>
        </div>

        {/* Research Workflow */}
        <div className="mt-16">
          <h2 className="text-2xl font-bold">Research Workflow</h2>

          <div className="mt-6 space-y-4">
            {[
              {
                step: '1',
                title: 'Data Collection & Validation',
                description: 'Upload MRI images through a robust validation pipeline that checks format, dimensions, and integrity.',
              },
              {
                step: '2',
                title: 'Model Analysis',
                description: 'Apply trained AI models to identify patterns associated with different stages of cognitive decline.',
              },
              {
                step: '3',
                title: 'Explainability & Interpretation',
                description: 'Use Grad-CAM visualizations to understand which brain regions influence model predictions.',
              },
              {
                step: '4',
                title: 'Uncertainty Quantification',
                description: 'Evaluate prediction confidence through Monte Carlo Dropout and ensemble methods.',
              },
              {
                step: '5',
                title: 'Model Evaluation',
                description: 'Assess model performance using comprehensive metrics including calibration analysis.',
              },
            ].map((item) => (
              <div
                key={item.step}
                className="flex gap-4 rounded-xl border border-border/40 bg-card p-6"
              >
                <div className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-full bg-primary/10 text-sm font-bold text-primary">
                  {item.step}
                </div>
                <div>
                  <h3 className="font-semibold">{item.title}</h3>
                  <p className="mt-1 text-sm text-muted-foreground">{item.description}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Ethical Considerations */}
        <div className="mt-16">
          <h2 className="text-2xl font-bold">Ethical Considerations</h2>

          <div className="mt-6 grid gap-4 md:grid-cols-2">
            <div className="flex items-start gap-3 rounded-xl border border-border/40 bg-card p-5">
              <AlertTriangle className="h-5 w-5 flex-shrink-0 text-orange-500" />
              <div>
                <h3 className="font-medium">Limitations</h3>
                <p className="mt-1 text-sm text-muted-foreground">
                  AI predictions should never replace professional medical judgment.
                  This platform is a research tool, not a diagnostic system.
                </p>
              </div>
            </div>

            <div className="flex items-start gap-3 rounded-xl border border-border/40 bg-card p-5">
              <Microscope className="h-5 w-5 flex-shrink-0 text-primary" />
              <div>
                <h3 className="font-medium">Research Focus</h3>
                <p className="mt-1 text-sm text-muted-foreground">
                  Designed for researchers investigating AI applications in neuroscience,
                  not for clinical decision-making.
                </p>
              </div>
            </div>

            <div className="flex items-start gap-3 rounded-xl border border-border/40 bg-card p-5">
              <BookOpen className="h-5 w-5 flex-shrink-0 text-primary" />
              <div>
                <h3 className="font-medium">Transparency</h3>
                <p className="mt-1 text-sm text-muted-foreground">
                  All model decisions are explained through interpretability methods
                  to support explainable AI research.
                </p>
              </div>
            </div>

            <div className="flex items-start gap-3 rounded-xl border border-border/40 bg-card p-5">
              <FileWarning className="h-5 w-5 flex-shrink-0 text-orange-500" />
              <div>
                <h3 className="font-medium">Data Privacy</h3>
                <p className="mt-1 text-sm text-muted-foreground">
                  User-uploaded images are processed within the platform and not shared
                  with third parties.
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Medical Disclaimer */}
        <div className="mt-16 rounded-xl border border-destructive/30 bg-destructive/5 p-8">
          <div className="flex items-start gap-4">
            <FlaskConical className="h-6 w-6 flex-shrink-0 text-destructive" />
            <div>
              <h3 className="text-lg font-semibold">Medical Disclaimer</h3>
              <p className="mt-2 text-sm text-muted-foreground">
                This platform is designed for educational and research purposes only. It is not
                intended to replace professional medical diagnosis or clinical judgment. The
                system does not provide confirmed medical diagnoses. All AI outputs should be
                considered AI-assisted research predictions and must never replace professional
                medical judgment. Always consult a qualified healthcare provider for medical decisions.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
