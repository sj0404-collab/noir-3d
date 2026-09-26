import { Component, type ErrorInfo, type ReactNode } from 'react'

type Props = { children: ReactNode }
type State = { error: Error | null }

export class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null }

  static getDerivedStateFromError(error: Error): State {
    return { error }
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    const msg = `${error.message} | ${info.componentStack ?? ''}`.slice(0, 900)
    document.title = `JSERR ${msg}`
    const pre = document.createElement('pre')
    pre.id = 'diag'
    pre.style.cssText =
      'position:fixed;z-index:99;left:0;top:0;right:0;color:#f66;background:#000c;' +
      'font:12px monospace;padding:8px;white-space:pre-wrap;max-height:60vh;overflow:auto'
    pre.textContent = msg
    document.body.appendChild(pre)
    console.error('[noir3d]', error, info.componentStack)
  }

  render() {
    if (this.state.error) {
      return (
        <pre style={{ color: '#f66', background: '#000', padding: 12, font: '12px monospace' }}>
          {String(this.state.error?.stack ?? this.state.error)}
        </pre>
      )
    }
    return this.props.children
  }
}
