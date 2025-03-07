import { ReactNode, useState } from 'react'
import { ChevronDown, ChevronUp } from 'lucide-react'

interface MetricCardProps {
  title: string;
  value: string | number;
  icon?: ReactNode;
  trend?: {
    value: number;
    isPositive: boolean;
  };
  detail?: ReactNode;
}

export function MetricCard({ title, value, icon, trend, detail }: MetricCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <div className="bg-white rounded-lg shadow-sm">
      <div className="p-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center">
            {icon && <div className="mr-3 text-gray-500">{icon}</div>}
            <h3 className="text-sm font-medium text-gray-600">{title}</h3>
          </div>
          {trend && (
            <span className={`text-sm ${trend.isPositive ? 'text-green-600' : 'text-red-600'}`}>
              {trend.value}%
            </span>
          )}
        </div>
        <p className="mt-2 text-3xl font-bold text-gray-900">{value}</p>

        {detail && (
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="mt-4 flex items-center text-sm text-blue-600 hover:text-blue-800"
          >
            {isExpanded ? (
              <>
                <ChevronUp className="h-4 w-4 mr-1" />
                Ver menos
              </>
            ) : (
              <>
                <ChevronDown className="h-4 w-4 mr-1" />
                Ver detalles
              </>
            )}
          </button>
        )}
      </div>

      {isExpanded && detail && (
        <div className="border-t border-gray-200 p-4">
          {detail}
        </div>
      )}
    </div>
  )
}