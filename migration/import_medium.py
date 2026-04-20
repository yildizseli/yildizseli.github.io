"""
Import Medium blog content into Jekyll posts via RSS feed.
Sets Medium as the canonical source for each post.
"""
import os
import re
import glob
import feedparser
from bs4 import BeautifulSoup

POSTS_DIR = "_posts"
RSS_URL = "https://medium.com/feed/@selimyildiz91"


def extract_medium_id(url):
    """Extract the unique Medium article ID (hex hash at end of URL)."""
    url = url.split("?")[0].rstrip("/")
    # Medium URLs end with a slug like: title-abc123def456
    # The hex ID is typically the last 12 chars after the final dash
    slug = url.split("/")[-1]
    match = re.search(r'-([0-9a-f]{8,})$', slug)
    if match:
        return match.group(1)
    return slug


def load_existing_posts():
    """Load existing posts and index them by their Medium article ID."""
    posts = {}
    for filepath in glob.glob(os.path.join(POSTS_DIR, "*.html")):
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        # Extract front matter
        match = re.match(r"^---\s*\n(.*?)\n---\s*\n?(.*)", content, re.DOTALL)
        if not match:
            continue
        front_matter = match.group(1)
        body = match.group(2).strip()
        # Extract link
        link_match = re.search(r'^link:\s*"([^"]+)"', front_matter, re.MULTILINE)
        if link_match:
            link = link_match.group(1)
            medium_id = extract_medium_id(link)
            posts[medium_id] = {
                "filepath": filepath,
                "front_matter": front_matter,
                "body": body,
                "link": link,
            }
    return posts


def clean_html_content(html_content):
    """Clean Medium RSS HTML content for embedding in Jekyll."""
    soup = BeautifulSoup(html_content, "html.parser")

    # Remove Medium-specific footer (e.g., "Continue reading on Medium...")
    for footer in soup.find_all("a", string=re.compile(r"Continue reading")):
        parent = footer.parent
        if parent:
            parent.decompose()

    # Remove empty figure tags / medium specific markup
    for fig in soup.find_all("figure"):
        img = fig.find("img")
        if not img:
            fig.decompose()

    html = str(soup)

    # Clean up excessive whitespace
    html = re.sub(r"\n{3,}", "\n\n", html)
    return html.strip()


def main():
    print(f"Fetching RSS feed from {RSS_URL}...")
    feed = feedparser.parse(RSS_URL)
    print(f"Found {len(feed.entries)} entries in RSS feed.\n")

    existing_posts = load_existing_posts()
    print(f"Found {len(existing_posts)} existing posts with Medium links.\n")

    updated = 0
    skipped = 0
    not_matched = 0

    for entry in feed.entries:
        entry_id = extract_medium_id(entry.link)
        title = entry.title

        # Find matching post by Medium article ID
        matched_post = existing_posts.get(entry_id)

        if not matched_post:
            not_matched += 1
            print(f"  [NO MATCH] {title}")
            print(f"             {entry_link}")
            continue

        # Skip if already has body content
        if len(matched_post["body"]) > 100:
            skipped += 1
            print(f"  [SKIP]     {title} (already has content)")
            continue

        # Extract and clean content
        content_html = entry.get("content", [{}])[0].get("value", "")
        if not content_html:
            content_html = entry.get("summary", "")

        if not content_html:
            print(f"  [EMPTY]    {title} (no content in RSS)")
            continue

        cleaned = clean_html_content(content_html)

        # Write updated post
        new_content = f"---\n{matched_post['front_matter']}\n---\n\n{cleaned}\n"
        with open(matched_post["filepath"], "w", encoding="utf-8") as f:
            f.write(new_content)

        updated += 1
        print(f"  [UPDATED]  {title}")

    print(f"\n--- Summary ---")
    print(f"Updated:     {updated}")
    print(f"Skipped:     {skipped} (already had content)")
    print(f"No match:    {not_matched} (not in _posts/)")
    print(f"Total RSS:   {len(feed.entries)}")


if __name__ == "__main__":
    main()
