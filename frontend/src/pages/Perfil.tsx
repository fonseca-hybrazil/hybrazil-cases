import { useRef, useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { del, enviarArquivo, patch, type Eu } from '../api'
import { useAuth } from '../auth'
import { Avatar, Erro } from '../components/comuns'
import { FormTrocarSenha } from './TrocarSenha'

export default function Perfil() {
  const { eu, atualizar } = useAuth()
  const qc = useQueryClient()
  const [nome, setNome] = useState(eu?.nome ?? '')
  const [email, setEmail] = useState(eu?.email ?? '')
  const [erro, setErro] = useState<unknown>(null)
  const [ok, setOk] = useState(false)
  const arquivo = useRef<HTMLInputElement>(null)
  if (!eu) return null

  const pronto = (novo: Eu) => {
    atualizar(novo)
    qc.invalidateQueries({ queryKey: ['usuarios'] })
  }

  return (
    <div className="pagina pagina-estreita">
      <h1>Meu perfil</h1>
      <section className="painel">
        <h2>Dados</h2>
        <div className="perfil-avatar">
          <Avatar u={eu} tamanho={64} />
          <div>
            <button className="btn" onClick={() => arquivo.current?.click()}>Trocar foto</button>
            {eu.avatar_url && (
              <button className="btn-link" onClick={async () => pronto(await del<Eu>('/api/auth/avatar'))}>Remover</button>
            )}
            <input ref={arquivo} type="file" accept="image/png,image/jpeg" hidden onChange={async (e) => {
              const f = e.target.files?.[0]
              e.target.value = ''
              if (!f) return
              try { pronto(await enviarArquivo<Eu>('/api/auth/avatar', f)) } catch (err) { setErro(err) }
            }} />
          </div>
        </div>
        <form className="form" onSubmit={async (e) => {
          e.preventDefault()
          setErro(null); setOk(false)
          try {
            pronto(await patch<Eu>('/api/auth/perfil', { nome, email: email || null }))
            setOk(true)
          } catch (err) { setErro(err) }
        }}>
          <label>Login<input value={eu.login} disabled /></label>
          <label>Nome<input value={nome} onChange={(e) => setNome(e.target.value)} required /></label>
          <label>E-mail<input type="email" value={email} onChange={(e) => setEmail(e.target.value)} /></label>
          <Erro erro={erro} />
          {ok && <div className="sucesso">Dados salvos.</div>}
          <button className="btn btn-primario">Salvar</button>
        </form>
      </section>
      <section className="painel" id="senha">
        <h2>Trocar senha</h2>
        <FormTrocarSenha aoConcluir={atualizar} />
      </section>
    </div>
  )
}
