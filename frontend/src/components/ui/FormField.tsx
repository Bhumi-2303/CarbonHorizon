/**
 * FormField.tsx — labelled input / select / textarea with error display.
 * Designed to work with React Hook Form's register() API.
 */
import React from 'react'
import { ChevronUp, ChevronDown } from 'lucide-react'

// ─── Common classes ───────────────────────────────────────────────────────────

const labelCls = 'block text-sm font-medium text-white mb-1.5'

// Using glass background, visible border, accent focus ring, near-white text (text-white)
// Disabled state matches Button.tsx
const inputCls =
  'w-full px-4 py-2.5 rounded-xl bg-white/5 border border-white/20 ' +
  'text-white placeholder-muted text-sm ' +
  'focus:outline-none focus:ring-2 focus:ring-accent focus:border-accent focus:bg-white/10 ' +
  'disabled:opacity-50 disabled:cursor-not-allowed disabled:border-slate-600 disabled:text-slate-400 ' +
  'transition-all duration-200'

const errorInputCls = 'border-danger focus:ring-danger focus:border-danger'
const errorMsgCls   = 'mt-1 text-xs text-danger'

// ─── Input variant ────────────────────────────────────────────────────────────

interface InputFieldProps extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'id'> {
  as?: 'input'
  label: string
  fieldId: string
  error?: string
  hint?: string
}

// ─── Select variant ───────────────────────────────────────────────────────────

interface SelectFieldProps extends Omit<React.SelectHTMLAttributes<HTMLSelectElement>, 'id'> {
  as: 'select'
  label: string
  fieldId: string
  error?: string
  hint?: string
  options: { value: string; label: string; disabled?: boolean; title?: string }[]
  placeholder?: string
}

// ─── TextArea variant ─────────────────────────────────────────────────────────

interface TextAreaFieldProps extends Omit<React.TextareaHTMLAttributes<HTMLTextAreaElement>, 'id'> {
  as: 'textarea'
  label: string
  fieldId: string
  error?: string
  hint?: string
}

type FormFieldProps = InputFieldProps | SelectFieldProps | TextAreaFieldProps

// ─── Component ────────────────────────────────────────────────────────────────

export const FormField = React.forwardRef<
  HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement,
  FormFieldProps
