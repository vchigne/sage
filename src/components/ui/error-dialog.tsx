import React from 'react'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from './dialog'

interface ErrorDialogProps {
  isOpen: boolean
  onClose: () => void
  error: {
    message: string
    details?: string
    validation_errors?: Array<{
      type: string
      message: string
      details?: string
    }>
  } | null
}

export function ErrorDialog({ isOpen, onClose, error }: ErrorDialogProps) {
  if (!error) return null

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle className="text-red-600">Error de Validación</DialogTitle>
        </DialogHeader>
        <div className="mt-4 space-y-4">
          <p className="text-gray-700 font-medium">{error.message}</p>

          {error.validation_errors && error.validation_errors.length > 0 && (
            <div className="space-y-3">
              <h4 className="font-medium text-gray-900">Detalles del error:</h4>
              {error.validation_errors.map((err, index) => (
                <div key={index} className="bg-red-50 p-3 rounded-md">
                  <p className="text-red-700">{err.message}</p>
                  {err.details && (
                    <p className="text-sm text-red-600 mt-1">{err.details}</p>
                  )}
                </div>
              ))}
            </div>
          )}

          {error.details && !error.validation_errors && (
            <p className="text-sm text-gray-600">{error.details}</p>
          )}
        </div>
      </DialogContent>
    </Dialog>
  )
}