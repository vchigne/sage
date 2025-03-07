import { NextResponse } from 'next/server'
import { query } from '../../../lib/db'

export const dynamic = 'force-dynamic'

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url)
  const installationId = searchParams.get('installation_id')

  try {
    let queryStr = `
      SELECT yaml_files.*, installations.organization_id,
             organizations.name as organization_name,
             countries.name as country_name,
             countries.code as country_code,
             products.name as product_name,
             products.code as product_code
      FROM yaml_files
      LEFT JOIN installations ON yaml_files.installation_id = installations.id
      LEFT JOIN organizations ON installations.organization_id = organizations.id
      LEFT JOIN countries ON installations.country_id = countries.id
      LEFT JOIN products ON installations.product_id = products.id
      WHERE yaml_files.type = 'senders'
      ORDER BY yaml_files.uploaded_at DESC
    `
    const params: any[] = []

    if (installationId) {
      queryStr += ' AND yaml_files.installation_id = $1'
      params.push(installationId)
    }

    const result = await query(queryStr, params)
    return NextResponse.json(result.rows)
  } catch (error) {
    console.error('Database error:', error)
    return NextResponse.json(
      { error: 'Failed to fetch sender YAMLs' },
      { status: 500 }
    )
  }
}

export async function POST(request: Request) {
  try {
    const formData = await request.formData()
    const name = formData.get('name') as string
    const content = formData.get('content') as string
    const installationId = formData.get('installation_id') as string
    const validationStatus = formData.get('validation_status') as string
    const uploadedBy = 'system' // TODO: Implement user authentication

    const result = await query(
      `INSERT INTO yaml_files (name, content, type, installation_id, validation_status, uploaded_by)
       VALUES ($1, $2, 'senders', $3, $4, $5)
       RETURNING *`,
      [name, content, installationId, validationStatus, uploadedBy]
    )

    return NextResponse.json(result.rows[0])
  } catch (error) {
    console.error('Database error:', error)
    return NextResponse.json(
      { error: 'Failed to create sender YAML' },
      { status: 500 }
    )
  }
}
