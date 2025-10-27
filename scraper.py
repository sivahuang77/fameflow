import sqlite3
import time
import json
import random
import sys
from pathlib import Path
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright, BrowserContext
from core_logic import analyze_post_content
from typing import Optional, Dict, Any

# --- Constants ---
DB_PATH = Path('influencers.db')
SELECTORS_PATH = Path('site_selectors.json')
DEFAULT_COOKIE_PATH = Path('instagram_cookies.json') # Default cookie file

# --- Database Functions ---

def get_social_account_info(social_id: int) -> Optional[Dict[str, Any]]:
    """Fetches social account info (URL, platform, influencer_id) for a given social_id."""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT influencer_id, platform_name, account_url FROM social_accounts WHERE id = ?", (social_id,))
        account = cursor.fetchone()
        if account:
            return dict(account)
        return None
    finally:
        if conn:
            conn.close()

# --- Scraper Core ---

def load_selectors(platform: str) -> Dict[str, str]:
    """Loads CSS selectors for a given platform from the JSON file."""
    if not SELECTORS_PATH.exists():
        raise FileNotFoundError(f"Selector file not found at: {SELECTORS_PATH}")
    with open(SELECTORS_PATH, 'r') as f:
        all_selectors = json.load(f)
    if platform not in all_selectors:
        raise ValueError(f"Platform '{platform}' not found in selectors file.")
    return all_selectors[platform]

def scrape_posts(social_id: int, influencer_id: int, url: str, platform: str, context: BrowserContext, selectors: Dict[str, str]):
    """
    Scrapes posts from a given URL using a pre-configured browser context and selectors.
    """
    print(f"--- Starting scrape for social account {social_id} ({platform}) at {url} ---")
    page = context.new_page()
    page.goto(url, wait_until='domcontentloaded', timeout=60000)

    # More robust infinite scroll
    print("Scrolling to load all posts...")
    last_height = page.evaluate('document.body.scrollHeight')
    while True:
        page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
        time.sleep(random.uniform(2, 4)) # Wait for content to load
        new_height = page.evaluate('document.body.scrollHeight')
        if new_height == last_height:
            print("Reached the end of the page.")
            break
        last_height = new_height

    html_content = page.content()
    page.close()

    soup = BeautifulSoup(html_content, 'html.parser')
    posts = soup.select(selectors['post_container'])
    print(f"Found {len(posts)} potential posts. Processing...")

    if not posts:
        print("No posts found with the given selector. Please check selectors or if the page loaded correctly.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    posts_added = 0

    for post in posts:
        try:
            # Adapt to new, more realistic selectors
            post_text = post.select_one(selectors['post_text']).get_text(strip=True) if post.select_one(selectors['post_text']) else ""
            
            # For Instagram, the link is the timestamp's parent 'a' tag
            post_link_element = post.select_one(selectors['post_timestamp']).find_parent('a') if post.select_one(selectors['post_timestamp']) else None
            post_url = ""
            if post_link_element and post_link_element.has_attr('href'):
                 post_url = "https://www.instagram.com" + post_link_element['href']

            if not post_text and not post_url:
                print("Skipping post with no text or link.")
                continue

            image_elements = post.select(selectors['post_image'])
            image_urls = [img['src'] for img in image_elements if img.has_attr('src')]
            image_urls_json = json.dumps(image_urls)

            # --- Database Operations ---
            cursor.execute("""
                INSERT INTO posts (influencer_id, post_url, post_content, image_urls, social_account_id)
                VALUES (?, ?, ?, ?, ?)
            """, (influencer_id, post_url, post_text, image_urls_json, social_id))
            post_id = cursor.lastrowid
            posts_added += 1
            print(f"\nSuccessfully saved post snippet. (ID: {post_id})")

            # --- AI Analysis ---
            first_image_url = image_urls[0] if image_urls else None
            print("  - Sending to AI for analysis...")
            analysis_results = analyze_post_content(post_text, first_image_url)

            if analysis_results:
                cursor.execute("""
                    UPDATE posts 
                    SET image_description_ai = ?, image_text_ai = ?, ai_sentiment = ?
                    WHERE id = ?
                """, (
                    analysis_results.get("description"),
                    analysis_results.get("extracted_text"),
                    analysis_results.get("sentiment"),
                    post_id
                ))
                print(f"  - AI Analysis successful. Updated post {post_id}.")
            else:
                print("  - AI Analysis failed or returned no data.")

        except Exception as e:
            print(f"Skipping a post due to an error: {e}")

    conn.commit()
    conn.close()
    print(f"\n--- Scraper Finished. Added {posts_added} new posts to the database. ---")


# --- Main Execution ---

def main():
    """
    Main function to run the scraper from the command line.
    Usage: python scraper.py <social_account_id> <platform> [cookie_file_path]
    """
    if len(sys.argv) < 3:
        print("Usage: python scraper.py <social_account_id> <platform> [cookie_file_path]")
        print("Example: python scraper.py 1 instagram")
        sys.exit(1)

    social_id = int(sys.argv[1])
    platform = sys.argv[2].lower()
    cookie_path = Path(sys.argv[3]) if len(sys.argv) > 3 else DEFAULT_COOKIE_PATH

    # --- Preparations ---
    account_info = get_social_account_info(social_id)
    if not account_info:
        print(f"Error: No social account found with ID {social_id}")
        sys.exit(1)

    selectors = load_selectors(platform)
    url = account_info['account_url']
    influencer_id = account_info['influencer_id']

    if not cookie_path.exists():
        print("--- IMPORTANT ---")
        print(f"Cookie file not found at: {cookie_path}")
        print("To scrape a logged-in site like Instagram, you need to provide session cookies.")
        print("1. Log in to Instagram in your regular Chrome/Edge browser.")
        print("2. Install a cookie exporter extension (e.g., 'Get cookies.txt LOCALLY' or 'EditThisCookie').")
        print(f"3. Export the cookies for 'instagram.com' as a JSON file and save it as '{cookie_path}'.")
        print("-----------------")
        sys.exit(1)

    # --- Playwright Setup & Execution ---
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False) # Run in non-headless mode to observe
        context = browser.new_context(storage_state=str(cookie_path))
        
        # Clear old posts for this social account for a clean run
        print(f"Clearing old posts for social account ID {social_id} for this demo...")
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM posts WHERE social_account_id = ?", (social_id,))
        conn.commit()
        conn.close()

        scrape_posts(social_id, influencer_id, url, platform, context, selectors)
        
        context.close()
        browser.close()

if __name__ == '__main__':
    main()