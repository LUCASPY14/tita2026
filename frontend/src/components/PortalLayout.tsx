import { Outlet } from 'react-router-dom'

export default function PortalLayout() {
  return (
    <div className="min-h-screen bg-green-50">
      <header className="bg-white shadow-sm border-b border-green-100">
        <div className="max-w-4xl mx-auto px-4 py-4 flex items-center gap-3">
          <span className="text-2xl">🍽️</span>
          <span className="text-xl font-bold text-green-800">La Cantina de Tita</span>
          <span className="text-sm text-gray-400 ml-2">Portal de Padres</span>
        </div>
      </header>
      <main className="max-w-4xl mx-auto px-4 py-8">
        <Outlet />
      </main>
    </div>
  )
}