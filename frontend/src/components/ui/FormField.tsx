/**
 * FormField.tsx — labelled input / select with error display.
 * Designed to work with React Hook Form's register() API.
 */
import React from 'react'

// ─── Common classes ───────────────────────────────────────────────────────────

const labelCls =
  'block text-sm font-medium text-slate-300 mb-1.5'

const inputCls =
  'w-full px-4 py-2.5 rounded-xl bg-slate-800/60 border border-slate-700 ' +
  'text-slate-100 placeholder-slate-500 text-sm ' +
  'focus:outline-none focus:ring-2 focus:ring-emerald-500/70 focus:border-emerald-500 ' +
  'transition-all duration-200'

const errorInputCls = 'border-red-500/70 focus:ring-red-500/50 focus:border-red-500'
const errorMsgCls   = 'mt-1 text-xs text-red-400'

// ─── Input variant ────────────────────────────────────────────────────────────

interface InputFieldProps extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'id'> {
  as?: 'input'
  label: string
  fieldId: string
  error?: string
}

// ─── Select variant ───────────────────────────────────────────────────────────

interface SelectFieldProps extends Omit<React.SelectHTMLAttributes<HTMLSelectElement>, 'id'> {
  as: 'select'
  label: string
  fieldId: string
  error?: string
  options: { value: string; label: string }[]
  placeholder?: string
}

type FormFieldProps = InputFieldProps | SelectFieldProps

// ─── Component ────────────────────────────────────────────────────────────────

export const FormField = React.forwardRef<
  HTMLInputElement | HTMLSelectElement,
  FormFieldProps
>((props, ref) => {
  if (props.as === 'select') {
    const { label, fieldId, error, options, placeholder, as: _as, ...rest } = props
    const cls = [inputCls, 'appearance-none cursor-pointer', error ? errorInputCls : ''].join(' ')
    const errorId = error ? `${fieldId}-error` : undefined
    return (
      <div>
        <label htmlFor={fieldId} className={labelCls}>
          {label}
        </label>
        <select
          id={fieldId}
          ref={ref as React.Ref<HTMLSelectElement>}
          className={cls}
          aria-invalid={error ? 'true' : 'false'}
          aria-describedby={errorId}
          {...rest}
        >
          {placeholder && (
            <option value="" className="bg-slate-800">
              {placeholder}
            </option>
          )}
          {options.map((o) => (
            <option key={o.value} value={o.value} className="bg-slate-800">
              {o.label}
            </option>
          ))}
        </select>
        {error && <p id={errorId} className={errorMsgCls} role="alert">{error}</p>}
      </div>
    )
  }

  const { label, fieldId, error, as: _as, ...rest } = props
  const cls = [inputCls, error ? errorInputCls : ''].join(' ')
  const errorId = error ? `${fieldId}-error` : undefined

  return (
    <div>
      <label htmlFor={fieldId} className={labelCls}>
        {label}
      </label>
      <input
        id={fieldId}
        ref={ref as React.Ref<HTMLInputElement>}
        className={cls}
        aria-invalid={error ? 'true' : 'false'}
        aria-describedby={errorId}
        {...rest}
      />
      {error && <p id={errorId} className={errorMsgCls} role="alert">{error}</p>}
    </div>
  )
})

FormField.displayName = 'FormField'
