from app.owner_profile.domain.constants import MAX_ADDRESS_LENGTH

INVALID_RUC = 'RUC must have 11 digits and start with 10, 15 or 20.'
INVALID_DNI = 'DNI must have exactly 8 digits.'
INVALID_DOCUMENT_NUMBER = 'Document number must have 1 to 15 letters or digits.'
INVALID_ADDRESS = 'Address must have the format Department-Province-District:Street.'
ADDRESS_TOO_LONG = f'Address must have at most {MAX_ADDRESS_LENGTH} characters.'
