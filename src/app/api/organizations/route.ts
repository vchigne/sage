import { NextResponse } from 'next/server'
import { query } from '../../../lib/db'

export const dynamic = 'force-dynamic'

export async function GET() {
  try {
    const result = await query('SELECT id, name FROM organizations')
    return NextResponse.json(result.rows)
  } catch (error) {
    console.error('Database error:', error)
    return NextResponse.json(
      { error: 'Failed to fetch organizations' },
      { status: 500 }
    )
  }
}