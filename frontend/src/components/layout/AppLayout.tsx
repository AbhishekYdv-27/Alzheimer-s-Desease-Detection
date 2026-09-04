import { Outlet, Link, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '@/context/AuthContext'
import { useTheme } from '@/context/ThemeContext'
import { cn } from '@/lib/utils'
import {
  Brain,
  LayoutDashboard,
  Scan,
  FolderOpen,
  BarChart3,
  FileText,
  Settings,
  LogOut,
  Sun,
  Moon,
  Monitor,
  Menu,
  X,
  ChevronLeft,
  Search,
  Bell,
} from 'lucide-react'
import { useEffect, useState } from 'react'
import { portalApi } from '@/services/api'

const patientLinks = [
  { href: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { href: '/analysis', label: 'AI Analysis', icon: Scan },
  { href: '/doctors', label: 'Find Doctors', icon: Search },
  { href: '/appointments', label: 'My Appointments', icon: FolderOpen },
  { href: '/progress', label: 'My Progress', icon: BarChart3 },
  { href: '/reports', label: 'Reports', icon: FileText },
]

const doctorLinks = [
  { href: '/doctor', label: 'Doctor Dashboard', icon: LayoutDashboard },
  { href: '/doctor/patients', label: 'Patients', icon: FolderOpen },
  { href: '/analysis', label: 'MRI Analysis', icon: Scan },
  { href: '/doctor/appointments', label: 'Appointments', icon: FileText },
  { href: '/doctor/profile', label: 'Doctor Profile', icon: Settings },
  { href: '/analytics', label: 'Patient Insights', icon: BarChart3 },
]

const bottomLinks = [
  { href: '/settings', label: 'Settings', icon: Settings },
]

export function AppLayout() {
  const { user, logout } = useAuth()
  const { theme, setTheme } = useTheme()
  const location = useLocation()
  const navigate = useNavigate()
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const [notifications, setNotifications] = useState<{ id: string; title: string; message: string; read_at?: string; created_at: string }[]>([])
  const [notificationOpen, setNotificationOpen] = useState(false)
  const sidebarLinks = user?.role === 'doctor' ? doctorLinks : patientLinks

  useEffect(() => {
    portalApi.notifications().then(setNotifications).catch(() => setNotifications([]))
  }, [user?.id])

  const unreadCount = notifications.filter(notification => !notification.read_at).length
  const markRead = async (id: string) => {
    await portalApi.markNotificationRead(id)
    setNotifications(items => items.map(item => item.id === id ? { ...item, read_at: new Date().toISOString() } : item))
  }

  const handleLogout = () => {
    logout()
    navigate('/')
  }

  const themeIcon = {
    light: Sun,
    dark: Moon,
    system: Monitor,
  }[theme]

  const ThemeIcon = themeIcon

  return (
    <div className="flex h-screen overflow-hidden bg-background">
      {/* Sidebar - Desktop */}
      <aside
        className={cn(
          'hidden border-r border-border/40 bg-card transition-all duration-300 lg:flex lg:flex-col',
          sidebarCollapsed ? 'w-16' : 'w-64'
        )}
      >
        {/* Logo */}
        <div className="flex h-16 items-center border-b border-border/40 px-4">
          <Link to="/" className="flex items-center gap-2">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary/10">
              <Brain className="h-5 w-5 text-primary" />
            </div>
            {!sidebarCollapsed && (
              <span className="text-lg font-semibold tracking-tight">Alzheimer Desease Detection</span>
            )}
          </Link>
        </div>

        {/* Nav links */}
        <nav className="flex-1 space-y-1 p-3">
          {sidebarLinks.map((link) => {
            const Icon = link.icon
            const isActive = location.pathname === link.href

            return (
              <Link
                key={link.href}
                to={link.href}
                className={cn(
                  'flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all',
                  isActive
                    ? 'bg-primary/10 text-primary'
                    : 'text-muted-foreground hover:bg-secondary hover:text-foreground'
                )}
              >
                <Icon className={cn('h-5 w-5 flex-shrink-0', sidebarCollapsed && 'mx-auto')} />
                {!sidebarCollapsed && <span>{link.label}</span>}
              </Link>
            )
          })}
        </nav>

        {/* Bottom section */}
        <div className="border-t border-border/40 p-3">
          {bottomLinks.map((link) => {
            const Icon = link.icon
            const isActive = location.pathname === link.href

            return (
              <Link
                key={link.href}
                to={link.href}
                className={cn(
                  'flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all',
                  isActive
                    ? 'bg-primary/10 text-primary'
                    : 'text-muted-foreground hover:bg-secondary hover:text-foreground'
                )}
              >
                <Icon className={cn('h-5 w-5 flex-shrink-0', sidebarCollapsed && 'mx-auto')} />
                {!sidebarCollapsed && <span>{link.label}</span>}
              </Link>
            )
          })}

          <button
            onClick={handleLogout}
            className="flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium text-muted-foreground transition-all hover:bg-destructive/10 hover:text-destructive"
          >
            <LogOut className={cn('h-5 w-5 flex-shrink-0', sidebarCollapsed && 'mx-auto')} />
            {!sidebarCollapsed && <span>Logout</span>}
          </button>
        </div>

        {/* Collapse toggle */}
        <button
          onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
          className="absolute -right-3 top-20 flex h-6 w-6 items-center justify-center rounded-full border border-border/40 bg-card shadow-sm transition-transform hover:scale-110"
        >
          <ChevronLeft
            className={cn('h-3 w-3 transition-transform', sidebarCollapsed && 'rotate-180')}
          />
        </button>
      </aside>

      {/* Main content area */}
      <div className="flex flex-1 flex-col overflow-hidden">
        {/* Top bar */}
        <header className="flex h-16 items-center justify-between border-b border-border/40 bg-card px-4 lg:px-6">
          {/* Mobile menu button */}
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="flex h-9 w-9 items-center justify-center rounded-lg lg:hidden"
          >
            <Menu className="h-5 w-5" />
          </button>

          {/* Search */}
          <div className="hidden items-center gap-2 lg:flex lg:flex-1 lg:max-w-md">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <input
                type="text"
                placeholder="Search..."
                className="h-9 w-full rounded-lg border border-border/40 bg-background pl-9 pr-4 text-sm placeholder:text-muted-foreground focus:border-primary/50 focus:outline-none focus:ring-2 focus:ring-primary/20"
              />
            </div>
          </div>

          {/* Right side */}
          <div className="flex items-center gap-2">
            <div className="relative">
              <button aria-label="Open notifications" aria-expanded={notificationOpen} onClick={() => setNotificationOpen(!notificationOpen)} className="relative flex h-9 w-9 items-center justify-center rounded-lg text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground">
                <Bell className="h-4 w-4" />
                {unreadCount > 0 && <span className="absolute right-1 top-1 flex h-4 min-w-4 items-center justify-center rounded-full bg-primary px-1 text-[10px] text-primary-foreground">{unreadCount}</span>}
              </button>
              {notificationOpen && <div role="dialog" aria-label="Notifications" className="fixed inset-x-4 top-16 z-40 w-auto max-w-none rounded-xl border border-border/40 bg-card p-3 shadow-xl sm:absolute sm:inset-x-auto sm:right-0 sm:top-11 sm:w-[calc(100vw-2rem)] sm:max-w-sm">
                <div className="flex items-center justify-between px-2 pb-2"><h2 className="font-semibold">Notifications</h2><span className="text-xs text-muted-foreground">{unreadCount} unread</span></div>
                <div className="max-h-80 space-y-1 overflow-auto">{notifications.length === 0 ? <p className="px-2 py-6 text-center text-sm text-muted-foreground">You are all caught up.</p> : notifications.map(notification => <button key={notification.id} onClick={() => !notification.read_at && markRead(notification.id)} className={cn('w-full rounded-lg p-2 text-left transition-colors hover:bg-secondary', !notification.read_at && 'bg-primary/5')}><p className="text-sm font-medium">{notification.title}</p><p className="mt-1 text-xs text-muted-foreground">{notification.message}</p><p className="mt-1 text-[11px] text-muted-foreground">{new Date(notification.created_at).toLocaleString()}</p></button>)}</div>
              </div>}
            </div>
            <button
              onClick={() => setTheme(theme === 'dark' ? 'light' : theme === 'light' ? 'system' : 'dark')}
              className="flex h-9 w-9 items-center justify-center rounded-lg text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground"
            >
              <ThemeIcon className="h-4 w-4" />
            </button>

            <div className="hidden items-center gap-3 lg:flex">
              <div className="flex h-9 w-9 items-center justify-center rounded-full bg-primary/10 text-sm font-medium text-primary">
                {user?.name?.charAt(0).toUpperCase() || 'U'}
              </div>
              <div className="text-sm">
                <p className="font-medium">{user?.name || 'User'}</p>
                <p className="text-xs text-muted-foreground">{user?.email || ''}</p>
              </div>
            </div>
          </div>
        </header>

        {/* Mobile sidebar overlay */}
        {mobileMenuOpen && (
          <div className="fixed inset-0 z-50 lg:hidden">
            <div
              className="absolute inset-0 bg-black/50"
              onClick={() => setMobileMenuOpen(false)}
            />
            <aside className="absolute inset-y-0 left-0 w-64 border-r border-border/40 bg-card p-4">
              <div className="flex h-10 items-center justify-between">
                <Link to="/" className="flex items-center gap-2">
                  <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/10">
                    <Brain className="h-4 w-4 text-primary" />
                  </div>
                  <span className="font-semibold">Alzheimer Desease Detection</span>
                </Link>
                <button onClick={() => setMobileMenuOpen(false)}>
                  <X className="h-5 w-5" />
                </button>
              </div>

              <nav className="mt-6 space-y-1">
                {sidebarLinks.map((link) => {
                  const Icon = link.icon
                  const isActive = location.pathname === link.href

                  return (
                    <Link
                      key={link.href}
                      to={link.href}
                      onClick={() => setMobileMenuOpen(false)}
                      className={cn(
                        'flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all',
                        isActive
                          ? 'bg-primary/10 text-primary'
                          : 'text-muted-foreground hover:bg-secondary hover:text-foreground'
                      )}
                    >
                      <Icon className="h-5 w-5" />
                      <span>{link.label}</span>
                    </Link>
                  )
                })}
              </nav>

              <div className="absolute bottom-4 left-4 right-4 space-y-1">
                {bottomLinks.map((link) => {
                  const Icon = link.icon
                  const isActive = location.pathname === link.href

                  return (
                    <Link
                      key={link.href}
                      to={link.href}
                      onClick={() => setMobileMenuOpen(false)}
                      className={cn(
                        'flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all',
                        isActive
                          ? 'bg-primary/10 text-primary'
                          : 'text-muted-foreground hover:bg-secondary hover:text-foreground'
                      )}
                    >
                      <Icon className="h-5 w-5" />
                      <span>{link.label}</span>
                    </Link>
                  )
                })}

                <button
                  onClick={handleLogout}
                  className="flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium text-muted-foreground transition-all hover:bg-destructive/10 hover:text-destructive"
                >
                  <LogOut className="h-5 w-5" />
                  <span>Logout</span>
                </button>
              </div>
            </aside>
          </div>
        )}

        {/* Page content */}
        <main className="flex-1 overflow-auto p-4 lg:p-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
