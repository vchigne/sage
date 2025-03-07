import { NextResponse } from 'next/server'
import { query } from '../../../lib/db'

export const dynamic = 'force-dynamic'

export async function GET() {
  try {
    const result = await query(`
      SELECT 
        installations.*,
        organizations.name as organization_name,
        countries.name as country_name,
        countries.code as country_code,
        products.name as product_name,
        products.code as product_code
      FROM installations
      LEFT JOIN organizations ON installations.organization_id = organizations.id
      LEFT JOIN countries ON installations.country_id = countries.id
      LEFT JOIN products ON installations.product_id = products.id
    `)
    
    // Transform the flat result into nested objects
    const installations = result.rows.map(row => ({
      id: row.id,
      organization_id: row.organization_id,
      country_id: row.country_id,
      product_id: row.product_id,
      organizations: {
        id: row.organization_id,
        name: row.organization_name
      },
      countries: {
        id: row.country_id,
        name: row.country_name,
        code: row.country_code
      },
      products: {
        id: row.product_id,
        name: row.product_name,
        code: row.product_code
      }
    }))

    return NextResponse.json(installations)
  } catch (error) {
    console.error('Database error:', error)
    return NextResponse.json(
      { error: 'Failed to fetch installations' },
      { status: 500 }
    )
  }
}
