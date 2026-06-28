# errors/exceptions.py

# PDF-related errors
class DocNotFoundError(Exception):
    """Raised when the PDF file cannot be found."""


class DocExtractionError(Exception):
    """Raised when PyMuPDF fails to extract content from the PDF."""

# Template-related errors
class TemplateGenerationError(Exception):
    """Raised when JSON cannot be converted into a Jinja2 template."""

class TemplateValidationError(Exception):
    """Raised when a generated template fails layout fidelity checks."""

class TemplateLoaderError(Exception):
    """Raised when a stored template cannot be loaded or parsed."""

# Storage-related errors
class StorageError(Exception):
    """Raised when saving or loading files fails."""

# Rendering-related errors
class RenderingError(Exception):
    """Raised when filling a template with content fails."""

# Page limit errors
class DOCTooManyPagesError(Exception):
    """Raised when the document has more than the allowed number of pages."""

class LLMServiceError(Exception):
    """Raised when the LLM client cannot be initialized properly."""

class LLMInvalidJSONError(Exception):
    """Raised when the LLM output cannot be parsed as valid JSON."""
