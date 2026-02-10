import { type FC } from 'react'
import { Construction } from 'lucide-react'
import styles from './Placeholder.module.css'

interface PlaceholderPageProps {
  title: string
}

export const PlaceholderPage: FC<PlaceholderPageProps> = ({ title }) => (
  <div>
    <h1 style={{ fontSize: '1.57rem', fontWeight: 700, marginBottom: 24 }}>{title}</h1>
    <div className={styles.placeholder}>
      <Construction size={48} strokeWidth={1} className={styles['placeholder-icon']} />
      <span className={styles['placeholder-title']}>
        עמוד {title} בבנייה
      </span>
      <span className={styles['placeholder-text']}>
        העמוד הזה יהיה זמין בקרוב
      </span>
    </div>
  </div>
)
