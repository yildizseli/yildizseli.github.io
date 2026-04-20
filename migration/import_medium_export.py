"""
Import Medium exported HTML posts into Jekyll _posts/ files.
Matches by Medium article ID (hex hash at end of URL/filename).
Sets Medium as canonical source.
"""
import os
import re
import glob
from bs4 import BeautifulSoup

POSTS_DIR = "_posts"
MEDIUM_EXPORT_DIR = r"C:\Users\SELUSYZ\OneDrive - Alfa Laval\Desktop\Personal\Medium\medium-export\posts"


def extract_medium_id(text):
    """Extract the unique Medium article ID (hex hash at end of slug)."""
    text = text.split("?")[0].rstrip("/")
    slug = text.split("/")[-1]
    # Remove file extension if present
    slug = re.sub(r'\.html$', '', slug)
    match = re.search(r'-([0-9a-f]{8,})$', slug)
    if match:
        return match.group(1)
    return None


def load_existing_posts():
    """Load existing Jekyll posts and index them by Medium article ID."""
    posts = {}
    for filepath in glob.glob(os.path.join(POSTS_DIR, "*.html")):
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        match = re.match(r"^---\s*\n(.*?)\n---\s*\n?(.*)", content, re.DOTALL)
        if not match:
            continue
        front_matter = match.group(1)
        body = match.group(2).strip()
        link_match = re.search(r'^link:\s*"([^"]+)"', front_matter, re.MULTILINE)
        if link_match:
            link = link_match.group(1)
            medium_id = extract_medium_id(link)
            if medium_id:
                posts[medium_id] = {
                    "filepath": filepath,
                    "front_matter": front_matter,
                    "body": body,
                    "link": link,
                }
    return posts


def extract_content_from_export(filepath):
    """Extract article content from Medium export HTML file."""
    with open(filepath, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "html.parser")

    sections = soup.find_all("section")
    if len(sections) < 2:
        return None

    # Skip section 0 (subtitle/description), take section 1+ as content
    content_sections = sections[1:]
    content_html = ""
    for section in content_sections:
        # Get inner HTML of each section
        inner = section.decode_contents()
        content_html += inner

    # Parse combined content for cleanup
    content_soup = BeautifulSoup(content_html, "html.parser")

    # Remove Medium-specific tracking images
    for img in content_soup.find_all("img"):
        src = img.get("src", "")
        if "medium.com/_/stat" in src:
            img.decompose()

    # Remove empty divs with only whitespace
    for div in content_soup.find_all("div"):
        if not div.get_text(strip=True) and not div.find("img"):
            div.decompose()

    result = str(content_soup)
    # Clean up excessive whitespace
    result = re.sub(r"\n{3,}", "\n\n", result)
    return result.strip()


def main():
    print("Loading existing Jekyll posts...")
    existing_posts = load_existing_posts()
    print(f"Found {len(existing_posts)} posts with Medium links.\n")

    # List Medium export files (skip drafts and comments)
    export_files = []
    for f in os.listdir(MEDIUM_EXPORT_DIR):
        if not f.endswith(".html"):
            continue
        if f.startswith("draft_"):
            continue
        export_files.append(f)

    print(f"Found {len(export_files)} exported Medium HTML files.\n")

    updated = 0
    skipped_has_content = 0
    skipped_comment = 0
    no_match = 0

    for filename in sorted(export_files):
        filepath = os.path.join(MEDIUM_EXPORT_DIR, filename)
        medium_id = extract_medium_id(filename)

        if not medium_id:
            print(f"  [SKIP]     {filename} (no Medium ID found)")
            continue

        # Check if it's a comment/reply (very small files, no matching post)
        file_size = os.path.getsize(filepath)
        if file_size < 2000 and medium_id not in existing_posts:
            skipped_comment += 1
            continue

        if medium_id not in existing_posts:
            no_match += 1
            print(f"  [NO MATCH] {filename}")
            continue

        post = existing_posts[medium_id]

        # Skip if already has substantial body content
        if len(post["body"]) > 200:
            skipped_has_content += 1
            print(f"  [SKIP]     {filename} (already has content)")
            continue

        # Extract content
        content = extract_content_from_export(filepath)
        if not content:
            print(f"  [EMPTY]    {filename} (no content extracted)")
            continue

        # Write updated post - ensure layout is set to default
        front_matter = post["front_matter"]
        if "layout: null" in front_matter:
            front_matter = front_matter.replace("layout: null", "layout: default")
        elif "layout:" not in front_matter:
            front_matter = "layout: default\n" + front_matter

        new_content = f"---\n{front_matter}\n---\n\n{content}\n"
        with open(post["filepath"], "w", encoding="utf-8") as f:
            f.write(new_content)

        updated += 1
        print(f"  [UPDATED]  {filename}")

    print(f"\n--- Summary ---")
    print(f"Updated:          {updated}")
    print(f"Already content:  {skipped_has_content}")
    print(f"Comments/replies: {skipped_comment}")
    print(f"No match:         {no_match}")
    print(f"Total exports:    {len(export_files)}")


if __name__ == "__main__":
    main()
