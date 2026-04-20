"""Fix <pre> blocks in export-imported posts:
1. Convert <br/> to newlines
2. Strip Medium hljs-* spans (keep text)
3. Remove Medium 'Level Up Coding' community footer
4. Remove duplicate content sections
"""
import glob
import re
from bs4 import BeautifulSoup

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
    body = parts[2]
    if not body.strip():
        continue

    original_body = body

    soup = BeautifulSoup(body, "html.parser")
    changed = False

    # 1. Fix <pre> blocks: convert <br/> to \n and strip spans
    for pre in soup.find_all("pre"):
        original_pre = str(pre)
        # Convert <br/> to newlines
        for br in pre.find_all("br"):
            br.replace_with("\n")
        # Unwrap all spans (keep text content)
        for span in pre.find_all("span"):
            span.unwrap()
        if str(pre) != original_pre:
            changed = True

    # 2. Remove "Level Up Coding" community sections
    for h3 in soup.find_all("h3"):
        if "Level Up Coding" in h3.get_text():
            # Remove everything from this h3 to the end of its section
            parent = h3.find_parent("section") or h3.find_parent("div", class_="section-content")
            if parent:
                parent.decompose()
                changed = True
            else:
                h3.decompose()
                changed = True

    # 3. Remove "Thanks for being a part of our community" paragraphs
    for p in soup.find_all("p"):
        text = p.get_text()
        if "Thanks for being a part of our community" in text:
            parent = p.find_parent("section") or p.find_parent("div", class_="section-content")
            if parent:
                parent.decompose()
                changed = True

    # 4. Remove "Join the Level Up talent collective" text
    for p in soup.find_all("p"):
        text = p.get_text()
        if "Join the Level Up talent collective" in text:
            p.decompose()
            changed = True

    # 5. Remove clap/follow/newsletter list items
    for li in soup.find_all("li"):
        text = li.get_text()
        if any(x in text for x in ["Clap for the story", "View more content in the Level Up", "Free coding interview course", "Follow us:"]):
            ul = li.find_parent("ul")
            if ul:
                ul.decompose()
                changed = True

    if changed:
        new_body = str(soup)
        with open(f, "w", encoding="utf-8") as fh:
            fh.write("---" + parts[1] + "---\n" + new_body + "\n")
        fixed += 1
        print(f"  [FIXED] {f}")

print(f"\nFixed {fixed} posts")
