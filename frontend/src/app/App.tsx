import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter, NavLink, Route, Routes, useLocation } from 'react-router-dom'
import { HomePage } from '../pages/HomePage'
import { IntegrationsPage } from '../pages/IntegrationsPage'
import { PropertiesPage } from '../pages/PropertiesPage'
import { SchedulerPage } from '../pages/SchedulerPage'

const queryClient = new QueryClient()

function AppShell() {
  const location = useLocation()
  const isHome = location.pathname === '/'

  return (
    <div className="min-h-screen bg-stone-50 text-slate-950">
      {!isHome && <header className="border-b-2 border-slate-950 bg-white">
        <div className="mx-auto flex max-w-[1440px] items-center justify-between gap-5 px-4 py-4 sm:px-6 sm:py-5 lg:px-10">
          <NavLink to="/" aria-label="Voltar para a home" className="flex shrink-0 items-center gap-3 text-xl font-extrabold tracking-[-0.04em]">
            <img src="/canaan-mark.svg" alt="" aria-hidden="true" className="h-10 w-10" />
            <span>Canaan<span className="text-rose-500">.</span></span>
          </NavLink>
          <nav aria-label="Navegação principal" className="flex items-center gap-1 overflow-x-auto rounded-2xl border border-slate-200 bg-slate-50 p-1 text-sm font-bold sm:gap-2">
            <NavLink to="/imoveis" className={({ isActive }) => `whitespace-nowrap rounded-xl px-3 py-2.5 transition sm:px-4 ${isActive ? 'bg-slate-950 text-white' : 'text-slate-600 hover:bg-white hover:text-slate-950'}`}>Imóveis</NavLink>
            <NavLink to="/integracoes" className={({ isActive }) => `whitespace-nowrap rounded-xl px-3 py-2.5 transition sm:px-4 ${isActive ? 'bg-slate-950 text-white' : 'text-slate-600 hover:bg-white hover:text-slate-950'}`}>Integrações</NavLink>
            <NavLink to="/configuracoes" className={({ isActive }) => `whitespace-nowrap rounded-xl px-3 py-2.5 transition sm:px-4 ${isActive ? 'bg-slate-950 text-white' : 'text-slate-600 hover:bg-white hover:text-slate-950'}`}>Filtros</NavLink>
          </nav>
        </div>
      </header>}
      <main>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/imoveis" element={<PropertiesPage />} />
          <Route path="/integracoes" element={<IntegrationsPage />} />
          <Route path="/configuracoes" element={<SchedulerPage />} />
        </Routes>
      </main>
    </div>
  )
}

export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AppShell />
      </BrowserRouter>
    </QueryClientProvider>
  )
}
