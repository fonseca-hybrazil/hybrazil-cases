// Visualizador de imagem em tela cheia: abre ajustada à tela; clicar na imagem alterna para o tamanho original.
import { useEffect, useState } from 'react'
import { createPortal } from 'react-dom'
import { ChevronLeft, ChevronRight, Download, ExternalLink, X } from 'lucide-react'

export interface ImagemLightbox { src: string; alt: string }

export default function Lightbox({ imagens, inicial, onFechar }: {
  imagens: ImagemLightbox[]
  inicial: number
  onFechar: () => void
}) {
  const [i, setI] = useState(inicial)
  const [original, setOriginal] = useState(false)
  const img = imagens[i]
  const varias = imagens.length > 1
  const ir = (d: number) => { setOriginal(false); setI((x) => (x + d + imagens.length) % imagens.length) }

  useEffect(() => {
    // captura no document: o Esc fecha só o visualizador, não o ticket por trás
    const tecla = (e: KeyboardEvent) => {
      if (e.key === 'Escape') { e.stopPropagation(); onFechar() }
      else if (varias && e.key === 'ArrowLeft') { e.stopPropagation(); ir(-1) }
      else if (varias && e.key === 'ArrowRight') { e.stopPropagation(); ir(1) }
    }
    document.addEventListener('keydown', tecla, true)
    return () => document.removeEventListener('keydown', tecla, true)
  })

  if (!img) return null
  const download = img.src.startsWith('/api/') ? `${img.src}?download=1` : img.src
  return createPortal(
    // o portal ainda propaga eventos pela árvore React: não deixa o clique chegar ao comentário/ticket por trás
    <div className="lightbox" role="dialog" aria-label="Imagem ampliada"
         onClick={(e) => { e.stopPropagation(); onFechar() }}
         onDoubleClick={(e) => e.stopPropagation()} onMouseDown={(e) => e.stopPropagation()}>
      <div className="lightbox-barra" onClick={(e) => e.stopPropagation()}>
        <span className="lightbox-nome">{img.alt || 'imagem'}{varias && ` · ${i + 1}/${imagens.length}`}</span>
        <a href={img.src} target="_blank" rel="noopener noreferrer" title="Abrir em nova aba"><ExternalLink size={18} /></a>
        <a href={download} title="Baixar"><Download size={18} /></a>
        <button type="button" onClick={onFechar} title="Fechar (Esc)"><X size={20} /></button>
      </div>
      <div className={original ? 'lightbox-area original' : 'lightbox-area'}>
        <img src={img.src} alt={img.alt}
             title={original ? 'Clique para ajustar à tela' : 'Clique para ver no tamanho original'}
             onClick={(e) => { e.stopPropagation(); setOriginal((o) => !o) }} />
      </div>
      {varias && <>
        <button type="button" className="lightbox-nav esq" title="Anterior (←)" onClick={(e) => { e.stopPropagation(); ir(-1) }}><ChevronLeft size={28} /></button>
        <button type="button" className="lightbox-nav dir" title="Próxima (→)" onClick={(e) => { e.stopPropagation(); ir(1) }}><ChevronRight size={28} /></button>
      </>}
    </div>,
    document.body,
  )
}
