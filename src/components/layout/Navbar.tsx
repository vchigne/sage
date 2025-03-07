import { Menu, Bell, User } from 'lucide-react'

interface NavbarProps {
  onMenuClick: () => void;
}

export function Navbar({ onMenuClick }: NavbarProps) {
  return (
    <nav className="bg-white shadow-sm z-10">
      <div className="px-4 h-14 flex items-center justify-between">
        <button
          onClick={onMenuClick}
          className="p-1.5 rounded-md hover:bg-gray-100"
          aria-label="Menu"
        >
          <Menu className="h-5 w-5 text-gray-600" />
        </button>

        <div className="flex items-center space-x-2">
          <button className="p-1.5 rounded-md hover:bg-gray-100 relative">
            <Bell className="h-5 w-5 text-gray-600" />
            <span className="absolute top-1 right-1 h-2 w-2 bg-red-500 rounded-full"></span>
          </button>

          <button className="p-1.5 rounded-md hover:bg-gray-100">
            <User className="h-5 w-5 text-gray-600" />
          </button>
        </div>
      </div>
    </nav>
  )
}