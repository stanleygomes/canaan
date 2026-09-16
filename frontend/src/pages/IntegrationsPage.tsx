import { useMemo } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { listScrapeRuns, startScrape } from '../lib/api/search'
import type { ScrapeRun } from '../lib/api/types'

function formatDate(value: string | null) {
  if (!value) return '—'
  return new Intl.DateTimeFormat('pt-BR', { dateStyle: 'short', timeStyle: 'short' }).format(new Date(value))
}

function statusLabel(status: ScrapeRun['status']) {
  return { running: 'Em andamento', completed: 'Concluída', failed: 'Falhou' }[status]
}

function statusClass(status: ScrapeRun['status']) {
  return { running: 'bg-amber-50 text-amber-700', completed: 'bg-emerald-50 text-emerald-700', failed: 'bg-rose-50 text-rose-700' }[status]
}

export function IntegrationsPage() {
  const queryClient = useQueryClient()
  const query = useQuery({
    queryKey: ['scrape-runs', 1, 20],
    queryFn: () => listScrapeRuns(1, 20),
    refetchInterval: (current) => current.state.data?.items.some((run) => run.status === 'running') ? 3000 : false,
  })
  const runMutation = useMutation({
    mutationFn: () => startScrape(),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['scrape-runs'] }),
  })
  const running = useMemo(() => query.data?.items.some((run) => run.status === 'running') ?? false, [query.data])

  return (
    <div className="mx-auto max-w-5xl px-4 py-8 sm:px-6 sm:py-12 lg:px-10">
      <section className="flex flex-col justify-between gap-6 border-b border-slate-200 pb-8 sm:flex-row sm:items-end">
        <div>
          <p className="mb-2 text-sm font-semibold uppercase tracking-[0.18em] text-rose-500">Integrações</p>
          <h1 className="text-3xl font-semibold tracking-[-0.04em] sm:text-4xl">Histórico de coletas.</h1>
          <p className="mt-3 max-w-xl leading-7 text-slate-500">Acompanhe as execuções dos scrapers e veja quando os anúncios foram atualizados.</p>
        </div>
        <button type="button" className="button-primary whitespace-nowrap" disabled={runMutation.isPending || running} onClick={() => runMutation.mutate()}>
          {runMutation.isPending ? 'Iniciando...' : running ? 'Coleta em andamento' : 'Disparar coleta agora'}
        </button>
      </section>

      {runMutation.isError && <p className="mt-6 rounded-xl bg-rose-50 p-4 text-sm text-rose-700">Não foi possível iniciar a coleta. Tente novamente.</p>}
      {query.isLoading && <p className="py-12 text-center text-slate-500">Carregando histórico...</p>}
      {query.isError && <p className="mt-8 rounded-xl bg-rose-50 p-4 text-sm text-rose-700">Não foi possível carregar o histórico.</p>}
      {!query.isLoading && !query.isError && query.data?.items.length === 0 && <p className="mt-8 rounded-2xl border border-dashed border-slate-300 p-10 text-center text-slate-500">Nenhuma execução registrada ainda.</p>}

      <div className="mt-8 space-y-3">
        {query.data?.items.map((run) => (
          <article key={run.run_id} className="rounded-2xl border border-slate-200 bg-white p-5 transition hover:border-slate-400">
            <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
              <div>
                <div className="flex flex-wrap items-center gap-3">
                  <h2 className="font-semibold text-slate-950">Coleta {run.source === 'all' ? 'completa' : run.source}</h2>
                  <span className={`rounded-full px-3 py-1 text-xs font-semibold ${statusClass(run.status)}`}>{statusLabel(run.status)}</span>
                </div>
                <p className="mt-2 text-sm text-slate-500">Iniciada em {formatDate(run.started_at)} · Finalizada em {formatDate(run.finished_at)}</p>
              </div>
              <p className="text-sm font-semibold text-slate-700">{run.properties_count ?? '—'} imóveis processados</p>
            </div>
            {run.error && <p className="mt-4 rounded-lg bg-rose-50 p-3 text-sm text-rose-700">{run.error}</p>}
            <p className="mt-3 truncate text-xs text-slate-400" title={run.run_id}>ID: {run.run_id}</p>
          </article>
        ))}
      </div>
    </div>
  )
}
