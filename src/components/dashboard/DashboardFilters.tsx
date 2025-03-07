import { useState, useEffect } from 'react'
import type { Organization, Country, Product } from '../../lib/supabase/types'

interface DashboardFiltersProps {
  onFilterChange: (filters: { organizationId?: string; countryId?: string; productId?: string }) => void;
  className?: string;
}

export default function DashboardFilters({ onFilterChange, className }: DashboardFiltersProps) {
  const [organizations, setOrganizations] = useState<Organization[]>([])
  const [countries, setCountries] = useState<Country[]>([])
  const [products, setProducts] = useState<Product[]>([])
  const [error, setError] = useState<string | null>(null)
  const [selectedOrganization, setSelectedOrganization] = useState<string>('')
  const [selectedCountry, setSelectedCountry] = useState<string>('')
  const [selectedProduct, setSelectedProduct] = useState<string>('')

  useEffect(() => {
    const loadData = async () => {
      try {
        // Cargar organizaciones
        const orgResponse = await fetch('/api/organizations')
        if (!orgResponse.ok) throw new Error('Failed to fetch organizations')
        const orgData = await orgResponse.json()
        setOrganizations(orgData)

        // Cargar países
        const countryResponse = await fetch('/api/countries')
        if (!countryResponse.ok) throw new Error('Failed to fetch countries')
        const countryData = await countryResponse.json()
        setCountries(countryData)

        // Cargar productos
        const productResponse = await fetch('/api/products')
        if (!productResponse.ok) throw new Error('Failed to fetch products')
        const productData = await productResponse.json()
        setProducts(productData)
      } catch (err) {
        console.error('Error:', err)
        setError(err instanceof Error ? err.message : 'Error loading data')
      }
    }

    loadData()
  }, [])

  useEffect(() => {
    onFilterChange({
      organizationId: selectedOrganization || undefined,
      countryId: selectedCountry || undefined,
      productId: selectedProduct || undefined
    })
  }, [selectedOrganization, selectedCountry, selectedProduct, onFilterChange])

  if (error) return <div className="text-red-600">Error: {error}</div>

  return (
    <div className={`grid grid-cols-1 md:grid-cols-3 gap-4 ${className}`}>
      <select 
        className="w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
        value={selectedOrganization}
        onChange={(e) => setSelectedOrganization(e.target.value)}
      >
        <option value="">Todas las organizaciones</option>
        {organizations.map((org) => (
          <option key={org.id} value={org.id}>
            {org.name}
          </option>
        ))}
      </select>

      <select 
        className="w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
        value={selectedCountry}
        onChange={(e) => setSelectedCountry(e.target.value)}
      >
        <option value="">Todos los países</option>
        {countries.map((country) => (
          <option key={country.id} value={country.id}>
            {country.name} ({country.code})
          </option>
        ))}
      </select>

      <select 
        className="w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
        value={selectedProduct}
        onChange={(e) => setSelectedProduct(e.target.value)}
      >
        <option value="">Todos los productos</option>
        {products.map((product) => (
          <option key={product.id} value={product.id}>
            {product.name} ({product.code})
          </option>
        ))}
      </select>
    </div>
  )
}