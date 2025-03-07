import { NextResponse } from 'next/server'
import { query } from '../../../lib/db'
import * as crypto from 'crypto'

export const dynamic = 'force-dynamic'

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url)
  const installationId = searchParams.get('installation_id')

  try {
    let queryStr = `
      WITH last_execution AS (
        SELECT 
          yaml_id,
          MAX(started_at) as last_execution_date,
          string_agg(DISTINCT error_message, '; ' ORDER BY error_message) FILTER (WHERE error_message IS NOT NULL) as recent_errors
        FROM execution_history
        GROUP BY yaml_id
      ),
      execution_status AS (
        SELECT 
          yaml_id,
          CASE 
            WHEN NOW() - started_at > INTERVAL '2 hours' AND status = 'processing' THEN 'delayed'
            WHEN status = 'processing' THEN 'processing'
            ELSE 'ready'
          END as current_status
        FROM execution_history eh
        WHERE (yaml_id, started_at) IN (
          SELECT yaml_id, MAX(started_at)
          FROM execution_history
          GROUP BY yaml_id
        )
      )
      SELECT DISTINCT
        y.id,
        y.config::json->>'name' as name,
        y.config::json->>'organization_name' as organization_name,
        y.config::json->>'country_name' as country_name,
        y.config::json->>'country_code' as country_code,
        y.config::json->>'product_name' as product_name,
        y.config::json->>'product_code' as product_code,
        y.config::json->>'installation' as installation,
        COALESCE(le.last_execution_date::text, 'Nunca') as last_upload_date,
        COALESCE(es.current_status, 'ready') as status,
        COALESCE(array_remove(string_to_array(le.recent_errors, '; '), ''), ARRAY[]::text[]) as last_errors
      FROM yaml_configs y
      LEFT JOIN last_execution le ON le.yaml_id = y.id
      LEFT JOIN execution_status es ON es.yaml_id = y.id
      WHERE y.active = true
    `
    const params: any[] = []

    if (installationId) {
      queryStr += " AND y.config::json->>'installation_id' = $1"
      params.push(installationId)
    }

    queryStr += ' ORDER BY last_upload_date DESC NULLS LAST'

    console.log('Executing query:', queryStr)
    console.log('Query params:', params)

    const result = await query(queryStr, params)
    console.log('Raw query result:', result.rows)

    // Ensure we always return an array
    const formattedResults = Array.isArray(result.rows) ? result.rows.map(row => ({
      id: row.id,
      name: row.name || 'Sin nombre',
      organization: {
        name: row.organization_name || 'Sin organización',
      },
      country: {
        name: row.country_name || 'Sin país',
        code: row.country_code
      },
      product: {
        name: row.product_name || 'Sin producto',
        code: row.product_code
      },
      installation: row.installation || 'Sin instalación',
      lastUploadDate: row.last_upload_date,
      status: row.status as 'ready' | 'processing' | 'delayed',
      lastErrors: Array.isArray(row.last_errors) ? row.last_errors : []
    })) : []

    console.log('Formatted results:', formattedResults)
    return NextResponse.json(formattedResults)
  } catch (error) {
    console.error('Database error:', error)
    return NextResponse.json([], { status: 500 })
  }
}

export async function POST(request: Request) {
  try {
    const formData = await request.formData()
    const name = formData.get('name') as string
    const content = formData.get('content') as string
    const installationId = formData.get('installation_id') as string
    const validationStatus = formData.get('validation_status') as string

    const config = {
      name,
      installation_id: installationId,
      validation_status: validationStatus,
      content
    }

    const result = await query(
      `INSERT INTO yaml_configs (id, config, active)
       VALUES ($1, $2, true)
       RETURNING *`,
      [crypto.randomUUID(), JSON.stringify(config)]
    )

    return NextResponse.json(result.rows[0])
  } catch (error) {
    console.error('Database error:', error)
    return NextResponse.json(
      { error: 'Error al crear el paquete YAML' },
      { status: 500 }
    )
  }
}