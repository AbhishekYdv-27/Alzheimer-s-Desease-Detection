import { Outlet, Link, useLocation } from 'react-router-dom'
import { useAuth } from '@/context/useAuth'
import { useTheme } from '@/context/useTheme'
import { cn } from '@/lib/utils'
import {
  Brain,
  Menu,
  X,
  Sun,
  Moon,
  Monitor,
  User,
} from 'lucide-react'
import { useState } from 'react'

const navLinks = [
  { href: '/', label: 'Home' },
  { href: '/platform', label: 'Platform' },
  { href: '/technology', label: 'Technology' },
  { href: '/research-public', label: 'Research' },
  { href: '/about', label: 'About' },
]

export function PublicLayout() {
  const { isAuthenticated } = useAuth()
  const { theme, setTheme } = useTheme()
  const location = useLocation()
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

  const themeIcon = {
    light: Sun,
    dark: Moon,
    system: Monitor,
  }[theme]

  const ThemeIcon = themeIcon

  return (
    <div className="min-h-screen bg-background">
      {/* Navigation */}
      <header className={cn('sticky top-0 z-50 w-full border-b backdrop-blur-xl', location.pathname === '/' ? 'border-white/10 bg-[#030617]/80 text-white' : 'border-border/40 bg-background/80')}>
        <nav className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-2">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary/10">
              <Brain className="h-5 w-5 text-primary" />
            </div>
            <span className="text-lg font-semibold tracking-tight">Alzheimer Desease Detection</span>
          </Link>

          {/* Desktop Nav */}
          <div className="hidden items-center gap-1 md:flex">
            {navLinks.map((link) => (
              <Link
                key={link.href}
                to={link.href}
                className={cn(
                  'relative px-4 py-2 text-sm font-medium transition-colors hover:text-primary',
                  location.pathname === link.href
                    ? 'text-primary'
                    : location.pathname === '/' ? 'text-slate-300' : 'text-muted-foreground'
                )}
              >
                {link.label}
                {location.pathname === link.href && (
                  <span className="absolute bottom-0 left-4 right-4 h-0.5 rounded-full bg-primary" />
                )}
              </Link>
            ))}
          </div>

          {/* Right side */}
          <div className="flex items-center gap-2">
            {/* Theme toggle */}
            <button
              onClick={() => setTheme(theme === 'dark' ? 'light' : theme === 'light' ? 'system' : 'dark')}
              className="flex h-9 w-9 items-center justify-center rounded-lg text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground"
            >
              <ThemeIcon className="h-4 w-4" />
            </button>

            {/* Auth buttons */}
            {isAuthenticated ? (
              <Link
                to="/dashboard"
                className="hidden items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90 md:flex"
              >
                <User className="h-4 w-4" />
                Dashboard
              </Link>
            ) : (
              <div className="hidden items-center gap-2 md:flex">
                <Link
                  to="/login"
                  className="rounded-lg px-4 py-2 text-sm font-medium text-muted-foreground transition-colors hover:text-foreground"
                >
                  Sign In
                </Link>
                <Link
                  to="/signup"
                  className="rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90"
                >
                  Get Started
                </Link>
              </div>
            )}

            {/* Mobile menu button */}
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="flex h-9 w-9 items-center justify-center rounded-lg md:hidden"
            >
              {mobileMenuOpen ? (
                <X className="h-5 w-5" />
              ) : (
                <Menu className="h-5 w-5" />
              )}
            </button>
          </div>
        </nav>

        {/* Mobile menu */}
        {mobileMenuOpen && (
          <div className="border-t border-border/40 md:hidden">
            <div className="space-y-1 px-4 py-4">
              {navLinks.map((link) => (
                <Link
                  key={link.href}
                  to={link.href}
                  onClick={() => setMobileMenuOpen(false)}
                  className={cn(
                    'flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium transition-colors',
                    location.pathname === link.href
                      ? 'bg-primary/10 text-primary'
                      : 'text-muted-foreground hover:bg-secondary hover:text-foreground'
                  )}
                >
                  {link.label}
                </Link>
              ))}
              {!isAuthenticated && (
                <div className="flex flex-col gap-2 pt-4">
                  <Link
                    to="/login"
                    onClick={() => setMobileMenuOpen(false)}
                    className="flex items-center justify-center gap-2 rounded-lg border border-border px-3 py-2 text-sm font-medium transition-colors hover:bg-secondary"
                  >
                    Sign In
                  </Link>
                  <Link
                    to="/signup"
                    onClick={() => setMobileMenuOpen(false)}
                    className="flex items-center justify-center gap-2 rounded-lg bg-primary px-3 py-2 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90"
                  >
                    Get Started
                  </Link>
                </div>
              )}
            </div>
          </div>
        )}
      </header>

      {/* Page content */}
      <main>
        <Outlet />
      </main>

      {/* Footer */}
      <footer className="border-t border-border/40 bg-secondary/30">
        <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
          <div className="grid grid-cols-2 gap-8 md:grid-cols-4">
            <div className="col-span-2 md:col-span-1">
              <Link to="/" className="flex items-center gap-2">
                <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/10">
                  <Brain className="h-4 w-4 text-primary" />
                </div>
                <span className="font-semibold">Alzheimer Desease Detection</span>
              </Link>
              <p className="mt-4 text-sm text-muted-foreground">
                AI-powered research platform for Alzheimer's Disease analysis.
              </p>
            </div>
            <div>
              <h4 className="text-sm font-semibold">Platform</h4>
              <ul className="mt-4 space-y-2 text-sm text-muted-foreground">
                <li><Link to="/platform" className="hover:text-foreground">Features</Link></li>
                <li><Link to="/technology" className="hover:text-foreground">Technology</Link></li>
                <li><Link to="/research-public" className="hover:text-foreground">Research</Link></li>
              </ul>
            </div>
            <div>
              <h4 className="text-sm font-semibold">Company</h4>
              <ul className="mt-4 space-y-2 text-sm text-muted-foreground">
                <li><Link to="/about" className="hover:text-foreground">About</Link></li>
                <li><Link to="/about#contact" className="hover:text-foreground">Contact</Link></li>
              </ul>
            </div>
            <div>
              <h4 className="text-sm font-semibold">Legal</h4>
              <ul className="mt-4 space-y-2 text-sm text-muted-foreground">
                <li><span className="hover:text-foreground cursor-pointer">Privacy Policy</span></li>
                <li><span className="hover:text-foreground cursor-pointer">Terms of Service</span></li>
                <li><span className="hover:text-foreground cursor-pointer">Medical Disclaimer</span></li>
              </ul>
            </div>
          </div>
          <div className="mt-8 flex flex-col items-center justify-between gap-4 border-t border-border/40 pt-8 text-center text-sm text-muted-foreground md:flex-row">
            <p>© 2026 Alzheimer Desease Detection. All rights reserved.</p>
            <p className="max-w-md text-xs">
              This platform is for research and educational purposes only. It is not a certified medical device.
            </p>
          </div>
        </div>
      </footer>
    </div>
  )
}
