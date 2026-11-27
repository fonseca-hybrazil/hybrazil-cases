import { useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { ArrowDown, ArrowUp, Pencil, Plus, Trash2 } from 'lucide-react'
import { ApiError, del, patch, post, put, type Categoria } from '../../api'
import { Carregando, Erro, Modal, SeletorCor } from '../../components/comuns'
import { ICONES, IconeCategoria } from '../../icones'
import { useCategorias } from '../../queries'

export default function AdminCategorias() {
  const qc = useQueryClient()
  const { data: cats, isLoading, error } = useCategorias()
  const [editando, setEditando] = useState<Categoria | 'nova' | null>(null)
  const [erro, setErro] = useState<unknown>(null)
  const recarregar = () => qc.invalidateQueries({ queryKey: ['categorias'] })

  if (isLoading) return <Carregando />
  const lista = cats ?? []

  const mover = async (i: number, d: -1 | 1) => {
    const ids = lista.map((c) => c.id)
    ;[ids[i], ids[i + d]] = [ids[i + d], ids[i]]
    try { await put('/api/categorias-ordem', { ids }); recarregar() } catch (e) { setErro(e) }
  }

  const excluir = async (c: Categoria) => {
    if (!window.confirm(`Excluir a categoria "${c.nome}"?`)) return
    try {
      await del(`/api/categorias/${c.id}`)
      recarregar()
    } catch (e) {
      if (e instanceof ApiError && e.status === 409 &&
          window.confirm('Esta categoria está em uso por tickets. Deseja desativá-la? Ela some das opções, mas continua nos tickets antigos.')) {
        await patch(`/api/categorias/${c.id}`, { ativa: false })
        recarregar()
      } else if (!(e instanceof ApiError && e.status === 409)) setErro(e)
    }
  }

  return (
    <div className="pagina pagina-estreita">
      <div className="pagina-topo">
        <h1>Categorias</h1>
        <button className="btn btn-primario" onClick={() => setEditando('nova')}><Plus size={16} /> Nova categoria</button>
      </div>
      <Erro erro={error || erro} />
      <div className="lista-admin">
        {lista.map((c, i) => (
          <div key={c.id} className={'linha-admin' + (c.ativa ? '' : ' inativo')}>
            <span className="cat-icone-grande" style={{ background: c.cor + '22' }}>
              <IconeCategoria nome={c.icone} cor={c.cor} tamanho={18} />
            </span>
            <span className="linha-nome">{c.nome}{!c.ativa && <span className="suave"> (inativa)</span>}</span>
            <button className="btn-icone" disabled={i === 0} onClick={() => mover(i, -1)} title="Subir"><ArrowUp size={15} /></button>
            <button className="btn-icone" disabled={i === lista.length - 1} onClick={() => mover(i, 1)} title="Descer"><ArrowDown size={15} /></button>
            <button className="btn-icone" onClick={() => setEditando(c)} title="Editar"><Pencil size={15} /></button>
            <button className="btn-icone" onClick={() => excluir(c)} title="Excluir"><Trash2 size={15} /></button>
          </div>
        ))}
      </div>
      {editando && (
        <FormCategoria
          cat={editando === 'nova' ? null : editando}
          onFechar={() => setEditando(null)}
          onSalvo={() => { setEditando(null); recarregar() }}
        />
      )}
    </div>
  )
}

function FormCategoria({ cat, onFechar, onSalvo }: { cat: Categoria | null; onFechar: () => void; onSalvo: () => void }) {
  const [nome, setNome] = useState(cat?.nome ?? '')
  const [icone, setIcone] = useState(cat?.icone ?? 'circle-alert')
  const [cor, setCor] = useState(cat?.cor ?? '#3e63dd')
  const [ativa, setAtiva] = useState(cat?.ativa ?? true)
  const [erro, setErro] = useState<unknown>(null)

  const salvar = async () => {
    try {
      if (cat) await patch(`/api/categorias/${cat.id}`, { nome, icone, cor, ativa })
      else await post('/api/categorias', { nome, icone, cor })
      onSalvo()
    } catch (e) {
      setErro(e)
    }
  }

  return (
    <Modal titulo={cat ? 'Editar categoria' : 'Nova categoria'} onFechar={onFechar} largura={560}>
      <form className="form" onSubmit={(e) => { e.preventDefault(); salvar() }}>
        <div className="previa-cat">
          <span className="cat-icone-grande" style={{ background: cor + '22' }}><IconeCategoria nome={icone} cor={cor} tamanho={22} /></span>
          <b style={{ color: cor }}>{nome || 'Nome da categoria'}</b>
        </div>
        <label>Nome<input value={nome} onChange={(e) => setNome(e.target.value)} required autoFocus maxLength={60} /></label>
        <div>
          <div className="rotulo">Ícone</div>
          <div className="grade-icones">
            {Object.keys(ICONES).map((k) => (
              <button type="button" key={k} title={k} className={'icone-op' + (k === icone ? ' sel' : '')} onClick={() => setIcone(k)}>
                <IconeCategoria nome={k} cor={k === icone ? cor : '#57606a'} tamanho={18} />
              </button>
            ))}
          </div>
        </div>
        <div>
          <div className="rotulo">Cor</div>
          <SeletorCor valor={cor} onChange={setCor} />
        </div>
        {cat && (
          <label className="check"><input type="checkbox" checked={ativa} onChange={(e) => setAtiva(e.target.checked)} /> Ativa</label>
        )}
        <Erro erro={erro} />
        <div className="acoes">
          <button type="button" className="btn" onClick={onFechar}>Cancelar</button>
          <button className="btn btn-primario">Salvar</button>
        </div>
      </form>
    </Modal>
  )
}
