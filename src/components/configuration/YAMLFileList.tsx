import { useState, useEffect, useRef } from 'react'
import { FileText, CheckCircle, XCircle, Eye, Trash2, BarChart2 } from 'lucide-react'
import type { Installation } from '../../lib/supabase/types'
import Prism from 'prismjs'
import 'prismjs/components/prism-yaml'
import 'prismjs/themes/prism.css'

interface YAMLFileListProps {
  type: 'catalogs' | 'packages' | 'senders'
}

interface Status {
  type: 'success' | 'error';
  message: string;
}

export function YAMLFileList({ type }: YAMLFileListProps) {
  const [files, setFiles] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedInstallation, setSelectedInstallation] = useState<string>('')
  const [installations, setInstallations] = useState<Installation[]>([])
  const [selectedFile, setSelectedFile] = useState<any | null>(null)
  const [showModal, setShowModal] = useState(false)
  const [showDashboard, setShowDashboard] = useState(false)
  const codeRef = useRef<HTMLElement>(null)
  const [status, setStatus] = useState<Status | null>(null);

  useEffect(() => {
    const highlightCode = () => {
      if (showModal && codeRef.current) {
        Prism.highlightElement(codeRef.current)
      }
    }

    highlightCode()

    const handleScroll = () => {
      requestAnimationFrame(highlightCode)
    }

    if (showModal) {
      window.addEventListener('scroll', handleScroll, true)
    }

    return () => {
      window.removeEventListener('scroll', handleScroll, true)
    }
  }, [showModal, selectedFile])

  useEffect(() => {
    const loadInstallations = async () => {
      try {
        const response = await fetch('/api/installations')
        if (!response.ok) throw new Error('Error cargando instalaciones')
        const data = await response.json()
        setInstallations(data)
      } catch (err) {
        console.error('Error en loadInstallations:', err)
        setError(err instanceof Error ? err.message : 'Error desconocido')
      }
    }

    loadInstallations()
  }, [])

  const loadFiles = async () => {
    try {
      setLoading(true)
      setError(null)

      const url = new URL(`/api/${type}`, window.location.origin)
      if (selectedInstallation) {
        url.searchParams.set('installation_id', selectedInstallation)
      }

      const response = await fetch(url)
      if (!response.ok) throw new Error(`Error cargando archivos ${type}`)
      const data = await response.json()
      setFiles(data)
    } catch (err) {
      console.error('Error en loadFiles:', err)
      setError(err instanceof Error ? err.message : 'Error inesperado al cargar los archivos')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadFiles()
    const interval = setInterval(loadFiles, 10000)
    return () => clearInterval(interval)
  }, [type, selectedInstallation])

  const handleDelete = async (file: any) => {
    if (!confirm('¿Estás seguro de que deseas eliminar este archivo?')) {
      return false
    }

    try {
      const response = await fetch(`/api/${type}/${file.id}`, {
        method: 'DELETE',
        headers: {
          'Accept': 'application/json'
        }
      })

      const contentType = response.headers.get('content-type')
      if (!contentType || !contentType.includes('application/json')) {
        setStatus({
          type: 'error',
          message: 'Respuesta inesperada del servidor'
        })
        return false
      }

      const text = await response.text()
      let data
      try {
        data = JSON.parse(text)
      } catch (e) {
        console.error('Error parsing response:', e, 'Response text:', text)
        setStatus({
          type: 'error',
          message: 'Error al procesar la respuesta del servidor'
        })
        return false
      }

      if (!response.ok) {
        setStatus({
          type: 'error',
          message: data.error || 'Error al eliminar el archivo'
        })
        return false
      }

      await loadFiles()
      setStatus({
        type: 'success',
        message: data.message || 'Archivo eliminado correctamente'
      })
      return true
    } catch (error) {
      console.error('Error al eliminar:', error)
      setStatus({
        type: 'error',
        message: error instanceof Error ? error.message : 'Error al eliminar el archivo'
      })
      return false
    }
  }

  const renderDashboard = () => {
    if (!selectedFile) return null

    const lastExecution = new Date(Date.now() - 2 * 60 * 60 * 1000)
    const executionHistory = [
      { timestamp: new Date(Date.now() - 15 * 60 * 1000), status: 'success', duration: '45s', user: 'admin@example.com', method: 'API' },
      { timestamp: new Date(Date.now() - 45 * 60 * 1000), status: 'error', duration: '32s', user: 'system', method: 'SFTP' },
      { timestamp: new Date(Date.now() - 90 * 60 * 1000), status: 'success', duration: '47s', user: 'admin@example.com', method: 'Web' },
    ]

    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
        <div className="bg-white rounded-lg w-full max-w-6xl h-[90vh] flex flex-col">
          <div className="p-4 border-b border-gray-200 flex justify-between items-center">
            <h3 className="text-lg font-medium">Dashboard - {selectedFile.name}</h3>
            <button onClick={() => setShowDashboard(false)} className="text-gray-400 hover:text-gray-500">✕</button>
          </div>
          <div className="flex-1 p-6 overflow-auto">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
                <h4 className="text-lg font-medium mb-4">Información General</h4>
                <dl className="space-y-2">
                  <div>
                    <dt className="text-sm text-gray-500">Última modificación</dt>
                    <dd className="text-sm font-medium">
                      {new Date(selectedFile.uploaded_at).toLocaleString()}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-sm text-gray-500">Estado de validación</dt>
                    <dd className="text-sm font-medium">
                      {selectedFile.validation_status === 'valid' ?
                        <span className="text-green-600">Válido</span> :
                        <span className="text-red-600">Inválido</span>
                      }
                    </dd>
                  </div>
                  <div>
                    <dt className="text-sm text-gray-500">Método de carga</dt>
                    <dd className="text-sm font-medium">{selectedFile.upload_method || 'Web'}</dd>
                  </div>
                  <div>
                    <dt className="text-sm text-gray-500">Subido por</dt>
                    <dd className="text-sm font-medium">{selectedFile.uploaded_by}</dd>
                  </div>
                  <div>
                    <dt className="text-sm text-gray-500">Email del cargador</dt>
                    <dd className="text-sm font-medium">{selectedFile.uploader_email || 'No disponible'}</dd>
                  </div>
                  <div>
                    <dt className="text-sm text-gray-500">Tamaño</dt>
                    <dd className="text-sm font-medium">{(selectedFile.content.length / 1024).toFixed(2)} KB</dd>
                  </div>
                </dl>
              </div>

              <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
                <h4 className="text-lg font-medium mb-4">Detalles de Instalación</h4>
                <dl className="space-y-2">
                  <div>
                    <dt className="text-sm text-gray-500">Organización</dt>
                    <dd className="text-sm font-medium">{selectedFile.organization_name}</dd>
                  </div>
                  <div>
                    <dt className="text-sm text-gray-500">País</dt>
                    <dd className="text-sm font-medium">
                      {selectedFile.country_name} ({selectedFile.country_code})
                    </dd>
                  </div>
                  <div>
                    <dt className="text-sm text-gray-500">Producto</dt>
                    <dd className="text-sm font-medium">{selectedFile.product_name}</dd>
                  </div>
                  <div>
                    <dt className="text-sm text-gray-500">ID de Instalación</dt>
                    <dd className="text-sm font-medium">{selectedFile.installation_id}</dd>
                  </div>
                </dl>
              </div>

              <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
                <h4 className="text-lg font-medium mb-4">Estadísticas de Uso</h4>
                <dl className="space-y-2">
                  <div>
                    <dt className="text-sm text-gray-500">Última ejecución</dt>
                    <dd className="text-sm font-medium">{lastExecution.toLocaleString()}</dd>
                  </div>
                  <div>
                    <dt className="text-sm text-gray-500">Estado actual</dt>
                    <dd className="text-sm font-medium text-green-600">Activo</dd>
                  </div>
                  <div>
                    <dt className="text-sm text-gray-500">Tasa de éxito (24h)</dt>
                    <dd className="text-sm font-medium">98%</dd>
                  </div>
                </dl>
              </div>
            </div>

            <div className="mt-8">
              <h4 className="text-lg font-medium mb-4">Historial de Ejecuciones</h4>
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                        Fecha y Hora
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                        Estado
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                        Duración
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                        Usuario
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                        Método
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {executionHistory.map((execution, index) => (
                      <tr key={index} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {execution.timestamp.toLocaleString()}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                            execution.status === 'success' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                          }`}>
                            {execution.status === 'success' ? 'Exitoso' : 'Error'}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {execution.duration}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {execution.user}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {execution.method}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="h-full flex flex-col space-y-4">
      <div className="bg-white p-4 rounded-lg shadow-sm">
        <div className="max-w-xl">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Instalación
          </label>
          <select
            className="w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
            value={selectedInstallation}
            onChange={(e) => setSelectedInstallation(e.target.value)}
          >
            <option value="">Todas las instalaciones</option>
            {installations.map((installation) => (
              <option key={installation.id} value={installation.id}>
                {installation.organizations?.name} - {installation.countries?.name} ({installation.countries?.code}) - {installation.products?.name}
              </option>
            ))}
          </select>
        </div>
      </div>

      {status && (
        <div className={`bg-${status.type === 'success' ? 'green' : 'red'}-50 border border-${status.type === 'success' ? 'green' : 'red'}-200 rounded-md p-4 text-${status.type === 'success' ? 'green' : 'red'}-600`}>
          {status.message}
        </div>
      )}

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-md p-4 text-red-600">
          {error}
        </div>
      )}

      <div className="hidden md:block flex-1 bg-white rounded-lg shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Archivo
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Instalación
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Estado
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Método
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Fecha
                </th>
                <th scope="col" className="relative px-6 py-3">
                  <span className="sr-only">Acciones</span>
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {files.map((file) => (
                <tr key={file.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <FileText className="h-5 w-5 text-gray-400 mr-2" />
                      <button
                        onClick={() => {
                          setSelectedFile(file)
                          setShowModal(true)
                        }}
                        className="text-sm text-blue-600 hover:text-blue-800"
                      >
                        {file.name}
                      </button>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {file.organization_name} - {file.country_name} ({file.country_code})
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      {file.validation_status === 'valid' ? (
                        <CheckCircle className="h-5 w-5 text-green-600" />
                      ) : (
                        <XCircle className="h-5 w-5 text-red-600" />
                      )}
                      <span className="ml-2 text-sm text-gray-900">
                        {file.validation_status === 'valid' ? 'Válido' : 'Inválido'}
                      </span>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {file.upload_method || 'Web'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {new Date(file.uploaded_at).toLocaleString()}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <div className="flex items-center justify-end space-x-2">
                      <button
                        onClick={() => {
                          setSelectedFile(file)
                          setShowDashboard(true)
                        }}
                        className="text-indigo-600 hover:text-indigo-900"
                        title="Ver dashboard"
                      >
                        <BarChart2 className="h-4 w-4" />
                      </button>
                      <button
                        onClick={() => {
                          setSelectedFile(file)
                          setShowModal(true)
                        }}
                        className="text-blue-600 hover:text-blue-900"
                        title="Ver archivo"
                      >
                        <Eye className="h-4 w-4" />
                      </button>
                      <button
                        onClick={() => handleDelete(file)}
                        className="text-red-600 hover:text-red-900"
                        title="Eliminar"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="md:hidden flex-1 space-y-4">
        {files.map((file) => (
          <div key={file.id} className="bg-white rounded-lg shadow-sm p-4">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center">
                <FileText className="h-5 w-5 text-gray-400 mr-2" />
                <button
                  onClick={() => {
                    setSelectedFile(file)
                    setShowModal(true)
                  }}
                  className="text-sm font-medium text-blue-600 hover:text-blue-800"
                >
                  {file.name}
                </button>
              </div>
              <div className="flex items-center space-x-2">
                <button
                  onClick={() => {
                    setSelectedFile(file)
                    setShowDashboard(true)
                  }}
                  className="text-indigo-600 hover:text-indigo-900 p-2"
                  title="Ver dashboard"
                >
                  <BarChart2 className="h-4 w-4" />
                </button>
                <button
                  onClick={() => {
                    setSelectedFile(file)
                    setShowModal(true)
                  }}
                  className="text-blue-600 hover:text-blue-900 p-2"
                  title="Ver archivo"
                >
                  <Eye className="h-4 w-4" />
                </button>
                <button
                  onClick={() => handleDelete(file)}
                  className="text-red-600 hover:text-red-900 p-2"
                  title="Eliminar"
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>
            </div>
            <div className="space-y-2 text-sm">
              <div>
                <span className="text-gray-500">Instalación:</span>
                <span className="ml-2">{file.organization_name} - {file.country_name}</span>
              </div>
              <div>
                <span className="text-gray-500">Estado:</span>
                <span className="ml-2 flex items-center">
                  {file.validation_status === 'valid' ? (
                    <>
                      <CheckCircle className="h-4 w-4 text-green-600 mr-1" />
                      <span>Válido</span>
                    </>
                  ) : (
                    <>
                      <XCircle className="h-4 w-4 text-red-600 mr-1" />
                      <span>Inválido</span>
                    </>
                  )}
                </span>
              </div>
              <div>
                <span className="text-gray-500">Método:</span>
                <span className="ml-2">{file.upload_method || 'Web'}</span>
              </div>
              <div>
                <span className="text-gray-500">Fecha:</span>
                <span className="ml-2">{new Date(file.uploaded_at).toLocaleString()}</span>
              </div>
            </div>
          </div>
        ))}

        {loading ? (
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
          </div>
        ) : files.length === 0 ? (
          <div className="text-center py-12 text-gray-500">
            No hay archivos {type} cargados
          </div>
        ) : null}
      </div>

      {showModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg w-full max-w-6xl h-[90vh] flex flex-col">
            <div className="p-4 border-b border-gray-200 flex justify-between items-center">
              <h3 className="text-lg font-medium">{selectedFile?.name}</h3>
              <button onClick={() => setShowModal(false)} className="text-gray-400 hover:text-gray-500">✕</button>
            </div>
            <div className="flex-1 p-4 overflow-hidden">
              <div className="h-full overflow-auto">
                <pre className="h-full p-4 rounded-lg bg-gray-50">
                  <code ref={codeRef} className="language-yaml">
                    {selectedFile?.content}
                  </code>
                </pre>
              </div>
            </div>
          </div>
        </div>
      )}

      {showDashboard && renderDashboard()}
    </div>
  )
}