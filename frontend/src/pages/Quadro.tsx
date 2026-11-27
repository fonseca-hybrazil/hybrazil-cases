import { memo, useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { useNavigate, useParams, useSearchParams } from 'react-router-dom'
import { keepPreviousData, useQueries, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  closestCorners, DndContext, DragOverlay, PointerSensor, useDroppable, useSensor, useSensors,
  type DragEndEvent, type DragOverEvent, type DragStartEvent,
} from '@dnd-kit/core'
import { arrayMove, SortableContext, useSortable, verticalListSortingStrategy } from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'
import { AlignLeft, Filter, ListChecks, MessageSquare, Plus, Search, Star, UserRound, X } from 'lucide-react'
import {
  filtrosAtivos, filtrosDeParams, filtrosParaParams, get, post, STATUS, STATUS_NOME,
  type Coluna, type Filtros, type Projeto, type Status, type TicketResumo,
} from '../api'
import { Avatar, CategoriaBadge, Carregando, Erro, LabelPill, useDebounce } from '../components/comuns'
import FiltroPainel from '../components/FiltroPainel'
import { IconeProjeto } from '../components/IconeProjeto'
import { porId, useCategorias, useLabels, useUsuarios } from '../queries'
import TicketModal from './TicketModal'
import { alternarFavorito } from './Inicio'

const PAGINA = 50
type Cols = Record<Status, TicketResumo[]>

export default function QuadroPagina() {
  const { projetoId, numero } = useParams()
  const pid = Number(projetoId)
  const [sp, setSp] = useSearchParams()
  const filtros = useMemo(() => filtrosDeParams(sp), [sp])
  const params = filtrosParaParams(filtros).toString()
  const qc = useQueryClient()
  const nav = useNavigate()

  const [limites, setLimites] = useState<Record<Status, number>>({ pendente: PAGINA, andamento: PAGINA, completado: PAGINA })
  useEffect(() => setLimites({ pendente: PAGINA, andamento: PAGINA, completado: PAGINA }), [pid, params])

  const projeto = useQuery({ queryKey: ['projeto', pid], queryFn: () => get<Projeto>(`/api/projetos/${pid}`) })
  const colunas = useQueries({
    queries: STATUS.map((s) => ({
      queryKey: ['coluna', pid, s, params, limites[s]],
      queryFn: () => get<Coluna>(`/api/projetos/${pid}/tickets?status=${s}&limite=${limites[s]}${params ? '&' + params : ''}`),
      placeholderData: keepPreviousData,
    })),
  })

  const setFiltros = (f: Filtros) => {
    const p = filtrosParaParams(f)
    setSp(p, { replace: true })
  }

  // busca rápida no cabeçalho (com atraso para não consultar a cada tecla)
  const [busca, setBusca] = useState(filtros.q)
  const buscaAtrasada = useDebounce(busca, 350)
  useEffect(() => setBusca(filtros.q), [pid]) // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => {
    if (buscaAtrasada !== filtros.q) setFiltros({ ...filtros, q: buscaAtrasada })
  }, [buscaAtrasada]) // eslint-disable-line react-hooks/exhaustive-deps

  const [painel, setPainel] = useState(false)

  if (projeto.isLoading) return <Carregando />
  if (projeto.error || !projeto.data) return <div className="pagina"><Erro erro={projeto.error ?? 'Projeto não encontrado.'} /></div>
  const p = projeto.data
  const ativos = filtrosAtivos(filtros)
  const qtdFiltros = filtros.label.length + filtros.categoria.length + filtros.responsavel.length
    + (filtros.q.trim() ? 1 : 0) + (filtros.numero.trim() ? 1 : 0)

  return (
    <div className="quadro-pagina">
      <header className="quadro-topo">
        {p.icone && (
          <span className="quadro-icone"><IconeProjeto icone={p.icone} cor={p.icone_cor ?? '#57606a'} tamanho={20} /></span>
        )}
        <h1>{p.nome}</h1>
        <button
          className="btn-icone claro"
          title={p.favorito ? 'Remover dos favoritos' : 'Favoritar'}
          onClick={async () => {
            await alternarFavorito(p)
            qc.invalidateQueries({ queryKey: ['projeto', pid] })
            qc.invalidateQueries({ queryKey: ['projetos'] })
          }}
        >
          <Star size={17} className={p.favorito ? 'estrela-on' : ''} />
        </button>
        <div className="busca-rapida">
          <Search size={15} />
          <input placeholder="Buscar em títulos e comentários…" value={busca} onChange={(e) => setBusca(e.target.value)} />
          {busca && <button className="btn-icone" onClick={() => setBusca('')} aria-label="Limpar busca"><X size={14} /></button>}
        </div>
        <div className="tb-rel">
          <button className={'btn-filtro' + (ativos ? ' ativo' : '')} onMouseDown={(e) => e.stopPropagation()}
                  onClick={() => setPainel((v) => !v)}>
            <Filter size={15} /> Filtro{qtdFiltros ? ` (${qtdFiltros})` : ''}
          </button>
          {painel && (
            <FiltroPainel filtros={filtros} onChange={setFiltros} onFechar={() => setPainel(false)} />
          )}
        </div>
        {ativos && (
          <button className="btn-limpar" onClick={() => { setBusca(''); setSp(new URLSearchParams(), { replace: true }) }}>
            <X size={14} /> Limpar filtros
          </button>
        )}
      </header>
      {p.arquivado && <div className="aviso">Este projeto está arquivado: não é possível criar tickets.</div>}
      <Board
        pid={pid}
        arquivado={p.arquivado}
        dados={colunas.map((c) => c.data)}
        erro={colunas.find((c) => c.error)?.error}
        totaisSemFiltro={p.contagem}
        filtrado={ativos}
        onMais={(s) => setLimites((l) => ({ ...l, [s]: l[s] + PAGINA }))}
        abrir={(t) => nav(`/p/${pid}/t/${t.numero}${sp.toString() ? '?' + sp.toString() : ''}`)}
      />
      {numero && (
        <TicketModal
          projetoId={pid}
          numero={Number(numero)}
          onFechar={() => nav(`/p/${pid}${sp.toString() ? '?' + sp.toString() : ''}`)}
        />
      )}
    </div>
  )
}

