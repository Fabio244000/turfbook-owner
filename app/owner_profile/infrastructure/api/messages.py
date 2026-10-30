SIGN_IN_REQUIRED = 'You must sign in to continue.'
INVALID_DATA = 'There were problems with the submitted data.'
UNEXPECTED_ERROR = 'An unexpected error occurred. Please try again later.'
UNEXPECTED_ERROR_LOG = 'Unexpected error while handling the request'
INVALID_JSON = 'The request body is not valid JSON.'

# Texts for request structure errors, by Pydantic error type. {field} is a label below.
FIELD_REQUIRED = '{field} is required.'
FIELD_INVALID_VALUE = '{field} has an invalid value.'
FIELD_INVALID = '{field} is invalid.'
DOCUMENT_TYPE_NOT_ALLOWED = 'Document type must be DNI, PASSPORT or CARNET_EXTRANJERIA.'

FIELD_LABELS = {
    '': 'Request body',
    'ruc': 'RUC',
    'identity_document': 'Identity document',
    'identity_document.document_type': 'Document type',
    'identity_document.document_number': 'Document number',
    'address': 'Address',
}
