import s from './LoadingSpinner.module.css'

interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg'
  text?: string
  fullPage?: boolean
}

export function LoadingSpinner({ size = 'md', text, fullPage = false }: LoadingSpinnerProps) {
  const content = (
    <div className={`${s.spinner} ${s[`spinner--${size}`]}`}>
      <div className={s.spinner__circle}>
        <div className={s.spinner__inner}></div>
      </div>
      {text && <div className={s.spinner__text}>{text}</div>}
    </div>
  )

  if (fullPage) {
    return (
      <div className={s.spinner__overlay}>
        {content}
      </div>
    )
  }

  return content
}
