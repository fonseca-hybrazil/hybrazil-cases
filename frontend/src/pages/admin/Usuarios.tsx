import { useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { KeyRound, Pencil, Plus } from 'lucide-react'
import { del, enviarArquivo, get, patch, post, type Eu, type Grupo, type UsuarioAdmin } from '../../api'
import { useAuth } from '../../auth'
import { Avatar, Carregando, EditorFoto, Erro, Modal } from '../../components/comuns'
import { dataHora } from '../../util'

function senhaAleatoria(): string {
  const c = 'abcdefghjkmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789'
  const a = new Uint32Array(12)
  crypto.getRandomValues(a)
  return Array.from(a, (n) => c[n % c.length]).join('')
}

export default function AdminUsuarios() {
  const qc = useQueryClient()
  const { eu } = useAuth()
  const usuarios = useQuery({ queryKey: ['admin-usuarios'], queryFn: () => get<UsuarioAdmin[]>('/api/admin/usuarios') })
  const grupos = useQuery({ queryKey: ['admin-grupos'], queryFn: () => get<Grupo[]>('/api/admin/grupos') })
  const [editando, setEditando] = useState<UsuarioAdmin | 'novo' | null>(null)
  const [senhaDe, setSenhaDe] = useState<UsuarioAdmin | null>(null)
  const [mostrarInativos, setMostrarInativos] = useState(false)

  const recarregar = () => {
    qc.invalidateQueries({ queryKey: ['admin-usuarios'] })
    qc.invalidateQueries({ queryKey: ['admin-grupos'] })
    qc.invalidateQueries({ queryKey: ['usuarios'] })
  }

  if (usuarios.isLoading) return <Carregando />
  const lista = (usuarios.data ?? []).filter((u) => mostrarInativos || u.ativo)

  return (
    <div className="pagina">
      <div className="pagina-topo">
        <h1>Usuários</h1>
        <label className="check">
          <input type="checkbox" checked={mostrarInativos} onChange={(e) => setMostrarInativos(e.target.checked)} />
          Mostrar desativados
        </label>
        <button className="btn btn-primario" onClick={() => setEditando('novo')}><Plus size={16} /> Novo usuário</button>
      </div>
      <Erro erro={usuarios.error} />
      <table className="tabela">
        <thead>
          <tr><th /><th>Nome</th><th>Login</th><th>Grupos</th><th>Último acesso</th><th>Situação</th><th /></tr>
        </thead>
        <tbody>
          {lista.map((u) => (
            <tr key={u.id} className={u.ativo ? '' : 'inativo'}>
              <td><Avatar u={u} tamanho={26} /></td>
              <td>{u.nome}{u.id === eu?.id && <span className="suave"> (você)</span>}<div className="suave pequeno">{u.email}</div></td>
              <td>{u.login}</td>
              <td>{u.grupos.map((g) => <span key={g.id} className="chip">{g.nome}</span>)}</td>
              <td className="pequeno">{u.ultimo_acesso ? dataHora(u.ultimo_acesso) : '—'}</td>
              <td className="pequeno">
                {!u.ativo ? 'Desativado' : u.trocar_senha ? 'Aguardando troca de senha' : 'Ativo'}
                {u.bloqueado_ate && new Date(u.bloqueado_ate) > new Date() && <div className="erro-texto">Bloqueado</div>}
              </td>
              <td className="acoes-linha">
                <button className="btn-icone" title="Editar" onClick={() => setEditando(u)}><Pencil size={15} /></button>
                <button className="btn-icone" title="Redefinir senha" onClick={() => setSenhaDe(u)}><KeyRound size={15} /></button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {editando && (
        <FormUsuario
          usuario={editando === 'novo' ? null : editando}
          grupos={grupos.data ?? []}
          onFotoAlterada={recarregar}
          onFechar={() => setEditando(null)}
          onSalvo={() => { setEditando(null); recarregar() }}
        />
      )}
      {senhaDe && <RedefinirSenha usuario={senhaDe} onFechar={() => { setSenhaDe(null); recarregar() }} />}
    </div>
  )
}

function FormUsuario({ usuario, grupos, onFechar, onSalvo, onFotoAlterada }: {
  usuario: UsuarioAdmin | null; grupos: Grupo[]; onFechar: () => void; onSalvo: () => void; onFotoAlterada: () => void
}) {
  const { eu, atualizar } = useAuth()
  const [foto, setFoto] = useState(usuario?.avatar_url ?? null)
  const fotoAlterada = async (novo: UsuarioAdmin) => {
    setFoto(novo.avatar_url)
    onFotoAlterada()
    if (novo.id === eu?.id) atualizar(await get<Eu>('/api/auth/me'))  // atualiza a foto na barra lateral
  }
  const [nome, setNome] = useState(usuario?.nome ?? '')
  const [login, setLogin] = useState(usuario?.login ?? '')
  const [email, setEmail] = useState(usuario?.email ?? '')
  const [ativo, setAtivo] = useState(usuario?.ativo ?? true)
  const padrao = grupos.find((g) => g.nome === 'Usuários')
  const [gids, setGids] = useState<number[]>(usuario?.grupos.map((g) => g.id) ?? (padrao ? [padrao.id] : []))
  const [senha] = useState(senhaAleatoria)
  const [erro, setErro] = useState<unknown>(null)
  const [criado, setCriado] = useState(false)

  const salvar = async () => {
    setErro(null)
    try {
      if (usuario) {
        await patch(`/api/admin/usuarios/${usuario.id}`, { nome, login, email: email || null, ativo, grupo_ids: gids })
        onSalvo()
      } else {
        await post('/api/admin/usuarios', { nome, login, email: email || null, senha, grupo_ids: gids })
        setCriado(true)
      }
    } catch (e) {
      setErro(e)
    }
  }

  if (criado) {
    return (
      <Modal titulo="Usuário criado" onFechar={onSalvo}>
        <p>Informe ao usuário os dados de acesso. Ele deverá trocar a senha no primeiro login.</p>
        <div className="caixa-senha">
          <div>Login: <b>{login}</b></div>
          <div>Senha inicial: <code>{senha}</code></div>
        </div>
        <div className="acoes">
          <button className="btn" onClick={() => navigator.clipboard?.writeText(`Login: ${login}\nSenha: ${senha}`)}>
            Copiar
          </button>
          <button className="btn btn-primario" onClick={onSalvo}>Concluir</button>
        </div>
      </Modal>
    )
  }

  return (
    <Modal titulo={usuario ? `Editar ${usuario.nome}` : 'Novo usuário'} onFechar={onFechar}>
      {usuario && (
        <EditorFoto
          u={{ nome: usuario.nome, avatar_url: foto }}
          enviar={async (f) => fotoAlterada(await enviarArquivo<UsuarioAdmin>(`/api/admin/usuarios/${usuario.id}/avatar`, f))}
          remover={async () => fotoAlterada(await del<UsuarioAdmin>(`/api/admin/usuarios/${usuario.id}/avatar`))}
        />
      )}
      <form className="form" onSubmit={(e) => { e.preventDefault(); salvar() }}>
        <label>Nome<input value={nome} onChange={(e) => setNome(e.target.value)} required autoFocus /></label>
        <label>Login<input value={login} onChange={(e) => setLogin(e.target.value)} required pattern="[A-Za-z0-9._@\-]+"
                            title="Letras, números, ponto, hífen, @ e sublinhado" /></label>
        <label>E-mail<input type="email" value={email} onChange={(e) => setEmail(e.target.value)} /></label>
        <fieldset>
          <legend>Grupos</legend>
          {grupos.map((g) => (
            <label key={g.id} className="check">
              <input type="checkbox" checked={gids.includes(g.id)}
                     onChange={() => setGids(gids.includes(g.id) ? gids.filter((x) => x !== g.id) : [...gids, g.id])} />
              {g.nome} <span className="suave pequeno">— {g.descricao}</span>
            </label>
          ))}
        </fieldset>
        {usuario && (
          <label className="check">
            <input type="checkbox" checked={ativo} onChange={(e) => setAtivo(e.target.checked)} />
            Ativo (desmarque para bloquear o acesso; o histórico é mantido)
          </label>
        )}
        {!usuario && <p className="suave pequeno">Uma senha inicial será gerada e mostrada após salvar.</p>}
        <Erro erro={erro} />
        <div className="acoes">
          <button type="button" className="btn" onClick={onFechar}>Cancelar</button>
          <button className="btn btn-primario">Salvar</button>
        </div>
      </form>
    </Modal>
  )
}

function RedefinirSenha({ usuario, onFechar }: { usuario: UsuarioAdmin; onFechar: () => void }) {
  const [senha] = useState(senhaAleatoria)
  const [feito, setFeito] = useState(false)
  const [erro, setErro] = useState<unknown>(null)
  return (
    <Modal titulo={`Redefinir senha de ${usuario.nome}`} onFechar={onFechar}>
      {feito ? (
        <>
          <p>Senha redefinida. O usuário deverá trocá-la no próximo acesso.</p>
          <div className="caixa-senha">
            <div>Login: <b>{usuario.login}</b></div>
            <div>Nova senha: <code>{senha}</code></div>
          </div>
          <div className="acoes"><button className="btn btn-primario" onClick={onFechar}>Concluir</button></div>
        </>
      ) : (
        <>
          <p>Uma nova senha temporária será gerada, as sessões abertas do usuário serão encerradas e o bloqueio por
            tentativas (se houver) será removido.</p>
          <Erro erro={erro} />
          <div className="acoes">
            <button className="btn" onClick={onFechar}>Cancelar</button>
            <button className="btn btn-primario" onClick={async () => {
              try {
                await post(`/api/admin/usuarios/${usuario.id}/redefinir-senha`, { nova_senha: senha })
                setFeito(true)
              } catch (e) { setErro(e) }
            }}>Redefinir</button>
          </div>
        </>
      )}
    </Modal>
  )
}
