"""Ejemplos de mensajes de validación."""
from sage.core.validation_utils import ValidationResult, format_validation_message

# Ejemplo 1: Regla con patrón reconocido (duplicados)
codigo_duplicado = ValidationResult(
    success=False,
    severity='ERROR',
    message='El código de producto debe ser único',
    field='codigo_producto',
    value='PROD001',
    line_number=2,
    validation_rule='~df["codigo_producto"].duplicated(keep=False)',
    error_context={'codigo_producto': 'PROD001'}
)

# Ejemplo 2: Regla con patrón reconocido (formato de fecha)
fecha_invalida = ValidationResult(
    success=False,
    severity='ERROR',
    message='Formato de fecha inválido',
    field='fecha_creacion',
    value='2025-13-32',
    line_number=3,
    validation_rule='pd.to_datetime(df["fecha_creacion"]) <= pd.Timestamp("today")',
    error_context={'fecha_creacion': '2025-13-32'}
)

# Ejemplo 3: Regla sin patrón específico (regla personalizada)
validacion_custom = ValidationResult(
    success=False,
    severity='ERROR',
    message='Error en validación personalizada',
    field='campo_custom',
    value='valor_invalido',
    line_number=5,
    validation_rule='df["campo_custom"].apply(lambda x: validar_custom(x))',
    error_context={'campo_custom': 'valor_invalido'}
)

print("\nEjemplo 1 - Regla con patrón conocido (duplicados):")
print(format_validation_message(codigo_duplicado))

print("\nEjemplo 2 - Regla con patrón conocido (fecha):")
print(format_validation_message(fecha_invalida))

print("\nEjemplo 3 - Regla sin patrón específico:")
print(format_validation_message(validacion_custom))