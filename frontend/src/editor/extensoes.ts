import { mergeAttributes, Node } from '@tiptap/react'
import StarterKit from '@tiptap/starter-kit'
import { Color, TextStyle } from '@tiptap/extension-text-style'
import CodeBlockLowlight from '@tiptap/extension-code-block-lowlight'
import Image from '@tiptap/extension-image'
import { Placeholder } from '@tiptap/extensions'
import { common, createLowlight } from 'lowlight'
import vbscript from 'highlight.js/lib/languages/vbscript'
import st from './linguagens/st'
import elipse from './linguagens/elipse'

export const lowlight = createLowlight(common)
lowlight.register({ st, elipse, vbscript })
lowlight.registerAlias({ st: ['iecst', 'codesys', 'scl'], elipse: ['e3', 'e3script'], vbscript: ['vbs'] })

// Lista do editor. Digitando ``` + nome (ex.: ```st) o bloco já nasce com a linguagem.
export const LINGUAGENS: [string, string][] = [
  ['', 'Automático'],
  ['plaintext', 'Texto'],
  ['st', 'Texto Estruturado (CODESYS)'],
  ['elipse', 'VBScript (Elipse E3)'],
  ['vbscript', 'VBScript'],
  ['python', 'Python'],
  ['javascript', 'JavaScript'],
  ['typescript', 'TypeScript'],
  ['csharp', 'C#'],
  ['c', 'C'],
  ['cpp', 'C++'],
  ['java', 'Java'],
  ['vbnet', 'VB.NET'],
  ['sql', 'SQL'],
  ['json', 'JSON'],
  ['xml', 'XML / HTML'],
  ['css', 'CSS'],
  ['bash', 'Bash'],
  ['ini', 'INI / Config'],
  ['yaml', 'YAML'],
  ['markdown', 'Markdown'],
  ['diff', 'Diff'],
]

// No modo "Automático", a detecção só considera as linguagens da lista: entre as ~40 da biblioteca ela
// errava muito em trechos curtos (Python virava CSS, JavaScript virava INI).
const SUBCONJUNTO_AUTO = LINGUAGENS.map(([v]) => v).filter((v) => v && !['plaintext', 'diff', 'elipse'].includes(v))
export function destacarAuto(texto: string) {
  return lowlight.highlightAuto(texto, { subset: SUBCONJUNTO_AUTO })
}
// Versão do lowlight entregue ao editor, com a mesma detecção restrita.
const lowlightEditor: typeof lowlight = { ...lowlight, highlightAuto: (t, o) => lowlight.highlightAuto(t, { subset: SUBCONJUNTO_AUTO, ...o }) }

const anexoIdAttr = {
  anexoId: {
    default: null,
    parseHTML: (el: HTMLElement) => {
      const v = el.getAttribute('data-anexo-id')
      return v ? Number(v) : null
    },
    renderHTML: (attrs: Record<string, any>) => (attrs.anexoId ? { 'data-anexo-id': attrs.anexoId } : {}),
  },
}

export const ImagemAnexo = Image.extend({
  addAttributes() {
    return { ...this.parent?.(), ...anexoIdAttr }
  },
}).configure({ inline: false, allowBase64: false })

export const VideoAnexo = Node.create({
  name: 'video',
  group: 'block',
  atom: true,
  draggable: true,
  addAttributes() {
    return { src: { default: null }, nome: { default: null }, ...anexoIdAttr }
  },
  parseHTML() {
    return [{ tag: 'video[src]' }]
  },
  renderHTML({ HTMLAttributes }) {
    return ['video', mergeAttributes({ controls: 'true', preload: 'metadata', class: 'rt-video' }, HTMLAttributes)]
  },
})

export const ArquivoAnexo = Node.create({
  name: 'arquivo',
  group: 'block',
  atom: true,
  draggable: true,
  addAttributes() {
    return {
      src: { default: null },
      nome: { default: 'arquivo' },
      tamanho: { default: null },
      mime: { default: null },
      ...anexoIdAttr,
    }
  },
  parseHTML() {
    return [{ tag: 'a[data-arquivo]' }]
  },
  renderHTML({ HTMLAttributes, node }) {
    return ['a', mergeAttributes(HTMLAttributes, {
      'data-arquivo': 'true', href: node.attrs.src, class: 'rt-arquivo', target: '_blank', rel: 'noopener',
    }), `📎 ${node.attrs.nome}`]
  },
})

export function extensoes(placeholder: string) {
  return [
    StarterKit.configure({
      codeBlock: false,
      heading: { levels: [2, 3] },
      link: { openOnClick: false, autolink: true, defaultProtocol: 'https' },
    }),
    TextStyle,
    Color,
    CodeBlockLowlight.configure({ lowlight: lowlightEditor, defaultLanguage: null }),
    ImagemAnexo,
    VideoAnexo,
    ArquivoAnexo,
    Placeholder.configure({ placeholder }),
  ]
}
