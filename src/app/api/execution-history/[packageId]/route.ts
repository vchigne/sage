import { NextRequest, NextResponse } from 'next/server';
import { query } from '../../../../lib/db';

export async function GET(
  request: NextRequest,
  { params }: { params: { packageId: string } }
) {
  try {
    const packageId = params.packageId;
    console.log('Fetching execution history for package:', packageId);

    const result = await query(
      `
      SELECT 
        id,
        yaml_id,
        started_at,
        completed_at,
        status,
        error_message,
        log_content
      FROM execution_history 
      WHERE yaml_id = $1 
      ORDER BY started_at DESC
      LIMIT 50
      `,
      [packageId]
    );

    console.log('Query result:', result.rows);

    const executions = result.rows.map(row => ({
      id: row.id,
      yamlId: row.yaml_id,
      startedAt: row.started_at,
      completedAt: row.completed_at,
      status: row.status,
      errorMessage: row.error_message,
      logContent: row.log_content
    }));

    console.log('Formatted executions:', executions);
    return NextResponse.json(executions);
  } catch (error) {
    console.error('Error fetching execution history:', error);
    return NextResponse.json(
      { error: 'Error al cargar el historial de ejecuciones' },
      { status: 500 }
    );
  }
}