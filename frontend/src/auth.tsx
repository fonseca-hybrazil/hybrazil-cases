import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { ApiError, get, post, quandoDeslogar, type Eu } from './api'

interface AuthCtx {
  eu: Eu | null
  carregando: boolean
  entrar: (login: string, senha: string, lembrar: boolean) => Promise<Eu>
  sair: () => Promise<void>
  atualizar: (eu: Eu) => void
  pode: (permissao: string) => boolean
}

const Ctx = createContext<AuthCtx | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [eu, setEu] = useState<Eu | null>(null)
  const [carregando, setCarregando] = useState(true)
  const qc = useQueryClient()

  useEffect(() => {
    get<Eu>('/api/auth/me')
      .then(setEu)
      .catch((e) => {
        if (!(e instanceof ApiError) || e.status !== 401) console.error(e)
      })
      .finally(() => setCarregando(false))
    quandoDeslogar(() => {
      setEu(null)
      qc.clear()
    })
  }, [qc])

  const entrar = useCallback(async (login: string, senha: string, lembrar: boolean) => {
    const r = await post<Eu>('/api/auth/login', { login, senha, lembrar })
    qc.clear()
    setEu(r)
    return r
  }, [qc])

  const sair = useCallback(async () => {
    try {
      await post('/api/auth/logout')
    } finally {
      setEu(null)
      qc.clear()
    }
  }, [qc])

  const pode = useCallback((p: string) => !!eu?.permissoes.includes(p), [eu])

  return (
    <Ctx.Provider value={{ eu, carregando, entrar, sair, atualizar: setEu, pode }}>{children}</Ctx.Provider>
  )
}

export function useAuth(): AuthCtx {
  const c = useContext(Ctx)
  if (!c) throw new Error('AuthProvider ausente')
  return c
}
