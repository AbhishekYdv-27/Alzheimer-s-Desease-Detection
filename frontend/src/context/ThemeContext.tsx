import { useEffect, useState, ReactNode } from 'react'
import { ThemeContext } from './theme-context'
import { Theme } from '@/types'

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [theme, setTheme] = useState<Theme>(() => {
    const stored = localStorage.getItem('theme') as Theme
    return stored || 'system'
  })

  const [resolvedTheme, setResolvedTheme] = useState<'light' | 'dark'>('light')

  useEffect(() => {
    const root = document.documentElement

    const updateTheme = () => {
      let resolved: 'light' | 'dark'

      if (theme === 'system') {
        resolved = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
      } else {
        resolved = theme
      }

      root.classList.remove('light', 'dark')
      root.classList.add(resolved)
      setResolvedTheme(resolved)
    }

    updateTheme()

    localStorage.setItem('theme', theme)

    if (theme === 'system') {
      const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
      const handler = () => updateTheme()
      mediaQuery.addEventListener('change', handler)
      return () => mediaQuery.removeEventListener('change', handler)
    }
  }, [theme])

  return (
    <ThemeContext.Provider value={{ theme, setTheme, resolvedTheme }}>
      {children}
    </ThemeContext.Provider>
  )
}