import { lazy, Suspense } from 'react'
import App from './App.jsx'

// Verificación pública de comprobantes de Tesorería (al escanear el QR); no requiere iniciar sesión
// (El QR de las boletas abre public/boleta.html, una página liviana fuera de esta app)
const params = new URLSearchParams(window.location.search)
const isPublicVerification = params.has('recibo') || params.has('estado-cuenta')
const PublicVerification = lazy(() => import('./modules/finances/PublicVerification.jsx'))

export default function AppRoot() {
  return isPublicVerification ? (
    <Suspense fallback={null}>
      <PublicVerification />
    </Suspense>
  ) : (
    <App />
  )
}
