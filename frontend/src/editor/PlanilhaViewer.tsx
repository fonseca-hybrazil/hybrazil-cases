// Visualizador de planilha anexada (xlsx/xlsm/csv) sem baixar: o servidor lê uma aba por vez e devolve os valores.
import { useEffect, useRef, useState } from 'react'
import { createPortal } from 'react-dom'
import { Download, FileSpreadsheet, Loader2, X } from 'lucide-react'
import { get } from '../api'

interface Planilha {
  abas: { nome: string; oculta: boolean }[]
  aba: number
  linhas: (string | number | null)[][]
  total_linhas: number | null
  mais_linhas: boolean
  mais_colunas: boolean
}

export const EXT_PLANILHA = /\.(xlsx|xlsm|csv)$/i

function letraColuna(i: number): string {
  let s = ''
  for (i += 1; i > 0; i = Math.floor((i - 1) / 26)) s = String.fromCharCode(65 + ((i - 1) % 26)) + s
  return s
}

const NUM = new Intl.NumberFormat('pt-BR', { useGrouping: false, maximumFractionDigits: 10 })

export default function PlanilhaViewer({ anexoId, nome, onFechar }: { anexoId: number; nome: string; onFechar: () => void }) {
  const [aba, setAba] = useState(0)
  const [dados, setDados] = useState<Planilha | null>(null)
  const [erro, setErro] = useState('')
  const [carregando, setCarregando] = useState(true)
  const grade = useRef<HTMLDivElement>(null)

  useEffect(() => {
    let vivo = true
    setCarregando(true)
    setErro('')
    get<Planilha>(`/api/anexos/${anexoId}/planilha?aba=${aba}`)
      .then((d) => { if (vivo) { setDados(d); grade.current?.scrollTo(0, 0) } })
      .catch((e: Error) => { if (vivo) setErro(e.message) })
      .finally(() => { if (vivo) setCarregando(false) })
    return () => { vivo = false }
  }, [anexoId, aba])

  useEffect(() => {
    const tecla = (e: KeyboardEvent) => { if (e.key === 'Escape') { e.stopPropagation(); onFechar() } }
    document.addEventListener('keydown', tecla, true)
    return () => document.removeEventListener('keydown', tecla, true)
  }, [onFechar])

  const linhas = dados?.linhas ?? []
  const colunas = linhas[0]?.length ?? 0
  return createPortal(
    // o portal propaga eventos pela árvore React: não deixa o clique chegar ao comentário/ticket por trás
    <div className="planilha-fundo" onClick={(e) => { e.stopPropagation(); onFechar() }}
         onDoubleClick={(e) => e.stopPropagation()} onMouseDown={(e) => e.stopPropagation()}>
      <div className="planilha-janela" role="dialog" aria-label={`Planilha ${nome}`} onClick={(e) => e.stopPropagation()}>
        <div className="planilha-topo">
          <FileSpreadsheet size={18} className="planilha-icone" />
          <span className="planilha-nome" title={nome}>{nome}</span>
          {carregando && dados && <Loader2 size={16} className="girando" />}
          <a href={`/api/anexos/${anexoId}/arquivo?download=1`} title="Baixar"><Download size={18} /></a>
          <button type="button" onClick={onFechar} title="Fechar (Esc)"><X size={20} /></button>
        </div>

        <div className="planilha-grade" ref={grade}>
          {erro ? <div className="planilha-aviso">{erro}</div>
            : !dados ? <div className="planilha-aviso"><Loader2 size={20} className="girando" /> Abrindo a planilha…</div>
            : !colunas ? <div className="planilha-aviso">Esta aba está vazia.</div>
            : (
              <table>
                <thead>
                  <tr><th className="planilha-canto" />{Array.from({ length: colunas }, (_, c) => <th key={c}>{letraColuna(c)}</th>)}</tr>
                </thead>
                <tbody>
                  {linhas.map((ln, r) => (
                    <tr key={r}>
                      <th>{r + 1}</th>
                      {ln.map((v, c) => typeof v === 'number'
                        ? <td key={c} className="num">{NUM.format(v)}</td>
                        : <td key={c} title={v && v.length > 40 ? v : undefined}>{v}</td>)}
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
        </div>

        {dados && (dados.mais_linhas || dados.mais_colunas) && (
          <div className="planilha-limite">
            Mostrando {dados.mais_linhas ? `as primeiras ${linhas.length.toLocaleString('pt-BR')} linhas` : 'todas as linhas'}
            {dados.mais_linhas && dados.total_linhas ? ` de ${dados.total_linhas.toLocaleString('pt-BR')}` : ''}
            {dados.mais_colunas ? ' e as primeiras 60 colunas' : ''}. Baixe o arquivo para ver tudo.
          </div>
        )}
        {dados && dados.abas.length > 1 && (
          <div className="planilha-abas">
            {dados.abas.map((a, i) => (
              <button key={i} type="button" className={i === dados.aba ? 'ativa' : a.oculta ? 'oculta' : undefined}
                      title={a.oculta ? 'Aba oculta na planilha' : undefined} onClick={() => setAba(i)}>
                {a.nome}
              </button>
            ))}
          </div>
        )}
      </div>
    </div>,
    document.body,
  )
}
