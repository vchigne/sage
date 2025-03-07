import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  try {
    const formData = await request.formData();
    const file = formData.get('file') as File;
    const packageId = formData.get('packageId') as string;

    if (!file) {
      return NextResponse.json(
        { 
          status: 'error',
          message: 'Error de validación',
          details: 'No se proporcionó ningún archivo'
        },
        { status: 400 }
      );
    }

    // Verificar extensión del archivo
    const allowedExtensions = ['.xlsx', '.xls', '.zip'];
    const fileExtension = file.name.toLowerCase().substring(file.name.lastIndexOf('.'));
    if (!allowedExtensions.includes(fileExtension)) {
      return NextResponse.json(
        { 
          status: 'error',
          message: 'Error de validación',
          details: `El archivo debe ser Excel (.xlsx, .xls) o ZIP (.zip). Extensión recibida: ${fileExtension}`
        },
        { status: 400 }
      );
    }

    // Leer el contenido del archivo como ArrayBuffer
    const arrayBuffer = await file.arrayBuffer();
    const fileData = Buffer.from(arrayBuffer);

    // Enviar el archivo al procesador Python
    const uploadFormData = new FormData();
    const fileBlob = new Blob([fileData], { type: file.type });
    uploadFormData.append('file', fileBlob, file.name);
    uploadFormData.append('package_id', packageId);

    try {
      const processorResponse = await fetch('http://127.0.0.1:5001/process', {
        method: 'POST',
        body: uploadFormData,
      });

      if (!processorResponse.ok) {
        const result = await processorResponse.json();
        return NextResponse.json(result, { status: processorResponse.status });
      }

      const result = await processorResponse.json();
      return NextResponse.json({
        status: 'success',
        message: 'Archivo procesado correctamente',
        ...result
      });

    } catch (fetchError) {
      console.error('Error en la comunicación con el servidor Python:', fetchError);
      return NextResponse.json(
        { 
          status: 'error',
          message: 'Error de procesamiento',
          details: 'No se pudo procesar el archivo en este momento. Por favor, inténtelo nuevamente.'
        },
        { status: 503 }
      );
    }

  } catch (error) {
    console.error('Error processing upload:', error);
    return NextResponse.json(
      { 
        status: 'error',
        message: 'Error del servidor',
        details: error instanceof Error ? error.message : 'Error interno del servidor'
      },
      { status: 500 }
    );
  }
}