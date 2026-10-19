import re

from django.core.exceptions import ValidationError

# XML 1.0 characters accepted by DOCX; preserve tabs and line endings.
UNSUPPORTED_TEXT = re.compile(r'[^\x09\x0A\x0D\x20-\uD7FF\uE000-\uFFFD\U00010000-\U0010FFFF]')


def validate_document_text(value):
    if UNSUPPORTED_TEXT.search(value):
        raise ValidationError('Remove unsupported control characters from this text.')
