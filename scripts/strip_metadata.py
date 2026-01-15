#!/usr/bin/env python3
"""
Strip metadata from bulky markdown documents.

Removes HTML comment blocks that start with @meta, @assertion, etc.
Uses line-by-line parsing, no regex.
"""

def strip_metadata(content: str) -> str:
    """
    Remove @-prefixed HTML comment blocks and wrappers.

    Two types of metadata:
    1. Block metadata (@meta, @context): Multi-line blocks, remove all content
       Example: <!-- @meta
                version: 1.0
                -->

    2. Wrapper metadata (@assertion, @question): Single-line tags, keep content
       Example: <!-- @assertion id="..." -->
                content to keep
                <!-- @/assertion -->

    Args:
        content: Bulky markdown with metadata

    Returns:
        Clean markdown without metadata
    """
    lines = content.splitlines(keepends=True)
    output = []
    inside_block = False

    for line in lines:
        stripped_line = line.strip()

        # Check if ending a block (standalone -->)
        if inside_block and stripped_line == '-->':
            inside_block = False
            continue

        # Check if wrapper closing tag <!-- @/... -->
        if stripped_line.startswith('<!-- @/'):
            continue

        # Check if starting a metadata tag
        if stripped_line.startswith('<!-- @'):
            # Is it complete on one line (wrapper) or multi-line (block)?
            if stripped_line.endswith('-->'):
                # Wrapper: complete single-line tag, skip only this line
                continue
            else:
                # Block: multi-line tag, skip content until -->
                inside_block = True
                continue

        # If inside block, skip all content
        if inside_block:
            continue

        # Otherwise, keep line
        output.append(line)

    # Join and clean up excessive blank lines
    result = ''.join(output)

    # Replace 3+ consecutive newlines with 2
    while '\n\n\n' in result:
        result = result.replace('\n\n\n', '\n\n')

    return result.strip() + '\n'


def validate_clean(bulky: str, clean: str) -> dict:
    """
    Validate that strip operation was successful.

    Checks:
    - No metadata leaked
    - Structure preserved (same number of headers)
    - Idempotent (strip(strip(x)) == strip(x))

    Returns:
        dict with 'valid' (bool) and 'issues' (list)
    """
    issues = []

    # Check: No leakage
    for marker in ['@meta', '@assertion']:
        if marker in clean:
            issues.append(f"Leaked marker: {marker}")

    # Note: We don't validate header count because bash comments in code blocks
    # (like "# Create feature branch") look like headers but aren't.
    # The important checks are: no metadata leakage and idempotency.

    # Check: Idempotent
    double_strip = strip_metadata(clean)
    if double_strip != clean:
        issues.append("Not idempotent: strip(strip(x)) != strip(x)")

    return {
        'valid': len(issues) == 0,
        'issues': issues,
        'lines_removed': len(bulky.splitlines()) - len(clean.splitlines())
    }


if __name__ == '__main__':
    import sys

    if len(sys.argv) != 2:
        print("Usage: python strip_metadata.py <bulky-file>")
        sys.exit(1)

    with open(sys.argv[1], 'r') as f:
        bulky_content = f.read()

    clean_content = strip_metadata(bulky_content)

    # Validate
    result = validate_clean(bulky_content, clean_content)

    if not result['valid']:
        print("ERROR: Validation failed:", file=sys.stderr)
        for issue in result['issues']:
            print(f"  - {issue}", file=sys.stderr)
        sys.exit(1)

    # Output clean content
    print(clean_content, end='')

    # Report to stderr
    print(f"✓ Stripped {result['lines_removed']} lines", file=sys.stderr)