function Board({
  pid, arquivado, dados, erro, totaisSemFiltro, filtrado, onMais, abrir,
}: {
  pid: number
  arquivado: boolean
  dados: (Coluna | undefined)[]
  erro: unknown
  totaisSemFiltro: Record<Status, number>
  filtrado: boolean
  onMais: (s: Status) => void
  abrir: (t: TicketResumo) => void
}) {
  const qc = useQueryClient()
  const [cols, setCols] = useState<Cols>({ pendente: [], andamento: [], completado: [] })
  const [arrastando, setArrastando] = useState<TicketResumo | null>(null)
  const [travado, setTravado] = useState(false)
  const [erroMover, setErroMover] = useState<unknown>(null)
  const sensores = useSensors(useSensor(PointerSensor, { activationConstraint: { distance: 6 } }))

  useEffect(() => {
    if (arrastando || travado) return
    setCols({
      pendente: dados[0]?.tickets ?? [],
      andamento: dados[1]?.tickets ?? [],
      completado: dados[2]?.tickets ?? [],
    })
  }, [dados[0], dados[1], dados[2], arrastando, travado]) // eslint-disable-line react-hooks/exhaustive-deps

  const recarregar = async () => {
    await Promise.all([
      qc.invalidateQueries({ queryKey: ['coluna', pid] }),
      qc.invalidateQueries({ queryKey: ['projeto', pid] }),
      qc.invalidateQueries({ queryKey: ['projetos'] }),
    ])
  }

  const ondeEsta = (id: string | number, c: Cols = cols): Status | null => {
    if (typeof id === 'string' && id.startsWith('col-')) return id.slice(4) as Status
    for (const s of STATUS) if (c[s].some((t) => t.id === id)) return s
    return null
  }

  const mover = async (t: TicketResumo, status: Status, aposId: number | null) => {
    setTravado(true)
    setErroMover(null)
    try {
      await post(`/api/tickets/${t.id}/mover`, { status, apos_id: aposId })
      qc.invalidateQueries({ queryKey: ['ticket', pid, t.numero] })
      qc.invalidateQueries({ queryKey: ['timeline', t.id] })
    } catch (e) {
      setErroMover(e)
    } finally {
      await recarregar()
      setTravado(false)
    }
  }

  // Funções estáveis para os cartões (memo): sempre chamam a versão mais recente.
  const moverRef = useRef(mover)
  moverRef.current = mover
  const abrirRef = useRef(abrir)
  abrirRef.current = abrir
  const alternarConcluido = useCallback((t: TicketResumo) =>
    moverRef.current(t, t.status === 'completado' ? 'pendente' : 'completado', null), [])
  const abrirCartao = useCallback((t: TicketResumo) => abrirRef.current(t), [])
  const onMaisRef = useRef(onMais)
  onMaisRef.current = onMais
  const mais = useMemo(() => Object.fromEntries(STATUS.map((s) => [s, () => onMaisRef.current(s)])) as Record<Status, () => void>, [])

  const inicio = (e: DragStartEvent) => {
    const s = ondeEsta(e.active.id)
    setArrastando(s ? cols[s].find((t) => t.id === e.active.id) ?? null : null)
  }

  const sobre = ({ active, over }: DragOverEvent) => {
    if (!over) return
    const de = ondeEsta(active.id)
    const para = ondeEsta(over.id)
    if (!de || !para || de === para) return
    setCols((c) => {
      const item = c[de].find((t) => t.id === active.id)
      if (!item) return c
      const destino = c[para].filter((t) => t.id !== active.id)
      const idx = destino.findIndex((t) => t.id === over.id)
      destino.splice(idx >= 0 ? idx : destino.length, 0, { ...item, status: para })
      return { ...c, [de]: c[de].filter((t) => t.id !== active.id), [para]: destino }
    })
  }

  const fim = ({ active, over }: DragEndEvent) => {
    const original = arrastando
    setArrastando(null)
    if (!over || !original) return
    const para = ondeEsta(over.id)
    if (!para) return
    let lista = cols[para]
    const de = lista.findIndex((t) => t.id === active.id)
    const ate = typeof over.id === 'number' ? lista.findIndex((t) => t.id === over.id) : lista.length - 1
    if (de >= 0 && ate >= 0 && de !== ate) lista = arrayMove(lista, de, ate)
    setCols((c) => ({ ...c, [para]: lista }))
    const pos = lista.findIndex((t) => t.id === active.id)
    const aposId = pos > 0 ? lista[pos - 1].id : null
    const antes = dados[STATUS.indexOf(original.status)]?.tickets ?? []
    const posOriginal = antes.findIndex((t) => t.id === original.id)
    const aposOriginal = posOriginal > 0 ? antes[posOriginal - 1].id : null
    if (para === original.status && aposId === aposOriginal) return
    mover(original, para, aposId)
  }

  return (
    <>
      <Erro erro={erro || erroMover} />
      <DndContext
        sensors={sensores}
        collisionDetection={closestCorners}
        onDragStart={inicio}
        onDragOver={sobre}
        onDragEnd={fim}
        onDragCancel={() => setArrastando(null)}
      >
        <div className="colunas">
          {STATUS.map((s, i) => (
            <ColunaView
              key={s}
              pid={pid}
              status={s}
              tickets={cols[s]}
              total={dados[i]?.total ?? 0}
              totalSemFiltro={totaisSemFiltro[s]}
              filtrado={filtrado}
              arquivado={arquivado}
              onMais={mais[s]}
              abrir={abrirCartao}
              alternarConcluido={alternarConcluido}
              aoCriar={recarregar}
            />
          ))}
        </div>
        <DragOverlay>
          {arrastando ? <Cartao t={arrastando} fantasma /> : null}
        </DragOverlay>
      </DndContext>
    </>
  )
}

