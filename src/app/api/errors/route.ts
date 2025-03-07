import { NextResponse } from 'next/server'
import { query } from '../../../lib/db'

export const dynamic = 'force-dynamic'

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url)
  const organizationId = searchParams.get('organizationId')

  try {
    let queryStr = `
      SELECT errors.*, submissions.responsible_name, submissions.responsible_email, submissions.organization_id
      FROM errors
      LEFT JOIN submissions ON errors.submission_id = submissions.id
      ORDER BY errors.created_at DESC
    `
    const params: any[] = []

    if (organizationId) {
      queryStr += ' WHERE submissions.organization_id = $1'
      params.push(organizationId)
    }

    const result = await query(queryStr, params)
    return NextResponse.json(result.rows)
  } catch (error) {
    console.error('Database error:', error)
    return NextResponse.json(
      { error: 'Failed to fetch errors' },
      { status: 500 }
    )
  }
}
