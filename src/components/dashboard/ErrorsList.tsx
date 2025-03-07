import { useEffect, useState } from 'react'
import { AlertTriangle } from 'lucide-react'
import type { Error } from '../../lib/supabase/types'
import { formatDistanceToNow } from 'date-fns'
import { es } from 'date-fns/locale'

interface ErrorsListProps {
  organizationId?: string;
  compact?: boolean;
}

export function ErrorsList({ organizationId, compact = false }: ErrorsListProps) {
  const [errors, setErrors] = useState<Error[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const loadErrors = async () => {
      try {
        const url = new URL('/api/errors', window.location.origin)
        if (organizationId) {
          url.searchParams.set('organizationId', organizationId)
        }

        const response = await fetch(url)
        if (!response.ok) {
          throw new Error('Failed to fetch errors')
        }

        const data = await response.json()
        setErrors(data)
      } catch (err) {
        console.error('Error loading errors:', err)
      } finally {
        setLoading(false)
      }
    }

    loadErrors()

    // Polling cada 30 segundos
    const interval = setInterval(loadErrors, 30000)
    return () => clearInterval(interval)
  }, [organizationId, compact])

  const getSeverityColor = (severity: Error['severity']) => {
    switch (severity) {
      case 'high':
        return 'bg-red-100 text-red-800';
      case 'medium':
        return 'bg-yellow-100 text-yellow-800';
      case 'low':
        return 'bg-blue-100 text-blue-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  }

  if (loading) {
    return <div>Cargando errores...</div>
  }

  if (compact) {
    return (
      <div className="space-y-2">
        {errors.slice(0, 3).map((error) => (
          <div key={error.id} className="flex items-center justify-between text-sm">
            <div className="flex items-center space-x-2">
              <span className={`px-1.5 py-0.5 rounded text-xs font-medium ${getSeverityColor(error.severity)}`}>
                {error.severity}
              </span>
              <span className="text-gray-600 truncate">{error.message}</span>
            </div>
          </div>
        ))}
      </div>
    )
  }

  return (
    <div className="bg-white rounded-lg shadow-sm">
      <div className="p-6 border-b border-gray-200">
        <div className="flex items-center">
          <AlertTriangle className="h-5 w-5 text-gray-500 mr-2" />
          <h2 className="text-lg font-medium text-gray-900">Últimos Errores</h2>
        </div>
      </div>

      <div className="divide-y divide-gray-200">
        {errors.map((error) => (
          <div key={error.id} className="p-6">
            <div className="flex items-center justify-between">
              <div className="flex-1">
                <div className="flex items-center space-x-2">
                  <span className="text-sm font-medium text-gray-900">
                    {error.responsible_name}
                  </span>
                  <span className={`px-2.5 py-0.5 rounded-full text-xs font-medium ${getSeverityColor(error.severity)}`}>
                    {error.severity}
                  </span>
                </div>
                <p className="mt-1 text-sm text-gray-600">{error.message}</p>
              </div>
              <p className="text-xs text-gray-500">
                {formatDistanceToNow(new Date(error.created_at), {
                  addSuffix: true,
                  locale: es
                })}
              </p>
            </div>
          </div>
        ))}

        {errors.length === 0 && (
          <div className="p-6 text-center text-gray-500">
            No hay errores recientes
          </div>
        )}
      </div>
    </div>
  )
}