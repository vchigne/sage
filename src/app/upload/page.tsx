'use client';

import { useState, useEffect } from 'react';
import { Upload, Clock, History, AlertCircle, Building, Globe, Package2, Check, XCircle } from 'lucide-react';
import Link from 'next/link';
import type { PackageInfo } from '@/lib/types';

interface ValidationDetails {
  fields: string[];
  rules: string[];
  failed_rows: number[];
  invalid_values: any[];
}

interface ValidationResponse {
  status: 'success' | 'error';
  message: string;
  details: string;
  error_type?: 'validation_error' | 'other_error';
  validation_details?: Record<string, ValidationDetails>;
}

interface PackageInfo {
  id: string;
  name: string;
  organization: {
    name: string;
  };
  country: {
    name: string;
    code: string;
  };
  product: {
    name: string;
    code: string;
  };
  installation: string;
  lastUploadDate: string;
  status: 'ready' | 'processing' | 'delayed';
  lastErrors: string[];
}

export default function UploadPage() {
  const [packages, setPackages] = useState<PackageInfo[]>([]);
  const [selectedPackage, setSelectedPackage] = useState<PackageInfo | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [validationResponse, setValidationResponse] = useState<ValidationResponse | null>(null);
  const [isValidated, setIsValidated] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  useEffect(() => {
    fetchPackages();
  }, []);

  const fetchPackages = async () => {
    try {
      setError(null);
      const response = await fetch('/api/packages');
      const data = await response.json();

      if (Array.isArray(data)) {
        setPackages(data);
      } else {
        console.error('Invalid data format:', data);
        setError('Error al cargar los paquetes disponibles: formato de datos inválido');
        setPackages([]);
      }
    } catch (err) {
      console.error('Error fetching packages:', err);
      setError('Error al cargar los paquetes disponibles');
      setPackages([]);
    }
  };

  const handlePackageSelect = (pkg: PackageInfo) => {
    setSelectedPackage(pkg);
    setFile(null);
    setValidationResponse(null);
    setIsValidated(false);
  };

  const handleDrop = async (e: React.DragEvent<HTMLDivElement>, pkg: PackageInfo) => {
    e.preventDefault();
    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile) {
      setSelectedPackage(pkg);
      setFile(droppedFile);
      await handleValidateSubmit(e, droppedFile, pkg.id);
    }
  };

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>, pkg: PackageInfo) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      setSelectedPackage(pkg);
      setFile(selectedFile);
      await handleValidateSubmit(e, selectedFile, pkg.id);
    }
  };

  const handleValidateSubmit = async (
    e: React.FormEvent | React.DragEvent,
    uploadFile: File | null = file,
    packageId: string = selectedPackage?.id || ''
  ) => {
    e.preventDefault();
    if (!uploadFile || !packageId) {
      setValidationResponse({
        status: 'error',
        message: 'Error de validación',
        details: !uploadFile ? 'Por favor seleccione un archivo' : 'Por favor seleccione un paquete'
      });
      return;
    }

    setLoading(true);
    setValidationResponse(null);

    try {
      const formData = new FormData();
      formData.append('file', uploadFile);
      formData.append('packageId', packageId);

      const response = await fetch('/api/upload', {
        method: 'POST',
        body: formData,
      });

      const data: ValidationResponse = await response.json();
      setValidationResponse(data);
      setIsValidated(data.status === 'success');
    } catch (err) {
      console.error('Error validating file:', err);
      setValidationResponse({
        status: 'error',
        message: 'Error del servidor',
        details: err instanceof Error ? err.message : 'Error al validar el archivo'
      });
    } finally {
      setLoading(false);
    }
  };

  const handleLoadToDB = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/load-to-db', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ packageId: selectedPackage?.id }),
      });

      const data = await response.json();

      if (response.ok) {
        setValidationResponse({
          status: 'success',
          message: 'Carga exitosa',
          details: 'Los datos han sido cargados correctamente a la base de datos'
        });
      } else {
        throw new Error(data.error || 'Error al cargar los datos');
      }
    } catch (err) {
      setValidationResponse({
        status: 'error',
        message: 'Error de carga',
        details: err instanceof Error ? err.message : 'Error al cargar los datos a la base de datos'
      });
    } finally {
      setLoading(false);
    }
  };


  return (
    <div className="min-h-screen bg-gray-100 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto">
        <div className="text-center mb-8">
          <h2 className="text-3xl font-bold text-gray-900">
            Portal de Carga de Archivos
          </h2>
          <p className="mt-2 text-gray-600">
            Seleccione un paquete y suba su archivo ZIP para procesamiento y validación
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {packages.map((pkg) => (
            <div
              key={pkg.id}
              className={`bg-white rounded-lg shadow p-6 cursor-pointer transition-all relative ${
                selectedPackage?.id === pkg.id ? 'ring-2 ring-blue-500' : 'hover:shadow-lg'
              }`}
              onDragOver={(e) => {
                e.preventDefault();
                e.currentTarget.classList.add('ring-2', 'ring-blue-300', 'bg-blue-50');
              }}
              onDragLeave={(e) => {
                e.preventDefault();
                e.currentTarget.classList.remove('ring-2', 'ring-blue-300', 'bg-blue-50');
              }}
              onDrop={(e) => handleDrop(e, pkg)}
            >
              <h3 className="text-lg font-semibold text-gray-900 mb-2 flex justify-between items-center">
                {pkg.name}
                <label
                  htmlFor={`file-upload-${pkg.id}`}
                  className="cursor-pointer p-2 rounded-full hover:bg-gray-100"
                >
                  <Upload className="h-5 w-5 text-gray-500" />
                </label>
              </h3>
              <input
                id={`file-upload-${pkg.id}`}
                type="file"
                className="hidden"
                accept=".zip"
                onChange={(e) => handleFileChange(e, pkg)}
              />

              <div className="space-y-3 mb-4">
                <div className="flex items-center text-sm">
                  <Building className="h-4 w-4 mr-2 text-gray-400" />
                  <span>{pkg.organization.name}</span>
                </div>
                <div className="flex items-center text-sm">
                  <Globe className="h-4 w-4 mr-2 text-gray-400" />
                  <span>{pkg.country.name} ({pkg.country.code})</span>
                </div>
                <div className="flex items-center text-sm">
                  <Package2 className="h-4 w-4 mr-2 text-gray-400" />
                  <span>{pkg.product.name} ({pkg.product.code})</span>
                </div>
                <p className="text-sm text-gray-500">
                  Instalación: {pkg.installation}
                </p>
              </div>
              <div className="space-y-2">
                <div className="flex items-center text-sm">
                  <Clock className="h-4 w-4 mr-2 text-gray-400" />
                  <span>Última carga: {pkg.lastUploadDate}</span>
                </div>
                <div className="flex items-center text-sm">
                  <History className="h-4 w-4 mr-2 text-gray-400" />
                  <Link
                    href={`/history/${pkg.id}`}
                    className="text-blue-600 hover:text-blue-800"
                  >
                    Ver historial
                  </Link>
                </div>
                {pkg.status === 'delayed' && (
                  <div className="flex items-center text-sm text-yellow-600">
                    <AlertCircle className="h-4 w-4 mr-2" />
                    <span>Procesamiento demorado</span>
                  </div>
                )}
                {pkg.lastErrors.length > 0 && (
                  <div className="mt-2">
                    <p className="text-sm font-medium text-red-600">Últimos errores:</p>
                    <ul className="mt-1 text-sm text-red-500">
                      {pkg.lastErrors.map((error, index) => (
                        <li key={index} className="truncate">
                          {error}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>

        {validationResponse && (
          <div className={`mt-4 p-4 rounded-md ${
            validationResponse.status === 'success'
              ? 'bg-green-50'
              : 'bg-red-50'
          }`}>
            <div className="flex">
              <div className="flex-shrink-0">
                {validationResponse.status === 'success' ? (
                  <Check className="h-5 w-5 text-green-400" />
                ) : (
                  <XCircle className="h-5 w-5 text-red-400" />
                )}
              </div>
              <div className="ml-3">
                <h3 className={`text-sm font-medium ${
                  validationResponse.status === 'success'
                    ? 'text-green-800'
                    : 'text-red-800'
                }`}>
                  {validationResponse.message}
                </h3>

                {validationResponse.error_type === 'validation_error' && validationResponse.validation_details && (
                  <div className="mt-4 space-y-4">
                    {Object.entries(validationResponse.validation_details).map(([component, details]) => (
                      <div key={component} className="bg-white p-4 rounded-md shadow-sm">
                        <h4 className="font-medium text-gray-900">{component}</h4>
                        <div className="mt-2 space-y-2">
                          {details.fields.map((field, idx) => (
                            <div key={idx} className="flex flex-col">
                              <span className="text-sm font-medium text-gray-700">Campo: {field}</span>
                              <span className="text-sm text-gray-600">Regla: {details.rules[idx]}</span>
                              <span className="text-sm text-gray-600">
                                Filas con error: {details.failed_rows.join(', ')}
                              </span>
                              <span className="text-sm text-gray-600">
                                Valores inválidos: {details.invalid_values.join(', ')}
                              </span>
                            </div>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                )}

                {(!validationResponse.validation_details || validationResponse.error_type !== 'validation_error') && (
                  <div className="mt-2 text-sm text-gray-700 whitespace-pre-line">
                    {validationResponse.details}
                  </div>
                )}

                {validationResponse.status === 'success' && (
                  <button
                    onClick={handleLoadToDB}
                    disabled={loading}
                    className="mt-4 px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50"
                  >
                    {loading ? 'Cargando...' : 'Cargar a Base de Datos'}
                  </button>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}