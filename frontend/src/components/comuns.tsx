import { useEffect, useRef, useState, type ReactNode } from 'react'
import { X } from 'lucide-react'
import type { Categoria, Label, UsuarioBasico } from '../api'
import { IconeCategoria } from '../icones'
import { corDoNome, corTexto, iniciais, PALETA, reduzirImagem } from '../util'

export function Avatar({ u, tamanho = 24 }: { u: Pick<UsuarioBasico, 'nome' | 'avatar_url'> | null; tamanho?: number }) {
  if (!u) return null
  const estilo = { width: tamanho, height: tamanho, fontSize: tamanho * 0.42 }
  if (u.avatar_url) return <img className="avatar" src={u.avatar_url} alt={u.nome} title={u.nome} style={estilo} />
  return (
    <span className="avatar avatar-iniciais" title={u.nome} style={{ ...estilo, background: corDoNome(u.nome) }}>
      {iniciais(u.nome)}
    </span>
  )
}

export function LabelPill({ label, onRemover }: { label: Label; onRemover?: () => void }) {
  return (
    <span className="label-pill" style={{ background: label.cor, color: corTexto(label.cor) }}>
      {label.nome}
      {onRemover && (
        <button className="label-x" onClick={onRemover} title="Remover label" aria-label="Remover label">
          <X size={11} />
        </button>
      )}
    </span>
  )
}

export function CategoriaBadge({ cat, comNome = false }: { cat: Categoria | undefined; comNome?: boolean }) {
  if (!cat) return null
  return (
    <span className="cat-badge" title={cat.nome} style={{ background: cat.cor + '22' }}>
      <IconeCategoria nome={cat.icone} cor={cat.cor} tamanho={13} />
      {comNome && <span style={{ color: cat.cor }}>{cat.nome}</span>}
    </span>
  )
}

export function Modal({
  titulo, onFechar, children, largura = 520,
}: { titulo: ReactNode; onFechar: () => void; children: ReactNode; largura?: number }) {
  useEffect(() => {
    const k = (e: KeyboardEvent) => e.key === 'Escape' && onFechar()
    window.addEventListener('keydown', k)
    return () => window.removeEventListener('keydown', k)
  }, [onFechar])
  return (
    <div className="modal-fundo" onMouseDown={(e) => e.target === e.currentTarget && onFechar()}>
      <div className="modal" style={{ width: largura }} role="dialog" aria-modal="true">
        <div className="modal-topo">
          <h3>{titulo}</h3>
          <button className="btn-icone" onClick={onFechar} aria-label="Fechar"><X size={18} /></button>
        </div>
        <div className="modal-corpo">{children}</div>
      </div>
    </div>
  )
}

// Caixa flutuante ancorada a um botão; fecha ao clicar fora ou com Esc
export function Popover({
  aberto, onFechar, children, alinhar = 'esquerda',
}: { aberto: boolean; onFechar: () => void; children: ReactNode; alinhar?: 'esquerda' | 'direita' }) {
  const ref = useRef<HTMLDivElement>(null)
  useEffect(() => {
    if (!aberto) return
    const clique = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as globalThis.Node)) onFechar()
    }
    const tecla = (e: KeyboardEvent) => e.key === 'Escape' && onFechar()
    setTimeout(() => document.addEventListener('mousedown', clique), 0)
    document.addEventListener('keydown', tecla)
    return () => {
      document.removeEventListener('mousedown', clique)
      document.removeEventListener('keydown', tecla)
    }
  }, [aberto, onFechar])
  if (!aberto) return null
  return (
    <div ref={ref} className={`popover popover-${alinhar}`}>
      {children}
    </div>
  )
}

export function SeletorCor({ valor, onChange }: { valor: string; onChange: (c: string) => void }) {
  return (
    <div className="seletor-cor">
      {PALETA.map((c) => (
        <button
          key={c}
          type="button"
          className={'amostra' + (c === valor.toLowerCase() ? ' sel' : '')}
          style={{ background: c }}
          onClick={() => onChange(c)}
          aria-label={c}
        />
      ))}
      <label className="amostra amostra-custom" title="Outra cor">
        <input type="color" value={valor} onChange={(e) => onChange(e.target.value)} />
      </label>
    </div>
  )
}

export function Erro({ erro }: { erro: unknown }) {
  if (!erro) return null
  return <div className="erro">{erro instanceof Error ? erro.message : String(erro)}</div>
}

/** Foto do usuário com botões "Trocar foto" / "Remover". A imagem é reduzida no navegador antes do envio. */
export function EditorFoto({ u, enviar, remover }: {
  u: Pick<UsuarioBasico, 'nome' | 'avatar_url'>
  enviar: (f: File) => Promise<unknown>
  remover: () => Promise<unknown>
}) {
  const input = useRef<HTMLInputElement>(null)
  const [ocupado, setOcupado] = useState(false)
  const [erro, setErro] = useState<unknown>(null)
  const executar = async (acao: () => Promise<unknown>) => {
    setErro(null); setOcupado(true)
    try { await acao() } catch (e) { setErro(e) } finally { setOcupado(false) }
  }
  return (
    <div className="perfil-avatar">
      <Avatar u={u} tamanho={64} />
      <div>
        <button type="button" className="btn" disabled={ocupado} onClick={() => input.current?.click()}>
          {ocupado ? 'Enviando…' : u.avatar_url ? 'Trocar foto' : 'Enviar foto'}
        </button>
        {u.avatar_url && (
          <button type="button" className="btn-link" disabled={ocupado} onClick={() => executar(remover)}>Remover</button>
        )}
        <input ref={input} type="file" accept="image/*" hidden onChange={(e) => {
          const f = e.target.files?.[0]
          e.target.value = ''
          if (f) executar(async () => enviar(await reduzirImagem(f)))
        }} />
        <Erro erro={erro} />
      </div>
    </div>
  )
}

export function useConfirmar() {
  return (msg: string) => window.confirm(msg)
}

export function Carregando({ texto = 'Carregando…' }: { texto?: string }) {
  return <div className="carregando">{texto}</div>
}

export function useDebounce<T>(valor: T, ms = 300): T {
  const [v, setV] = useState(valor)
  useEffect(() => {
    const t = setTimeout(() => setV(valor), ms)
    return () => clearTimeout(t)
  }, [valor, ms])
  return v
}
