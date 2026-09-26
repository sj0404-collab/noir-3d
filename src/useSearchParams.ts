/** Минимальный хук чтения query-параметров (используется точечно). */
import { useMemo } from 'react'

export function useSearchParams() {
  return useMemo(() => new URLSearchParams(location.search), [])
}