>((props, ref) => {
  if (props.as === 'select') {
    const { label, fieldId, error, hint, options, placeholder, as: _as, className = '', onChange, ...rest } = props
    const cls = [inputCls, 'appearance-none cursor-pointer data-[chosen=false]:text-muted', error ? errorInputCls : '', className].join(' ')
    const errorId = error ? `${fieldId}-error` : undefined
    const hintId = hint ? `${fieldId}-hint` : undefined
    
    // We use a local state to track if a valid option is selected to style the placeholder differently
    const isChosenInitial = rest.value !== undefined ? rest.value !== '' : (rest.defaultValue !== undefined ? rest.defaultValue !== '' : false);
    const [chosen, setChosen] = React.useState(isChosenInitial);

    const handleChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
      setChosen(e.target.value !== '')
      if (onChange) onChange(e)
    }

    return (
      <div>
        <label htmlFor={fieldId} className={labelCls}>
          {label}
        </label>
        <div className="relative">
          <select
            id={fieldId}
            ref={ref as React.Ref<HTMLSelectElement>}
            className={cls}
            aria-invalid={error ? 'true' : 'false'}
            aria-describedby={errorId}
            onChange={handleChange}
            data-chosen={chosen ? 'true' : 'false'}
            {...rest}
          >
            {placeholder && (
              <option value="" disabled className="bg-bg-primary text-muted">
                {placeholder}
              </option>
            )}
            {options.map((o) => (
              <option 
                key={o.value} 
                value={o.value} 
                className="bg-bg-primary text-white disabled:text-slate-500"
                disabled={o.disabled}
                title={o.title}
              >
                {o.label}
              </option>
            ))}
          </select>
          <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-4 text-slate-400">
            <ChevronDown className="w-4 h-4" />
          </div>
        </div>
        {hint && !error && <p id={hintId} className="mt-1 text-xs text-muted">{hint}</p>}
        {error && <p id={errorId} className={errorMsgCls} role="alert">{error}</p>}
      </div>
    )
  }

  if (props.as === 'textarea') {
    const { label, fieldId, error, hint, as: _as, className = '', ...rest } = props
    const cls = [inputCls, 'resize-y min-h-[100px]', error ? errorInputCls : '', className].join(' ')
    const errorId = error ? `${fieldId}-error` : undefined
    const hintId = hint ? `${fieldId}-hint` : undefined
    return (
      <div>
        <label htmlFor={fieldId} className={labelCls}>
          {label}
        </label>
        <textarea
          id={fieldId}
          ref={ref as React.Ref<HTMLTextAreaElement>}
          className={cls}
          aria-invalid={error ? 'true' : 'false'}
          aria-describedby={errorId}
          {...rest}
        />
        {hint && !error && <p id={hintId} className="mt-1 text-xs text-muted">{hint}</p>}
        {error && <p id={errorId} className={errorMsgCls} role="alert">{error}</p>}
      </div>
    )
  }

  const { label, fieldId, error, hint, as: _as, className = '', type, ...rest } = props
  const cls = [inputCls, error ? errorInputCls : '', className].join(' ')
  const errorId = error ? `${fieldId}-error` : undefined
  const hintId = hint ? `${fieldId}-hint` : undefined

  // Number input custom spinner logic
  const internalRef = React.useRef<HTMLInputElement | null>(null)
  
  const setRefs = React.useCallback(
    (node: HTMLInputElement) => {
      internalRef.current = node
      if (typeof ref === 'function') {
        ref(node)
      } else if (ref) {
        (ref as React.MutableRefObject<HTMLInputElement | null>).current = node
      }
    },
    [ref]
  )

  const handleIncrement = (e: React.MouseEvent) => {
    e.preventDefault()
    if (internalRef.current) {
      internalRef.current.stepUp()
      internalRef.current.dispatchEvent(new Event('input', { bubbles: true }))
      internalRef.current.dispatchEvent(new Event('change', { bubbles: true }))
    }
  }

  const handleDecrement = (e: React.MouseEvent) => {
    e.preventDefault()
    if (internalRef.current) {
      internalRef.current.stepDown()
      internalRef.current.dispatchEvent(new Event('input', { bubbles: true }))
      internalRef.current.dispatchEvent(new Event('change', { bubbles: true }))
    }
  }

  if (type === 'number') {
    return (
      <div>
        <label htmlFor={fieldId} className={labelCls}>
          {label}
        </label>
        <div className="relative">
          <input
            id={fieldId}
            ref={setRefs}
            type="number"
            className={cls + " pr-10"}
            aria-invalid={error ? 'true' : 'false'}
            aria-describedby={errorId}
            {...rest}
          />
          <div className="absolute right-2 top-0 bottom-0 flex flex-col justify-center gap-0.5">
            <button 
              type="button" 
              onClick={handleIncrement} 
              className="p-0.5 text-muted hover:text-accent transition-colors disabled:opacity-50"
              disabled={rest.disabled}
              tabIndex={-1}
              aria-label="Increase"
            >
              <ChevronUp className="w-3.5 h-3.5" />
            </button>
            <button 
              type="button" 
              onClick={handleDecrement} 
              className="p-0.5 text-muted hover:text-accent transition-colors disabled:opacity-50"
              disabled={rest.disabled}
              tabIndex={-1}
              aria-label="Decrease"
            >
              <ChevronDown className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
        {hint && !error && <p id={hintId} className="mt-1 text-xs text-muted">{hint}</p>}
        {error && <p id={errorId} className={errorMsgCls} role="alert">{error}</p>}
      </div>
    )
  }

  return (
    <div>
      <label htmlFor={fieldId} className={labelCls}>
        {label}
      </label>
      <input
        id={fieldId}
        ref={ref as React.Ref<HTMLInputElement>}
        type={type}
        className={cls}
        aria-invalid={error ? 'true' : 'false'}
        aria-describedby={errorId}
        {...rest}
      />
      {hint && !error && <p id={hintId} className="mt-1 text-xs text-muted">{hint}</p>}
      {error && <p id={errorId} className={errorMsgCls} role="alert">{error}</p>}
    </div>
  )
})

FormField.displayName = 'FormField'
