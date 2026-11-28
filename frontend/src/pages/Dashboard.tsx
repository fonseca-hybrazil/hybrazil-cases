import { useEffect, useMemo, useRef, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { keepPreviousData, useQuery } from '@tanstack/react-query'
import { BarChart3, X } from 'lucide-react'
import { get, STATUS, STATUS_NOME } from '../api'
import { Carregando, Erro } from '../components/comuns'
import { useCategorias, useLabels, useProjetos, useUsuarios } from '../queries'

// ---------------------------------------------------------------- tipos da API
interface Fatia { id: number | null; nome: string; cor: string | null; total: number }
interface DadosDashboard {
  totais: { total: number; abertos: number; completados: number; dias_medio: number | null; dias_mediana: number | null }
  por_mes: { mes: string; criados: number; concluidos: number }[]
  por_categoria: Fatia[]
  por_label: { itens: Fatia[]; outras: number; qtd_outras: number; sem_label: number }
  por_responsavel: Fatia[]
}

// ---------------------------------------------------------------- período
type Periodo = '12m' | 'ano' | 'ano-passado' | 'tudo' | 'personalizado'
const PERIODOS: [Periodo, string][] = [
  ['12m', 'Últimos 12 meses'], ['ano', 'Este ano'], ['ano-passado', 'Ano passado'], ['tudo', 'Tudo'],
  ['personalizado', 'Personalizado'],
]
const iso = (d: Date) => `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
const ultimoDia = (ano: number, mes: number) => new Date(ano, mes, 0).getDate()   // mes 1..12

function intervalo(p: Periodo, de: string, ate: string): { de?: string; ate?: string } {
  const hoje = new Date()
  const a = hoje.getFullYear()
  switch (p) {
    case '12m': return { de: iso(new Date(a, hoje.getMonth() - 11, 1)), ate: iso(hoje) }
    case 'ano': return { de: `${a}-01-01`, ate: iso(hoje) }
    case 'ano-passado': return { de: `${a - 1}-01-01`, ate: `${a - 1}-12-31` }
    case 'tudo': return {}
    default: return { de: de || undefined, ate: ate || undefined }
  }
}

const MESES = ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez']
const nomeMes = (m: string) => `${MESES[Number(m.slice(5)) - 1]}/${m.slice(2, 4)}`
const num = (n: number) => n.toLocaleString('pt-BR')
const dias = (d: number | null) => d === null ? '—' : d < 1 ? `${num(Math.round(d * 24))} h` : `${num(d)} dia${d === 1 ? '' : 's'}`

// ---------------------------------------------------------------- página
export default function Dashboard() {
  const [sp, setSp] = useSearchParams()
  const periodo = (sp.get('periodo') as Periodo) || '12m'
  const f = {
    projeto: sp.get('projeto') ?? '', status: sp.get('status') ?? 'todos', categoria: sp.get('categoria') ?? '',
    label: sp.get('label') ?? '', responsavel: sp.get('responsavel') ?? '', de: sp.get('de') ?? '', ate: sp.get('ate') ?? '',
  }

  const mudar = (mudancas: Record<string, string | null>) => {
    const p = new URLSearchParams(sp)
    for (const [k, v] of Object.entries(mudancas)) {
      if (v === null || v === '') p.delete(k)
      else p.set(k, v)
    }
    setSp(p, { replace: true })
  }
  // clique num gráfico: aplica o filtro; clicar de novo no mesmo item tira
  const alternar = (chave: string, valor: number | null) => {
    const v = valor === null ? '0' : String(valor)
    mudar({ [chave]: f[chave as keyof typeof f] === v ? null : v })
  }

  const faixa = intervalo(periodo, f.de, f.ate)
  const consulta = new URLSearchParams()
  if (f.projeto) consulta.set('projeto_id', f.projeto)
  if (faixa.de) consulta.set('de', faixa.de)
  if (faixa.ate) consulta.set('ate', faixa.ate)
  if (f.status !== 'todos') consulta.set('status', f.status)
  if (f.categoria) consulta.set('categoria_id', f.categoria)
  if (f.label) consulta.set('label_id', f.label)
  if (f.responsavel) consulta.set('responsavel_id', f.responsavel)
  const q = consulta.toString()

  const dados = useQuery({
    queryKey: ['dashboard', q],
    queryFn: () => get<DadosDashboard>(`/api/dashboard${q ? '?' + q : ''}`),
    placeholderData: keepPreviousData,
  })
  const { data: projetos } = useProjetos()
  const { data: categorias } = useCategorias()
  const { data: labels } = useLabels()
  const { data: usuarios } = useUsuarios()
  const labelsOrdenadas = useMemo(() => [...(labels ?? [])].sort((a, b) => a.nome.localeCompare(b.nome, 'pt-BR')), [labels])

  const filtrado = !!(f.projeto || f.status !== 'todos' || f.categoria || f.label || f.responsavel || periodo !== '12m')
  const d = dados.data

  return (
    <div className="pagina dash">
      <div className="pagina-topo">
        <h1><BarChart3 size={22} className="dash-titulo-icone" /> Dashboard</h1>
        {dados.isFetching && <span className="dash-atualizando">Atualizando…</span>}
      </div>

      <div className="dash-filtros">
        <label>Período
          <select value={periodo} onChange={(e) => {
            const p = e.target.value as Periodo
            // ao escolher "personalizado", começa com o intervalo que estava na tela
            if (p === 'personalizado') mudar({ periodo: p, de: faixa.de ?? '', ate: faixa.ate ?? '' })
            else mudar({ periodo: p === '12m' ? null : p, de: null, ate: null })
          }}>
            {PERIODOS.map(([v, n]) => <option key={v} value={v}>{n}</option>)}
          </select>
        </label>
        {periodo === 'personalizado' && (
          <>
            <label>De<input type="date" value={f.de} onChange={(e) => mudar({ de: e.target.value })} /></label>
            <label>Até<input type="date" value={f.ate} onChange={(e) => mudar({ ate: e.target.value })} /></label>
          </>
        )}
        <label>Projeto
          <select value={f.projeto} onChange={(e) => mudar({ projeto: e.target.value })}>
            <option value="">Todos</option>
            {(projetos ?? []).map((p) => <option key={p.id} value={p.id}>{p.nome}{p.arquivado ? ' (arquivado)' : ''}</option>)}
          </select>
        </label>
        <label>Status
          <select value={f.status} onChange={(e) => mudar({ status: e.target.value === 'todos' ? null : e.target.value })}>
            <option value="todos">Todos</option>
            <option value="abertos">Abertos (pendente + em andamento)</option>
            {STATUS.map((s) => <option key={s} value={s}>{STATUS_NOME[s]}</option>)}
          </select>
        </label>
        <label>Categoria
          <select value={f.categoria} onChange={(e) => mudar({ categoria: e.target.value })}>
            <option value="">Todas</option>
            <option value="0">Sem categoria</option>
            {(categorias ?? []).map((c) => <option key={c.id} value={c.id}>{c.nome}</option>)}
          </select>
        </label>
        <label>Label
          <select value={f.label} onChange={(e) => mudar({ label: e.target.value })}>
            <option value="">Todas</option>
            {labelsOrdenadas.map((l) => <option key={l.id} value={l.id}>{l.nome}</option>)}
          </select>
        </label>
        <label>Responsável
          <select value={f.responsavel} onChange={(e) => mudar({ responsavel: e.target.value })}>
            <option value="">Todos</option>
            <option value="0">Sem responsável</option>
            {(usuarios ?? []).map((u) => <option key={u.id} value={u.id}>{u.nome}</option>)}
          </select>
        </label>
        {filtrado && (
          <button className="btn-limpar-dash" onClick={() => setSp(new URLSearchParams(), { replace: true })}>
            <X size={14} /> Limpar filtros
          </button>
        )}
      </div>

      <Erro erro={dados.error} />
      {!d ? <Carregando /> : (
        <>
          <div className="dash-numeros">
            <Numero titulo="Cases no período" valor={num(d.totais.total)} dica="Criados no período, com os filtros aplicados" />
            <Numero titulo="Abertos" valor={num(d.totais.abertos)} cor="var(--pendente)" dica="Pendentes + em andamento" />
            <Numero titulo="Completados" valor={num(d.totais.completados)} cor="var(--completado)" />
            <Numero
              titulo="Tempo até concluir"
              valor={dias(d.totais.dias_medio)}
              detalhe={d.totais.dias_mediana !== null ? `metade fecha em até ${dias(d.totais.dias_mediana)}` : undefined}
              dica="Média entre a criação e a conclusão dos completados (a mediana mostra o caso típico)"
            />
          </div>

          <section className="painel dash-painel">
            <div className="dash-painel-topo">
              <h2>Cases por mês</h2>
              <span className="dash-legenda">
                <i style={{ background: 'var(--primaria)' }} /> criados <i style={{ background: 'var(--completado)' }} /> concluídos
              </span>
            </div>
            <GraficoMeses
              meses={d.por_mes}
              onMes={(m) => {
                const [a, mm] = m.split('-').map(Number)
                mudar({ periodo: 'personalizado', de: `${m}-01`, ate: `${m}-${String(ultimoDia(a, mm)).padStart(2, '0')}` })
              }}
            />
            <p className="dash-nota">Clique num mês para ver só aquele mês. Concluídos contam no mês da conclusão.</p>
          </section>

          <div className="dash-grade">
            <section className="painel dash-painel">
              <h2>Por categoria</h2>
              <Barras
                itens={d.por_categoria}
                total={d.totais.total}
                ativo={f.categoria}
                corPadrao="#8b96a3"
                onClick={(id) => alternar('categoria', id)}
              />
            </section>

            <section className="painel dash-painel">
              <h2>Por responsável</h2>
              <Barras
                itens={d.por_responsavel}
                total={d.totais.total}
                ativo={f.responsavel}
                corPadrao="var(--primaria)"
                onClick={(id) => alternar('responsavel', id)}
              />
            </section>

            <section className="painel dash-painel dash-largo">
              <h2>Por label</h2>
              <Barras
                itens={d.por_label.itens}
                total={d.totais.total}
                ativo={f.label}
                corPadrao="#8b96a3"
                onClick={(id) => id !== null && alternar('label', id)}
                extras={[
                  ...(d.por_label.qtd_outras > 0
                    ? [{ nome: `Outras (${num(d.por_label.qtd_outras)} labels)`, total: d.por_label.outras }] : []),
                  ...(d.por_label.sem_label > 0 ? [{ nome: 'Sem label', total: d.por_label.sem_label }] : []),
                ]}
              />
              <p className="dash-nota">Um case com várias labels conta em cada uma delas.</p>
            </section>
          </div>
        </>
      )}
    </div>
  )
}

function Numero({ titulo, valor, detalhe, cor, dica }: {
  titulo: string; valor: string; detalhe?: string; cor?: string; dica?: string
}) {
  return (
    <div className="dash-numero" title={dica}>
      <span className="dash-numero-titulo">{titulo}</span>
      <span className="dash-numero-valor" style={cor ? { color: cor } : undefined}>{valor}</span>
      {detalhe && <span className="dash-numero-detalhe">{detalhe}</span>}
    </div>
  )
}

// ---------------------------------------------------------------- barras horizontais
function Barras({ itens, total, ativo, corPadrao, onClick, extras = [] }: {
  itens: Fatia[]
  total: number
  ativo: string
  corPadrao: string
  onClick: (id: number | null) => void
  extras?: { nome: string; total: number }[]   // linhas só informativas (não clicáveis)
}) {
  const maior = Math.max(1, ...itens.map((i) => i.total), ...extras.map((e) => e.total))
  if (itens.length === 0 && extras.length === 0) return <div className="dash-vazio">Nenhum case com estes filtros.</div>
  const linha = (chave: string, nome: string, n: number, cor: string, sem: boolean, clicavel: boolean, selecionado: boolean,
                 acao?: () => void) => (
    <button
      key={chave}
      className={'dash-barra' + (sem ? ' sem' : '') + (selecionado ? ' selecionado' : '') + (clicavel ? '' : ' fixo')}
      onClick={acao}
      disabled={!clicavel}
      title={clicavel ? (selecionado ? 'Clique para tirar o filtro' : 'Clique para filtrar por este item') : undefined}
    >
      <span className="dash-barra-nome">{nome}</span>
      <span className="dash-barra-trilho">
        <span className="dash-barra-cheio" style={{ width: `${(n / maior) * 100}%`, background: cor }} />
      </span>
      <span className="dash-barra-num">
        {num(n)}{total > 0 && <small> {Math.round((n / total) * 100)}%</small>}
      </span>
    </button>
  )
  return (
    <div className="dash-barras">
      {itens.map((i) => {
        const valor = i.id === null ? '0' : String(i.id)
        return linha(String(i.id), i.nome, i.total, i.id === null ? '#c4cad1' : i.cor || corPadrao, i.id === null, true,
          ativo === valor, () => onClick(i.id))
      })}
      {extras.map((e) => linha('extra-' + e.nome, e.nome, e.total, '#c4cad1', true, false, false))}
    </div>
  )
}

// ---------------------------------------------------------------- colunas por mês (SVG)
function passoBonito(maior: number) {
  const bruto = maior / 4
  if (bruto <= 1) return 1
  const mag = Math.pow(10, Math.floor(Math.log10(bruto)))
  const n = bruto / mag
  return (n <= 1 ? 1 : n <= 2 ? 2 : n <= 5 ? 5 : 10) * mag
}

function GraficoMeses({ meses, onMes }: {
  meses: DadosDashboard['por_mes']; onMes: (mes: string) => void
}) {
  const [foco, setFoco] = useState<number | null>(null)
  const [largura, setLargura] = useState(0)
  const caixa = useRef<HTMLDivElement>(null)
  useEffect(() => {
    const el = caixa.current
    if (!el) return
    const obs = new ResizeObserver(([e]) => setLargura(e.contentRect.width))
    obs.observe(el)
    return () => obs.disconnect()
  }, [])
  // com muitos meses o gráfico rola na horizontal: começa mostrando os mais recentes
  const primeiro = meses[0]?.mes
  useEffect(() => {
    const el = caixa.current
    if (el) el.scrollLeft = el.scrollWidth
  }, [primeiro, meses.length, largura])
  const ALT = 210, BASE = 22, TOPO = 10, ESQ = 36
  // cada mês ocupa o espaço disponível; com muitos meses, fica no mínimo 30px e o gráfico rola na horizontal
  const grupo = Math.max(30, Math.min(90, ((largura || 600) - ESQ - 4) / meses.length))
  const larg = ESQ + meses.length * grupo + 4
  const b = Math.min(26, Math.max(9, grupo * 0.34))   // largura de cada barra
  const maior = Math.max(1, ...meses.map((m) => Math.max(m.criados, m.concluidos)))
  const passo = passoBonito(maior)
  const teto = Math.ceil(maior / passo) * passo
  const y = (v: number) => TOPO + (ALT - TOPO - BASE) * (1 - v / teto)
  const marcas: number[] = []
  for (let v = 0; v <= teto; v += passo) marcas.push(v)
  const cadaRotulo = Math.max(1, Math.ceil(44 / grupo))   // evita rótulos de mês sobrepostos

  return (
    <div className="dash-meses" ref={caixa}>
      {meses.length === 0 ? <div className="dash-vazio">Sem dados no período.</div> : <>
      <svg width={larg} height={ALT} role="img" aria-label="Cases criados e concluídos por mês">
        {marcas.map((v) => (
          <g key={v}>
            <line x1={ESQ} x2={larg} y1={y(v)} y2={y(v)} className="dash-grade-linha" />
            <text x={ESQ - 6} y={y(v) + 4} textAnchor="end" className="dash-eixo">{v}</text>
          </g>
        ))}
        {meses.map((m, i) => {
          const x = ESQ + i * grupo + (grupo - 2 * b - 2) / 2
          return (
            <g
              key={m.mes}
              className={'dash-mes' + (foco === i ? ' foco' : '')}
              onMouseEnter={() => setFoco(i)}
              onMouseLeave={() => setFoco(null)}
              onClick={() => onMes(m.mes)}
            >
              <rect x={ESQ + i * grupo} y={TOPO} width={grupo} height={ALT - TOPO - BASE + 4} className="dash-mes-fundo" />
              <rect x={x} y={y(m.criados)} width={b} height={y(0) - y(m.criados)} rx={2} fill="var(--primaria)" />
              <rect x={x + b + 2} y={y(m.concluidos)} width={b} height={y(0) - y(m.concluidos)} rx={2} fill="var(--completado)" />
              {(i % cadaRotulo === 0 || foco === i) && (
                <text x={ESQ + i * grupo + grupo / 2} y={ALT - 6} textAnchor="middle" className="dash-eixo">{nomeMes(m.mes)}</text>
              )}
              <title>{`${nomeMes(m.mes)}: ${m.criados} criados, ${m.concluidos} concluídos`}</title>
            </g>
          )
        })}
      </svg>
      <div className="dash-dica">
        {foco !== null
          ? <><b>{nomeMes(meses[foco].mes)}</b> · {num(meses[foco].criados)} criados · {num(meses[foco].concluidos)} concluídos</>
          : <>&nbsp;</>}
      </div>
      </>}
    </div>
  )
}
