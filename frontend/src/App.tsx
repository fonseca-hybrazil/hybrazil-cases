import type { ReactNode } from 'react'
import { Navigate, Outlet, Route, Routes, useLocation } from 'react-router-dom'
import { useAuth } from './auth'
import { Carregando } from './components/comuns'
import Layout from './components/Layout'
import Login from './pages/Login'
import TrocarSenha from './pages/TrocarSenha'
import Inicio from './pages/Inicio'
import QuadroPagina from './pages/Quadro'
import Perfil from './pages/Perfil'
import Dashboard from './pages/Dashboard'
import AdminUsuarios from './pages/admin/Usuarios'
import AdminGrupos from './pages/admin/Grupos'
import AdminCategorias from './pages/admin/Categorias'
import AdminLabels from './pages/admin/Labels'
import AdminProjetos from './pages/admin/Projetos'

function Protegido() {
  const { eu, carregando } = useAuth()
  const loc = useLocation()
  if (carregando) return <Carregando />
  if (!eu) return <Navigate to="/login" replace state={{ de: loc.pathname + loc.search }} />
  if (eu.trocar_senha) return <Navigate to="/trocar-senha" replace />
  return <Layout><Outlet /></Layout>
}

function ComPermissao({ p, children }: { p: string; children: ReactNode }) {
  const { pode } = useAuth()
  return pode(p) ? <>{children}</> : <div className="pagina"><p>Você não tem acesso a esta página.</p></div>
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/trocar-senha" element={<TrocarSenha />} />
      <Route element={<Protegido />}>
        <Route path="/" element={<Inicio />} />
        <Route path="/p/:projetoId" element={<QuadroPagina />} />
        <Route path="/p/:projetoId/t/:numero" element={<QuadroPagina />} />
        <Route path="/perfil" element={<Perfil />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/admin/usuarios" element={<ComPermissao p="admin_usuarios"><AdminUsuarios /></ComPermissao>} />
        <Route path="/admin/grupos" element={<ComPermissao p="admin_usuarios"><AdminGrupos /></ComPermissao>} />
        <Route path="/admin/categorias" element={<ComPermissao p="admin_categorias"><AdminCategorias /></ComPermissao>} />
        <Route path="/admin/labels" element={<AdminLabels />} />
        <Route path="/admin/projetos" element={<ComPermissao p="admin_projetos"><AdminProjetos /></ComPermissao>} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  )
}
