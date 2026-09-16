import { Link } from 'react-router-dom'

const destinations = [
  { to: '/imoveis', eyebrow: 'Explorar', title: 'Imóveis', description: 'Encontre anúncios, compare atributos e abra o imóvel no portal de origem.', accent: 'bg-rose-500' },
  { to: '/integracoes', eyebrow: 'Monitorar', title: 'Integrações', description: 'Acompanhe o histórico das coletas e dispare uma nova execução.', accent: 'bg-slate-950' },
  { to: '/configuracoes', eyebrow: 'Configurar', title: 'Filtros', description: 'Defina cidade, finalidade, faixa de preço e fontes da sua busca.', accent: 'bg-amber-400' },
]

export function HomePage() {
  return (
    <div className="mx-auto flex min-h-[calc(100vh-5rem)] max-w-6xl flex-col justify-center px-4 py-12 sm:px-6 lg:px-10">
      <section className="text-center">
        <img src="/canaan-mark.svg" alt="Canaan" className="mx-auto h-24 w-24 sm:h-28 sm:w-28" />
        <p className="mt-8 text-sm font-semibold uppercase tracking-[0.22em] text-rose-500">Busca inteligente</p>
        <h1 className="mt-3 text-4xl font-semibold tracking-[-0.05em] text-slate-950 sm:text-6xl">Canaan<span className="text-rose-500">.</span></h1>
        <p className="mx-auto mt-5 max-w-xl text-base leading-7 text-slate-500 sm:text-lg">Seu centro de busca imobiliária: anúncios reunidos, coletas monitoradas e filtros sob seu controle.</p>
      </section>

      <nav aria-label="Acessos principais" className="mt-12 grid gap-4 md:grid-cols-3">
        {destinations.map((destination) => (
          <Link key={destination.to} to={destination.to} className="group rounded-3xl border border-slate-200 bg-white p-6 transition hover:-translate-y-1 hover:border-slate-400 hover:shadow-lg focus:outline-none focus:ring-2 focus:ring-slate-950 focus:ring-offset-4 sm:p-8">
            <span className={`block h-2 w-12 rounded-full ${destination.accent}`} />
            <p className="mt-8 text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">{destination.eyebrow}</p>
            <h2 className="mt-2 text-2xl font-semibold tracking-[-0.03em] text-slate-950 group-hover:text-rose-600">{destination.title}</h2>
            <p className="mt-3 min-h-14 text-sm leading-6 text-slate-500">{destination.description}</p>
            <span className="mt-7 inline-flex items-center gap-2 text-sm font-semibold text-slate-950">Acessar <span aria-hidden="true" className="transition group-hover:translate-x-1">→</span></span>
          </Link>
        ))}
      </nav>
    </div>
  )
}
