import sqlite3
import json
import datetime
from collections import defaultdict

DB_PATH = 'influencers.db'
LOG_FILE_PATH = 'conversation_log.jsonl'

def generate_raw_report():
    """Gathers data and generates a raw text report with detailed debugging prints."""
    print("--- [DEBUG] Starting Raw Report Generation ---")

    # 1. Fetch all influencers from the database
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        print("--- [DEBUG] Database connection successful ---")
        
        cursor.execute("SELECT * FROM influencers")
        influencers_raw = cursor.fetchall()
        
        if not influencers_raw:
            print("--- [DEBUG] No influencers found in the database. Exiting. ---")
            conn.close()
            return

        print(f"--- [DEBUG] Found {len(influencers_raw)} influencers in the database. ---")
        influencers = {inf['id']: dict(inf) for inf in influencers_raw}
    except sqlite3.Error as e:
        print(f"--- [DEBUG] Database error while fetching influencers: {e} ---")
        return
    finally:
        if 'conn' in locals() and conn:
            conn.close()
            print("--- [DEBUG] Database connection closed. ---")

    # 2. Read conversation logs
    conversation_logs = defaultdict(list)
    try:
        with open(LOG_FILE_PATH, 'r', encoding='utf-8') as f:
            log_lines = f.readlines()
            print(f"--- [DEBUG] Log file found. Read {len(log_lines)} lines. ---")
            for line in log_lines:
                if line.strip(): # Ensure line is not empty
                    log = json.loads(line)
                    inf_id = log.get('influencer_id')
                    if inf_id:
                        conversation_logs[inf_id].append(log)
    except FileNotFoundError:
        print("--- [DEBUG] Log file not found. Skipping conversation analysis. ---")
    except Exception as e:
        print(f"--- [DEBUG] Error reading log file: {e} ---")

    # 3. Assemble the report string
    print("--- [DEBUG] Assembling final report string... ---")
    report_parts = []
    report_parts.append(f"# 網紅彙整分析原始報告")
    report_parts.append(f"報告生成時間: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_parts.append("="*40)

    for inf_id, influencer_data in influencers.items():
        report_parts.append(f"\n## 網紅檔案：{influencer_data['name']} (ID: {inf_id})")
        report_parts.append("-"*20)
        report_parts.append(f"個性分析: {influencer_data.get('personality_analysis', 'N/A')}")
        report_parts.append(f"近期動態 (爬蟲): {influencer_data.get('recent_report', 'N/A')}")
        report_parts.append(f"商案歷史: {influencer_data.get('business_history', 'N/A')}")
        
        report_parts.append("\n### 近期對話紀錄:")
        user_logs = conversation_logs.get(inf_id)
        if user_logs:
            user_logs.sort(key=lambda x: x.get('timestamp', ''))
            for log in user_logs:
                role = log.get('role', 'unknown')
                content = log.get('content', '').replace('\n', ' ')
                timestamp = log.get('timestamp', '')
                report_parts.append(f"  - [{timestamp}] [{role}]: {content}")
        else:
            report_parts.append("  (無對話紀錄)")
        
        report_parts.append("="*40)

    final_report = "\n".join(report_parts)
    
    print("\n--- FINAL RAW REPORT ---")
    print(final_report)
    print("\n--- [DEBUG] Raw Report Generation Finished ---")
    return final_report # Return the report string

if __name__ == '__main__':
    raw_report_content = generate_raw_report()
    if raw_report_content:
        import core_logic # Import core_logic here to avoid circular dependencies if it's not already imported
        print("\n--- [DEBUG] Sending raw report to AI for summarization... ---")
        # Assuming core_logic.process_message can take a dummy identifier for this purpose
        # Or we can directly call get_ai_response if it doesn't need influencer_data strongly
        # Let's use get_ai_response directly as process_message also logs things we might not want for summarization context.
        # We also need a dummy influencer_data for get_ai_response, or modify get_ai_response to handle None for influencer_data.
        # For simplicity, let's just make a direct call to get_ai_response with a dummy influencer_data.
        dummy_influencer_data = {"id": 0, "name": "Report_Summarizer"} # Dummy data
        ai_summary = core_logic.get_ai_response(dummy_influencer_data, "請總結以下針對網紅的原始報告，提取關鍵資訊和潛在合作機會：\n" + raw_report_content)
        
        print("\n--- AI SUMMARIZED REPORT ---")
        if ai_summary:
            print(ai_summary)
        else:
            print("AI summarization failed or returned no content.")
        print("\n--- [DEBUG] AI Summarization Finished ---")