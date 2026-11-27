import { mergeAttributes, Node } from '@tiptap/react'
import StarterKit from '@tiptap/starter-kit'
import { Color, TextStyle } from '@tiptap/extension-text-style'
import CodeBlockLowlight from '@tiptap/extension-code-block-lowlight'
import Image from '@tiptap/extension-image'
import { Placeholder } from '@tiptap/extensions'
import { common, createLowlight } from 'lowlight'

export const lowlight = createLowlight(common)

export const LINGUAGENS: [string, string][] = [
  ['', 'Automático'],
  ['plaintext', 'Texto'],
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
    CodeBlockLowlight.configure({ lowlight, defaultLanguage: null }),
    ImagemAnexo,
    VideoAnexo,
    ArquivoAnexo,
    Placeholder.configure({ placeholder }),
  ]
}
