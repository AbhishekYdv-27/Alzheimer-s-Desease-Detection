import { useEffect, useState } from 'react'
import { useAuth } from '@/context/AuthContext'
import { useTheme } from '@/context/ThemeContext'
import { authApi } from '@/services/api'
import { User, Palette, Lock, Sun, Moon, Monitor, Loader2 } from 'lucide-react'

export default function SettingsPage() {
  const { user, updateUser } = useAuth()
  const { theme, setTheme } = useTheme()
  const [name, setName] = useState(user?.name || '')
  const [isSaving, setIsSaving] = useState(false)
  const [message, setMessage] = useState('')
  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [passwordMessage, setPasswordMessage] = useState('')

  useEffect(() => {
    if (user?.name) setName(user.name)
  }, [user?.name])

  const handleSave = async () => {
    setIsSaving(true)
    setMessage('')
    try {
      const updatedUser = await authApi.updateMe(name)
      updateUser(updatedUser)
      setMessage('Profile saved successfully')
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'Unable to save profile')
    } finally {
      setIsSaving(false)
    }
  }

  const handlePasswordSave = async () => {
    setIsSaving(true)
    setPasswordMessage('')
    if (newPassword !== confirmPassword) {
      setPasswordMessage('New passwords do not match')
      setIsSaving(false)
      return
    }
    try {
      await authApi.updatePassword(currentPassword, newPassword)
      setCurrentPassword('')
      setNewPassword('')
      setConfirmPassword('')
      setPasswordMessage('Password updated successfully')
    } catch (error) {
      setPasswordMessage(error instanceof Error ? error.message : 'Unable to update password')
    } finally {
      setIsSaving(false)
    }
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold">Settings</h1>
        <p className="mt-1 text-muted-foreground">Manage your account and application preferences</p>
      </div>

      <div className="rounded-xl border border-border/40 bg-card p-6">
        <div className="flex items-center gap-3"><User className="h-5 w-5 text-primary" /><h2 className="font-semibold">Profile Settings</h2></div>
        <div className="mt-6 space-y-4">
          <div><label className="block text-sm font-medium">Name</label><input type="text" value={name} onChange={(e) => setName(e.target.value)} className="mt-1 block w-full rounded-lg border border-border/40 bg-background px-4 py-2.5 text-sm" /></div>
          <div><label className="block text-sm font-medium">Email</label><input type="email" value={user?.email || ''} disabled className="mt-1 block w-full rounded-lg border border-border/40 bg-secondary px-4 py-2.5 text-sm text-muted-foreground" /></div>
        </div>
        <button onClick={handleSave} disabled={isSaving} className="mt-6 flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground disabled:opacity-50">{isSaving && <Loader2 className="h-4 w-4 animate-spin" />}Save Changes</button>
        {message && <p className="mt-3 text-sm text-muted-foreground">{message}</p>}
      </div>

      <div className="rounded-xl border border-border/40 bg-card p-6">
        <div className="flex items-center gap-3"><Palette className="h-5 w-5 text-primary" /><h2 className="font-semibold">Appearance</h2></div>
        <div className="mt-6"><label className="mb-3 block text-sm font-medium">Theme</label><div className="grid grid-cols-3 gap-3">
          {[{ value: 'light', label: 'Light', icon: Sun }, { value: 'dark', label: 'Dark', icon: Moon }, { value: 'system', label: 'System', icon: Monitor }].map((option) => { const Icon = option.icon; return <button key={option.value} onClick={() => setTheme(option.value as 'light' | 'dark' | 'system')} className={`flex flex-col items-center gap-2 rounded-lg border p-4 ${theme === option.value ? 'border-primary bg-primary/5' : 'border-border/40'}`}><Icon className="h-5 w-5" /><span className="text-sm font-medium">{option.label}</span></button> })}
        </div></div>
      </div>

      <div className="rounded-xl border border-border/40 bg-card p-6">
        <div className="flex items-center gap-3"><Lock className="h-5 w-5 text-primary" /><h2 className="font-semibold">Security</h2></div>
        <div className="mt-6 space-y-4">
          <div><label className="block text-sm font-medium">Current Password</label><input type="password" value={currentPassword} onChange={(e) => setCurrentPassword(e.target.value)} className="mt-1 block w-full rounded-lg border border-border/40 bg-background px-4 py-2.5 text-sm" /></div>
          <div><label className="block text-sm font-medium">New Password</label><input type="password" minLength={6} value={newPassword} onChange={(e) => setNewPassword(e.target.value)} className="mt-1 block w-full rounded-lg border border-border/40 bg-background px-4 py-2.5 text-sm" /></div>
          <div><label className="block text-sm font-medium">Confirm New Password</label><input type="password" value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} className="mt-1 block w-full rounded-lg border border-border/40 bg-background px-4 py-2.5 text-sm" /></div>
        </div>
        <button onClick={handlePasswordSave} disabled={isSaving} className="mt-6 flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground disabled:opacity-50">{isSaving && <Loader2 className="h-4 w-4 animate-spin" />}Update Password</button>
        {passwordMessage && <p className="mt-3 text-sm text-muted-foreground">{passwordMessage}</p>}
      </div>
    </div>
  )
}
