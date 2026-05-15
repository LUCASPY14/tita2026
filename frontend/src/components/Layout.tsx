import { useState } from 'react'
import { Outlet, useNavigate, useLocation } from 'react-router-dom'
import { Layout, Menu, Button, Dropdown } from 'antd'
import {
  DashboardOutlined,
  ShoppingCartOutlined,
  ShoppingOutlined,
  UserOutlined,
  BoxPlotOutlined,
  WalletOutlined,
  CalculatorOutlined,
  LogoutOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
} from '@ant-design/icons'
import { useAuthStore } from '../store/authStore'

const { Header, Sider, Content } = Layout

const menuItems = [
  { key: '/dashboard', icon: <DashboardOutlined />, label: 'Dashboard' },
  { key: '/ventas', icon: <ShoppingCartOutlined />, label: 'Ventas' },
  { key: '/compras', icon: <ShoppingOutlined />, label: 'Compras' },
  { key: '/clientes', icon: <UserOutlined />, label: 'Clientes' },
  { key: '/productos', icon: <BoxPlotOutlined />, label: 'Productos' },
  { key: '/tarjetas', icon: <WalletOutlined />, label: 'Tarjetas' },
  { key: '/caja', icon: <CalculatorOutlined />, label: 'Caja' },
]

export default function AppLayout() {
  const [collapsed, setCollapsed] = useState(false)
  const navigate = useNavigate()
  const location = useLocation()
  const { user, logout } = useAuthStore()

  return (
    <Layout className="min-h-screen">
      <Sider trigger={null} collapsible collapsed={collapsed} theme="dark">
        <div className="p-4 text-white text-center font-bold text-lg border-b border-green-700">
          {collapsed ? 'CT' : 'Cantina Tita'}
        </div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={({ key }) => navigate(key)}
        />
      </Sider>
      <Layout>
        <Header className="bg-white px-4 flex justify-between items-center shadow-sm">
          <Button
            type="text"
            icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
            onClick={() => setCollapsed(!collapsed)}
          />
          <Dropdown menu={{
            items: [
              { key: 'logout', icon: <LogoutOutlined />, label: 'Cerrar sesion', onClick: logout }
            ]
          }}>
            <Button type="text" icon={<UserOutlined />}>
              {user?.nombre || 'Usuario'}
            </Button>
          </Dropdown>
        </Header>
        <Content className="m-4 p-4 bg-white rounded-lg">
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  )
}