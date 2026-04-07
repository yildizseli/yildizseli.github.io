import re
import pathlib
import urllib.request
import urllib.error

POSTS_DIR = pathlib.Path('_posts')
IMAGES_DIR = pathlib.Path('assets/images')
IMAGES_DIR.mkdir(parents=True, exist_ok=True)

EXT_PATTERN = re.compile(r'\.(jpe?g|png|webp|gif)(?:\?|$)', re.I)
IMAGE_URL_PATTERN = re.compile(r'image:\s*"([^"]+)"')

posts = sorted(POSTS_DIR.glob('*.html'))
updated = []

for post_file in posts:
    text = post_file.read_text(encoding='utf-8')
    m = IMAGE_URL_PATTERN.search(text)
    if not m:
        continue
    url = m.group(1).strip()
    if url.startswith('/assets/images/') or url.startswith('./assets/images/'):
        continue
    if EXT_PATTERN.search(url):
        continue
    slug = post_file.stem
    print(f'Processing {post_file.name}: {url}')
    # decide extension
    if 'format:webp' in url:
        ext = '.webp'
    else:
        ext = None
    if ext is None:
        try:
            req = urllib.request.Request(url, method='HEAD', headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=20) as resp:
                ctype = resp.headers.get('Content-Type', '')
                if 'image/webp' in ctype:
                    ext = '.webp'
                elif 'image/png' in ctype:
                    ext = '.png'
                elif 'image/jpeg' in ctype:
                    ext = '.jpg'
                elif 'image/gif' in ctype:
                    ext = '.gif'
                else:
                    ext = '.jpg'
        except Exception as e:
            print(f'  HEAD failed: {e}; defaulting to .jpg')
            ext = '.jpg'
    local_name = f'{slug}{ext}'
    local_path = IMAGES_DIR / local_name
    try:
        if not local_path.exists():
            print(f'  downloading to {local_path}')
            with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'}), timeout=60) as resp:
                data = resp.read()
            local_path.write_bytes(data)
        else:
            print(f'  already exists {local_path}')
        new_url = f'/assets/images/{local_name}'
        new_text = text.replace(url, new_url, 1)
        post_file.write_text(new_text, encoding='utf-8')
        updated.append((post_file.name, url, new_url))
    except urllib.error.HTTPError as e:
        print(f'  HTTP error {e.code} for {url}')
    except Exception as e:
        print(f'  error downloading {url}: {e}')

print(f'Updated {len(updated)} posts:')
for item in updated:
    print(item[0], '->', item[2])
