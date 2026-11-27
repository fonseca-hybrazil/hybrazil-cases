// Cor do texto (preto/branco) legível sobre um fundo
export function corTexto(fundo: string): string {
  const m = /^#?([0-9a-f]{2})([0-9a-f]{2})([0-9a-f]{2})$/i.exec(fundo)
  if (!m) return '#fff'
  const [r, g, b] = [m[1], m[2], m[3]].map((h) => parseInt(h, 16) / 255)
  const lin = (c: number) => (c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4)
  const L = 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b)
  return L > 0.45 ? '#1f2328' : '#fff'
}

const fmtHora = new Intl.DateTimeFormat('pt-BR', { hour: '2-digit', minute: '2-digit' })
const fmtData = new Intl.DateTimeFormat('pt-BR', { day: '2-digit', month: 'short', year: 'numeric' })
const fmtDataHora = new Intl.DateTimeFormat('pt-BR', { dateStyle: 'short', timeStyle: 'short' })

export const hora = (iso: string) => fmtHora.format(new Date(iso))
export const data = (iso: string) => fmtData.format(new Date(iso))
export const dataHora = (iso: string) => fmtDataHora.format(new Date(iso))

export function diaRelativo(iso: string): string {
  const d = new Date(iso)
  const hoje = new Date()
  const ontem = new Date()
  ontem.setDate(hoje.getDate() - 1)
  if (d.toDateString() === hoje.toDateString()) return 'Hoje'
  if (d.toDateString() === ontem.toDateString()) return 'Ontem'
  return fmtData.format(d)
}

export function tamanhoArquivo(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 ** 2) return `${(bytes / 1024).toFixed(0)} KB`
  if (bytes < 1024 ** 3) return `${(bytes / 1024 ** 2).toFixed(1)} MB`
  return `${(bytes / 1024 ** 3).toFixed(2)} GB`
}

export function iniciais(nome: string): string {
  const p = nome.trim().split(/\s+/)
  return ((p[0]?.[0] ?? '') + (p.length > 1 ? p[p.length - 1][0] : '')).toUpperCase()
}

// Cor estável para o avatar sem foto
export function corDoNome(nome: string): string {
  const cores = ['#e5484d', '#f76b15', '#ffb224', '#30a46c', '#12a594', '#0091ff', '#3e63dd', '#8e4ec6', '#d6409f']
  let h = 0
  for (const c of nome) h = (h * 31 + c.charCodeAt(0)) >>> 0
  return cores[h % cores.length]
}

export const PALETA = [
  '#e5484d', '#f76b15', '#ffb224', '#f5d90a', '#99d52a', '#46a758', '#30a46c', '#12a594',
  '#05a2c2', '#0091ff', '#3e63dd', '#6e56cf', '#8e4ec6', '#ab4aba', '#d6409f', '#e93d82',
  '#ad7f58', '#978365', '#687076', '#1f2328',
]

// Reduz uma foto (ex.: do celular, vários MB) para no máximo `lado` px, em JPEG, antes de enviar como avatar.
export async function reduzirImagem(arquivo: File, lado = 512): Promise<File> {
  let bmp: ImageBitmap
  try {
    bmp = await createImageBitmap(arquivo)
  } catch {
    throw new Error('Não foi possível ler esta imagem. Use uma foto JPEG, PNG ou WebP.')
  }
  const escala = Math.min(1, lado / Math.max(bmp.width, bmp.height))
  const canvas = document.createElement('canvas')
  canvas.width = Math.round(bmp.width * escala)
  canvas.height = Math.round(bmp.height * escala)
  const ctx = canvas.getContext('2d')!
  ctx.fillStyle = '#fff'
  ctx.fillRect(0, 0, canvas.width, canvas.height)
  ctx.drawImage(bmp, 0, 0, canvas.width, canvas.height)
  bmp.close()
  const blob = await new Promise<Blob | null>((ok) => canvas.toBlob(ok, 'image/jpeg', 0.9))
  if (!blob) throw new Error('Falha ao processar a imagem.')
  return new File([blob], 'avatar.jpg', { type: 'image/jpeg' })
}
