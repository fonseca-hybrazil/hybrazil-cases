import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useQueryClient } from '@tanstack/react-query'
import { Plus, Star } from 'lucide-react'
import { del, post, put, type Projeto } from '../api'
import { useAuth } from '../auth'
import { Carregando, Erro, Modal } from '../components/comuns'
import { useProjetos } from '../queries'

export function FormProjeto({ inicial, onSalvar, onCancelar }: {
  inicial?: Partial<Projeto>; onSalvar: (d: { nome: string; descricao: string }) => Promise<void>; onCancelar: () => void
}) {
  const [nome, setNome] = useState(inicial?.nome ?? '')
  const [descricao, setDescricao] = useState(inicial?.descricao ?? '')
  const [erro, setErro] = useState<unknown>(null)
  return (
    <form className="form" onSubmit={async (e) => {
      e.preventDefault()
      try { await onSalvar({ nome, descricao }) } catch (err) { setErro(err) }
    }}>
      <label>Nome<input value={nome} onChange={(e) => setNome(e.target.value)} required autoFocus maxLength={100} /></label>
      <label>Descrição<textarea value={descricao} onChange={(e) => setDescricao(e.target.value)} rows={3} /></label>
      <Erro erro={erro} />
      <div className="acoes">
        <button type="button" className="btn" onClick={onCancelar}>Cancelar</button>
        <button className="btn btn-primario">Salvar</button>
      </div>
    </form>
  )
}

export async function alternarFavorito(p: Projeto) {
  if (p.favorito) await del(`/api/projetos/${p.id}/favorito`)
  else await put(`/api/projetos/${p.id}/favorito`)
}

export default function Inicio() {
  const { data, isLoading, error } = useProjetos()
  const { pode } = useAuth()
  const [novo, setNovo] = useState(false)
  const qc = useQueryClient()
  const nav = useNavigate()

  if (isLoading) return <Carregando />
  const projetos = (data ?? []).filter((p) => !p.arquivado)
  projetos.sort((a, b) => Number(b.favorito) - Number(a.favorito))

  return (
    <div className="pagina">
      <div className="pagina-topo">
        <h1>Projetos</h1>
        {pode('admin_projetos') && (
          <button className="btn btn-primario" onClick={() => setNovo(true)}><Plus size={16} /> Novo projeto</button>
        )}
      </div>
      <Erro erro={error} />
      {projetos.length === 0 && (
        <p className="suave">
          Nenhum projeto ainda.{pode('admin_projetos') ? ' Crie o primeiro com o botão "Novo projeto".' : ''}
        </p>
      )}
      <div className="grade-projetos">
        {projetos.map((p) => (
          <Link key={p.id} to={`/p/${p.id}`} className="cartao-projeto">
            <div className="cartao-projeto-topo">
              <h3>{p.nome}</h3>
              <button
                className="btn-icone"
                title={p.favorito ? 'Remover dos favoritos' : 'Favoritar'}
                onClick={async (e) => {
                  e.preventDefault()
                  await alternarFavorito(p)
                  qc.invalidateQueries({ queryKey: ['projetos'] })
                }}
              >
                <Star size={16} className={p.favorito ? 'estrela-on' : ''} />
              </button>
            </div>
            {p.descricao && <p className="suave">{p.descricao}</p>}
            <div className="contagens">
              <span className="cont cont-pendente">{p.contagem.pendente} pendentes</span>
              <span className="cont cont-andamento">{p.contagem.andamento} em andamento</span>
              <span className="cont cont-completado">{p.contagem.completado} completados</span>
            </div>
          </Link>
        ))}
      </div>
      {novo && (
        <Modal titulo="Novo projeto" onFechar={() => setNovo(false)}>
          <FormProjeto
            onCancelar={() => setNovo(false)}
            onSalvar={async (d) => {
              const p = await post<Projeto>('/api/projetos', d)
              await qc.invalidateQueries({ queryKey: ['projetos'] })
              setNovo(false)
              nav(`/p/${p.id}`)
            }}
          />
        </Modal>
      )}
    </div>
  )
}
