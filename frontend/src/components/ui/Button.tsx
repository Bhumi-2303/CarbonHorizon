import React from 'react'

type ButtonVariant = 'primary' | 'secondary' | 'ghost' | 'danger'

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className = '', variant = 'primary', disabled, children, ...props }, ref) => {
    
    // Base classes for all buttons
    const baseCls = 'inline-flex items-center justify-center font-semibold rounded-xl px-4 py-2 transition-all duration-200 focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-offset-bg-primary'
    
    // Disabled classes (shared everywhere a button is disabled)
    // We use a slight desaturation approach via slate colors and opacity reduction.
    const disabledCls = 'disabled:opacity-50 disabled:cursor-not-allowed disabled:border-slate-600 disabled:text-slate-400 disabled:hover:bg-transparent'

    const variantStyles: Record<ButtonVariant, string> = {
      primary: 'bg-accent text-bg-primary hover:bg-accent/90 focus-visible:ring-accent',
      secondary: 'glass-panel border-white/20 text-primary hover:bg-white/10 focus-visible:ring-accent',
      ghost: 'bg-transparent text-primary hover:bg-white/10 focus-visible:ring-white/20',
      danger: 'glass-panel border-danger text-danger hover:bg-danger/10 focus-visible:ring-danger',
    }

    return (
      <button
        ref={ref}
        disabled={disabled}
        className={`${baseCls} ${variantStyles[variant]} ${disabledCls} ${className}`}
        {...props}
      >
        {children}
      </button>
    )
  }
)

Button.displayName = 'Button'
