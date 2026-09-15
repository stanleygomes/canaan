import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter, NavLink, Route, Routes } from 'react-router-dom'
import { PropertiesPage } from '../pages/PropertiesPage'
import { SchedulerPage } from '../pages/SchedulerPage'

const queryClient = new QueryClient()

export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <div className="min-h-screen bg-stone-50 text-slate-950">
          <header className="border-b border-slate-200 bg-white/95">
            <div className="mx-auto flex max-w-[1440px] items-center justify-between px-6 py-5 lg:px-10">
              <NavLink to="/" className="text-xl font-semibold tracking-tight">
                Canaan<span className="text-rose-500">.</span>
              </NavLink>
              <nav className="flex items-center gap-2 text-sm font-medium text-slate-500">
                <NavLink
                  to="/"
                  className={({ isActive }) =>
                    `rounded-full px-4 py-2 transition ${isActive ? 'bg-slate-950 text-white' : 'hover:bg-slate-100 hover:text-slate-950'}`
                  }
                  end
                >
                  Imóveis
                </NavLink>
                <NavLink
                  to="/configuracoes"
                  className={({ isActive }) =>
                    `rounded-full px-4 py-2 transition ${isActive ? 'bg-slate-950 text-white' : 'hover:bg-slate-100 hover:text-slate-950'}`
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
              <Route path="/configuracoes" element={<SchedulerPage />} />
            </Routes>
          </main>
        </div>
      </BrowserRouter>
    </QueryClientProvider>
  )
}
