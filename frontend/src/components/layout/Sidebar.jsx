import { NavLink } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'

const navItems = [
  { to: '/', label: 'Dashboard', end: true },
  { to: '/recommendations', label: 'Recommendations' },
  { to: '/purchase-orders', label: 'Purchase Orders' },
  { to: '/dead-stock', label: 'Dead Stock' },
  { to: '/demand-forecast', label: 'Demand Forecast' },
  { to: '/supplier-analytics', label: 'Supplier Analytics' },
  { to: '/seasonal-events', label: 'Seasonal Events' },
  { to: '/notifications', label: 'Notifications' },
  { to: '/reports', label: 'Reports' },
  { to: '/categories', label: 'Categories', ownerOnly: true },
  { to: '/suppliers', label: 'Suppliers', ownerOnly: true },
  { to: '/products', label: 'Products' },
  { to: '/sales', label: 'Sales' },
  { to: '/settings', label: 'Settings', ownerOnly: true },
  { to: '/staff', label: 'Staff', ownerOnly: true },
]

export default function Sidebar() {
  const { isOwner } = useAuth()

  const visibleItems = navItems.filter((item) => !item.ownerOnly || isOwner)

  return (
    <aside className="flex w-64 flex-col border-r border-slate-200 bg-white">
      <div className="border-b border-slate-200 px-6 py-5">
        <div className="text-lg font-bold text-brand-700">SmartSupply</div>
        <div className="text-xs text-slate-500">Inventory Assistant</div>
      </div>
      <nav className="flex-1 space-y-1 p-4">
        {visibleItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.end}
            className={({ isActive }) =>
              `block rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
                isActive
                  ? 'bg-brand-50 text-brand-700'
                  : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
              }`
            }
          >
            {item.label}
          </NavLink>
        ))}
      </nav>
    </aside>
  )
}
