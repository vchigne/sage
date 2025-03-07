import { NextResponse } from 'next/server'
import { query } from '../../../../lib/db'

export const dynamic = 'force-dynamic'

export async function DELETE(
  _request: Request,
  { params }: { params: { id: string } }
) {
  try {
    const result = await query(
      'DELETE FROM yaml_files WHERE id = $1 AND type = $2 RETURNING id',
      [params.id, 'catalogs']
    )

    if (result.rowCount === 0) {
      return new NextResponse(
        JSON.stringify({ error: 'Archivo no encontrado' }),
        {
          status: 404,
          headers: {
            'Content-Type': 'application/json',
            'Cache-Control': 'no-store'
          }
        }
      )
    }

    return new NextResponse(
      JSON.stringify({ message: 'Archivo eliminado correctamente' }),
      {
        status: 200,
        headers: {
          'Content-Type': 'application/json',
          'Cache-Control': 'no-store'
        }
      }
    )
  } catch (error) {
    console.error('Error al eliminar archivo:', error)
    return new NextResponse(
      JSON.stringify({ error: 'Error al eliminar el archivo' }),
      {
        status: 500,
        headers: {
          'Content-Type': 'application/json',
          'Cache-Control': 'no-store'
        }
      }
    )
  }
}