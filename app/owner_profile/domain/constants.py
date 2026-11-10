import re

# [0-9], not \d: \d also matches non-ASCII digits (e.g. Arabic-Indic), which are not
# valid in a RUC or a DNI.
RUC_PATTERN = re.compile(r'^(10|15|20)[0-9]{9}$')
DNI_PATTERN = re.compile(r'^[0-9]{8}$')
DOCUMENT_NUMBER_PATTERN = re.compile(r'^[A-Za-z0-9]{1,15}$')
# Each part and the street need one character that is not a space, so a part made only
# of spaces counts as empty. Leading spaces and the first visible character are matched
# by disjoint classes, so no two quantifiers compete for the same text.
_LOCATION_PART = r'\s*[^-:\s][^-:]*'
_STREET = r'[^\S\n]*\S[^\n]*'
ADDRESS_PATTERN = re.compile(
    rf'^{_LOCATION_PART}-{_LOCATION_PART}-{_LOCATION_PART}:{_STREET}$'
)
MAX_ADDRESS_LENGTH = 400
