"""Remove duplicate content sections in export-imported posts.
Some posts have the article content duplicated (appears twice).
"""
import glob
import re

POSTS_DIR = "_posts"
files = glob.glob(f"{POSTS_DIR}/*.html")
fixed = 0

for f in files:
    with open(f, "r", encoding="utf-8") as fh:
        content = fh.read()

    parts = content.split("---", 2)
    if len(parts) < 3:
        continue
    front = parts[1]
    body = parts[2].strip()
    if not body:
        continue

    # Check for duplicate section-content divs
    # The export format wraps in <div class="section-content"><div class="section-inner sectionLayout--insetColumn">
    # If the same section appears twice, remove the second one
    marker = '<div class="section-content"><div class="section-inner sectionLayout--insetColumn">'
    occurrences = body.count(marker)

    if occurrences >= 2:
        # Find second occurrence and everything after first content block
        # Keep only the first section-content block
        idx1 = body.find(marker)
        idx2 = body.find(marker, idx1 + len(marker))
        if idx2 > 0:
            # Trim everything from second occurrence onwards
            trimmed = body[:idx2].strip()
            with open(f, "w", encoding="utf-8") as fh:
                fh.write("---" + parts[1] + "---\n" + trimmed + "\n")
            fixed += 1
            print(f"  [DEDUP] {f} (had {occurrences} sections, kept first)")

print(f"\nDe-duplicated {fixed} posts")
