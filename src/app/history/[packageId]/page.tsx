'use client';

import { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import { CheckCircle, XCircle, Clock, AlertTriangle } from 'lucide-react';

interface Execution {
  id: number;
  yamlId: string;
  startedAt: string;
  completedAt: string | null;
  status: string;
  errorMessage: string | null;
  logContent: string | null;
}

export default function HistoryPage() {
  const params = useParams();
  const [executions, setExecutions] = useState<Execution[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedExecution, setSelectedExecution] = useState<Execution | null>(null);

  useEffect(() => {
    const fetchHistory = async () => {
      try {
        setLoading(true);
        setError(null);

        console.log('Fetching history for package ID:', params.packageId);
        const response = await fetch(`/api/execution-history/${params.packageId}`);

        if (!response.ok) {
          const errorText = await response.text();
          console.error('API Error:', errorText);
          throw new Error(`Error al cargar el historial: ${errorText}`);
        }

        const data = await response.json();
        console.log('Received execution history:', data);
        setExecutions(data);
      } catch (err) {
        console.error('Error fetching history:', err);
        setError(err instanceof Error ? err.message : 'Error desconocido');
      } finally {
        setLoading(false);
      }
    };

    if (params.packageId) {
      fetchHistory();
    }
  }, [params.packageId]);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'success':
        return <CheckCircle className="h-5 w-5 text-green-500" />;
      case 'error':
        return <XCircle className="h-5 w-5 text-red-500" />;
      case 'processing':
        return <Clock className="h-5 w-5 text-blue-500" />;
      default:
        return <AlertTriangle className="h-5 w-5 text-yellow-500" />;
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4">
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <p className="text-red-600">{error}</p>
          <p className="text-sm text-red-500 mt-2">ID del paquete: {params.packageId}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-bold mb-6">Historial de Ejecuciones</h1>

      <div className="grid md:grid-cols-2 gap-6">
        <div className="space-y-4">
          {executions.map((execution) => (
            <div
              key={execution.id}
              className={`bg-white rounded-lg shadow-sm p-4 border cursor-pointer transition-colors ${
                selectedExecution?.id === execution.id
                  ? 'border-blue-500'
                  : 'border-gray-200 hover:border-blue-300'
              }`}
              onClick={() => setSelectedExecution(execution)}
            >
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center space-x-2">
                  {getStatusIcon(execution.status)}
                  <span className="font-medium">
                    {execution.status === 'success' ? 'Exitoso' :
                     execution.status === 'error' ? 'Error' :
                     execution.status === 'processing' ? 'En Proceso' : 'Desconocido'}
                  </span>
                </div>
                <span className="text-sm text-gray-500">
                  {new Date(execution.startedAt).toLocaleString()}
                </span>
              </div>

              {execution.errorMessage && (
                <p className="text-sm text-red-600 mt-2">{execution.errorMessage}</p>
              )}
            </div>
          ))}

          {executions.length === 0 && (
            <div className="text-center py-8 text-gray-500">
              No hay ejecuciones registradas para este paquete
            </div>
          )}
        </div>

        {selectedExecution && (
          <div className="bg-white rounded-lg shadow-sm p-4 border border-gray-200">
            <h2 className="text-lg font-medium mb-4">Detalles de la Ejecución</h2>
            <dl className="space-y-3">
              <div>
                <dt className="text-sm text-gray-500">ID</dt>
                <dd className="mt-1 text-sm">{selectedExecution.id}</dd>
              </div>
              <div>
                <dt className="text-sm text-gray-500">Inicio</dt>
                <dd className="mt-1 text-sm">
                  {new Date(selectedExecution.startedAt).toLocaleString()}
                </dd>
              </div>
              {selectedExecution.completedAt && (
                <div>
                  <dt className="text-sm text-gray-500">Finalización</dt>
                  <dd className="mt-1 text-sm">
                    {new Date(selectedExecution.completedAt).toLocaleString()}
                  </dd>
                </div>
              )}
              <div>
                <dt className="text-sm text-gray-500">Estado</dt>
                <dd className="mt-1 text-sm flex items-center">
                  {getStatusIcon(selectedExecution.status)}
                  <span className="ml-2">
                    {selectedExecution.status === 'success' ? 'Exitoso' :
                     selectedExecution.status === 'error' ? 'Error' :
                     selectedExecution.status === 'processing' ? 'En Proceso' : 'Desconocido'}
                  </span>
                </dd>
              </div>
              {selectedExecution.errorMessage && (
                <div>
                  <dt className="text-sm text-gray-500">Mensaje de Error</dt>
                  <dd className="mt-1 text-sm text-red-600">
                    {selectedExecution.errorMessage}
                  </dd>
                </div>
              )}
              {selectedExecution.logContent && (
                <div>
                  <dt className="text-sm text-gray-500">Logs</dt>
                  <dd className="mt-1">
                    <pre className="text-xs bg-gray-50 p-3 rounded-md overflow-auto max-h-96">
                      {selectedExecution.logContent}
                    </pre>
                  </dd>
                </div>
              )}
            </dl>
          </div>
        )}
      </div>
    </div>
  );
}