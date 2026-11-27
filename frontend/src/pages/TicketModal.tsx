import { Fragment, useEffect, useMemo, useRef, useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import {
  Check, ChevronDown, Link as LinkIcon, MoreHorizontal, Pencil, Plus, Tag, Trash2, UserRound, X,
} from 'lucide-react'
import {
  del, get, patch, post, STATUS, STATUS_NOME, type Doc, type ItemTimeline, type Label, type Node as RtNode,
  type Status, type TicketDetalhe,
} from '../api'
import { useAuth } from '../auth'
import { Avatar, CategoriaBadge, Carregando, Erro, LabelPill, Popover, SeletorCor } from '../components/comuns'
import { IconeCategoria } from '../icones'
import RichEditor from '../editor/RichEditor'
import RichView from '../editor/RichView'
import { porId, useCategorias, useLabels, useUsuarios } from '../queries'
import { dataHora, diaRelativo, hora, PALETA } from '../util'

export default function TicketModal({ projetoId, numero, onFechar }: {
  projetoId: number; numero: number; onFechar: () => void
}) {
  const qc = useQueryClient()
  const chave = ['ticket', projetoId, numero]
  const { data: t, error, isLoading } = useQuery({
    queryKey: chave,
    queryFn: () => get<TicketDetalhe>(`/api/projetos/${projetoId}/tickets/numero/${numero}`),
  })

  useEffect(() => {
    const k = (e: KeyboardEvent) => {
      if (e.key !== 'Escape') return
      // não fecha se o Esc foi para um campo/edição aberta
      const alvo = e.target as HTMLElement
      if (alvo.closest('.ProseMirror, input, textarea, select, .popover')) return
      onFechar()
    }
    window.addEventListener('keydown', k)
    return () => window.removeEventListener('keydown', k)
  }, [onFechar])

  const atualizado = (novo: TicketDetalhe) => {
    qc.setQueryData(chave, novo)
    qc.invalidateQueries({ queryKey: ['coluna', projetoId] })
    qc.invalidateQueries({ queryKey: ['timeline', novo.id] })
    qc.invalidateQueries({ queryKey: ['projeto', projetoId] })
    qc.invalidateQueries({ queryKey: ['projetos'] })
  }

  return (
    <div className="modal-fundo ticket-fundo" onMouseDown={(e) => e.target === e.currentTarget && onFechar()}>
      <div className="ticket-painel" role="dialog" aria-modal="true">
        {isLoading && <Carregando />}
        {error && (
          <div className="ticket-corpo">
            <div className="ticket-barra"><span /><button className="btn-icone" onClick={onFechar}><X size={18} /></button></div>
            <Erro erro={error} />
          </div>
        )}
        {t && <Conteudo t={t} onAtualizado={atualizado} onFechar={onFechar} />}
      </div>
    </div>
  )
}

function Conteudo({ t, onAtualizado, onFechar }: {
  t: TicketDetalhe; onAtualizado: (t: TicketDetalhe) => void; onFechar: () => void
}) {
  const qc = useQueryClient()
  const { data: cats = [] } = useCategorias()
  const { data: labels = [] } = useLabels()
  const mapaL = useMemo(() => porId(labels), [labels])
  const [erro, setErro] = useState<unknown>(null)
  const [menu, setMenu] = useState(false)
  const [copiado, setCopiado] = useState(false)

  const salvar = async (dados: Record<string, unknown>) => {
    setErro(null)
    try {
      onAtualizado(await patch<TicketDetalhe>(`/api/tickets/${t.id}`, dados))
    } catch (e) {
      setErro(e)
      throw e
    }
  }

  const mover = async (status: Status) => {
    setErro(null)
    try {
      onAtualizado(await post<TicketDetalhe>(`/api/tickets/${t.id}/mover`, { status, apos_id: null }))
    } catch (e) {
      setErro(e)
    }
  }

  const excluir = async () => {
    if (!window.confirm(`Excluir o ticket #${t.numero} "${t.titulo}"?`)) return
    try {
      await del(`/api/tickets/${t.id}`)
      qc.invalidateQueries({ queryKey: ['coluna', t.projeto_id] })
      qc.invalidateQueries({ queryKey: ['projetos'] })
      qc.invalidateQueries({ queryKey: ['projeto', t.projeto_id] })
      onFechar()
    } catch (e) {
      setErro(e)
    }
  }

  const copiarLink = async () => {
    await navigator.clipboard?.writeText(`${location.origin}/p/${t.projeto_id}/t/${t.numero}`)
    setCopiado(true)
    setTimeout(() => setCopiado(false), 1500)
    setMenu(false)
  }

  const feito = t.status === 'completado'
  return (
    <>
      <div className="ticket-barra">
        <div className="ticket-barra-esq">
          <span className="ticket-num">#{t.numero}</span>
          <SeletorCategoria atual={t.categoria_id} onEscolher={(id) => salvar({ categoria_id: id })} />
          <span className="suave">na lista</span>
          <select className="select-status" value={t.status} onChange={(e) => mover(e.target.value as Status)}>
            {STATUS.map((s) => <option key={s} value={s}>{STATUS_NOME[s]}</option>)}
          </select>
          {copiado && <span className="sucesso-inline">Link copiado</span>}
        </div>
        <div className="ticket-barra-dir tb-rel">
          <button className="btn-icone" title="Mais ações" onMouseDown={(e) => e.stopPropagation()}
                  onClick={() => setMenu((v) => !v)}>
            <MoreHorizontal size={18} />
          </button>
          <Popover aberto={menu} onFechar={() => setMenu(false)} alinhar="direita">
            <button className="menu-item" onClick={copiarLink}><LinkIcon size={14} /> Copiar link do ticket</button>
            {t.pode_excluir && (
              <button className="menu-item perigo" onClick={() => { setMenu(false); excluir() }}>
                <Trash2 size={14} /> Excluir ticket
              </button>
            )}
          </Popover>
          <button className="btn-icone" onClick={onFechar} title="Fechar (Esc)"><X size={18} /></button>
        </div>
      </div>

      <div className="ticket-corpo">
        <div className="ticket-titulo-linha">
          <input
            type="checkbox"
            className="check-ticket grande"
            checked={feito}
            title={feito ? 'Reabrir' : 'Marcar como completado'}
            onChange={() => mover(feito ? 'pendente' : 'completado')}
          />
          <Titulo valor={t.titulo} feito={feito} onSalvar={(titulo) => salvar({ titulo })} />
        </div>

        <div className="ticket-labels">
          {t.label_ids.map((id) => {
            const l = mapaL.get(id)
            return l ? (
              <LabelPill key={id} label={l}
                         onRemover={() => salvar({ label_ids: t.label_ids.filter((x) => x !== id) })} />
            ) : null
          })}
          <SeletorLabels selecionadas={t.label_ids} onMudar={(ids) => salvar({ label_ids: ids })} />
        </div>

        <div className="ticket-campos">
          <SeletorResponsavel atual={t.responsavel?.id ?? null} onEscolher={(id) => salvar({ responsavel_id: id })} />
          {t.categoria_id && (
            <span className="suave pequeno">
              Categoria: <CategoriaBadge cat={cats.find((c) => c.id === t.categoria_id)} comNome />
            </span>
          )}
        </div>

        <Erro erro={erro} />

        <Descricao t={t} onSalvar={(descricao) => salvar({ descricao })} />

        <Timeline t={t} />
      </div>

      <NovoComentario t={t} />
    </>
  )
}

function Titulo({ valor, feito, onSalvar }: { valor: string; feito: boolean; onSalvar: (v: string) => Promise<void> }) {
  const [editando, setEditando] = useState(false)
  const [v, setV] = useState(valor)
  const ref = useRef<HTMLTextAreaElement>(null)
  useEffect(() => setV(valor), [valor])
  useEffect(() => {
    if (editando && ref.current) {
      ref.current.focus()
      ref.current.style.height = 'auto'
      ref.current.style.height = ref.current.scrollHeight + 'px'
    }
  }, [editando])
  const confirmar = async () => {
    const novo = v.trim()
    setEditando(false)
    if (novo && novo !== valor) {
      try { await onSalvar(novo) } catch { setV(valor) }
    } else setV(valor)
  }
  if (!editando) {
    return (
      <h2 className={'ticket-titulo' + (feito ? ' feito' : '')} onClick={() => setEditando(true)} title="Clique para editar">
        {valor}
      </h2>
    )
  }
  return (
    <textarea
      ref={ref}
      className="ticket-titulo-edit"
      value={v}
      maxLength={500}
      onChange={(e) => {
        setV(e.target.value.replace(/\n/g, ' '))
        e.target.style.height = 'auto'
        e.target.style.height = e.target.scrollHeight + 'px'
      }}
      onBlur={confirmar}
      onKeyDown={(e) => {
        if (e.key === 'Enter') { e.preventDefault(); confirmar() }
        if (e.key === 'Escape') { setV(valor); setEditando(false) }
      }}
    />
  )
}

function SeletorCategoria({ atual, onEscolher }: { atual: number | null; onEscolher: (id: number | null) => void }) {
  const { data: cats = [] } = useCategorias()
  const [aberto, setAberto] = useState(false)
  const cat = cats.find((c) => c.id === atual)
  return (
    <span className="tb-rel">
      <button className="pill-btn" onMouseDown={(e) => e.stopPropagation()} onClick={() => setAberto((v) => !v)}
              title="Categoria">
        {cat ? <><IconeCategoria nome={cat.icone} cor={cat.cor} /> {cat.nome}</> : 'Categoria'}
        <ChevronDown size={13} />
      </button>
      <Popover aberto={aberto} onFechar={() => setAberto(false)}>
        {cats.filter((c) => c.ativa || c.id === atual).map((c) => (
          <button key={c.id} className="menu-item" onClick={() => { setAberto(false); onEscolher(c.id) }}>
            <IconeCategoria nome={c.icone} cor={c.cor} /> {c.nome}
            {c.id === atual && <Check size={14} className="dir" />}
          </button>
        ))}
        {atual && (
          <button className="menu-item suave" onClick={() => { setAberto(false); onEscolher(null) }}>
            <X size={14} /> Sem categoria
          </button>
        )}
      </Popover>
    </span>
  )
}

function SeletorResponsavel({ atual, onEscolher }: { atual: number | null; onEscolher: (id: number | null) => void }) {
  const { data: usuarios = [] } = useUsuarios()
  const { eu } = useAuth()
  const [aberto, setAberto] = useState(false)
  const [busca, setBusca] = useState('')
  const u = usuarios.find((x) => x.id === atual)
  const lista = usuarios.filter((x) => x.ativo && x.nome.toLowerCase().includes(busca.toLowerCase()))
  return (
    <span className="tb-rel">
      <button className="pill-btn" onMouseDown={(e) => e.stopPropagation()} onClick={() => setAberto((v) => !v)}>
        {u ? <><Avatar u={u} tamanho={18} /> {u.nome}</> : <><UserRound size={14} /> Atribuir</>}
      </button>
      <Popover aberto={aberto} onFechar={() => setAberto(false)}>
        <input className="popover-busca" placeholder="Procurar pessoa…" value={busca} autoFocus
               onChange={(e) => setBusca(e.target.value)} />
        {eu && atual !== eu.id && !busca && (
          <button className="menu-item" onClick={() => { setAberto(false); onEscolher(eu.id) }}>
            <Avatar u={eu} tamanho={18} /> Atribuir a mim
          </button>
        )}
        <div className="popover-rolagem">
          {lista.map((x) => (
            <button key={x.id} className="menu-item" onClick={() => { setAberto(false); onEscolher(x.id) }}>
              <Avatar u={x} tamanho={18} /> {x.nome}
              {x.id === atual && <Check size={14} className="dir" />}
            </button>
          ))}
        </div>
        {atual && (
          <button className="menu-item suave" onClick={() => { setAberto(false); onEscolher(null) }}>
            <X size={14} /> Remover responsável
          </button>
        )}
      </Popover>
    </span>
  )
}

function SeletorLabels({ selecionadas, onMudar }: { selecionadas: number[]; onMudar: (ids: number[]) => void }) {
  const { data: labels = [] } = useLabels()
  const qc = useQueryClient()
  const [aberto, setAberto] = useState(false)
  const [busca, setBusca] = useState('')
  const [cor, setCor] = useState(PALETA[9])
  const [erro, setErro] = useState<unknown>(null)
  const lista = labels.filter((l) => l.nome.toLowerCase().includes(busca.trim().toLowerCase()))
  const existe = labels.some((l) => l.nome.toLowerCase() === busca.trim().toLowerCase())

  const criar = async () => {
    setErro(null)
    try {
      const l = await post<Label>('/api/labels', { nome: busca.trim(), cor })
      await qc.invalidateQueries({ queryKey: ['labels'] })
      onMudar([...selecionadas, l.id])
      setBusca('')
    } catch (e) {
      setErro(e)
    }
  }

  return (
    <span className="tb-rel">
      <button className="pill-btn pequeno" onMouseDown={(e) => e.stopPropagation()} onClick={() => setAberto((v) => !v)}>
        <Tag size={13} /> {selecionadas.length ? <Plus size={13} /> : 'Labels'}
      </button>
      <Popover aberto={aberto} onFechar={() => setAberto(false)}>
        <input
          className="popover-busca"
          placeholder="Procurar ou criar label…"
          value={busca}
          autoFocus
          onChange={(e) => setBusca(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && busca.trim() && !existe && criar()}
        />
        <div className="popover-rolagem">
          {lista.map((l) => (
            <label key={l.id} className="filtro-op">
              <input
                type="checkbox"
                checked={selecionadas.includes(l.id)}
                onChange={() => onMudar(selecionadas.includes(l.id)
                  ? selecionadas.filter((x) => x !== l.id) : [...selecionadas, l.id])}
              />
              <LabelPill label={l} />
            </label>
          ))}
        </div>
        {busca.trim() && !existe && (
          <div className="criar-label">
            <div className="suave pequeno">Criar label "{busca.trim()}"</div>
            <SeletorCor valor={cor} onChange={setCor} />
            <button className="btn btn-primario pequeno" onClick={criar}>
              Criar <LabelPill label={{ id: 0, nome: busca.trim(), cor }} />
            </button>
          </div>
        )}
        <Erro erro={erro} />
      </Popover>
    </span>
  )
}

function Descricao({ t, onSalvar }: { t: TicketDetalhe; onSalvar: (d: Doc | null) => Promise<void> }) {
  const [editando, setEditando] = useState(false)
  const [doc, setDoc] = useState<Doc | null>(t.descricao)
  const [salvando, setSalvando] = useState(false)

  const salvar = async () => {
    setSalvando(true)
    try {
      await onSalvar(doc)
      setEditando(false)
    } catch {
      /* erro exibido acima */
    } finally {
      setSalvando(false)
    }
  }

  if (editando) {
    return (
      <div className="descricao">
        <RichEditor
          ticketId={t.id}
          inicial={t.descricao}
          placeholder="Descreva o problema, o procedimento…"
          onChange={setDoc}
          onCtrlEnter={salvar}
          autoFocus
        />
        <div className="acoes">
          <button className="btn" onClick={() => { setDoc(t.descricao); setEditando(false) }}>Cancelar</button>
          <button className="btn btn-primario" disabled={salvando} onClick={salvar}>
            {salvando ? 'Salvando…' : 'Salvar descrição'}
          </button>
        </div>
      </div>
    )
  }
  if (!t.descricao) {
    return <button className="add-descricao" onClick={() => setEditando(true)}>Adicionar descrição…</button>
  }
  return (
    <div className="descricao descricao-view" onDoubleClick={() => setEditando(true)}>
      <button className="btn-icone editar-desc" title="Editar descrição" onClick={() => setEditando(true)}>
        <Pencil size={14} />
      </button>
      <RichView doc={t.descricao} projetoId={t.projeto_id} />
    </div>
  )
}

function textoAtividade(i: ItemTimeline, mapaL: Map<number, Label>, cats: ReturnType<typeof useCategorias>['data'],
                        usuarios: ReturnType<typeof useUsuarios>['data']) {
  const d = i.dados ?? {}
  const nomeUsuario = (id: number | null) => usuarios?.find((u) => u.id === id)?.nome ?? 'alguém'
  const cat = (id: number | null) => cats?.find((c) => c.id === id)
  switch (i.atividade) {
    case 'criou': return <>criou este ticket</>
    case 'moveu': return <>moveu de <b>{STATUS_NOME[d.de as Status]}</b> para <b>{STATUS_NOME[d.para as Status]}</b></>
    case 'titulo': return <>alterou o título de <i>“{d.de}”</i></>
    case 'descricao': return <>editou a descrição</>
    case 'categoria':
      return d.para ? <>definiu a categoria <CategoriaBadge cat={cat(d.para)} comNome /></> : <>removeu a categoria</>
    case 'responsavel':
      return d.para ? <>atribuiu a <b>{nomeUsuario(d.para)}</b></> : <>removeu o responsável</>
    case 'label_add': {
      const l = mapaL.get(d.label_id)
      return <>adicionou {l ? <LabelPill label={l} /> : 'uma label'}</>
    }
    case 'label_rem': {
      const l = mapaL.get(d.label_id)
      return <>removeu {l ? <LabelPill label={l} /> : 'uma label'}</>
    }
    default: return <>{i.atividade}</>
  }
}

function Timeline({ t }: { t: TicketDetalhe }) {
  const { data: itens, error } = useQuery({
    queryKey: ['timeline', t.id],
    queryFn: () => get<ItemTimeline[]>(`/api/tickets/${t.id}/timeline`),
  })
  const { data: labels } = useLabels()
  const { data: cats } = useCategorias()
  const { data: usuarios } = useUsuarios()
  const mapaL = useMemo(() => porId(labels), [labels])
  const [soComentarios, setSoComentarios] = useState(false)

  if (error) return <Erro erro={error} />
  if (!itens) return <Carregando />
  const visiveis = soComentarios ? itens.filter((i) => i.tipo === 'comentario') : itens
  let diaAnterior = ''
  return (
    <div className="timeline">
      <div className="timeline-topo">
        <button className="btn-link" onClick={() => setSoComentarios((v) => !v)}>
          {soComentarios ? 'Mostrar atividades' : 'Ocultar atividades'}
        </button>
      </div>
      {visiveis.map((i) => {
        const dia = diaRelativo(i.criado_em)
        const separador = dia !== diaAnterior
        diaAnterior = dia
        const u = i.usuario ? (usuarios?.find((x) => x.id === i.usuario!.id) ?? i.usuario) : null
        return (
          <Fragment key={`${i.tipo}-${i.id}`}>
            {separador && <div className="timeline-dia"><span>{dia}</span></div>}
            {i.tipo === 'atividade' ? (
              <div className="atividade">
                <Avatar u={u} tamanho={20} />
                <span><b>{u?.nome ?? 'Sistema'}</b> {textoAtividade(i, mapaL, cats, usuarios)}</span>
                <span className="hora" title={dataHora(i.criado_em)}>{hora(i.criado_em)}</span>
              </div>
            ) : (
              <Comentario i={i} u={u} t={t} />
            )}
          </Fragment>
        )
      })}
    </div>
  )
}

function Comentario({ i, u, t }: { i: ItemTimeline; u: ItemTimeline['usuario']; t: TicketDetalhe }) {
  const qc = useQueryClient()
  const [editando, setEditando] = useState(false)
  const [doc, setDoc] = useState<Doc | null>(i.conteudo ?? null)
  const [erro, setErro] = useState<unknown>(null)

  const salvar = async () => {
    setErro(null)
    try {
      await patch(`/api/comentarios/${i.id}`, { conteudo: doc })
      setEditando(false)
      qc.invalidateQueries({ queryKey: ['timeline', t.id] })
    } catch (e) {
      setErro(e)
    }
  }
  const excluir = async () => {
    if (!window.confirm('Excluir este comentário?')) return
    try {
      await del(`/api/comentarios/${i.id}`)
      qc.invalidateQueries({ queryKey: ['timeline', t.id] })
      qc.invalidateQueries({ queryKey: ['coluna', t.projeto_id] })
    } catch (e) {
      setErro(e)
    }
  }

  return (
    <div className="comentario">
      <Avatar u={u} tamanho={32} />
      <div className="comentario-corpo">
        <div className="comentario-topo">
          <b>{u?.nome ?? '—'}</b>
          <span className="hora" title={dataHora(i.criado_em)}>{hora(i.criado_em)}</span>
          {i.editado_em && <span className="suave pequeno" title={dataHora(i.editado_em)}>(editado)</span>}
          <span className="comentario-acoes">
            {i.pode_editar && !editando && (
              <button className="btn-icone" title="Editar" onClick={() => setEditando(true)}><Pencil size={13} /></button>
            )}
            {i.pode_excluir && (
              <button className="btn-icone" title="Excluir" onClick={excluir}><Trash2 size={13} /></button>
            )}
          </span>
        </div>
        {editando ? (
          <>
            <RichEditor ticketId={t.id} inicial={i.conteudo} onChange={setDoc} onCtrlEnter={salvar} autoFocus />
            <div className="acoes">
              <button className="btn" onClick={() => setEditando(false)}>Cancelar</button>
              <button className="btn btn-primario" onClick={salvar}>Salvar</button>
            </div>
          </>
        ) : (
          <RichView doc={i.conteudo} projetoId={t.projeto_id} />
        )}
        <Erro erro={erro} />
      </div>
    </div>
  )
}

function vazio(doc: Doc | null): boolean {
  if (!doc?.content?.length) return true
  const temConteudo = (n: RtNode): boolean =>
    !!(n.text?.trim()) || ['image', 'video', 'arquivo', 'horizontalRule'].includes(n.type) ||
    (n.content ?? []).some(temConteudo)
  return !doc.content.some(temConteudo)
}

function NovoComentario({ t }: { t: TicketDetalhe }) {
  const qc = useQueryClient()
  const [doc, setDoc] = useState<Doc | null>(null)
  const [versao, setVersao] = useState(0)
  const [enviando, setEnviando] = useState(false)
  const [erro, setErro] = useState<unknown>(null)
  const docRef = useRef(doc)
  docRef.current = doc

  const enviar = async () => {
    const atual = docRef.current
    if (vazio(atual) || enviando) return
    setEnviando(true)
    setErro(null)
    try {
      await post(`/api/tickets/${t.id}/comentarios`, { conteudo: atual })
      setDoc(null)
      setVersao((v) => v + 1)
      await qc.invalidateQueries({ queryKey: ['timeline', t.id] })
      qc.invalidateQueries({ queryKey: ['coluna', t.projeto_id] })
      const rolar = () => document.querySelector('.ticket-corpo')?.scrollTo({ top: 1e9, behavior: 'smooth' })
      setTimeout(rolar, 100)
      setTimeout(rolar, 600) // de novo, depois que as imagens carregam
    } catch (e) {
      setErro(e)
    } finally {
      setEnviando(false)
    }
  }

  return (
    <div className="novo-comentario">
      <RichEditor
        key={versao}
        ticketId={t.id}
        placeholder="Escreva um comentário… (Ctrl+Enter envia; cole ou arraste imagens e arquivos)"
        onChange={setDoc}
        onCtrlEnter={enviar}
        compacto
      />
      <Erro erro={erro} />
      <div className="acoes">
        <button className="btn btn-primario" disabled={enviando || vazio(doc)} onClick={enviar}>
          {enviando ? 'Enviando…' : 'Comentar'}
        </button>
      </div>
    </div>
  )
}
