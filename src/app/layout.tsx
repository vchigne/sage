'use client'

import { useState } from 'react'
import { Sidebar } from '../components/layout/Sidebar'
import { Navbar } from '../components/layout/Navbar'
import './globals.css'
import { Inter } from 'next/font/google'

const inter = Inter({ subsets: ['latin'] })

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const [isSidebarOpen, setIsSidebarOpen] = useState(false)

  const handleCloseSidebar = () => {
    setIsSidebarOpen(false)
  }

  return (
    <html lang="es" className="h-full bg-gray-100">
      <head>
        <title>SAGE Admin</title>
        <meta name="description" content="Sistema de validación y procesamiento de datos basado en YAML" />
      </head>
      <body className={`${inter.className} h-full`}>
        <div className="flex h-screen bg-gray-50">
          {/* Sidebar - desktop version */}
          <Sidebar className="hidden md:block" />

          {/* Mobile sidebar */}
          {isSidebarOpen && (
            <div 
              className="fixed inset-0 bg-black bg-opacity-50 z-40 md:hidden"
              onClick={handleCloseSidebar}
            >
              <div onClick={e => e.stopPropagation()}>
                <Sidebar 
                  className="absolute h-full w-64 transform transition-transform duration-200 ease-in-out bg-white" 
                  isOpen={true}
                  onClose={handleCloseSidebar}
                />
              </div>
            </div>
          )}

          {/* Main content */}
          <div className="flex-1 flex flex-col">
            <Navbar onMenuClick={() => setIsSidebarOpen(!isSidebarOpen)} />
            <main className="flex-1 p-4 md:p-6 overflow-y-auto">
              {children}
            </main>
          </div>
        </div>
      </body>
    </html>
  )
}