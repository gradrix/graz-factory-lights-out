Install csvfold: pip install .
CLI: csvfold input.txt
Python API: core.run(text)
Test: python -m pytest
Input format and ordering: Expose run(text: str)->list[dict] in core.py. Parse CSV with exact header
label,quantity in that order. CSV quoting and embedded commas are supported.
Empty text, missing/wrong/extra/duplicate header fields, extra/missing row fields,
blank data rows, malformed quotes, and non-string input raise ValueError. A header
alone produces []. Each label must be a string whose stripped form is 1..40
characters; reject CR or LF anywhere in the raw label. Trim labels, preserve case
and Unicode. Quantities match ASCII [+-]?[0-9]+ exactly with no whitespace; no
float or exponent notation. Sum integer quantities per normalized label, including
negative and zero totals, with no input-order dependence. Return one dict per label
exactly {"label": label, "quantity": integer_total}, sorted by label using Python
string ordering. Support LF and CRLF row endings. Do not mutate external state.

Invalid input raises ValueError; CLI returns 2.
