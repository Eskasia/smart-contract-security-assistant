from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .schema import REPORT_SCHEMA


@dataclass
class ValidationResult:
    valid: bool
    errors: list[str]


def validate_report(report: dict[str, Any]) -> ValidationResult:
    try:
        import jsonschema
    except ImportError:
        missing = [key for key in REPORT_SCHEMA["required"] if key not in report]
        return ValidationResult(
            valid=not missing, errors=[f"Missing required key: {key}" for key in missing]
        )

    validator = jsonschema.Draft202012Validator(REPORT_SCHEMA)
    errors = sorted(validator.iter_errors(report), key=lambda error: list(error.path))
    return ValidationResult(valid=not errors, errors=[error.message for error in errors])
