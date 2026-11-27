import { useRef, useState } from 'react'
import { EditorContent, useEditor, useEditorState, type Editor } from '@tiptap/react'
import {
  Bold, Code, FileCode2, Heading2, Heading3, Italic, Link2, List, ListChecks, ListOrdered, Minus, Paperclip, Palette, Quote,
  Strikethrough, Underline, Loader2,
} from 'lucide-react'
import { enviarArquivo, type Anexo, type Doc } from '../api'
import { Popover } from '../components/comuns'
import { PALETA } from '../util'
import { extensoes, LINGUAGENS } from './extensoes'

interface Props {
  ticketId: number
  inicial?: Doc | null
  placeholder?: string
  onChange?: (doc: Doc) => void
  onCtrlEnter?: () => void
  autoFocus?: boolean
  compacto?: boolean
}

// O navegador sabe tocar este vídeo? (MP4/H.264, WebM e Ogg sim; AVI, MKV e WMV não, viram cartão para baixar)
function videoTocavel(mime: string): boolean {
  return mime.startsWith('video/') && document.createElement('video').canPlayType(mime) !== ''
}

export function inserirAnexo(editor: Editor, a: Anexo) {
  const attrs = { src: a.url, anexoId: a.id, nome: a.nome }
  const no = a.tipo_mime.startsWith('image/')
    ? { type: 'image', attrs: { src: a.url, alt: a.nome, anexoId: a.id } }
    : videoTocavel(a.tipo_mime)
      ? { type: 'video', attrs }
      : { type: 'arquivo', attrs: { ...attrs, tamanho: a.tamanho, mime: a.tipo_mime } }
  // insere depois da seleção atual (sem substituir um anexo recém-inserido que esteja selecionado)
  const pos = editor.state.selection.to
  editor.chain().focus().insertContentAt(pos, no).run()
}

export default function RichEditor({
  ticketId, inicial, placeholder = 'Escreva…', onChange, onCtrlEnter, autoFocus, compacto,
}: Props) {
  const [enviando, setEnviando] = useState(0)
  const [erro, setErro] = useState<string | null>(null)
  const ctrlEnter = useRef(onCtrlEnter)
  ctrlEnter.current = onCtrlEnter

  const enviar = async (arquivos: File[], editor: Editor) => {
    setErro(null)
    for (const f of arquivos) {
      setEnviando((n) => n + 1)
      try {
        const a = await enviarArquivo<Anexo>(`/api/tickets/${ticketId}/anexos`, f)
        inserirAnexo(editor, a)
      } catch (e) {
        setErro(`Falha ao enviar "${f.name}": ${e instanceof Error ? e.message : e}`)
      } finally {
        setEnviando((n) => n - 1)
      }
    }
  }
  const enviarRef = useRef(enviar)
  enviarRef.current = enviar

  const editor = useEditor({
    extensions: extensoes(placeholder),
    content: inicial ?? '',
    autofocus: autoFocus ? 'end' : false,
    onUpdate: ({ editor }) => onChange?.(editor.getJSON() as Doc),
    editorProps: {
      attributes: { class: 'rt rt-editor' + (compacto ? ' compacto' : '') },
      handleKeyDown: (_v, e) => {
        if (e.key === 'Enter' && (e.ctrlKey || e.metaKey) && ctrlEnter.current) {
          ctrlEnter.current()
          return true
        }
        return false
      },
      handlePaste: (_v, e) => {
        const arquivos = Array.from(e.clipboardData?.files ?? [])
        if (arquivos.length && editorRef.current) {
          enviarRef.current(arquivos, editorRef.current)
          return true
        }
        return false
      },
      handleDrop: (_v, e) => {
        const arquivos = Array.from((e as DragEvent).dataTransfer?.files ?? [])
        if (arquivos.length && editorRef.current) {
          e.preventDefault()
          enviarRef.current(arquivos, editorRef.current)
          return true
        }
        return false
      },
    },
  })
  const editorRef = useRef<Editor | null>(null)
  editorRef.current = editor

  if (!editor) return null
  return (
    <div className="editor-caixa">
      <Barra editor={editor} onArquivos={(fs) => enviar(fs, editor)} enviando={enviando > 0} />
      <EditorContent editor={editor} />
      {erro && <div className="erro pequeno">{erro}</div>}
    </div>
  )
}

