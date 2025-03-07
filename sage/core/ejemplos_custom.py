"""Ejemplo de validación con regla personalizada."""
from sage.core.validation_utils import ValidationResult, format_validation_message

# Crear un ejemplo con una regla personalizada que no tiene patrón de legibilidad
validacion_custom = ValidationResult(
    success=False,
    severity='ERROR',
    message='Error en validación: formato de datos no permitido',
    field='datos_especiales',
    value='[A123, B456]',
    line_number=10,
    validation_rule='df["datos_especiales"].apply(lambda x: validar_formato_especial(x, parametros=["A", "B"]))',
    error_context={
        'datos_especiales': '[A123, B456]',
        'formatos_validos': 'A###, B### donde # son números',
        'parametros': '["A", "B"]'
    }
)

# Mostrar el mensaje formateado
print("\nEjemplo - Regla de validación personalizada:")
print(format_validation_message(validacion_custom))
