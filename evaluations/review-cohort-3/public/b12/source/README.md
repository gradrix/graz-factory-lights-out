# Existing JSON utility

Use `python cli.py` with one JSON object on stdin. Existing action: length. Domain functions accept the payload object; api.dispatch routes it. CLI reports ValueError/KeyError with stderr and exit 2.

## New usage

Action index with text (Unicode string without surrogate code points) and byte_offsets (list of integers). Build the UTF-8 byte boundary map for Python Unicode code-point indices (NOT grapheme clusters, normalization or display widths). Return {byte_length:integer,char_to_byte:list,byte_to_char:list}. char_to_byte has len(text)+1 cumulative UTF-8 byte offsets, starting 0 and including the end; byte_to_char maps each requested byte offset to its code-point index, preserving requests order/repetitions. If any requested offset is negative, beyond encoded byte length or inside a multi-byte code point, raise ValueError. End offset is valid and maps to len(text). Empty text has boundaries [0]. Preserve length returning Python code-point length. No normalization, case conversion or grapheme segmentation.

Example:

```sh
printf '%s\n' '{"action": "index", "text": "aé😀", "byte_offsets": [0, 3, 7]}' | python cli.py
```

Output:

```json
{"byte_length": 7, "char_to_byte": [0, 1, 3, 7], "byte_to_char": [0, 2, 3]}
```

Inputs that violate the rules above raise ValueError; the CLI then prints the message on stderr and exits with status 2. Run the regression tests with `python -m unittest discover`.
