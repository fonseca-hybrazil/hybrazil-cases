// Escolha do ícone do projeto: ícones padrão (Lucide, ~1.600, com busca em português nos sugeridos)
// ou imagens da biblioteca (PNG, SVG, ICO…), que podem ser enviadas aqui.
import { useMemo, useRef, useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { Trash2, Upload } from 'lucide-react'
import { DynamicIcon, iconNames, type IconName } from 'lucide-react/dynamic'
import { del, enviarArquivo, get, type IconeBiblioteca } from '../api'
import { useAuth } from '../auth'
import { Erro } from './comuns'
import { IconeProjeto } from './IconeProjeto'

// Sugeridos para os projetos da HyBrazil, com palavras em português para a busca.
const SUGERIDOS: [string, string][] = [
  ['zap', 'energia eletrica raio'], ['plug-zap', 'energia tomada'], ['power', 'liga desliga'],
  ['battery-charging', 'bateria carga'], ['sun', 'sol solar'], ['solar-panel', 'solar painel usina fotovoltaica'],
  ['wind', 'vento eolica'], ['droplets', 'agua hidro'], ['waves', 'agua rio hidreletrica pch'], ['dam', 'barragem represa pch'],
  ['factory', 'usina fabrica industria'], ['utility-pole', 'poste linha transmissao rede eletrica'], ['cable', 'cabo'],
  ['gauge', 'medidor medicao'], ['thermometer', 'temperatura'], ['flame', 'fogo termica'], ['fuel', 'combustivel'],
  ['lightbulb', 'ideia lampada'], ['cpu', 'automacao clp processador'], ['circuit-board', 'placa eletronica'],
  ['microchip', 'chip'], ['cog', 'engrenagem configuracao'], ['settings', 'configuracao ajustes'], ['bot', 'robo automacao'],
  ['workflow', 'fluxo processo'], ['monitor', 'tela supervisorio scada ihm'], ['monitor-cog', 'supervisorio scada'],
  ['terminal', 'codigo comando'], ['code', 'codigo programacao'], ['binary', 'dados binario'], ['database', 'banco de dados'],
  ['hard-drive', 'disco armazenamento'], ['network', 'rede'], ['router', 'roteador rede mikrotik'], ['wifi', 'rede sem fio'],
  ['ethernet-port', 'rede cabo porta'], ['server', 'servidor'], ['server-cog', 'servidor configuracao'], ['globe', 'internet mundo'],
  ['cloud', 'nuvem'], ['satellite-dish', 'satelite antena'], ['radio-tower', 'torre radio comunicacao'], ['antenna', 'antena'],
  ['shield', 'seguranca protecao'], ['shield-check', 'seguranca protecao'], ['lock', 'cadeado seguranca'],
  ['brick-wall', 'firewall muro'], ['cctv', 'camera cftv seguranca'], ['camera', 'foto camera'],
  ['wrench', 'ferramenta manutencao'], ['hammer', 'ferramenta'], ['hard-hat', 'capacete obra campo seguranca'],
  ['construction', 'obra construcao'], ['bug', 'erro problema'], ['life-buoy', 'suporte ajuda problema'],
  ['headset', 'suporte atendimento'], ['clipboard-list', 'lista tarefas checklist'], ['book-open', 'documentacao manual'],
  ['file-text', 'documento arquivo'], ['folder-kanban', 'projeto quadro'], ['briefcase', 'trabalho comercial'],
  ['building-2', 'predio escritorio empresa'], ['house', 'casa'], ['warehouse', 'galpao almoxarifado estoque'],
  ['package', 'pacote material'], ['truck', 'caminhao logistica'], ['car', 'carro veiculo'], ['tractor', 'trator'],
  ['map-pin', 'local mapa'], ['map', 'mapa'], ['mountain', 'montanha'], ['leaf', 'folha ambiental'],
  ['tree-pine', 'arvore ambiental'], ['users', 'equipe pessoas'], ['user-cog', 'usuario administracao'],
  ['calendar', 'agenda data'], ['chart-line', 'grafico relatorio'], ['chart-bar', 'grafico relatorio'],
  ['activity', 'monitoramento atividade'], ['bell', 'alarme alerta aviso'], ['flag', 'marco bandeira'],
  ['target', 'meta alvo'], ['rocket', 'lancamento'], ['star', 'estrela'], ['puzzle', 'integracao'], ['layers', 'camadas'],
  ['phone', 'telefone'], ['mail', 'email'], ['message-square', 'mensagem'],
]

const CORES = ['#1e88e5', '#0d9488', '#16a34a', '#65a30d', '#f59e0b', '#ea580c', '#dc2626', '#db2777', '#7c3aed', '#475569']
const PAGINA = 180

const semAcento = (s: string) => s.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase()
const NOMES = new Set<string>(iconNames)

export default function SeletorIcone({ icone, cor, onChange }: {
  icone: string | null
  cor: string | null
  onChange: (icone: string | null, cor: string | null) => void
}) {
  const { pode } = useAuth()
  const qc = useQueryClient()
  const [aba, setAba] = useState<'padrao' | 'biblioteca'>(icone?.startsWith('lib:') ? 'biblioteca' : 'padrao')
  const [busca, setBusca] = useState('')
  const [limite, setLimite] = useState(PAGINA)
  const [erro, setErro] = useState<unknown>(null)
  const [enviando, setEnviando] = useState(false)
  const input = useRef<HTMLInputElement>(null)
  const biblioteca = useQuery({ queryKey: ['icones'], queryFn: () => get<IconeBiblioteca[]>('/api/icones') })

  const lista = useMemo(() => {
    const q = semAcento(busca.trim())
    const sugeridos = SUGERIDOS.filter(([n]) => NOMES.has(n))
    if (!q) return { nomes: sugeridos.map(([n]) => n), todos: false }
    const porPalavra = sugeridos.filter(([n, pt]) => semAcento(pt).includes(q) || n.includes(q)).map(([n]) => n)
    const porNome = iconNames.filter((n) => n.replace(/-/g, ' ').includes(q) || n.includes(q))
    return { nomes: [...new Set([...porPalavra, ...porNome])], todos: true }
  }, [busca])
  const [verTodos, setVerTodos] = useState(false)
  const nomes = verTodos && !busca.trim() ? iconNames : lista.nomes
  const selLucide = icone?.startsWith('lucide:') ? icone.slice(7) : null

  const enviar = async (arquivos: FileList | null) => {
    if (!arquivos?.length) return
    setErro(null)
    setEnviando(true)
    try {
      let ultimo: IconeBiblioteca | null = null
      for (const f of Array.from(arquivos)) ultimo = await enviarArquivo<IconeBiblioteca>('/api/icones', f)
      await qc.invalidateQueries({ queryKey: ['icones'] })
      if (ultimo) onChange(`lib:${ultimo.id}`, cor)
    } catch (e) {
      setErro(e)
    } finally {
      setEnviando(false)
      if (input.current) input.current.value = ''
    }
  }

  return (
    <div className="seletor-icone">
      <div className="seletor-icone-topo">
        <span className="seletor-icone-atual" style={{ background: (cor ?? '#57606a') + '1f' }}>
          <IconeProjeto icone={icone} cor={cor} tamanho={26} />
        </span>
        <div className="abas-mini">
          <button type="button" className={aba === 'padrao' ? 'ativa' : ''} onClick={() => setAba('padrao')}>Ícones padrão</button>
          <button type="button" className={aba === 'biblioteca' ? 'ativa' : ''} onClick={() => setAba('biblioteca')}>
            Biblioteca{biblioteca.data?.length ? ` (${biblioteca.data.length})` : ''}
          </button>
        </div>
        {icone && <button type="button" className="btn-link" onClick={() => onChange(null, null)}>Remover ícone</button>}
      </div>

      {aba === 'padrao' && (
        <>
          <div className="seletor-icone-cores">
            {CORES.map((c) => (
              <button type="button" key={c} className={'cor-op' + (c === cor ? ' sel' : '')} style={{ background: c }}
                      title={c} onClick={() => onChange(icone?.startsWith('lucide:') ? icone : 'lucide:folder-kanban', c)} />
            ))}
            <input type="color" value={cor ?? '#57606a'} title="Outra cor"
                   onChange={(e) => onChange(icone?.startsWith('lucide:') ? icone : 'lucide:folder-kanban', e.target.value)} />
          </div>
          <input className="seletor-icone-busca" placeholder="Buscar ícone (ex.: solar, rede, servidor, zap)…" value={busca}
                 onChange={(e) => { setBusca(e.target.value); setLimite(PAGINA) }} />
          <div className="grade-icones seletor-icone-grade">
            {nomes.slice(0, limite).map((n) => (
              <button type="button" key={n} title={n} className={'icone-op' + (n === selLucide ? ' sel' : '')}
                      onClick={() => onChange(`lucide:${n}`, cor)}>
                <DynamicIcon name={n as IconName} size={18} color={n === selLucide ? (cor ?? undefined) : '#57606a'} />
              </button>
            ))}
            {!nomes.length && <span className="suave pequeno">Nenhum ícone encontrado. Busque em inglês para ver todos (ex.: “solar”, “factory”).</span>}
          </div>
          <div className="seletor-icone-rodape suave pequeno">
            {nomes.length > limite
              ? <button type="button" className="btn-link" onClick={() => setLimite((l) => l + PAGINA)}>Mostrar mais ({nomes.length - limite})</button>
              : <span />}
            {!busca.trim() && (
              <button type="button" className="btn-link" onClick={() => { setVerTodos((v) => !v); setLimite(PAGINA) }}>
                {verTodos ? 'Só os sugeridos' : `Ver todos (${iconNames.length.toLocaleString('pt-BR')})`}
              </button>
            )}
          </div>
        </>
      )}

      {aba === 'biblioteca' && (
        <>
          <div className="grade-icones seletor-icone-grade">
            {(biblioteca.data ?? []).map((i) => (
              <div key={i.id} className={'icone-op icone-lib' + (icone === `lib:${i.id}` ? ' sel' : '')} title={i.nome}
                   onClick={() => onChange(`lib:${i.id}`, null)}>
                <img src={i.url} alt={i.nome} />
                {pode('admin_projetos') && (
                  <button type="button" className="icone-lib-excluir" title="Excluir da biblioteca" onClick={async (e) => {
                    e.stopPropagation()
                    const aviso = i.em_uso ? `\n\nEle está em uso em ${i.em_uso} projeto(s), que voltarão ao ícone padrão.` : ''
                    if (!window.confirm(`Excluir o ícone "${i.nome}" da biblioteca?${aviso}`)) return
                    try {
                      await del(`/api/icones/${i.id}`)
                      if (icone === `lib:${i.id}`) onChange(null, null)
                      qc.invalidateQueries({ queryKey: ['icones'] })
                      qc.invalidateQueries({ queryKey: ['projetos'] })
                    } catch (err) { setErro(err) }
                  }}><Trash2 size={11} /></button>
                )}
              </div>
            ))}
            {biblioteca.data?.length === 0 && <span className="suave pequeno">A biblioteca ainda está vazia.</span>}
          </div>
          {pode('admin_projetos') && (
            <div className="seletor-icone-rodape">
              <button type="button" className="btn" disabled={enviando} onClick={() => input.current?.click()}>
                <Upload size={15} /> {enviando ? 'Enviando…' : 'Enviar ícones'}
              </button>
              <span className="suave pequeno">PNG, SVG, ICO, JPG, WebP ou GIF, até 512 KB. Ficam disponíveis para todos os projetos.</span>
              <input ref={input} type="file" multiple hidden accept=".png,.svg,.ico,.jpg,.jpeg,.webp,.gif,image/*"
                     onChange={(e) => enviar(e.target.files)} />
            </div>
          )}
        </>
      )}
      <Erro erro={erro} />
    </div>
  )
}
