import { NextResponse } from 'next/server'
import { query } from '../../../lib/db'

export const dynamic = 'force-dynamic'

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url)
  const organizationId = searchParams.get('organizationId')

  try {
    let queryStr = `
      SELECT *
      FROM submissions
      WHERE status IN ('pending', 'late')
      ORDER BY due_date ASC
    `
    const params: any[] = []

    if (organizationId) {
      queryStr += ' AND organization_id = $1'
      params.push(organizationId)
    }

    const result = await query(queryStr, params)
    return NextResponse.json(result.rows)
  } catch (error) {
    console.error('Database error:', error)
    return NextResponse.json(
      { error: 'Failed to fetch submissions' },
      { status: 500 }
    )
  }
}
