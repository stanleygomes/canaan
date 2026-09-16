import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter, NavLink, Route, Routes } from 'react-router-dom'
import { PropertiesPage } from '../pages/PropertiesPage'
import { PropertyDetailPage } from '../pages/PropertyDetailPage'
import { SchedulerPage } from '../pages/SchedulerPage'

const queryClient = new QueryClient()

export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <div className="min-h-screen bg-stone-50 text-slate-950">
          <header className="border-b border-slate-200 bg-white/95">
            <div className="mx-auto flex max-w-[1440px] items-center justify-between gap-4 px-4 py-4 sm:px-6 sm:py-5 lg:px-10">
              <NavLink to="/" className="flex items-center gap-2 text-xl font-semibold tracking-tight">
                <img src="/canaan-mark.svg" alt="" aria-hidden="true" className="h-8 w-8" />
                <span>Canaan<span className="text-rose-500">.</span></span>
              </NavLink>
              <nav className="flex items-center gap-1 text-xs font-medium text-slate-500 sm:gap-2 sm:text-sm">
                <NavLink
                  to="/"
                  className={({ isActive }) =>
                    `rounded-full px-3 py-2 transition sm:px-4 ${isActive ? 'bg-slate-950 text-white' : 'hover:bg-slate-100 hover:text-slate-950'}`
                  }
                  end
                >
                  Imóveis
                </NavLink>
                <NavLink
                  to="/configuracoes"
                  className={({ isActive }) =>
                    `rounded-full px-3 py-2 transition sm:px-4 ${isActive ? 'bg-slate-950 text-white' : 'hover:bg-slate-100 hover:text-slate-950'}`
                  }
                >
                  Automação
                </NavLink>
              </nav>
            </div>
          </header>
          <main>
            <Routes>
              <Route path="/" element={<PropertiesPage />} />
              <Route path="/imoveis/:propertyId" element={<PropertyDetailPage />} />
              <Route path="/configuracoes" element={<SchedulerPage />} />
            </Routes>
          </main>
        </div>
      </BrowserRouter>
    </QueryClientProvider>
  )
}
