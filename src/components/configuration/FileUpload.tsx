import { useState, useEffect } from 'react'
import { Upload } from 'lucide-react'
import type { Installation } from '../../lib/supabase/types'
import { ErrorDialog } from '../ui/error-dialog'
import { ProcessingDialog } from '../ui/processing-dialog'

interface FileUploadProps {
  type: 'catalogs' | 'packages' | 'senders'
}

interface Step {
  message: string
  status: 'pending' | 'processing' | 'completed' | 'error'
}

export function FileUpload({ type }: FileUploadProps) {
  const [isDragging, setIsDragging] = useState(false)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [installations, setInstallations] = useState<Installation[]>([])
  const [loadingInstallations, setLoadingInstallations] = useState(true)
  const [errorInstallations, setErrorInstallations] = useState<string | null>(null)
  const [selectedInstallation, setSelectedInstallation] = useState<string>('')
  const [showErrorDialog, setShowErrorDialog] = useState(false)
  const [errorDetails, setErrorDetails] = useState<any>(null)
  const [status, setStatus] = useState<{
    type: 'info' | 'success' | 'error'
    message: string
  } | null>(null)
  const [processingSteps, setProcessingSteps] = useState<Step[]>([
    { message: 'Iniciando procesamiento del archivo...', status: 'pending' },
    { message: 'Validando formato y extensión...', status: 'pending' },
    { message: 'Analizando contenido...', status: 'pending' },
    { message: 'Enviando al servidor...', status: 'pending' }
  ])
  const [showProcessingDialog, setShowProcessingDialog] = useState(false)

  useEffect(() => {
    const loadInstallations = async () => {
      try {
        setLoadingInstallations(true)
        setErrorInstallations(null)
        const response = await fetch('/api/installations')
        if (!response.ok) {
          throw new Error('Error al cargar instalaciones')
        }
        const data = await response.json()
        setInstallations(data)
      } catch (err) {
        console.error('Error en loadInstallations:', err)
        setErrorInstallations(err instanceof Error ? err.message : 'Error desconocido')
      } finally {
        setLoadingInstallations(false)
      }
    }

    loadInstallations()
  }, [])

  const updateStep = (index: number, status: Step['status'], message?: string) => {
    setProcessingSteps(steps =>
      steps.map((step, i) => 
        i === index 
          ? { ...step, status, message: message || step.message }
          : step
      )
    )
  }

  const handleFileSelect = async (file: File) => {
    console.log('Archivo seleccionado:', file.name)
    setShowProcessingDialog(true)
    setSelectedFile(file)

    try {
      // Paso 1: Inicio
      updateStep(0, 'processing')
      await new Promise(resolve => setTimeout(resolve, 500))
      updateStep(0, 'completed')

      // Paso 2: Validación
      updateStep(1, 'processing')
      if (!file.name.endsWith('.xlsx') && !file.name.endsWith('.xls') && !file.name.endsWith('.zip')) {
        updateStep(1, 'error', 'Formato de archivo no soportado')
        throw new Error('El archivo debe ser Excel (.xlsx, .xls) o ZIP (.zip)')
      }
      await new Promise(resolve => setTimeout(resolve, 500))
      updateStep(1, 'completed')

      // Paso 3: Análisis
      updateStep(2, 'processing')
      if (file.name.endsWith('.zip')) {
        updateStep(2, 'completed', 'ZIP validado correctamente')
      } else {
        updateStep(2, 'completed', 'Excel validado correctamente')
      }

      // Paso 4: Preparación para envío
      updateStep(3, 'processing')
      setSelectedInstallation('')

    } catch (error) {
      console.error('Error procesando archivo:', error)
      setStatus({
        type: 'error',
        message: error instanceof Error ? error.message : 'Error procesando el archivo'
      })
      setShowErrorDialog(true)
    }
  }

  const handleSave = async () => {
    if (!selectedFile || !selectedInstallation) {
      setStatus({
        type: 'error',
        message: 'Seleccione una instalación antes de continuar'
      })
      return
    }

    try {
      const formData = new FormData()
      formData.append('file', selectedFile)
      formData.append('package_id', selectedInstallation)

      console.log('Enviando archivo al servidor...')
      const response = await fetch('/api/upload', {
        method: 'POST',
        body: formData
      })

      const data = await response.json()
      console.log('Respuesta del servidor:', data)

      if (!response.ok) {
        updateStep(3, 'error')
        if (data.validation_errors) {
          setErrorDetails(data)
          setShowErrorDialog(true)
        }
        throw new Error(data.message || 'Error al procesar el archivo')
      }

      updateStep(3, 'completed')
      setStatus({
        type: 'success',
        message: 'Archivo procesado correctamente'
      })

      setTimeout(() => {
        setShowProcessingDialog(false)
        setSelectedFile(null)
      }, 2000)

    } catch (error) {
      console.error('Error al procesar archivo:', error)
      setStatus({
        type: 'error',
        message: error instanceof Error ? error.message : 'Error al procesar el archivo'
      })
      updateStep(3, 'error')
    }
  }

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
    const file = e.dataTransfer.files[0]
    if (file) {
      await handleFileSelect(file)
    }
  }

  if (loadingInstallations) {
    return <div>Cargando instalaciones...</div>
  }

  if (errorInstallations) {
    return <div className="text-red-600">Error: {errorInstallations}</div>
  }

  return (
    <>
      <div className={`
        border-2 border-dashed rounded-lg p-6 text-center
        ${isDragging ? 'border-blue-500 bg-blue-50' : 'border-gray-300'}
      `}
        onDragOver={(e) => {
          e.preventDefault()
          setIsDragging(true)
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
      >
        <div className="flex flex-col items-center">
          <Upload className="h-12 w-12 mb-4 text-gray-400" />
          <p className="text-gray-600">
            Arrastra y suelta un archivo Excel o ZIP aquí
          </p>
          <p className="text-sm text-gray-500 mt-1">o</p>
          <button
            className="mt-2 px-4 py-2 text-sm font-medium text-blue-600 hover:text-blue-800 disabled:opacity-50"
            onClick={() => document.getElementById('file-upload')?.click()}
          >
            Selecciona un archivo
          </button>
          <input
            id="file-upload"
            type="file"
            className="hidden"
            accept=".xlsx,.xls,.zip"
            onChange={(e) => {
              const file = e.target.files?.[0]
              if (file) {
                handleFileSelect(file)
              }
            }}
          />

          {selectedFile && (
            <div className="mt-6 w-full max-w-md">
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Instalación
                </label>
                <select
                  className="w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                  value={selectedInstallation}
                  onChange={(e) => setSelectedInstallation(e.target.value)}
                >
                  <option value="">Seleccione una instalación</option>
                  {installations.map((installation) => (
                    <option key={installation.id} value={installation.id}>
                      {installation.organizations?.name} - {installation.countries?.name} ({installation.countries?.code}) - {installation.products?.name}
                    </option>
                  ))}
                </select>
              </div>

              <button
                className="w-full px-4 py-2 text-sm font-medium bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
                onClick={handleSave}
                disabled={!selectedInstallation}
              >
                Procesar archivo
              </button>
            </div>
          )}

          {status && (
            <div className={`mt-4 text-sm ${
              status.type === 'success' ? 'text-green-600' :
              status.type === 'error' ? 'text-red-600' :
              'text-blue-600'
            }`}>
              {status.message}
            </div>
          )}
        </div>
      </div>

      <ProcessingDialog
        isOpen={showProcessingDialog}
        onClose={() => setShowProcessingDialog(false)}
        steps={processingSteps}
      />

      <ErrorDialog
        isOpen={showErrorDialog}
        onClose={() => setShowErrorDialog(false)}
        error={errorDetails}
      />
    </>
  )
}