function ColunaView({
  pid, status, tickets, total, totalSemFiltro, filtrado, arquivado, onMais, abrir, alternarConcluido, aoCriar,
}: {
  pid: number
  status: Status
  tickets: TicketResumo[]
  total: number
  totalSemFiltro: number
  filtrado: boolean
  arquivado: boolean
  onMais: () => void
  abrir: (t: TicketResumo) => void
  alternarConcluido: (t: TicketResumo) => void
  aoCriar: () => Promise<void>
}) {
  const { setNodeRef } = useDroppable({ id: `col-${status}` })
  const [titulo, setTitulo] = useState('')
  const [criando, setCriando] = useState(false)
  const [erro, setErro] = useState<unknown>(null)

  // Rolagem infinita: quando o botão "Carregar mais" aparece no fim da coluna, carrega a próxima página sozinho.
  // O observador é recriado a cada página; se o botão continuar visível (coluna alta), pede a seguinte.
  const sentinela = useRef<HTMLButtonElement>(null)
  const pedido = useRef('')   // "total:quantidade" quando a última página foi pedida (evita pedir duas vezes)
  const chave = `${total}:${tickets.length}`
  const [, forcar] = useState(0)
  useEffect(() => {
    const el = sentinela.current
    if (!el || tickets.length >= total) return
    const obs = new IntersectionObserver(([e]) => {
      if (e.isIntersecting && pedido.current !== chave) {
        pedido.current = chave
        forcar((n) => n + 1)
        onMais()
      }
    })
    obs.observe(el)
    return () => obs.disconnect()
  }, [chave, tickets.length, total, onMais])

  const criar = async () => {
    const t = titulo.trim()
    if (!t) return
    setCriando(true)
    setErro(null)
    try {
      await post(`/api/projetos/${pid}/tickets`, { titulo: t, status })
      setTitulo('')
      await aoCriar()
    } catch (e) {
      setErro(e)
    } finally {
      setCriando(false)
    }
  }

  return (
    <section className={`coluna coluna-${status}`}>
      <div className="coluna-topo">
        <span className="coluna-nome">{STATUS_NOME[status]}</span>
        <span className="coluna-cont" title={filtrado ? `${total} de ${totalSemFiltro} com os filtros aplicados` : undefined}>
          {filtrado ? `${total} / ${totalSemFiltro}` : total}
        </span>
      </div>
      {!arquivado && (
        <div className="novo-ticket">
          <Plus size={15} />
          <input
            placeholder="Novo ticket…"
            value={titulo}
            disabled={criando}
            onChange={(e) => setTitulo(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') criar()
              if (e.key === 'Escape') setTitulo('')
            }}
          />
        </div>
      )}
      <Erro erro={erro} />
      <div className="coluna-lista" ref={setNodeRef}>
        <SortableContext items={tickets.map((t) => t.id)} strategy={verticalListSortingStrategy}>
          {tickets.map((t) => (
            <CartaoArrastavel key={t.id} t={t} abrir={abrir} alternarConcluido={alternarConcluido} />
          ))}
        </SortableContext>
        {tickets.length === 0 && <div className="coluna-vazia">{filtrado ? 'Nenhum ticket com estes filtros' : 'Vazio'}</div>}
        {tickets.length < total && (
          <button ref={sentinela} className="btn-mais" onClick={onMais}>
            {pedido.current === chave ? 'Carregando…' : `Carregar mais (${total - tickets.length} restantes)`}
          </button>
        )}
      </div>
    </section>
  )
}

