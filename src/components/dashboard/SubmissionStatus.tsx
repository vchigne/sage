import { useEffect, useState } from 'react'
import { Calendar, Mail, Phone } from 'lucide-react'
import type { Submission } from '../../lib/supabase/types'
import { formatDistanceToNow } from 'date-fns'
import { es } from 'date-fns/locale'

interface SubmissionStatusProps {
  organizationId?: string;
  compact?: boolean;
}

export function SubmissionStatus({ organizationId, compact = false }: SubmissionStatusProps) {
  const [submissions, setSubmissions] = useState<Submission[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const loadSubmissions = async () => {
      try {
        const url = new URL('/api/submissions', window.location.origin)
        if (organizationId) {
          url.searchParams.set('organizationId', organizationId)
        }

        const response = await fetch(url)
        if (!response.ok) {
          throw new Error('Failed to fetch submissions')
        }

        const data = await response.json()
        setSubmissions(data)
      } catch (err) {
        console.error('Error loading submissions:', err)
      } finally {
        setLoading(false)
      }
    }

    loadSubmissions()

    // Polling cada 30 segundos
    const interval = setInterval(loadSubmissions, 30000)
    return () => clearInterval(interval)
  }, [organizationId, compact])

  const getTimeStatus = (submission: Submission) => {
    const dueDate = new Date(submission.due_date)
    const now = new Date()

    if (submission.status === 'late') {
      return {
        text: `Retrasado por ${formatDistanceToNow(dueDate, { locale: es })}`,
        color: 'text-red-600'
      }
    }

    if (dueDate > now) {
      return {
        text: `Vence en ${formatDistanceToNow(dueDate, { locale: es })}`,
        color: 'text-yellow-600'
      }
    }

    return {
      text: `Vencido hace ${formatDistanceToNow(dueDate, { locale: es })}`,
      color: 'text-red-600'
    }
  }

  if (loading) {
    return <div>Cargando envíos...</div>
  }

  if (compact) {
    return (
      <div className="space-y-2">
        {submissions.slice(0, 3).map((submission) => {
          const timeStatus = getTimeStatus(submission)
          return (
            <div key={submission.id} className="flex items-center justify-between text-sm">
              <span className="text-gray-600 truncate">{submission.responsible_name}</span>
              <span className={`text-xs font-medium ${timeStatus.color}`}>
                {timeStatus.text}
              </span>
            </div>
          )
        })}
      </div>
    )
  }

  return (
    <div className="bg-white rounded-lg shadow-sm">
      <div className="p-6 border-b border-gray-200">
        <div className="flex items-center">
          <Calendar className="h-5 w-5 text-gray-500 mr-2" />
          <h2 className="text-lg font-medium text-gray-900">Estado de Envíos</h2>
        </div>
      </div>

      <div className="divide-y divide-gray-200">
        {submissions.map((submission) => {
          const timeStatus = getTimeStatus(submission)

          return (
            <div key={submission.id} className="p-6">
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <p className="text-sm font-medium text-gray-900">{submission.responsible_name}</p>
                  <div className="mt-1 flex items-center space-x-4 text-sm text-gray-500">
                    <a 
                      href={`mailto:${submission.responsible_email}`}
                      className="flex items-center hover:text-blue-600"
                    >
                      <Mail className="h-4 w-4 mr-1" />
                      {submission.responsible_email}
                    </a>
                    {submission.responsible_phone && (
                      <a 
                        href={`tel:${submission.responsible_phone}`}
                        className="flex items-center hover:text-blue-600"
                      >
                        <Phone className="h-4 w-4 mr-1" />
                        {submission.responsible_phone}
                      </a>
                    )}
                  </div>
                </div>

                <div className="text-right">
                  <p className={`text-sm font-medium ${timeStatus.color}`}>
                    {timeStatus.text}
                  </p>
                  <p className="mt-1 text-xs text-gray-500">
                    Fecha límite: {new Date(submission.due_date).toLocaleDateString()}
                  </p>
                </div>
              </div>
            </div>
          )
        })}

        {submissions.length === 0 && (
          <div className="p-6 text-center text-gray-500">
            No hay envíos pendientes
          </div>
        )}
      </div>
    </div>
  )
}