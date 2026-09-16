import { Link } from 'react-router-dom'

const destinations = [
  { to: '/imoveis', eyebrow: 'Explorar', title: 'Imóveis', description: 'Encontre anúncios, compare atributos e abra o imóvel no portal de origem.', accent: 'bg-rose-500', size: 'md:col-span-2' },
  { to: '/integracoes', eyebrow: 'Monitorar', title: 'Integrações', description: 'Acompanhe o histórico das coletas e dispare uma nova execução.', accent: 'bg-slate-950', size: '' },
  { to: '/configuracoes', eyebrow: 'Configurar', title: 'Filtros', description: 'Defina cidade, finalidade, faixa de preço e fontes da sua busca.', accent: 'bg-amber-400', size: '' },
]

export function HomePage() {
  return (
    <div className="mx-auto flex min-h-screen max-w-6xl flex-col justify-center px-4 py-8 sm:px-6 sm:py-12 lg:px-10">
      <section className="rounded-[2rem] bg-slate-950 p-7 text-white shadow-xl sm:p-12">
        <img src="/canaan-mark.svg" alt="Canaan" className="h-20 w-20 rounded-[1.5rem] sm:h-24 sm:w-24" />
        <p className="mt-10 text-sm font-extrabold uppercase tracking-[0.22em] text-rose-300">Busca inteligente</p>
        <h1 className="mt-3 max-w-3xl text-5xl font-extrabold leading-[0.98] tracking-[-0.07em] sm:text-7xl">Encontre a casa certa, em um só lugar<span className="text-rose-400">.</span></h1>
        <p className="mt-6 max-w-2xl text-base leading-7 text-slate-300 sm:text-lg">Reunimos anúncios, coletas e filtros para deixar sua busca mais simples até encontrar o lugar ideal.</p>
      </section>

      <nav aria-label="Acessos principais" className="mt-4 grid gap-4 md:grid-cols-2">
        {destinations.map((destination) => (
          <Link key={destination.to} to={destination.to} className={`group rounded-[2rem] border-2 border-slate-200 bg-white p-6 transition hover:-translate-y-1 hover:border-slate-950 hover:shadow-xl focus:outline-none focus:ring-4 focus:ring-rose-300 sm:p-8 ${destination.size}`}>
            <span className={`block h-2 w-12 rounded-full ${destination.accent}`} />
            <p className="mt-8 text-xs font-extrabold uppercase tracking-[0.18em] text-slate-500">{destination.eyebrow}</p>
            <h2 className="mt-2 text-3xl font-extrabold tracking-[-0.05em] text-slate-950 group-hover:text-rose-600 sm:text-4xl">{destination.title}</h2>
            <p className="mt-3 min-h-14 max-w-lg text-base leading-7 text-slate-600">{destination.description}</p>
            <span className="mt-8 inline-flex items-center gap-2 text-base font-extrabold text-slate-950">Acessar <span aria-hidden="true" className="transition group-hover:translate-x-1">→</span></span>
          </Link>
        ))}
      </nav>
    </div>
  )
}
