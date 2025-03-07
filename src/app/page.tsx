'use client'

import { useState } from 'react'
import { AlertTriangle, Clock, CheckCircle } from 'lucide-react'
import { MetricCard } from '../components/dashboard/MetricCard'
import { ErrorsList } from '../components/dashboard/ErrorsList'
import { SubmissionStatus } from '../components/dashboard/SubmissionStatus'
import DashboardFilters from '../components/dashboard/DashboardFilters'

export default function Home() {
  const [filters, setFilters] = useState<{
    organizationId?: string;
    countryId?: string;
    productId?: string;
  }>({})

  return (
    <>
      <h1 className="text-2xl font-bold text-gray-800 mb-4">Dashboard</h1>
      <DashboardFilters 
        onFilterChange={setFilters}
        className="mb-6"
      />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
        <MetricCard
          title="Envíos Pendientes"
          value="2"
          icon={<Clock className="h-6 w-6" />}
          trend={{ value: -10, isPositive: true }}
          detail={<SubmissionStatus {...filters} compact />}
        />
        <MetricCard
          title="Errores Detectados"
          value="5"
          icon={<AlertTriangle className="h-6 w-6" />}
          trend={{ value: 15, isPositive: false }}
          detail={<ErrorsList {...filters} compact />}
        />
        <MetricCard
          title="Tasa de Éxito"
          value="85%"
          icon={<CheckCircle className="h-6 w-6" />}
          trend={{ value: 5, isPositive: true }}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <ErrorsList {...filters} />
        <SubmissionStatus {...filters} />
      </div>
    </>
  )
}