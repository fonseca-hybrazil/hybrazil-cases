// Cliente da API e tipos compartilhados.

export type Status = 'pendente' | 'andamento' | 'completado'
export const STATUS: Status[] = ['pendente', 'andamento', 'completado']
export const STATUS_NOME: Record<Status, string> = {
  pendente: 'Pendências',
  andamento: 'Doing',
  completado: 'Completadas',
}

export type Doc = { type: 'doc'; content?: Node[] }
export type Node = {
  type: string
  text?: string
  attrs?: Record<string, any>
  marks?: { type: string; attrs?: Record<string, any> }[]
  content?: Node[]
}

export interface UsuarioBasico {
  id: number
  nome: string
  login: string
  avatar_url: string | null
  ativo: boolean
}

export interface Eu extends UsuarioBasico {
  email: string | null
  trocar_senha: boolean
  permissoes: string[]
}

export interface UsuarioAdmin extends UsuarioBasico {
  email: string | null
  trocar_senha: boolean
  ultimo_acesso: string | null
  bloqueado_ate: string | null
  criado_em: string
  grupos: { id: number; nome: string }[]
}

export interface Grupo {
  id: number
  nome: string
  descricao: string
  permissoes: string[]
  sistema: boolean
  usuario_ids: number[]
}

export interface Permissao {
  chave: string
  descricao: string
}

export interface Categoria {
  id: number
  nome: string
  icone: string
  cor: string
  ordem: number
  ativa: boolean
}

export interface Label {
  id: number
  nome: string
  cor: string
}

export interface Projeto {
  id: number
  nome: string
  descricao: string
  arquivado: boolean
  favorito: boolean
  contagem: Record<Status, number>
}

export interface TicketResumo {
  id: number
  projeto_id: number
  numero: number
  titulo: string
  status: Status
  categoria_id: number | null
  responsavel: UsuarioBasico | null
  label_ids: number[]
  qtd_comentarios: number
  tem_descricao: boolean
  tarefas_total: number
  tarefas_feitas: number
  ordem: number
  criado_em: string
  concluido_em: string | null
}

export interface TicketDetalhe extends TicketResumo {
  descricao: Doc | null
  criado_por: UsuarioBasico | null
  atualizado_em: string
  pode_excluir: boolean
}

export interface Coluna {
  total: number
  tickets: TicketResumo[]
}

export type Quadro = Record<Status, Coluna> & { total_sem_filtro: Record<Status, number> }

export interface ItemTimeline {
  tipo: 'comentario' | 'atividade'
  id: number
  criado_em: string
  usuario: UsuarioBasico | null
  conteudo?: Doc | null
  editado_em?: string | null
  pode_editar: boolean
  pode_excluir: boolean
  atividade?: string | null
  dados?: Record<string, any> | null
}

export interface Anexo {
  id: number
  nome: string
  tipo_mime: string
  tamanho: number
  url: string
  criado_em: string
}

export class ApiError extends Error {
  status: number
  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

function mensagemDeErro(status: number, corpo: any): string {
  const d = corpo?.detail
  if (typeof d === 'string') return d
  if (Array.isArray(d) && d.length) {
    const campo = d[0]?.loc?.slice(-1)[0]
    return `Dados inválidos${campo ? ` (${campo})` : ''}: ${d[0]?.msg ?? ''}`
  }
  if (status === 413) return 'Arquivo grande demais.'
  return `Erro ${status}`
}

// Avisado quando a sessão expira (401) ou quando é preciso trocar a senha (403 específico)
let aoDeslogar: (() => void) | null = null
export function quandoDeslogar(fn: () => void) {
  aoDeslogar = fn
}

export async function api<T = any>(metodo: string, url: string, corpo?: unknown): Promise<T> {
  const init: RequestInit = { method: metodo, credentials: 'same-origin', headers: {} }
  if (corpo instanceof FormData) {
    init.body = corpo
  } else if (corpo !== undefined) {
    init.body = JSON.stringify(corpo)
    ;(init.headers as Record<string, string>)['Content-Type'] = 'application/json'
  }
  const r = await fetch(url, init)
  if (r.status === 204) return undefined as T
  let dados: any = null
  try {
    dados = await r.json()
  } catch {
    /* sem corpo */
  }
  if (!r.ok) {
    if (r.status === 401 && !url.startsWith('/api/auth/login')) aoDeslogar?.()
    throw new ApiError(r.status, mensagemDeErro(r.status, dados))
  }
  return dados as T
}

export const get = <T = any>(url: string) => api<T>('GET', url)
export const post = <T = any>(url: string, corpo?: unknown) => api<T>('POST', url, corpo)
export const patch = <T = any>(url: string, corpo?: unknown) => api<T>('PATCH', url, corpo)
export const put = <T = any>(url: string, corpo?: unknown) => api<T>('PUT', url, corpo)
export const del = <T = any>(url: string) => api<T>('DELETE', url)

export function enviarArquivo<T = any>(url: string, arquivo: File): Promise<T> {
  const fd = new FormData()
  fd.append('arquivo', arquivo)
  return post<T>(url, fd)
}

// ------------------------------------------------------------------ filtros
export interface Filtros {
  label: number[]
  labels_modo: 'qualquer' | 'todas'
  categoria: number[]
  responsavel: number[]
  q: string
  numero: string
}

export const FILTROS_VAZIOS: Filtros = {
  label: [],
  labels_modo: 'qualquer',
  categoria: [],
  responsavel: [],
  q: '',
  numero: '',
}

export function filtrosAtivos(f: Filtros): boolean {
  return !!(f.label.length || f.categoria.length || f.responsavel.length || f.q.trim() || f.numero.trim())
}

export function filtrosParaParams(f: Filtros): URLSearchParams {
  const p = new URLSearchParams()
  f.label.forEach((v) => p.append('label', String(v)))
  if (f.label.length > 1 && f.labels_modo === 'todas') p.set('labels_modo', 'todas')
  f.categoria.forEach((v) => p.append('categoria', String(v)))
  f.responsavel.forEach((v) => p.append('responsavel', String(v)))
  if (f.q.trim()) p.set('q', f.q.trim())
  const n = f.numero.replace(/[^0-9]/g, '')
  if (n) p.set('numero', n)
  return p
}

export function filtrosDeParams(p: URLSearchParams): Filtros {
  const nums = (k: string) => p.getAll(k).map(Number).filter((n) => Number.isFinite(n))
  return {
    label: nums('label'),
    labels_modo: p.get('labels_modo') === 'todas' ? 'todas' : 'qualquer',
    categoria: nums('categoria'),
    responsavel: nums('responsavel'),
    q: p.get('q') ?? '',
    numero: p.get('numero') ?? '',
  }
}
