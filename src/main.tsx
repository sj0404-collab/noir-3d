import { createRoot } from 'react-dom/client'
import App from './App.tsx'
import { ErrorBoundary } from './ErrorBoundary'

// Диагностика для headless-рендера: любая ошибка попадает в title и в #diag,
// их можно прочитать через chromium --dump-dom.
window.addEventListener('error', (e) => {
  document.title = `JSERR ${e.message}`
})
window.addEventListener('unhandledrejection', (e) => {
  document.title = `JSREJ ${String(e.reason).slice(0, 300)}`
})

createRoot(document.getElementById('root')!).render(
  <ErrorBoundary>
    <App />
  </ErrorBoundary>,
)
