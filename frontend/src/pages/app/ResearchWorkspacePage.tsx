import { FlaskConical, GitBranch, Database, Activity } from 'lucide-react'

export default function ResearchWorkspacePage() {
  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold">Research Workspace</h1>
        <p className="mt-1 text-muted-foreground">
          Experiment tracking and research management
        </p>
      </div>

      {/* Experiment Status */}
      <div className="grid gap-4 md:grid-cols-3">
        <div className="rounded-xl border border-border/40 bg-card p-6">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-orange-500/10">
              <GitBranch className="h-5 w-5 text-orange-500" />
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Experiments</p>
              <p className="text-2xl font-bold">0</p>
            </div>
          </div>
        </div>

        <div className="rounded-xl border border-border/40 bg-card p-6">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
              <Activity className="h-5 w-5 text-primary" />
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Completed</p>
              <p className="text-2xl font-bold">0</p>
            </div>
          </div>
        </div>

        <div className="rounded-xl border border-border/40 bg-card p-6">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-purple-500/10">
              <Database className="h-5 w-5 text-purple-500" />
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Dataset Version</p>
              <p className="text-lg font-bold">Not Connected</p>
            </div>
          </div>
        </div>
      </div>

      {/* Empty State */}
      <div className="flex flex-col items-center justify-center rounded-xl border border-border/40 bg-card py-16">
        <div className="flex h-20 w-20 items-center justify-center rounded-full bg-secondary">
          <FlaskConical className="h-10 w-10 text-muted-foreground" />
        </div>
        <p className="mt-4 font-medium">No completed experiments</p>
        <p className="mt-1 text-sm text-muted-foreground">
          Experiment results will appear here after running training
        </p>
      </div>

      {/* Experiment Info */}
      <div className="rounded-xl border border-border/40 bg-card p-6">
        <h3 className="font-semibold">Experiment Tracking</h3>
        <p className="mt-1 text-sm text-muted-foreground">
          Track and compare model training experiments
        </p>

        <div className="mt-6 space-y-3">
          {[
            { name: 'ResNet50 provenance review', status: 'Not verified' },
            { name: 'Swin Transformer training', status: 'Not configured' },
            { name: 'Ensemble experiment', status: 'Not configured' },
          ].map((exp) => (
            <div
              key={exp.name}
              className="flex items-center justify-between rounded-lg border border-border/40 bg-secondary/30 p-4"
            >
              <span className="font-medium">{exp.name}</span>
              <span className="rounded bg-orange-500/10 px-2 py-0.5 text-xs font-medium text-orange-600">
                {exp.status}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Disclaimer */}
      <div className="rounded-lg border border-orange-500/30 bg-orange-500/10 p-4">
        <p className="text-xs text-orange-600 dark:text-orange-400">
          <strong>Note:</strong> The local ResNet50 checkpoint loads for a synthetic
          software smoke test, but its provenance and training history are unverified.
          No real-MRI evaluation has been run.
        </p>
      </div>
    </div>
  )
}
