"""Remove duplicate leading <h3> title from imported Medium posts."""
import glob
import re
from bs4 import BeautifulSoup

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

    # Get the title from front matter
    title_match = re.search(r'^title:\s*"(.+?)"', front, re.MULTILINE)
    if not title_match:
        continue
    title = title_match.group(1).strip()

    soup = BeautifulSoup(body, "html.parser")
    changed = False

    # Find the first <h3> — if its text matches the title, remove it
    first_h3 = soup.find("h3")
    if first_h3:
        h3_text = first_h3.get_text().strip()
        if h3_text == title:
            first_h3.decompose()
            changed = True
            print(f"  [H3 REMOVED] {f}")

    if changed:
        new_body = str(soup)
        with open(f, "w", encoding="utf-8") as fh:
            fh.write(front + new_body + "\n")
        fixed += 1

print(f"\nFixed {fixed} posts")
