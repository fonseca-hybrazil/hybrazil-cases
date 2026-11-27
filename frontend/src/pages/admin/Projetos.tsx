import { useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { Archive, ArchiveRestore, Pencil, Plus } from 'lucide-react'
import { patch, post, type Projeto } from '../../api'
import { Carregando, Erro, Modal } from '../../components/comuns'
import { useProjetos } from '../../queries'
import { FormProjeto } from '../Inicio'

export default function AdminProjetos() {
  const qc = useQueryClient()
  const { data, isLoading, error } = useProjetos()
  const [editando, setEditando] = useState<Projeto | 'novo' | null>(null)
  const [erro, setErro] = useState<unknown>(null)
  const recarregar = () => {
    qc.invalidateQueries({ queryKey: ['projetos'] })
    qc.invalidateQueries({ queryKey: ['projeto'] })
  }
  if (isLoading) return <Carregando />

  return (
    <div className="pagina pagina-estreita">
      <div className="pagina-topo">
        <h1>Projetos</h1>
        <button className="btn btn-primario" onClick={() => setEditando('novo')}><Plus size={16} /> Novo projeto</button>
      </div>
      <Erro erro={error || erro} />
      <div className="lista-admin">
        {(data ?? []).map((p) => {
          const total = p.contagem.pendente + p.contagem.andamento + p.contagem.completado
          return (
            <div key={p.id} className={'linha-admin' + (p.arquivado ? ' inativo' : '')}>
              <span className="linha-nome">
                <b>{p.nome}</b>{p.arquivado && <span className="suave"> (arquivado)</span>}
                <div className="suave pequeno">{total} ticket(s){p.descricao ? ` · ${p.descricao}` : ''}</div>
              </span>
              <button className="btn-icone" title="Editar" onClick={() => setEditando(p)}><Pencil size={15} /></button>
              <button className="btn-icone" title={p.arquivado ? 'Desarquivar' : 'Arquivar'} onClick={async () => {
                if (!p.arquivado && !window.confirm(`Arquivar "${p.nome}"? Ele sai da lista lateral e não aceita novos tickets.`)) return
                try { await patch(`/api/projetos/${p.id}`, { arquivado: !p.arquivado }); recarregar() } catch (e) { setErro(e) }
              }}>
                {p.arquivado ? <ArchiveRestore size={15} /> : <Archive size={15} />}
              </button>
            </div>
          )
        })}
      </div>
      {editando && (
        <Modal titulo={editando === 'novo' ? 'Novo projeto' : 'Editar projeto'} onFechar={() => setEditando(null)}>
          <FormProjeto
            inicial={editando === 'novo' ? undefined : editando}
            onCancelar={() => setEditando(null)}
            onSalvar={async (d) => {
              if (editando === 'novo') await post('/api/projetos', d)
              else await patch(`/api/projetos/${editando.id}`, d)
              setEditando(null)
              recarregar()
            }}
          />
        </Modal>
      )}
    </div>
  )
}
