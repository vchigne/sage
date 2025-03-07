import { NextResponse } from 'next/server'
import { query } from '../../../lib/db'

export const dynamic = 'force-dynamic'

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url)
  const installationId = searchParams.get('installation_id')

  try {
    let queryStr = `
      SELECT 
        yaml_files.*,
        organizations.name as organization_name,
        countries.name as country_name,
        countries.code as country_code,
        products.name as product_name,
        products.code as product_code,
        installations.upload_method,
        installations.uploader_email
      FROM yaml_files
      LEFT JOIN installations ON yaml_files.installation_id = installations.id
      LEFT JOIN organizations ON installations.organization_id = organizations.id
      LEFT JOIN countries ON installations.country_id = countries.id
      LEFT JOIN products ON installations.product_id = products.id
      WHERE yaml_files.type = 'catalogs'
    `
    const params: any[] = []

    if (installationId) {
      queryStr += ' AND yaml_files.installation_id = $1'
      params.push(installationId)
    }

    queryStr += ' ORDER BY yaml_files.uploaded_at DESC'

    const result = await query(queryStr, params)
    return NextResponse.json(result.rows)
  } catch (error) {
    console.error('Database error:', error)
    return NextResponse.json(
      { error: 'Failed to fetch catalog YAMLs' },
      { status: 500 }
    )
  }
}

export async function POST(request: Request) {
  try {
    const formData = await request.formData()
    const file = formData.get('file') as File
    const installationId = formData.get('installation_id') as string
    const validationStatus = formData.get('validation_status') as string

    if (!file || !installationId) {
      return NextResponse.json(
        { error: 'Missing required fields' },
        { status: 400 }
      )
    }

    // Get the file content as an ArrayBuffer and convert to Buffer
    const fileBuffer = await file.arrayBuffer()
    const content = Buffer.from(fileBuffer)

    // Primero obtener la información de la instalación
    const installationResult = await query(
      `SELECT organization_id, product_id FROM installations WHERE id = $1`,
      [installationId]
    )

    if (installationResult.rows.length === 0) {
      return NextResponse.json(
        { error: 'Installation not found' },
        { status: 404 }
      )
    }

    const { organization_id, product_id } = installationResult.rows[0]

    // Insertar el nuevo archivo
    const result = await query(
      `INSERT INTO yaml_files (
        name, content, type, installation_id, organization_id, product_id,
        validation_status, uploaded_by
      ) VALUES ($1, $2, 'catalogs', $3, $4, $5, $6, $7)
      RETURNING id`,
      [file.name, content, installationId, organization_id, product_id, validationStatus, 'system']
    )

    // Obtener los datos completos del archivo recién creado
    const newFileResult = await query(`
      SELECT 
        yaml_files.*,
        organizations.name as organization_name,
        countries.name as country_name,
        countries.code as country_code,
        products.name as product_name,
        products.code as product_code,
        installations.upload_method,
        installations.uploader_email
      FROM yaml_files
      LEFT JOIN installations ON yaml_files.installation_id = installations.id
      LEFT JOIN organizations ON installations.organization_id = organizations.id
      LEFT JOIN countries ON installations.country_id = countries.id
      LEFT JOIN products ON installations.product_id = products.id
      WHERE yaml_files.id = $1
    `, [result.rows[0].id])

    return NextResponse.json(newFileResult.rows[0])
  } catch (error) {
    console.error('Database error:', error)
    return NextResponse.json(
      { error: 'Failed to create catalog file' },
      { status: 500 }
    )
  }
}