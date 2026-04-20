"""Re-import truncated posts from Medium export files."""
import glob
import os
import re
from bs4 import BeautifulSoup

EXPORT_DIR = r"C:\Users\SELUSYZ\OneDrive - Alfa Laval\Desktop\Personal\Medium\medium-export\posts"
POSTS_DIR = "_posts"

# Build a mapping of local posts by their Medium link hex ID
local_posts = {}
for f in glob.glob(f"{POSTS_DIR}/*.html"):
    with open(f, "r", encoding="utf-8") as fh:
        content = fh.read()
    # Extract the link from front matter
    link_match = re.search(r'link:\s*"(.+?)"', content)
    if link_match:
        link = link_match.group(1)
        # Extract hex ID from the Medium URL
        hex_match = re.search(r'-([0-9a-f]{8,})(?:\?|$)', link)
        if hex_match:
            local_posts[hex_match.group(1)] = f

print(f"Found {len(local_posts)} local posts with Medium links")

# Check each local post size vs export
reimported = 0
for hex_id, local_file in local_posts.items():
    # Find matching export file
    export_file = None
    for ef in glob.glob(f"{EXPORT_DIR}/*.html"):
        if hex_id in ef:
            export_file = ef
            break
    
    if not export_file:
        continue
    
    local_size = os.path.getsize(local_file)
    export_size = os.path.getsize(export_file)
    
    # If local is less than 40% of export, it's likely truncated
    if local_size < export_size * 0.4:
        print(f"\n  TRUNCATED: {os.path.basename(local_file)}")
        print(f"    Local: {local_size} bytes, Export: {export_size} bytes ({local_size/export_size*100:.0f}%)")
        
        # Read the front matter from local
        with open(local_file, "r", encoding="utf-8") as fh:
            content = fh.read()
        parts = content.split("---", 2)
        if len(parts) < 3:
            continue
        front_matter = parts[1]
        
        # Read the export file and extract body
        with open(export_file, "r", encoding="utf-8") as fh:
            export_soup = BeautifulSoup(fh.read(), "html.parser")
        
        # Get all article sections (exclude footer)
        body_parts = []
        for section in export_soup.find_all("section"):
            name = section.get("name", "")
            section_classes = section.get("class", [])
            # Include body sections, skip pure footer
            if "section--body" in section_classes or not section_classes:
                body_parts.append(str(section))
        
        if not body_parts:
            # Fallback: get everything in <body>
            body_tag = export_soup.find("body")
            if body_tag:
                body_parts = [str(body_tag)]
        
        new_body = "\n".join(body_parts)
        
        # Clean: fix <br/> to newlines in pre, strip hljs spans
        body_soup = BeautifulSoup(new_body, "html.parser")
        
        for pre in body_soup.find_all("pre"):
            for br in pre.find_all("br"):
                br.replace_with("\n")
            for span in pre.find_all("span"):
                span.unwrap()
        
        # Remove duplicate title h3
        title_match = re.search(r'title:\s*"(.+?)"', front_matter)
        if title_match:
            import unicodedata
            def normalize(s):
                return re.sub(r'\s+', ' ', unicodedata.normalize('NFKC', s)).strip()
            title = title_match.group(1).strip()
            first_h3 = body_soup.find("h3")
            if first_h3 and normalize(first_h3.get_text()) == normalize(title):
                first_h3.decompose()
        
        # Remove Medium community footer
        for h3 in body_soup.find_all("h3"):
            if "Level Up Coding" in h3.get_text():
                parent = h3.find_parent("section")
                if parent:
                    parent.decompose()
        
        # Remove tracking pixels
        for img in body_soup.find_all("img"):
            src = img.get("src", "")
            if "medium.com/_/stat" in src:
                img.decompose()
            h = img.get("height", "")
            if h == "1":
                img.decompose()
        
        new_body = str(body_soup)
        
        with open(local_file, "w", encoding="utf-8") as fh:
            fh.write("---" + front_matter + "---\n" + new_body + "\n")
        
        new_size = os.path.getsize(local_file)
        print(f"    Re-imported: {new_size} bytes")
        reimported += 1

print(f"\nRe-imported {reimported} truncated posts")
