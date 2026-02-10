import { Component, type ReactNode, type ErrorInfo } from 'react'

interface Props {
  children: ReactNode
  fallback?: ReactNode
}

interface State {
  hasError: boolean
  error: Error | null
}

/**
 * Error Boundary - catches React errors and shows a friendly fallback UI
 * instead of crashing the entire app with an infinite loop
 */
export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    // Log error to console with details (could send to monitoring service)
    console.error('[ErrorBoundary] Caught error:', error)
    console.error('[ErrorBoundary] Component stack:', errorInfo.componentStack)
  }

  handleRetry = () => {
    this.setState({ hasError: false, error: null })
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback
      }

      return (
        <div style={{
          padding: '40px',
          textAlign: 'center',
          direction: 'rtl',
          fontFamily: 'system-ui, sans-serif'
        }}>
          <div style={{
            background: 'var(--color-bg-secondary, #fef2f2)',
            border: '1px solid var(--color-error, #ef4444)',
            borderRadius: '8px',
            padding: '24px',
            maxWidth: '500px',
            margin: '0 auto'
          }}>
            <h2 style={{ 
              color: 'var(--color-error, #dc2626)', 
              margin: '0 0 12px 0',
              fontSize: '1.25rem'
            }}>
              אירעה שגיאה
            </h2>
            <p style={{ 
              color: 'var(--color-text-secondary, #666)', 
              margin: '0 0 16px 0' 
            }}>
              משהו השתבש בטעינת העמוד. ניתן לנסות שוב או לרענן את הדף.
            </p>
            {this.state.error && (
              <details style={{
                textAlign: 'left',
                direction: 'ltr',
                background: 'var(--color-bg-primary, #fff)',
                borderRadius: '4px',
                padding: '8px 12px',
                marginBottom: '16px',
                fontSize: '0.85rem',
                color: '#666'
              }}>
                <summary style={{ cursor: 'pointer', marginBottom: '8px' }}>
                  Technical details
                </summary>
                <pre style={{
                  margin: 0,
                  whiteSpace: 'pre-wrap',
                  wordBreak: 'break-word'
                }}>
                  {this.state.error.message}
                </pre>
              </details>
            )}
            <div style={{ display: 'flex', gap: '12px', justifyContent: 'center' }}>
              <button
                onClick={this.handleRetry}
                style={{
                  padding: '8px 20px',
                  background: 'var(--color-primary, #2563eb)',
                  color: 'white',
                  border: 'none',
                  borderRadius: '6px',
                  cursor: 'pointer',
                  fontSize: '0.9rem'
                }}
              >
                נסה שוב
              </button>
              <button
                onClick={() => window.location.reload()}
                style={{
                  padding: '8px 20px',
                  background: 'transparent',
                  color: 'var(--color-text-primary, #333)',
                  border: '1px solid var(--color-border, #ddd)',
                  borderRadius: '6px',
                  cursor: 'pointer',
                  fontSize: '0.9rem'
                }}
              >
                רענן דף
              </button>
            </div>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}
