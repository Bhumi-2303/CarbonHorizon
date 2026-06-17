import { render, screen, act } from '@testing-library/react'
import { ThemeProvider, useTheme } from '../ThemeContext'
import { vi, describe, it, expect, beforeEach } from 'vitest'

// Mock matchMedia
const matchMediaMock = vi.fn().mockImplementation((query: string) => ({
  matches: false,
  media: query,
  onchange: null,
  addListener: vi.fn(),
  removeListener: vi.fn(),
  addEventListener: vi.fn(),
  removeEventListener: vi.fn(),
  dispatchEvent: vi.fn(),
}))
window.matchMedia = window.matchMedia || matchMediaMock

const TestComponent = () => {
  const { theme, setTheme } = useTheme()
  return (
    <div>
      <span data-testid="theme-val">{theme}</span>
      <button onClick={() => setTheme('light')} data-testid="btn-light">Light</button>
      <button onClick={() => setTheme('dark')} data-testid="btn-dark">Dark</button>
      <button onClick={() => setTheme('system')} data-testid="btn-system">System</button>
    </div>
  )
}

describe('ThemeContext', () => {
  beforeEach(() => {
    localStorage.clear()
    document.documentElement.className = ''
  })

  it('defaults to dark mode if no local storage value is present', () => {
    render(
      <ThemeProvider>
        <TestComponent />
      </ThemeProvider>
    )
    expect(screen.getByTestId('theme-val').textContent).toBe('dark')
    expect(document.documentElement.classList.contains('dark')).toBe(true)
  })

  it('toggles theme correctly and stores preference in localStorage', () => {
    render(
      <ThemeProvider>
        <TestComponent />
      </ThemeProvider>
    )

    const btnLight = screen.getByTestId('btn-light')
    act(() => {
      btnLight.click()
    })

    expect(screen.getByTestId('theme-val').textContent).toBe('light')
    expect(document.documentElement.classList.contains('light')).toBe(true)
    expect(localStorage.getItem('ch_theme')).toBe('light')
  })
})
