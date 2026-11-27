import { useState, type FormEvent } from 'react'
import { Navigate, useNavigate } from 'react-router-dom'
import { post, type Eu } from '../api'
import { useAuth } from '../auth'
import { Carregando, Erro } from '../components/comuns'

export function FormTrocarSenha({ aoConcluir }: { aoConcluir: (eu: Eu) => void }) {
  const [atual, setAtual] = useState('')
  const [nova, setNova] = useState('')
  const [conf, setConf] = useState('')
  const [erro, setErro] = useState<unknown>(null)
  const [ok, setOk] = useState(false)

  const enviar = async (e: FormEvent) => {
    e.preventDefault()
    setErro(null)
    setOk(false)
    if (nova !== conf) return setErro('A confirmação não confere com a nova senha.')
    try {
      const eu = await post<Eu>('/api/auth/trocar-senha', { senha_atual: atual, nova_senha: nova })
      setAtual(''); setNova(''); setConf('')
      setOk(true)
      aoConcluir(eu)
    } catch (err) {
      setErro(err)
    }
  }

  return (
    <form className="form" onSubmit={enviar}>
      <label>Senha atual
        <input type="password" value={atual} onChange={(e) => setAtual(e.target.value)} required autoComplete="current-password" />
      </label>
      <label>Nova senha (mínimo 8 caracteres)
        <input type="password" value={nova} onChange={(e) => setNova(e.target.value)} required minLength={8} autoComplete="new-password" />
      </label>
      <label>Confirme a nova senha
        <input type="password" value={conf} onChange={(e) => setConf(e.target.value)} required autoComplete="new-password" />
      </label>
      <Erro erro={erro} />
      {ok && <div className="sucesso">Senha alterada.</div>}
      <button className="btn btn-primario">Alterar senha</button>
    </form>
  )
}

export default function TrocarSenha() {
  const { eu, carregando, atualizar, sair } = useAuth()
  const nav = useNavigate()
  if (carregando) return <Carregando />
  if (!eu) return <Navigate to="/login" replace />
  return (
    <div className="tela-login">
      <div className="cartao-login">
        <h2>Defina uma nova senha</h2>
        <p className="suave">Olá, {eu.nome}. Por segurança, troque a senha inicial antes de continuar.</p>
        <FormTrocarSenha aoConcluir={(novo) => { atualizar(novo); nav('/', { replace: true }) }} />
        <button className="btn-link" onClick={() => sair().then(() => nav('/login'))}>Sair</button>
      </div>
    </div>
  )
}
