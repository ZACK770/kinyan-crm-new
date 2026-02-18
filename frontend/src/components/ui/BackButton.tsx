import { ArrowRight } from 'lucide-react'
import s from '@/styles/shared.module.css'

interface BackButtonProps {
  onClick: () => void
  label?: string
}

export function BackButton({ onClick, label = 'חזרה לרשימה' }: BackButtonProps) {
  return (
    <button
      className={`${s.btn} ${s['btn-ghost']} ${s['back-btn']}`}
      onClick={onClick}
    >
      <ArrowRight size={16} strokeWidth={2} />
      {label}
    </button>
  )
}
