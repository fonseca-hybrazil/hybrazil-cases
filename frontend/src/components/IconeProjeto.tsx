// Ícone de um projeto: ícone padrão (Lucide, carregado sob demanda) ou imagem da biblioteca.
import { FolderKanban } from 'lucide-react'
import { DynamicIcon, type IconName } from 'lucide-react/dynamic'

export function IconeProjeto({ icone, cor, tamanho = 16, className }: {
  icone: string | null | undefined
  cor?: string | null
  tamanho?: number
  className?: string
}) {
  const cls = 'icone-projeto' + (className ? ' ' + className : '')
  if (icone?.startsWith('lib:')) {
    return <img className={cls} src={`/api/icones/${icone.slice(4)}/arquivo`} alt="" width={tamanho} height={tamanho} draggable={false} />
  }
  if (icone?.startsWith('lucide:')) {
    const reserva = () => <span style={{ display: 'inline-block', width: tamanho, height: tamanho }} />
    return <DynamicIcon className={cls} name={icone.slice(7) as IconName} size={tamanho} color={cor ?? undefined} fallback={reserva} />
  }
  return <FolderKanban className={cls} size={tamanho} color={cor ?? undefined} />
}
