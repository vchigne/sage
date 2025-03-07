import { X, LayoutDashboard, Settings, Activity, Users, FileText, Bell, Mail, Upload } from 'lucide-react'
import { useRouter } from 'next/navigation'

interface SidebarProps {
  className?: string;
  isOpen?: boolean;
  onClose?: () => void;
}

const menuItems = [
  { path: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { path: '/upload', icon: Upload, label: 'Subir Archivos' },
  { path: '/configuration', icon: Settings, label: 'Configuración' },
  { path: '/monitoring', icon: Activity, label: 'Monitoreo' },
  { path: '/users', icon: Users, label: 'Usuarios' },
  { path: '/reports', icon: FileText, label: 'Reportes' },
  { path: '/alerts', icon: Bell, label: 'Alertas' },
  { path: '/subscriptions', icon: Mail, label: 'Suscripciones' }
]

export function Sidebar({ className, isOpen, onClose }: SidebarProps) {
  const router = useRouter()

  const handleNavigation = (path: string) => {
    router.push(path)
    if (onClose) {
      onClose()
    }
  }

  return (
    <aside className={`w-64 bg-white shadow-lg ${className || ''}`}>
      <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
        <h1 className="text-xl font-bold text-gray-800">SAGE Admin</h1>
        {isOpen && (
          <button 
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-lg flex items-center justify-center"
            aria-label="Cerrar menú"
          >
            <X className="h-6 w-6 text-gray-800" />
          </button>
        )}
      </div>

      <nav className="mt-4">
        {menuItems.map((item) => (
          <button
            key={item.path}
            onClick={() => handleNavigation(item.path)}
            className="w-full px-6 py-3 flex items-center text-gray-700 hover:bg-gray-100 hover:text-blue-600 transition-colors duration-200"
          >
            <item.icon className="h-5 w-5 flex-shrink-0" />
            <span className="ml-3 text-sm font-medium">{item.label}</span>
          </button>
        ))}
      </nav>
    </aside>
  )
}