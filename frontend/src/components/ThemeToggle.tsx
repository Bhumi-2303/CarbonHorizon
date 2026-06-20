import { useTheme } from '@/context/ThemeContext'
import { Sun, Moon, Contrast, Monitor } from 'lucide-react'

export default function ThemeToggle() {
  const { theme, setTheme } = useTheme()

  const cycleTheme = () => {
    if (theme === 'light') setTheme('dark')
    else if (theme === 'dark') setTheme('high-contrast')
    else if (theme === 'high-contrast') setTheme('system')
    else setTheme('light')
  }

  const getIcon = () => {
    switch (theme) {
      case 'light': return <Sun className="w-5 h-5" aria-hidden="true" />
      case 'dark': return <Moon className="w-5 h-5" aria-hidden="true" />
      case 'high-contrast': return <Contrast className="w-5 h-5" aria-hidden="true" />
      case 'system': return <Monitor className="w-5 h-5" aria-hidden="true" />
    }
  }

  const getLabel = () => {
    switch (theme) {
      case 'light': return 'Switch to dark mode'
      case 'dark': return 'Switch to high contrast mode'
      case 'high-contrast': return 'Switch to system theme'
      case 'system': return 'Switch to light mode'
    }
  }

  return (
    <button
      onClick={cycleTheme}
      className="p-2 rounded-full text-slate-400 hover:text-primary hover:bg-white/5 transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400"
      aria-label={getLabel()}
      title={getLabel()}
    >
      {getIcon()}
    </button>
  )
}
