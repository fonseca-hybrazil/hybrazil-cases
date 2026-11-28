import { useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { X } from 'lucide-react'
import { FILTROS_VAZIOS, get, type Filtros, type Label } from '../api'
import { useAuth } from '../auth'
import { IconeCategoria } from '../icones'
import { useCategorias, useLabels, useUsuarios } from '../queries'
import { Avatar, LabelPill, Popover } from './comuns'

function alternar(lista: number[], v: number): number[] {
  return lista.includes(v) ? lista.filter((x) => x !== v) : [...lista, v]
}

export default function FiltroPainel({ projetoId, filtros, onChange, onFechar }: {
  projetoId: number; filtros: Filtros; onChange: (f: Filtros) => void; onFechar: () => void
}) {
  const { data: todasLabels = [] } = useLabels()
  // quantos tickets do projeto têm cada label: mostra o número e ordena da mais usada para a menos usada
  const { data: usoLabels } = useQuery({
    queryKey: ['labels-uso', projetoId],
    queryFn: () => get<(Label & { uso: number })[]>(`/api/labels-uso?projeto_id=${projetoId}`),
    staleTime: 10_000,
  })
  const uso = useMemo(() => new Map((usoLabels ?? []).map((l) => [l.id, l.uso])), [usoLabels])
  const labels = useMemo(() => [...todasLabels].sort((a, b) =>
    (uso.get(b.id) ?? 0) - (uso.get(a.id) ?? 0) || a.nome.localeCompare(b.nome, 'pt-BR')), [todasLabels, uso])
  const { data: cats = [] } = useCategorias()
  const { data: usuarios = [] } = useUsuarios()
  const { eu } = useAuth()
  const [buscaLabel, setBuscaLabel] = useState('')
  const [numero, setNumero] = useState(filtros.numero)

  const set = (parcial: Partial<Filtros>) => onChange({ ...filtros, ...parcial })
  const labelsVisiveis = labels.filter((l) => l.nome.toLowerCase().includes(buscaLabel.toLowerCase()))
  const ativos = usuarios.filter((u) => u.ativo)

  return (
    <Popover aberto onFechar={onFechar} alinhar="direita">
      <div className="filtro-painel">
        <div className="filtro-topo">
          <strong>Filtrar tickets</strong>
          <button className="btn-link" onClick={() => onChange(FILTROS_VAZIOS)}>Limpar tudo</button>
          <button className="btn-icone" onClick={onFechar} aria-label="Fechar"><X size={16} /></button>
        </div>

        <div className="filtro-secao">
          <div className="filtro-titulo">ID do ticket</div>
          <input
            placeholder="#123"
            value={numero}
            onChange={(e) => setNumero(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && set({ numero })}
            onBlur={() => numero !== filtros.numero && set({ numero })}
          />
        </div>

        <div className="filtro-secao">
          <div className="filtro-titulo">
            Labels
            {filtros.label.length > 1 && (
              <span className="modo">
                <label><input type="radio" checked={filtros.labels_modo === 'qualquer'}
                              onChange={() => set({ labels_modo: 'qualquer' })} /> qualquer</label>
                <label><input type="radio" checked={filtros.labels_modo === 'todas'}
                              onChange={() => set({ labels_modo: 'todas' })} /> todas</label>
              </span>
            )}
          </div>
          {labels.length > 8 && (
            <input placeholder="Procurar label…" value={buscaLabel} onChange={(e) => setBuscaLabel(e.target.value)} />
          )}
          <div className="filtro-lista">
            {labelsVisiveis.map((l) => (
              <label key={l.id} className="filtro-op">
                <input type="checkbox" checked={filtros.label.includes(l.id)}
                       onChange={() => set({ label: alternar(filtros.label, l.id) })} />
                <LabelPill label={l} />
                {usoLabels && <span className={'filtro-qtd' + (uso.get(l.id) ? '' : ' zero')}>{uso.get(l.id) ?? 0}</span>}
              </label>
            ))}
            {labels.length === 0 && <span className="suave">Nenhuma label criada.</span>}
          </div>
        </div>

        <div className="filtro-secao">
          <div className="filtro-titulo">Categoria</div>
          <div className="filtro-lista">
            {cats.map((c) => (
              <label key={c.id} className="filtro-op">
                <input type="checkbox" checked={filtros.categoria.includes(c.id)}
                       onChange={() => set({ categoria: alternar(filtros.categoria, c.id) })} />
                <IconeCategoria nome={c.icone} cor={c.cor} /> {c.nome}{!c.ativa && ' (inativa)'}
              </label>
            ))}
            <label className="filtro-op">
              <input type="checkbox" checked={filtros.categoria.includes(0)}
                     onChange={() => set({ categoria: alternar(filtros.categoria, 0) })} />
              <span className="suave">Sem categoria</span>
            </label>
          </div>
        </div>

        <div className="filtro-secao">
          <div className="filtro-titulo">Responsável</div>
          <div className="filtro-lista">
            {eu && (
              <label className="filtro-op">
                <input type="checkbox" checked={filtros.responsavel.includes(eu.id)}
                       onChange={() => set({ responsavel: alternar(filtros.responsavel, eu.id) })} />
                <Avatar u={eu} tamanho={18} /> <b>Meus tickets</b>
              </label>
            )}
            {ativos.filter((u) => u.id !== eu?.id).map((u) => (
              <label key={u.id} className="filtro-op">
                <input type="checkbox" checked={filtros.responsavel.includes(u.id)}
                       onChange={() => set({ responsavel: alternar(filtros.responsavel, u.id) })} />
                <Avatar u={u} tamanho={18} /> {u.nome}
              </label>
            ))}
            <label className="filtro-op">
              <input type="checkbox" checked={filtros.responsavel.includes(0)}
                     onChange={() => set({ responsavel: alternar(filtros.responsavel, 0) })} />
              <span className="suave">Sem responsável</span>
            </label>
          </div>
        </div>
      </div>
    </Popover>
  )
}
