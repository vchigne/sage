import React from 'react'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from './dialog'
import { Loader2 } from 'lucide-react'

interface ProcessingDialogProps {
  isOpen: boolean
  onClose: () => void
  steps: Array<{
    message: string
    status: 'pending' | 'processing' | 'completed' | 'error'
  }>
}

export function ProcessingDialog({ isOpen, onClose, steps }: ProcessingDialogProps) {
  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="fixed top-[50%] left-[50%] max-w-md w-[90vw] translate-x-[-50%] translate-y-[-50%] z-50">
        <DialogHeader>
          <DialogTitle>Procesando Archivo</DialogTitle>
        </DialogHeader>
        <div className="mt-4">
          <div className="space-y-4">
            {steps.map((step, index) => (
              <div key={index} className="flex items-center space-x-3">
                {step.status === 'processing' && (
                  <Loader2 className="h-5 w-5 animate-spin text-blue-500" />
                )}
                {step.status === 'completed' && (
                  <div className="h-5 w-5 rounded-full bg-green-500 flex items-center justify-center">
                    <svg className="h-3 w-3 text-white" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                    </svg>
                  </div>
                )}
                {step.status === 'error' && (
                  <div className="h-5 w-5 rounded-full bg-red-500 flex items-center justify-center">
                    <svg className="h-3 w-3 text-white" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                    </svg>
                  </div>
                )}
                {step.status === 'pending' && (
                  <div className="h-5 w-5 rounded-full bg-gray-300" />
                )}
                <span className={`text-sm font-medium ${
                  step.status === 'error' ? 'text-red-600' :
                  step.status === 'completed' ? 'text-green-600' :
                  step.status === 'processing' ? 'text-blue-600' :
                  'text-gray-500'
                }`}>
                  {step.message}
                </span>
              </div>
            ))}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}