function Barra({ editor, onArquivos, enviando }: { editor: Editor; onArquivos: (f: File[]) => void; enviando: boolean }) {
  const [corAberta, setCorAberta] = useState(false)
  const inputArquivo = useRef<HTMLInputElement>(null)
  const s = useEditorState({
    editor,
    selector: ({ editor: e }) => ({
      bold: e.isActive('bold'),
      italic: e.isActive('italic'),
      underline: e.isActive('underline'),
      strike: e.isActive('strike'),
      code: e.isActive('code'),
      h2: e.isActive('heading', { level: 2 }),
      h3: e.isActive('heading', { level: 3 }),
      ul: e.isActive('bulletList'),
      ol: e.isActive('orderedList'),
      tarefas: e.isActive('taskList'),
      quote: e.isActive('blockquote'),
      codeBlock: e.isActive('codeBlock'),
      lang: (e.getAttributes('codeBlock').language as string | null) ?? '',
      link: e.isActive('link'),
      cor: (e.getAttributes('textStyle').color as string | undefined) ?? null,
    }),
  })

  const B = ({ ativo, titulo, onClick, children }: {
    ativo?: boolean; titulo: string; onClick: () => void; children: React.ReactNode
  }) => (
    <button
      type="button"
      className={'tb-btn' + (ativo ? ' ativo' : '')}
      title={titulo}
      aria-label={titulo}
      onMouseDown={(e) => { e.preventDefault(); e.stopPropagation() }}
      onClick={onClick}
    >
      {children}
    </button>
  )

  const link = () => {
    const atual = editor.getAttributes('link').href as string | undefined
    const url = window.prompt('Endereço do link (deixe vazio para remover):', atual ?? 'https://')
    if (url === null) return
    if (!url.trim() || url.trim() === 'https://') editor.chain().focus().extendMarkRange('link').unsetLink().run()
    else editor.chain().focus().extendMarkRange('link').setLink({ href: url.trim() }).run()
  }

  const c = () => editor.chain().focus()
  return (
    <div className="editor-barra">
      <B titulo="Negrito (Ctrl+B)" ativo={s.bold} onClick={() => c().toggleBold().run()}><Bold size={15} /></B>
      <B titulo="Itálico (Ctrl+I)" ativo={s.italic} onClick={() => c().toggleItalic().run()}><Italic size={15} /></B>
      <B titulo="Sublinhado (Ctrl+U)" ativo={s.underline} onClick={() => c().toggleUnderline().run()}><Underline size={15} /></B>
      <B titulo="Riscado" ativo={s.strike} onClick={() => c().toggleStrike().run()}><Strikethrough size={15} /></B>
      <span className="tb-rel">
        <B titulo="Cor do texto" ativo={!!s.cor} onClick={() => setCorAberta((v) => !v)}>
          <Palette size={15} color={s.cor ?? undefined} />
        </B>
        <Popover aberto={corAberta} onFechar={() => setCorAberta(false)}>
          <div className="seletor-cor">
            {PALETA.map((cor) => (
              <button
                key={cor}
                type="button"
                className="amostra"
                style={{ background: cor }}
                onMouseDown={(e) => e.preventDefault()}
                onClick={() => { c().setColor(cor).run(); setCorAberta(false) }}
                aria-label={cor}
              />
            ))}
          </div>
          <button type="button" className="btn-link" onClick={() => { c().unsetColor().run(); setCorAberta(false) }}>
            Remover cor
          </button>
        </Popover>
      </span>
      <span className="tb-sep" />
      <B titulo="Título" ativo={s.h2} onClick={() => c().toggleHeading({ level: 2 }).run()}><Heading2 size={15} /></B>
      <B titulo="Subtítulo" ativo={s.h3} onClick={() => c().toggleHeading({ level: 3 }).run()}><Heading3 size={15} /></B>
      <B titulo="Lista" ativo={s.ul} onClick={() => c().toggleBulletList().run()}><List size={15} /></B>
      <B titulo="Lista numerada" ativo={s.ol} onClick={() => c().toggleOrderedList().run()}><ListOrdered size={15} /></B>
      <B titulo="Lista de tarefas (ou digite [ ] e espaço)" ativo={s.tarefas} onClick={() => c().toggleTaskList().run()}><ListChecks size={15} /></B>
      <B titulo="Citação" ativo={s.quote} onClick={() => c().toggleBlockquote().run()}><Quote size={15} /></B>
      <B titulo="Linha divisória" onClick={() => c().setHorizontalRule().run()}><Minus size={15} /></B>
      <span className="tb-sep" />
      <B titulo="Código na linha" ativo={s.code} onClick={() => c().toggleCode().run()}><Code size={15} /></B>
      <B titulo="Bloco de código" ativo={s.codeBlock} onClick={() => c().toggleCodeBlock().run()}><FileCode2 size={15} /></B>
      {s.codeBlock && (
        <select
          className="tb-select"
          value={s.lang}
          onChange={(e) => c().updateAttributes('codeBlock', { language: e.target.value || null }).run()}
          title="Linguagem do código"
        >
          {LINGUAGENS.map(([v, n]) => <option key={v} value={v}>{n}</option>)}
        </select>
      )}
      <B titulo="Link" ativo={s.link} onClick={link}><Link2 size={15} /></B>
      <span className="tb-sep" />
      <B titulo="Anexar fotos, vídeos ou arquivos" onClick={() => inputArquivo.current?.click()}>
        {enviando ? <Loader2 size={15} className="girando" /> : <Paperclip size={15} />}
      </B>
      <input
        ref={inputArquivo}
        type="file"
        multiple
        hidden
        onChange={(e) => {
          const fs = Array.from(e.target.files ?? [])
          e.target.value = ''
          if (fs.length) onArquivos(fs)
        }}
      />
    </div>
  )
}
