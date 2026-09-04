import { Brain, Heart, Lightbulb, Users, Shield, Code2 } from 'lucide-react'

export default function AboutPage() {
  return (
    <div className="py-16">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mx-auto max-w-3xl text-center">
          <h1 className="text-4xl font-bold tracking-tight sm:text-5xl">
            About the Platform
          </h1>
          <p className="mt-4 text-lg text-muted-foreground">
            Advancing Alzheimer's research through explainable AI.
          </p>
        </div>

        {/* Mission */}
        <div className="mt-16 grid gap-8 lg:grid-cols-2">
          <div className="flex flex-col justify-center">
            <h2 className="text-2xl font-bold">Our Mission</h2>
            <p className="mt-4 text-muted-foreground">
              We are building an AI research platform specifically designed to support
              investigators studying Alzheimer's disease. Our focus is on explainability,
              uncertainty quantification, and model interpretability—ensuring that AI
              serves as a transparent research tool rather than a black box.
            </p>
            <p className="mt-4 text-muted-foreground">
              The platform integrates state-of-the-art deep learning architectures with
              proven interpretability methods, enabling researchers to understand not just
              what a model predicts, but why it makes those predictions.
            </p>
          </div>

          <div className="flex items-center justify-center">
            <div className="relative">
              <div className="flex h-64 w-64 items-center justify-center rounded-full bg-primary/10">
                <Brain className="h-32 w-32 text-primary" />
              </div>
              <div className="absolute -right-4 -top-4 flex h-16 w-16 items-center justify-center rounded-full bg-accent/10">
                <Lightbulb className="h-8 w-8 text-accent" />
              </div>
            </div>
          </div>
        </div>

        {/* Why This Matters */}
        <div className="mt-24">
          <h2 className="text-center text-2xl font-bold">Why Explainable AI Matters</h2>

          <div className="mt-8 grid gap-6 md:grid-cols-3">
            <div className="rounded-xl border border-border/40 bg-card p-6">
              <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-primary/10">
                <Heart className="h-6 w-6 text-primary" />
              </div>
              <h3 className="mt-4 font-semibold">Trust & Transparency</h3>
              <p className="mt-2 text-sm text-muted-foreground">
                Researchers need to understand model decisions. Explainability builds
                trust in AI-assisted research by revealing the reasoning behind
                each prediction.
              </p>
            </div>

            <div className="rounded-xl border border-border/40 bg-card p-6">
              <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-primary/10">
                <Shield className="h-6 w-6 text-primary" />
              </div>
              <h3 className="mt-4 font-semibold">Risk Mitigation</h3>
              <p className="mt-2 text-sm text-muted-foreground">
                Understanding where AI succeeds and fails helps researchers identify
                edge cases and potential failure modes before they impact real
                applications.
              </p>
            </div>

            <div className="rounded-xl border border-border/40 bg-card p-6">
              <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-primary/10">
                <Users className="h-6 w-6 text-primary" />
              </div>
              <h3 className="mt-4 font-semibold">Scientific Discovery</h3>
              <p className="mt-2 text-sm text-muted-foreground">
                AI visualizations can reveal unexpected patterns in brain imaging data,
                potentially surfacing new research hypotheses and insights.
              </p>
            </div>
          </div>
        </div>

        {/* Architecture */}
        <div className="mt-24">
          <h2 className="text-2xl font-bold">Engineering Architecture</h2>

          <div className="mt-8 rounded-xl border border-border/40 bg-card p-8">
            <div className="flex items-start gap-4">
              <Code2 className="h-6 w-6 flex-shrink-0 text-primary" />
              <div>
                <h3 className="font-semibold">Modern Tech Stack</h3>
                <p className="mt-2 text-sm text-muted-foreground">
                  Built with modern, maintainable technologies: FastAPI for the backend,
                  React 18 with TypeScript for the frontend, and PyTorch for deep learning.
                  The architecture follows best practices for security, scalability, and
                  code maintainability.
                </p>
              </div>
            </div>

            <div className="mt-6 grid gap-6 md:grid-cols-2">
              <div>
                <h4 className="font-medium">Backend</h4>
                <ul className="mt-2 space-y-1 text-sm text-muted-foreground">
                  <li>• FastAPI - Async Python web framework</li>
                  <li>• PyTorch - Neural network operations</li>
                  <li>• SQLite - User & analysis records</li>
                  <li>• JWT Auth - Secure token-based auth</li>
                </ul>
              </div>
              <div>
                <h4 className="font-medium">Frontend</h4>
                <ul className="mt-2 space-y-1 text-sm text-muted-foreground">
                  <li>• React 18 - Component-based UI</li>
                  <li>• TypeScript - Type-safe code</li>
                  <li>• Tailwind CSS - Modern styling</li>
                  <li>• React Router - SPA navigation</li>
                </ul>
              </div>
            </div>
          </div>
        </div>

        {/* Contact */}
        <div id="contact" className="mt-16 text-center">
          <h2 className="text-2xl font-bold">Get in Touch</h2>
          <p className="mt-4 text-muted-foreground">
            Interested in collaborating or have questions about the platform?
          </p>
          <p className="mt-2 text-sm text-muted-foreground">
            This is an educational research project. For inquiries, please refer to
            the project documentation.
          </p>
        </div>
      </div>
    </div>
  )
}
