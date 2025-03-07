import { NextResponse } from 'next/server'
import { Pool } from 'pg'

const pool = new Pool({
  connectionString: process.env.DATABASE_URL
})

export async function GET(req: Request) {
  const { searchParams } = new URL(req.url)
  const table = searchParams.get('table')
  const orgId = searchParams.get('organizationId')

  if (!table) {
    return NextResponse.json({ error: 'Table parameter is required' }, { status: 400 })
  }

  try {
    let query = ''
    let params: any[] = []

    switch (table) {
      case 'organizations':
        query = 'SELECT * FROM organizations ORDER BY name'
        break
      case 'products':
        if (!orgId) {
          return NextResponse.json({ error: 'organizationId is required for products' }, { status: 400 })
        }
        query = 'SELECT * FROM products WHERE organization_id = $1 ORDER BY name'
        params = [orgId]
        break
      default:
        return NextResponse.json({ error: 'Invalid table parameter' }, { status: 400 })
    }

    const result = await pool.query(query, params)
    return NextResponse.json({ data: result.rows })
  } catch (error) {
    console.error('Database error:', error)
    return NextResponse.json(
      { error: 'Error accessing database' }, 
      { status: 500 }
    )
  }
}

export async function POST(req: Request) {
  try {
    const body = await req.json()
    const { name, type, content, organizationId, productId, uploadedBy } = body

    const result = await pool.query(
      `INSERT INTO yaml_files (
        name, type, content, organization_id, product_id, 
        uploaded_by, validation_status
      ) VALUES ($1, $2, $3, $4, $5, $6, $7) RETURNING *`,
      [name, type, content, organizationId, productId, uploadedBy, 'valid']
    )

    return NextResponse.json({ data: result.rows[0] })
  } catch (error) {
    console.error('Error saving file:', error)
    return NextResponse.json(
      { error: 'Error saving file to database' },
      { status: 500 }
    )
  }
}
