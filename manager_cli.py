import sqlite3
import argparse
import json

DB_PATH = 'influencers.db'

def connect_db():
    """Establishes a connection to the SQLite database."""
    return sqlite3.connect(DB_PATH)

def add_influencer():
    """Interactively prompts to add a new influencer and their social accounts."""
    print("--- Add New Influencer ---")
    real_name = input("Real Name: ")
    email = input("Contact Email: ")
    phone = input("Contact Phone: ")
    compensation_preference = input("Compensation Preference: ")
    personal_preference = input("Personal Preference: ")
    notes = input("Notes: ")

    conn = connect_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO influencers (real_name, email, phone, compensation_preference, personal_preference, notes)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (real_name, email, phone, compensation_preference, personal_preference, notes))
        
        influencer_id = cursor.lastrowid
        print(f"\nSuccessfully added '{real_name}' with ID: {influencer_id}")

        while True:
            add_social = input("\nAdd a social media account? (y/n): ").lower()
            if add_social != 'y':
                break
            
            platform = input("  Platform Name (e.g., Instagram): ")
            account_id = input("  Account ID/Handle (e.g., @nasa): ")
            display_name = input("  Display Name: ")
            url = input("  Full URL to profile: ")

            cursor.execute("""
                INSERT INTO social_accounts (influencer_id, platform_name, account_id, display_name, url)
                VALUES (?, ?, ?, ?, ?)
            """, (influencer_id, platform, account_id, display_name, url))
            print(f"  - Added {platform} account.")

        conn.commit()
        print("\nInfluencer and social accounts saved successfully!")

    except sqlite3.Error as e:
        print(f"\nDatabase Error: {e}")
        conn.rollback()
    finally:
        conn.close()

def view_influencer(name):
    """Displays detailed information for an influencer, including all social accounts."""
    conn = connect_db()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM influencers WHERE real_name LIKE ?", ('%' + name + '%',))
    influencer = cursor.fetchone()
    
    if influencer:
        influencer_id = influencer['id']
        print(f"--- Details for {influencer['real_name']} (ID: {influencer_id}) ---")
        for key, value in dict(influencer).items():
            print(f"{key.replace('_', ' ').title()}: {value or '(Not set)'}")
        
        print("\nSocial Media Accounts:")
        cursor.execute("SELECT * FROM social_accounts WHERE influencer_id = ?", (influencer_id,))
        social_accounts = cursor.fetchall()
        
        if social_accounts:
            for account in social_accounts:
                print(f"  - Platform: {account['platform_name']}")
                print(f"    Display Name: {account['display_name']}")
                print(f"    Account ID: {account['account_id']}")
                print(f"    URL: {account['url']}")
        else:
            print("  (No social media accounts linked)")

        print("--- End of Details ---")
    else:
        print(f"Could not find an influencer with the name '{name}'.")
        
    conn.close()

def list_influencers():
    """Lists the names and IDs of all influencers in the database."""
    conn = connect_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, real_name, email FROM influencers ORDER BY real_name")
    all_influencers = cursor.fetchall()
    
    if all_influencers:
        print("--- All Influencers ---")
        print(f"{'ID':<5}{'Real Name':<20}{'Email':<30}")
        print("-" * 55)
        for inf in all_influencers:
            print(f"{inf[0]:<5}{inf[1]:<20}{inf[2] or '(Not set)':<30}")
    else:
        print("The database is currently empty. Use the 'add' command to add an influencer.")
        
    conn.close()

def show_posts(influencer_id):
    """Displays all scraped posts for a given influencer ID, including AI analysis."""
    conn = connect_db()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT real_name FROM influencers WHERE id = ?", (influencer_id,))
    influencer_name = cursor.fetchone()

    if not influencer_name:
        print(f"Error: Influencer with ID {influencer_id} not found.")
        conn.close()
        return

    print(f"--- Showing Scraped Posts for: {influencer_name['real_name']} (ID: {influencer_id}) ---")

    cursor.execute("""
        SELECT post_url, post_content, image_urls, scraped_at, image_description_ai, image_text_ai, ai_sentiment
        FROM posts 
        WHERE influencer_id = ? 
        ORDER BY scraped_at DESC
    """, (influencer_id,))
    
    posts = cursor.fetchall()

    if not posts:
        print("No posts found for this influencer yet.")
    else:
        for i, post in enumerate(posts):
            print(f"\n--- Post {i+1} (Scraped at: {post['scraped_at']}) ---")
            print(f"  Content: {post['post_content']}")
            print(f"  URL: {post['post_url']}")
            try:
                image_urls = json.loads(post['image_urls'])
                if image_urls:
                    print("  Images:")
                    for img_url in image_urls:
                        print(f"    - {img_url}")
            except (json.JSONDecodeError, TypeError):
                print(f"  (Could not parse image URLs: {post['image_urls']})")

            # Display AI Analysis
            if post['ai_sentiment']:
                print(f"  AI Sentiment: {post['ai_sentiment']}")
            if post['image_description_ai']:
                print("  AI Description: " + post['image_description_ai'])
            if post['image_text_ai']:
                formatted_text = "\n".join(["    " + line for line in post['image_text_ai'].split('\n')])
                print(f"  AI Extracted Text:\n{formatted_text}")


    print("\n--- End of Posts ---")
    conn.close()

def main():
    parser = argparse.ArgumentParser(description="Manager CLI for the Influencer Database.")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    subparsers.add_parser('add', help='Add a new influencer to the database.')
    
    parser_view = subparsers.add_parser('view', help='View details of a specific influencer.')
    parser_view.add_argument('name', type=str, help="The real name of the influencer to view.")

    subparsers.add_parser('list', help='List all influencers in the database.')

    parser_recommend = subparsers.add_parser('recommend', help='Get AI recommendations for a business case.')
    parser_recommend.add_argument('description', type=str, help="A description of the business case for AI analysis.")

    parser_show = subparsers.add_parser('show_posts', help='Show all scraped posts for a specific influencer.')
    parser_show.add_argument('influencer_id', type=int, help="The ID of the influencer whose posts you want to see.")

    args = parser.parse_args()

    if args.command == 'add':
        add_influencer()
    elif args.command == 'view':
        view_influencer(args.name)
    elif args.command == 'list':
        list_influencers()
    elif args.command == 'recommend':
        import core_logic
        recommendation = core_logic.get_business_case_recommendation(args.description)
        print("\n--- AI Business Case Recommendation ---")
        print(recommendation)
        print("\n--- End of Recommendation ---")
    elif args.command == 'show_posts':
        show_posts(args.influencer_id)
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