// memo: durante o arrasto o dnd-kit atualiza todos os itens a cada movimento; com as props estáveis,
// só o "invólucro" (posição) é refeito e o conteúdo do cartão não é redesenhado.
const CartaoArrastavel = memo(function CartaoArrastavel({ t, abrir, alternarConcluido }: {
  t: TicketResumo; abrir: (t: TicketResumo) => void; alternarConcluido: (t: TicketResumo) => void
}) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({ id: t.id })
  return (
    <div
      ref={setNodeRef}
      style={{ transform: CSS.Translate.toString(transform), transition, opacity: isDragging ? 0.35 : 1 }}
      {...attributes}
      {...listeners}
      onClick={() => abrir(t)}
      onKeyDown={(e) => e.key === 'Enter' && abrir(t)}
    >
      <Cartao t={t} alternarConcluido={alternarConcluido} />
    </div>
  )
})

const Cartao = memo(function Cartao({ t, fantasma, alternarConcluido }: {
  t: TicketResumo; fantasma?: boolean; alternarConcluido?: (t: TicketResumo) => void
}) {
  const { data: labels } = useLabels()
  const { data: cats } = useCategorias()
  const { data: usuarios } = useUsuarios()
  const mapaL = useMemo(() => porId(labels), [labels])
  const mapaC = useMemo(() => porId(cats), [cats])
  const resp = t.responsavel ? porId(usuarios).get(t.responsavel.id) ?? t.responsavel : null
  const feito = t.status === 'completado'
  return (
    <div className={'cartao' + (fantasma ? ' fantasma' : '') + (feito ? ' feito' : '')}>
      <div className="cartao-linha">
        <input
          type="checkbox"
          className="check-ticket"
          checked={feito}
          title={feito ? 'Reabrir' : 'Marcar como completado'}
          onClick={(e) => e.stopPropagation()}
          onPointerDown={(e) => e.stopPropagation()}
          onChange={() => alternarConcluido?.(t)}
        />
        <span className="cartao-titulo">{t.titulo}</span>
      </div>
      {t.label_ids.length > 0 && (
        <div className="cartao-labels">
          {t.label_ids.map((id) => {
            const l = mapaL.get(id)
            return l ? <LabelPill key={id} label={l} /> : null
          })}
        </div>
      )}
      <div className="cartao-rodape">
        <span className="cartao-num">#{t.numero}</span>
        <CategoriaBadge cat={t.categoria_id ? mapaC.get(t.categoria_id) : undefined} />
        {t.qtd_comentarios > 0 && (
          <span className="cartao-meta" title={`${t.qtd_comentarios} comentário(s)`}>
            <MessageSquare size={13} /> {t.qtd_comentarios}
          </span>
        )}
        {t.tem_descricao && <span className="cartao-meta" title="Tem descrição"><AlignLeft size={13} /></span>}
        {t.tarefas_total > 0 && (
          <span className={t.tarefas_feitas === t.tarefas_total ? 'cartao-meta tarefas-ok' : 'cartao-meta'}
                title={`${t.tarefas_feitas} de ${t.tarefas_total} tarefas feitas`}>
            <ListChecks size={13} /> {t.tarefas_feitas}/{t.tarefas_total}
          </span>
        )}
        <span className="cartao-resp">
          {resp ? <Avatar u={resp} tamanho={22} /> : <span className="sem-resp" title="Sem responsável"><UserRound size={13} /></span>}
        </span>
      </div>
    </div>
  )
})
