"""Utility functions and classes for validation."""
from typing import Any, Optional, NamedTuple, Dict
import pandas as pd

class ValidationResult(NamedTuple):
    """Result of a validation rule."""
    success: bool
    severity: str  # ERROR, WARNING, INFO
    message: str
    field: str
    value: Any = None
    line_number: Optional[int] = None
    validation_rule: Optional[str] = None
    error_context: Optional[Dict[str, Any]] = None

    def to_dict(self) -> dict:
        """Convert ValidationResult to dictionary format for notifications."""
        result = {
            'severity': self.severity,
            'message': self.message,
            'field': self.field
        }
        if self.value is not None:
            result['value'] = str(self.value) if not pd.isna(self.value) else 'NULL'
        if self.line_number is not None:
            result['line'] = self.line_number
        if self.validation_rule is not None:
            result['validation_rule'] = self.validation_rule
        if self.error_context:
            result['context'] = {
                field: str(value) if not pd.isna(value) else 'NULL'
                for field, value in self.error_context.items()
            }
        return result

def format_validation_message(result: ValidationResult) -> str:
    """Format validation result message with details."""
    message_parts = []

    # Add severity header with icon and type
    if result.severity == 'ERROR':
        message_parts.append("❌ ERROR - Corrección requerida")
    elif result.severity == 'WARNING':
        message_parts.append("⚠️ ADVERTENCIA - Revisar sugerido")
    else:
        message_parts.append("ℹ️ INFORMACIÓN")

    # Add the main message with indentation
    message_parts.append(f"    {result.message}")

    # Add field name if available and not catalog validation
    if result.field and result.field not in ['catalog_validation', 'row_validation']:
        message_parts.append(f"📋 Campo: {result.field}")

    # Add line number if available
    if result.line_number:
        message_parts.append(f"📍 Línea: {result.line_number}")

    # Add value if available and not null
    if result.value is not None:
        if pd.isna(result.value):
            message_parts.append("📝 Valor: NULL")
        else:
            message_parts.append(f"📝 Valor: {result.value}")

    # Add error context if available
    if result.error_context:
        context_parts = []
        for field, value in result.error_context.items():
            # Format pattern information specially
            if field == 'pattern':
                context_parts.append(f"🔍 Formato esperado: {value}")
            # Format validation rule specially
            elif field == 'validation':
                context_parts.append(f"🔍 Regla completa: {value}")
            # Format error message specially
            elif field == 'error':
                context_parts.append(f"❗ Error específico: {value}")
            # Format date validation errors specially
            elif field == 'fecha_creacion' or field == 'fecha_venta':
                context_parts.append(f"📅 Fecha: {value}")
                context_parts.append("💡 Formato correcto: AAAA-MM-DD")
                if 'future' in str(result.validation_rule).lower():
                    context_parts.append("💡 La fecha no puede ser futura")
            # Format numeric validations specially
            elif any(num in field.lower() for num in ['precio', 'total', 'cantidad', 'stock']):
                context_parts.append(f"💰 {field.title()}: {value}")
                if field == 'total' and 'coincide' in result.message:
                    context_parts.append("💡 El total debe ser igual a cantidad × precio unitario")
                elif 'descuento' in result.message.lower():
                    context_parts.append("💡 El descuento no puede exceder el total de la venta")
            # Format other fields with appropriate icons
            elif 'codigo' in field.lower():
                context_parts.append(f"🔑 {field.title()}: {value}")
            elif 'nombre' in field.lower() or 'descripcion' in field.lower():
                context_parts.append(f"📄 {field.title()}: {value}")
            elif 'estado' in field.lower():
                context_parts.append(f"🔄 {field.title()}: {value}")
                if 'Activo' in str(result.validation_rule):
                    context_parts.append("💡 Estados válidos: Activo, Descontinuado, Proximamente")
            elif 'categoria' in field.lower():
                context_parts.append(f"📁 {field.title()}: {value}")
                if 'Alimentos' in str(result.validation_rule):
                    context_parts.append("💡 Categorías válidas: Alimentos, Bebidas, Limpieza, Cuidado Personal")
            else:
                context_parts.append(f"📌 {field.title()}: {value}")

        if context_parts:
            message_parts.append("📋 Contexto:\n    " + "\n    ".join(context_parts))

    # Add validation rule if available (only if no context already shows it)
    if result.validation_rule and not any('Regla completa' in p for p in message_parts):
        # Format the rule to be more readable
        rule = result.validation_rule
        if '|' in rule or '&' in rule:
            # Replace boolean operators with more readable text
            rule = rule.replace('|', '\n    O ')
            rule = rule.replace('&', '\n    Y ')

        # Add special formatting for common validation patterns
        if 'isin' in rule:
            rule = rule.replace('isin', 'debe estar en')
            rule = rule.replace('[', 'la lista: [')
        elif 'notna' in rule:
            rule = "no puede estar vacío"
        elif 'str.match' in rule:
            # Format regex patterns to be more readable
            pattern = rule.split("r'")[1].split("'")[0]
            rule = f"debe cumplir el formato: {pattern}"
            if '^[A-Za-z0-9 ]{3,50}$' in pattern:
                rule = "solo puede contener letras, números y espacios (entre 3 y 50 caracteres)"
            elif '^[A-Z0-9]+$' in pattern:
                rule = "solo puede contener letras mayúsculas y números"
            elif '^PROD[0-9]{4}$' in pattern:  
                rule = "debe tener el formato PRODXXXX (donde X son números)"
            elif '^VTA[0-9]{6}$' in pattern:
                rule = "debe tener el formato VTAXXXXXX (donde X son números)"
        elif '>' in rule or '<' in rule or '>=' in rule or '<=' in rule:
            # Make numeric comparisons more readable
            rule = rule.replace('>', 'mayor que')
            rule = rule.replace('<', 'menor que')
            rule = rule.replace('=', ' o igual a')
            # Add hints for common numeric validations
            if 'precio' in rule.lower():
                rule += "\n    💡 El precio debe ser un valor positivo y razonable"
            elif 'cantidad' in rule.lower() or 'stock' in rule.lower():
                rule += "\n    💡 La cantidad debe ser un número positivo"
            elif 'descuento' in rule.lower():
                if '0.50' in rule:
                    rule += "\n    💡 Descuentos mayores al 50% solo permitidos en pedidos grandes"
                else:
                    rule += "\n    💡 El descuento debe estar entre 0 y el total de la venta"
        elif '.duplicated' in rule:
            rule = "debe ser único (no se permiten duplicados)"
            rule += "\n    💡 Verifique que no haya códigos repetidos"

        message_parts.append(f"🔍 Regla de validación:\n    {rule}")

    # Join all parts with newlines for better readability
    return "\n".join(message_parts)