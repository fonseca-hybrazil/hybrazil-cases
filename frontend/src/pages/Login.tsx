import { useState, type FormEvent } from 'react'
import { Navigate, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth'
import { Erro } from '../components/comuns'

export default function Login() {
  const { eu, entrar } = useAuth()
  const [login, setLogin] = useState('')
  const [senha, setSenha] = useState('')
  const [lembrar, setLembrar] = useState(true)
  const [erro, setErro] = useState<unknown>(null)
  const [enviando, setEnviando] = useState(false)
  const nav = useNavigate()
  const de = (useLocation().state as { de?: string } | null)?.de ?? '/'

  if (eu) return <Navigate to={eu.trocar_senha ? '/trocar-senha' : de} replace />

  const enviar = async (e: FormEvent) => {
    e.preventDefault()
    setErro(null)
    setEnviando(true)
    try {
      const r = await entrar(login, senha, lembrar)
      nav(r.trocar_senha ? '/trocar-senha' : de, { replace: true })
    } catch (err) {
      setErro(err)
    } finally {
      setEnviando(false)
    }
  }

  return (
    <div className="tela-login">
      <form className="cartao-login" onSubmit={enviar}>
        <div className="logo logo-grande">
          <img src="/favicon.svg" alt="" width={40} height={40} />
          <span>HyBrazil <b>Cases</b></span>
        </div>
        <label>
          Usuário
          <input value={login} onChange={(e) => setLogin(e.target.value)} autoFocus autoComplete="username" required />
        </label>
        <label>
          Senha
          <input type="password" value={senha} onChange={(e) => setSenha(e.target.value)}
                 autoComplete="current-password" required />
        </label>
        <label className="check">
          <input type="checkbox" checked={lembrar} onChange={(e) => setLembrar(e.target.checked)} />
          Manter conectado
        </label>
        <Erro erro={erro} />
        <button className="btn btn-primario" disabled={enviando}>{enviando ? 'Entrando…' : 'Entrar'}</button>
      </form>
    </div>
  )
}
