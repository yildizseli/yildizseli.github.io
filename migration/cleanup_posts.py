"""Clean up imported Medium content in Jekyll posts."""
import glob
import re

POSTS_DIR = "_posts"

files = glob.glob(f"{POSTS_DIR}/*.html")
fixed = 0

for f in files:
    with open(f, "r", encoding="utf-8") as fh:
        content = fh.read()

    # Split front matter and body
    match = re.match(r"^(---\s*\n.*?\n---\s*\n)(.*)", content, re.DOTALL)
    if not match:
        continue
    front = match.group(1)
    body = match.group(2).strip()
    if not body:
        continue

    original_body = body

    # 1. Fix <br/> in <pre> blocks to actual newlines
    def fix_pre(m):
        code = m.group(1)
        code = re.sub(r"<br\s*/?>", "\n", code)
        return "<pre>" + code + "</pre>"

    body = re.sub(r"<pre>(.*?)</pre>", fix_pre, body, flags=re.DOTALL)

    # 2. Remove Medium tracking pixels (1x1 images)
    body = re.sub(r'<img[^>]*medium\.com/_/stat[^>]*/?\s*>', "", body)

    # 3. Remove Medium footer ("was originally published in...")
    body = re.sub(
        r"<hr\s*/?>\s*<p>.*?was originally published in.*?</p>\s*$",
        "",
        body,
        flags=re.DOTALL,
    )

    # 4. Remove duplicate title - first <h3> matching the front matter title
    title_match = re.search(r'^title:\s*"(.+?)"', front, re.MULTILINE)
    if title_match:
        title = title_match.group(1)
        escaped = re.escape(title)
        body = re.sub(
            r"^\s*<h3>" + escaped + r"</h3>\s*", "", body, count=1
        )

    if body != original_body:
        with open(f, "w", encoding="utf-8") as fh:
            fh.write(front + body + "\n")
        fixed += 1
        print(f"  [CLEANED] {f}")

print(f"\nCleaned {fixed} posts")
