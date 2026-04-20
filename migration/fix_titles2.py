"""Remove duplicate leading <h3> from ALL posts - more robust version."""
import glob
import re
from bs4 import BeautifulSoup

POSTS_DIR = "_posts"
files = glob.glob(f"{POSTS_DIR}/*.html")
fixed = 0

for f in files:
    with open(f, "r", encoding="utf-8") as fh:
        content = fh.read()

    # Split on the second --- to separate front matter from body
    parts = content.split("---", 2)
    if len(parts) < 3:
        continue
    front = parts[1]  # front matter content (between the two ---)
    body = parts[2].strip()
    if not body:
        continue

    # Get title from front matter
    title_match = re.search(r'title:\s*"(.+?)"', front)
    if not title_match:
        continue
    title = title_match.group(1).strip()

    soup = BeautifulSoup(body, "html.parser")

    # Find the first <h3>
    first_h3 = soup.find("h3")
    if not first_h3:
        continue

    h3_text = first_h3.get_text().strip()

    # Normalize whitespace (Medium uses \xa0 non-breaking spaces)
    import unicodedata
    def normalize(s):
        return re.sub(r'\s+', ' ', unicodedata.normalize('NFKC', s)).strip()

    title_norm = normalize(title)
    h3_norm = normalize(h3_text)

    if h3_norm == title_norm:
        first_h3.decompose()
        new_body = str(soup)
        with open(f, "w", encoding="utf-8") as fh:
            fh.write("---" + parts[1] + "---\n" + new_body + "\n")
        fixed += 1
        print(f"    -> REMOVED")

print(f"\nFixed {fixed} posts")
