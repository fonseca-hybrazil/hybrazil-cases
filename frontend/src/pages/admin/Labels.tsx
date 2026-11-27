import { useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { GitMerge, Pencil, Plus, Trash2 } from 'lucide-react'
import { del, get, patch, post, type Label } from '../../api'
import { useAuth } from '../../auth'
import { Carregando, Erro, LabelPill, Modal, SeletorCor } from '../../components/comuns'

type LabelUso = Label & { uso: number }

export default function AdminLabels() {
  const qc = useQueryClient()
  const { pode } = useAuth()
  const admin = pode('admin_labels')
  const { data, isLoading, error } = useQuery({ queryKey: ['labels-uso'], queryFn: () => get<LabelUso[]>('/api/labels-uso') })
  const [editando, setEditando] = useState<LabelUso | 'nova' | null>(null)
  const [mesclando, setMesclando] = useState<LabelUso | null>(null)
  const [busca, setBusca] = useState('')
  const [erro, setErro] = useState<unknown>(null)

  const recarregar = () => {
    qc.invalidateQueries({ queryKey: ['labels-uso'] })
    qc.invalidateQueries({ queryKey: ['labels'] })
  }
  if (isLoading) return <Carregando />
  const lista = (data ?? []).filter((l) => l.nome.toLowerCase().includes(busca.toLowerCase()))

  return (
    <div className="pagina pagina-estreita">
      <div className="pagina-topo">
        <h1>Labels</h1>
        <input className="busca" placeholder="Procurar…" value={busca} onChange={(e) => setBusca(e.target.value)} />
        <button className="btn btn-primario" onClick={() => setEditando('nova')}><Plus size={16} /> Nova label</button>
      </div>
      <p className="suave">As labels são compartilhadas entre todos os projetos.
        {!admin && ' Para editar, mesclar ou excluir labels é preciso ter permissão de administração de labels.'}</p>
      <Erro erro={error || erro} />
      <div className="lista-admin">
        {lista.map((l) => (
          <div key={l.id} className="linha-admin">
            <LabelPill label={l} />
            <span className="linha-nome suave pequeno">{l.uso} ticket(s)</span>
            {admin && (
              <>
                <button className="btn-icone" title="Editar" onClick={() => setEditando(l)}><Pencil size={15} /></button>
                <button className="btn-icone" title="Mesclar com outra label" onClick={() => setMesclando(l)}><GitMerge size={15} /></button>
                <button className="btn-icone" title="Excluir" onClick={async () => {
                  if (!window.confirm(`Excluir a label "${l.nome}"? Ela será removida de ${l.uso} ticket(s).`)) return
                  try { await del(`/api/labels/${l.id}`); recarregar() } catch (e) { setErro(e) }
                }}><Trash2 size={15} /></button>
              </>
            )}
          </div>
        ))}
        {lista.length === 0 && <p className="suave">Nenhuma label.</p>}
      </div>
      {editando && (
        <FormLabel label={editando === 'nova' ? null : editando} onFechar={() => setEditando(null)}
                   onSalvo={() => { setEditando(null); recarregar() }} />
      )}
      {mesclando && (
        <Mesclar origem={mesclando} labels={data ?? []} onFechar={() => setMesclando(null)}
                 onSalvo={() => { setMesclando(null); recarregar() }} />
      )}
    </div>
  )
}

function FormLabel({ label, onFechar, onSalvo }: { label: Label | null; onFechar: () => void; onSalvo: () => void }) {
  const [nome, setNome] = useState(label?.nome ?? '')
  const [cor, setCor] = useState(label?.cor ?? '#0091ff')
  const [erro, setErro] = useState<unknown>(null)
  return (
    <Modal titulo={label ? 'Editar label' : 'Nova label'} onFechar={onFechar}>
      <form className="form" onSubmit={async (e) => {
        e.preventDefault()
        try {
          if (label) await patch(`/api/labels/${label.id}`, { nome, cor })
          else await post('/api/labels', { nome, cor })
          onSalvo()
        } catch (err) { setErro(err) }
      }}>
        <div className="previa-cat"><LabelPill label={{ id: 0, nome: nome || 'Prévia', cor }} /></div>
        <label>Nome<input value={nome} onChange={(e) => setNome(e.target.value)} required autoFocus maxLength={60} /></label>
        <div><div className="rotulo">Cor</div><SeletorCor valor={cor} onChange={setCor} /></div>
        <Erro erro={erro} />
        <div className="acoes">
          <button type="button" className="btn" onClick={onFechar}>Cancelar</button>
          <button className="btn btn-primario">Salvar</button>
        </div>
      </form>
    </Modal>
  )
}

function Mesclar({ origem, labels, onFechar, onSalvo }: {
  origem: LabelUso; labels: LabelUso[]; onFechar: () => void; onSalvo: () => void
}) {
  const [destino, setDestino] = useState<number | ''>('')
  const [erro, setErro] = useState<unknown>(null)
  return (
    <Modal titulo="Mesclar labels" onFechar={onFechar}>
      <p>Todos os tickets com <LabelPill label={origem} /> passarão a ter a label escolhida abaixo,
        e <LabelPill label={origem} /> será excluída.</p>
      <select value={destino} onChange={(e) => setDestino(e.target.value ? Number(e.target.value) : '')}>
        <option value="">Escolha a label de destino…</option>
        {labels.filter((l) => l.id !== origem.id).map((l) => <option key={l.id} value={l.id}>{l.nome}</option>)}
      </select>
      <Erro erro={erro} />
      <div className="acoes">
        <button className="btn" onClick={onFechar}>Cancelar</button>
        <button className="btn btn-primario" disabled={!destino} onClick={async () => {
          try { await post(`/api/labels/${origem.id}/mesclar`, { destino_id: destino }); onSalvo() } catch (e) { setErro(e) }
        }}>Mesclar</button>
      </div>
    </Modal>
  )
}
