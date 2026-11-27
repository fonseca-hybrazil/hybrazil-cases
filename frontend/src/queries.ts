import { useQuery } from '@tanstack/react-query'
import { get, type Categoria, type Label, type Projeto, type UsuarioBasico } from './api'

export const useCategorias = () =>
  useQuery({ queryKey: ['categorias'], queryFn: () => get<Categoria[]>('/api/categorias'), staleTime: 60_000 })

export const useLabels = () =>
  useQuery({ queryKey: ['labels'], queryFn: () => get<Label[]>('/api/labels'), staleTime: 30_000 })

export const useUsuarios = () =>
  useQuery({ queryKey: ['usuarios'], queryFn: () => get<UsuarioBasico[]>('/api/usuarios'), staleTime: 60_000 })

export const useProjetos = () =>
  useQuery({ queryKey: ['projetos'], queryFn: () => get<Projeto[]>('/api/projetos'), staleTime: 15_000 })

export function porId<T extends { id: number }>(lista: T[] | undefined): Map<number, T> {
  return new Map((lista ?? []).map((x) => [x.id, x]))
}
