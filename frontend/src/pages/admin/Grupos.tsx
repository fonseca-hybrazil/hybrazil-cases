import { useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { Pencil, Plus, Trash2 } from 'lucide-react'
import { del, get, patch, post, type Grupo, type Permissao, type UsuarioAdmin } from '../../api'
import { Avatar, Carregando, Erro, Modal } from '../../components/comuns'

export default function AdminGrupos() {
  const qc = useQueryClient()
  const grupos = useQuery({ queryKey: ['admin-grupos'], queryFn: () => get<Grupo[]>('/api/admin/grupos') })
  const perms = useQuery({ queryKey: ['permissoes'], queryFn: () => get<Permissao[]>('/api/admin/permissoes') })
  const usuarios = useQuery({ queryKey: ['admin-usuarios'], queryFn: () => get<UsuarioAdmin[]>('/api/admin/usuarios') })
  const [editando, setEditando] = useState<Grupo | 'novo' | null>(null)
  const [erro, setErro] = useState<unknown>(null)

  const recarregar = () => {
    qc.invalidateQueries({ queryKey: ['admin-grupos'] })
    qc.invalidateQueries({ queryKey: ['admin-usuarios'] })
  }
  if (grupos.isLoading || perms.isLoading) return <Carregando />
  const descr = new Map((perms.data ?? []).map((p) => [p.chave, p.descricao]))

  return (
    <div className="pagina">
      <div className="pagina-topo">
        <h1>Grupos e permissões</h1>
        <button className="btn btn-primario" onClick={() => setEditando('novo')}><Plus size={16} /> Novo grupo</button>
      </div>
      <p className="suave">
        As permissões de um usuário são a soma das permissões de todos os grupos a que ele pertence.
        Todos os usuários podem ver os projetos, criar e editar tickets, comentar, anexar arquivos e criar labels.
      </p>
      <Erro erro={grupos.error || erro} />
      <div className="grade-grupos">
        {(grupos.data ?? []).map((g) => (
          <div key={g.id} className="painel">
            <div className="painel-topo">
              <h2>{g.nome}</h2>
              <button className="btn-icone" title="Editar" onClick={() => setEditando(g)}><Pencil size={15} /></button>
              {!g.sistema && (
                <button className="btn-icone" title="Excluir" onClick={async () => {
                  if (!window.confirm(`Excluir o grupo "${g.nome}"? Os usuários perdem as permissões dele.`)) return
                  try { await del(`/api/admin/grupos/${g.id}`); recarregar() } catch (e) { setErro(e) }
                }}><Trash2 size={15} /></button>
              )}
            </div>
            {g.descricao && <p className="suave">{g.descricao}</p>}
            <ul className="lista-perms">
              {g.permissoes.length === 0 && <li className="suave">Sem permissões extras</li>}
              {g.permissoes.map((p) => <li key={p}>{descr.get(p) ?? p}</li>)}
            </ul>
            <div className="membros">
              {g.usuario_ids.map((id) => {
                const u = usuarios.data?.find((x) => x.id === id)
                return u ? <span key={id} className="membro"><Avatar u={u} tamanho={20} /> {u.nome}</span> : null
              })}
              {g.usuario_ids.length === 0 && <span className="suave pequeno">Nenhum membro</span>}
            </div>
          </div>
        ))}
      </div>
      {editando && (
        <FormGrupo
          grupo={editando === 'novo' ? null : editando}
          perms={perms.data ?? []}
          usuarios={usuarios.data ?? []}
          onFechar={() => setEditando(null)}
          onSalvo={() => { setEditando(null); recarregar() }}
        />
      )}
    </div>
  )
}

function FormGrupo({ grupo, perms, usuarios, onFechar, onSalvo }: {
  grupo: Grupo | null; perms: Permissao[]; usuarios: UsuarioAdmin[]; onFechar: () => void; onSalvo: () => void
}) {
  const [nome, setNome] = useState(grupo?.nome ?? '')
  const [descricao, setDescricao] = useState(grupo?.descricao ?? '')
  const [ps, setPs] = useState<string[]>(grupo?.permissoes ?? [])
  const [membros, setMembros] = useState<number[]>(grupo?.usuario_ids ?? [])
  const [erro, setErro] = useState<unknown>(null)
  const travado = grupo?.sistema && grupo.nome === 'Administradores'

  const salvar = async () => {
    setErro(null)
    try {
      if (grupo) {
        await patch(`/api/admin/grupos/${grupo.id}`, {
          nome, descricao, usuario_ids: membros, ...(travado ? {} : { permissoes: ps }),
        })
      } else {
        const g = await post<Grupo>('/api/admin/grupos', { nome, descricao, permissoes: ps })
        if (membros.length) await patch(`/api/admin/grupos/${g.id}`, { usuario_ids: membros })
      }
      onSalvo()
    } catch (e) {
      setErro(e)
    }
  }

  return (
    <Modal titulo={grupo ? `Editar grupo ${grupo.nome}` : 'Novo grupo'} onFechar={onFechar} largura={620}>
      <form className="form" onSubmit={(e) => { e.preventDefault(); salvar() }}>
        <label>Nome<input value={nome} onChange={(e) => setNome(e.target.value)} required autoFocus /></label>
        <label>Descrição<input value={descricao} onChange={(e) => setDescricao(e.target.value)} /></label>
        <fieldset disabled={travado}>
          <legend>Permissões {travado && <span className="suave pequeno">(o grupo Administradores sempre tem todas)</span>}</legend>
          {perms.map((p) => (
            <label key={p.chave} className="check">
              <input type="checkbox" checked={travado || ps.includes(p.chave)}
                     onChange={() => setPs(ps.includes(p.chave) ? ps.filter((x) => x !== p.chave) : [...ps, p.chave])} />
              {p.descricao}
            </label>
          ))}
        </fieldset>
        <fieldset>
          <legend>Membros</legend>
          <div className="membros-lista">
            {usuarios.filter((u) => u.ativo).map((u) => (
              <label key={u.id} className="check">
                <input type="checkbox" checked={membros.includes(u.id)}
                       onChange={() => setMembros(membros.includes(u.id) ? membros.filter((x) => x !== u.id) : [...membros, u.id])} />
                <Avatar u={u} tamanho={18} /> {u.nome}
              </label>
            ))}
          </div>
        </fieldset>
        <Erro erro={erro} />
        <div className="acoes">
          <button type="button" className="btn" onClick={onFechar}>Cancelar</button>
          <button className="btn btn-primario">Salvar</button>
        </div>
      </form>
    </Modal>
  )
}
