import { useState, type ReactNode } from 'react'
import { Link, NavLink, useNavigate } from 'react-router-dom'
import {
  Archive, BarChart3, ChevronDown, FolderKanban, LogOut, Menu, Settings, Shapes, Star, Tag, User, Users, UsersRound,
} from 'lucide-react'
import { useAuth } from '../auth'
import { useProjetos } from '../queries'
import { Avatar, Popover } from './comuns'
import { IconeProjeto } from './IconeProjeto'

export default function Layout({ children }: { children: ReactNode }) {
  const { eu, sair, pode } = useAuth()
  const { data: projetos } = useProjetos()
  const [menu, setMenu] = useState(false)
  const [aberta, setAberta] = useState(false)
  const nav = useNavigate()

  const ativos = (projetos ?? []).filter((p) => !p.arquivado)
  const favoritos = ativos.filter((p) => p.favorito)
  const outros = ativos.filter((p) => !p.favorito)

  const item = (p: (typeof ativos)[number]) => (
    <NavLink key={p.id} to={`/p/${p.id}`} className="side-item" onClick={() => setAberta(false)}>
      {p.icone ? <IconeProjeto icone={p.icone} cor={p.icone_cor} tamanho={15} />
        : p.favorito ? <Star size={14} className="estrela-on" /> : <FolderKanban size={14} />}
      <span className="side-texto">{p.nome}</span>
      <span className="side-num">{p.contagem.pendente + p.contagem.andamento || ''}</span>
    </NavLink>
  )

  return (
    <div className={'app' + (aberta ? ' side-aberta' : '')}>
      <aside className="side">
        <Link to="/" className="logo" onClick={() => setAberta(false)}>
          <img src="/favicon.svg" alt="" width={26} height={26} />
          <span>HyBrazil <b>Cases</b></span>
        </Link>
        <nav className="side-nav">
          <NavLink to="/dashboard" className="side-item" onClick={() => setAberta(false)}>
            <BarChart3 size={14} /> <span className="side-texto">Dashboard</span>
          </NavLink>
          {favoritos.length > 0 && <div className="side-titulo">Favoritos</div>}
          {favoritos.map(item)}
          <div className="side-titulo">Projetos</div>
          {outros.map(item)}
          {ativos.length === 0 && <div className="side-vazio">Nenhum projeto</div>}
          <div className="side-titulo">Configurações</div>
          <NavLink to="/admin/labels" className="side-item" onClick={() => setAberta(false)}>
            <Tag size={14} /> <span className="side-texto">Labels</span>
          </NavLink>
          {pode('admin_categorias') && (
            <NavLink to="/admin/categorias" className="side-item" onClick={() => setAberta(false)}>
              <Shapes size={14} /> <span className="side-texto">Categorias</span>
            </NavLink>
          )}
          {pode('admin_projetos') && (
            <NavLink to="/admin/projetos" className="side-item" onClick={() => setAberta(false)}>
              <Archive size={14} /> <span className="side-texto">Projetos</span>
            </NavLink>
          )}
          {pode('admin_usuarios') && (
            <>
              <NavLink to="/admin/usuarios" className="side-item" onClick={() => setAberta(false)}>
                <Users size={14} /> <span className="side-texto">Usuários</span>
              </NavLink>
              <NavLink to="/admin/grupos" className="side-item" onClick={() => setAberta(false)}>
                <UsersRound size={14} /> <span className="side-texto">Grupos e permissões</span>
              </NavLink>
            </>
          )}
        </nav>
        <div className="side-rodape tb-rel">
          <button className="usuario-btn" onMouseDown={(e) => e.stopPropagation()} onClick={() => setMenu((v) => !v)}>
            <Avatar u={eu} tamanho={28} />
            <span className="side-texto">{eu?.nome}</span>
            <ChevronDown size={14} />
          </button>
          <Popover aberto={menu} onFechar={() => setMenu(false)}>
            <button className="menu-item" onClick={() => { setMenu(false); setAberta(false); nav('/perfil') }}>
              <User size={14} /> Meu perfil
            </button>
            <button className="menu-item" onClick={() => { setMenu(false); nav('/perfil#senha') }}>
              <Settings size={14} /> Trocar senha
            </button>
            <button className="menu-item" onClick={() => sair().then(() => nav('/login'))}>
              <LogOut size={14} /> Sair
            </button>
          </Popover>
        </div>
      </aside>
      <button className="side-toggle" onClick={() => setAberta((v) => !v)} aria-label="Menu"><Menu size={20} /></button>
      <div className="side-veu" onClick={() => setAberta(false)} />
      <main className="conteudo">{children}</main>
    </div>
  )
}
