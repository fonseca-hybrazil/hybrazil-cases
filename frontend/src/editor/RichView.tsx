// Renderiza o documento do editor como React (sem HTML cru), com destaque de código e links #123.
import { Fragment, type ReactNode } from 'react'
import { Link } from 'react-router-dom'
import type { Doc, Node } from '../api'
import { tamanhoArquivo } from '../util'
import { lowlight } from './extensoes'

const COR_OK = /^(#[0-9a-f]{3,8}|rgba?\([\d\s.,%]+\))$/i
const URL_ANEXO = /^\/api\/anexos\/\d+\/arquivo$/

function urlSegura(href: unknown): string | null {
  if (typeof href !== 'string') return null
  const h = href.trim()
  if (URL_ANEXO.test(h) || /^(https?:|mailto:)/i.test(h)) return h
  if (/^[\w.-]+\.[a-z]{2,}(\/|$)/i.test(h)) return 'https://' + h
  return null
}

type HastNo = { type: string; value?: string; tagName?: string; properties?: { className?: string[] }; children?: HastNo[] }

function hast(n: HastNo, k: number): ReactNode {
  if (n.type === 'text') return n.value
  const filhos = (n.children ?? []).map(hast)
  if (n.type === 'element') return <span key={k} className={(n.properties?.className ?? []).join(' ')}>{filhos}</span>
  return <Fragment key={k}>{filhos}</Fragment>
}

function codigo(texto: string, lang: string | null): ReactNode {
  try {
    const arv = lang && lowlight.registered(lang) ? lowlight.highlight(lang, texto)
      : lang === 'plaintext' ? null : lowlight.highlightAuto(texto)
    if (!arv) return texto
    return (arv.children as HastNo[]).map(hast)
  } catch {
    return texto
  }
}

function comReferencias(texto: string, projetoId: number | undefined): ReactNode {
  if (!projetoId) return texto
  const partes: ReactNode[] = []
  const re = /(^|[^\w&/])#(\d{1,7})\b/g
  let ultimo = 0
  let m: RegExpExecArray | null
  while ((m = re.exec(texto))) {
    const ini = m.index + m[1].length
    partes.push(texto.slice(ultimo, ini))
    partes.push(<Link key={ini} className="ref-ticket" to={`/p/${projetoId}/t/${m[2]}`}>#{m[2]}</Link>)
    ultimo = ini + m[2].length + 1
  }
  if (!partes.length) return texto
  partes.push(texto.slice(ultimo))
  return partes
}

function texto(n: Node, k: number, projetoId?: number): ReactNode {
  const marks = n.marks ?? []
  const temCodigoOuLink = marks.some((m) => m.type === 'code' || m.type === 'link')
  let el: ReactNode = temCodigoOuLink ? n.text : comReferencias(n.text ?? '', projetoId)
  for (const m of marks) {
    switch (m.type) {
      case 'bold': el = <strong>{el}</strong>; break
      case 'italic': el = <em>{el}</em>; break
      case 'underline': el = <u>{el}</u>; break
      case 'strike': el = <s>{el}</s>; break
      case 'code': el = <code>{el}</code>; break
      case 'textStyle': {
        const cor = m.attrs?.color
        if (typeof cor === 'string' && COR_OK.test(cor)) el = <span style={{ color: cor }}>{el}</span>
        break
      }
      case 'link': {
        const href = urlSegura(m.attrs?.href)
        if (href) el = <a href={href} target="_blank" rel="noopener noreferrer">{el}</a>
        break
      }
    }
  }
  return <Fragment key={k}>{el}</Fragment>
}

function no(n: Node, k: number, projetoId?: number): ReactNode {
  const filhos = () => (n.content ?? []).map((f, i) => no(f, i, projetoId))
  const a = n.attrs ?? {}
  switch (n.type) {
    case 'text': return texto(n, k, projetoId)
    case 'paragraph': return <p key={k}>{filhos()}</p>
    case 'heading': return a.level === 3 ? <h3 key={k}>{filhos()}</h3> : <h2 key={k}>{filhos()}</h2>
    case 'bulletList': return <ul key={k}>{filhos()}</ul>
    case 'orderedList': return <ol key={k} start={Number(a.start) || 1}>{filhos()}</ol>
    case 'listItem': return <li key={k}>{filhos()}</li>
    case 'blockquote': return <blockquote key={k}>{filhos()}</blockquote>
    case 'hardBreak': return <br key={k} />
    case 'horizontalRule': return <hr key={k} />
    case 'codeBlock': {
      const t = (n.content ?? []).map((c) => c.text ?? '').join('')
      const lang = typeof a.language === 'string' ? a.language : null
      return (
        <pre key={k} data-lang={lang ?? undefined}><code className="hljs">{codigo(t, lang)}</code></pre>
      )
    }
    case 'image': {
      const src = urlSegura(a.src)
      if (!src) return null
      return (
        <a key={k} href={src} target="_blank" rel="noopener noreferrer" className="rt-img-link">
          <img src={src} alt={a.alt ?? ''} loading="lazy" />
        </a>
      )
    }
    case 'video': {
      const src = urlSegura(a.src)
      return src ? <video key={k} className="rt-video" src={src} controls preload="metadata" /> : null
    }
    case 'arquivo': {
      const src = urlSegura(a.src)
      if (!src) return null
      return (
        <a key={k} className="rt-arquivo" href={`${src}?download=1`}>
          <span className="rt-arquivo-icone">📎</span>
          <span className="rt-arquivo-nome">{a.nome}</span>
          {a.tamanho ? <span className="rt-arquivo-tam">{tamanhoArquivo(a.tamanho)}</span> : null}
          {src.startsWith('/api/') && /pdf/i.test(a.mime ?? '') && (
            <span className="rt-arquivo-abrir" onClick={(e) => { e.preventDefault(); window.open(src, '_blank') }}>
              abrir
            </span>
          )}
        </a>
      )
    }
    default: return <Fragment key={k}>{filhos()}</Fragment>
  }
}

export default function RichView({ doc, projetoId }: { doc: Doc | null | undefined; projetoId?: number }) {
  if (!doc?.content?.length) return null
  return <div className="rt rt-view">{doc.content.map((n, i) => no(n, i, projetoId))}</div>
}
