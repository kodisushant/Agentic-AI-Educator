import re

with open('docs/STATUS.md', 'rb') as f:
    content = f.read().decode('utf-8')

# Pattern to match the conflict block
conflict_pattern = re.compile(
    r'<<<<<<< HEAD\r?\n(.*?)=======\r?\n(.*?)>>>>>>> 4ced56f.*?\r?\n',
    re.DOTALL
)

def merge_conflict(m):
    head_side = m.group(1)
    our_side = m.group(2)
    # Merge: keep item 10 from HEAD (TTS integration), then add item 11 from our side (Lesson Generator)
    # HEAD side has item 10 (TTS) + "What is REAL" with TTS info
    # Our side has item 10 (Lesson Generator) + "What is REAL" with lesson info
    # We want: item 10 (TTS), item 11 (Lesson Generator), merged "What is REAL"

    # Extract item 10 from HEAD (everything before "- **What is REAL")
    head_items = re.split(r'- \*\*What is REAL', head_side, maxsplit=1)
    head_real = re.split(r'- \*\*What is REAL', our_side, maxsplit=1)

    head_item10 = head_items[0]  # "  10. **Full Codebase Sync...\n"
    head_verified = head_items[1] if len(head_items) > 1 else ''

    our_item10 = head_real[0]  # "  10. **Lesson Generator...\n"
    our_verified = head_real[1] if len(head_real) > 1 else ''

    # Renumber our item 10 → item 11
    our_item11 = re.sub(r'^\s*10\.', '  11.', our_item10, count=1)

    # Merge the "What is REAL" sections
    merged_real = '- **What is REAL & VERIFIED:**\r\n'
    # Extract bullets from head_verified
    head_bullets = re.sub(r'^\*\*What is REAL.*?:\*\*\r?\n', '', ('- **What is REAL' + head_verified).strip(), count=1, flags=re.DOTALL)
    our_bullets = re.sub(r'^\*\*What is REAL.*?:\*\*\r?\n', '', ('- **What is REAL' + our_verified).strip(), count=1, flags=re.DOTALL)

    merged = head_item10 + our_item11 + merged_real + head_bullets + '\r\n' + our_bullets + '\r\n'
    return merged

result = conflict_pattern.sub(merge_conflict, content)

if result == content:
    print("WARNING: No conflict found or pattern didn't match!")
    # Try simpler approach
    start = content.find('<<<<<<< HEAD')
    end = content.find('>>>>>>> 4ced56f')
    if start != -1 and end != -1:
        end = content.find('\n', end) + 1
        conflict_block = content[start:end]
        print("Conflict block found, length:", len(conflict_block))

        # Simple merge: take HEAD side + add our item 11 + merge real sections
        head_start = start + len('<<<<<<< HEAD\r\n')
        sep = content.find('=======\r\n', start)
        our_start = sep + len('=======\r\n')
        our_end = content.find('>>>>>>> 4ced56f', our_start)
        end_line = content.find('\n', our_end) + 1

        head_text = content[head_start:sep]
        our_text = content[our_start:our_end]

        # From HEAD: item 10 TTS + What is REAL (TTS version)
        # From ours: item 10 (Lesson Gen) → rename to 11 + What is REAL (lesson version)

        head_lines = head_text.splitlines(keepends=True)
        our_lines = our_text.splitlines(keepends=True)

        # Find split point in head: "- **What is REAL"
        head_body = []
        head_real_lines = []
        in_real = False
        for line in head_lines:
            if '- **What is REAL' in line:
                in_real = True
            if in_real:
                head_real_lines.append(line)
            else:
                head_body.append(line)

        our_body = []
        our_real_lines = []
        in_real = False
        for line in our_lines:
            if '- **What is REAL' in line:
                in_real = True
            if in_real:
                our_real_lines.append(line)
            else:
                our_body.append(line)

        # Renumber our item 10 to 11
        our_body_text = ''.join(our_body)
        our_body_text = our_body_text.replace('  10. **Lesson Generator', '  11. **Lesson Generator', 1)

        # Merge "What is REAL" - take head's label line + all bullets from both
        merged_real = head_real_lines[0]  # "- **What is REAL & VERIFIED:**\r\n"
        for line in head_real_lines[1:]:
            merged_real += line
        # Add our real bullets (skip the label line)
        for line in our_real_lines[1:]:
            merged_real += line

        replacement = ''.join(head_body) + our_body_text + merged_real
        result = content[:start] + replacement + content[end_line:]
        print("Simple merge done.")
    else:
        print("No conflict markers found at all!")
else:
    print("Regex merge succeeded.")

with open('docs/STATUS.md', 'wb') as f:
    f.write(result.encode('utf-8'))
print("Written docs/STATUS.md")
# Verify no conflict markers remain
if '<<<<<<' in result or '>>>>>>>' in result:
    print("ERROR: Conflict markers still present!")
else:
    print("OK: No conflict markers remaining.")
