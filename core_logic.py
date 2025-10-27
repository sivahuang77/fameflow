
import sqlite3
import json
import datetime
import logging
import google.generativeai as genai
import os
from collections import defaultdict
import requests
from PIL import Image
import io

# Configure the Gemini API key from an environment variable
# It's highly recommended to set your API key as an environment variable
# For example: export GOOGLE_API_KEY='YOUR_API_KEY'
genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))

# --- Constants ---
DB_PATH = 'influencers.db'
LOG_FILE_PATH = 'conversation_log.jsonl'

# --- Logger Setup ---
logger = logging.getLogger(__name__)

# --- Core Functions ---

def log_conversation(influencer_id: int, influencer_name: str, role: str, content: str):
    """Appends a conversation entry to the JSONL log file."""
    log_entry = {
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "influencer_id": influencer_id,
        "influencer_name": influencer_name,
        "role": role, # 'user' or 'assistant'
        "content": content
    }
    try:
        with open(LOG_FILE_PATH, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
    except Exception as e:
        logger.error(f"Failed to write to log file: {e}")

def get_ai_response(influencer_data, user_message):
    """Generates a response using the Gemini LLM."""
    logger.info("AI brain is online. Generating response with Gemini LLM.")
    try:
        allowed_models = [
            'models/gemini-2.5-pro',
            'models/gemini-2.5-flash-lite',
            'models/gemini-2.0-flash'
        ]
        selected_model_name = os.environ.get("GEMINI_MODEL", "models/gemini-2.5-flash-lite")

        if selected_model_name not in allowed_models:
            logger.warning(f"Selected model '{selected_model_name}' is not in the allowed list. Defaulting to 'models/gemini-2.5-pro'.")
            selected_model_name = "models/gemini-2.5-pro"

        model = genai.GenerativeModel(selected_model_name)
        # You might want to add more context or conversation history here
        # For now, we'll just send the user's message
        response = model.generate_content(user_message)
        return response.text
    except Exception as e:
        logger.error(f"Error generating AI response with Gemini: {e}")
        return "AI 服務目前無法使用，請稍後再試。"

def get_influencer(identifier, platform: str):
    """Fetches influencer data based on a platform-specific identifier."""
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    query_column = ''
    if platform == 'telegram':
        query_column = 'telegram_id'
    elif platform == 'email':
        query_column = 'contact_info' # Assuming contact_info stores the email
    elif platform == 'line':
        query_column = 'line_id'
    else:
        return None # Unsupported platform

    query = f"SELECT * FROM influencers WHERE {query_column} = ?"
    cursor.execute(query, (identifier,))
    influencer = cursor.fetchone()
    conn.close()
    return dict(influencer) if influencer else None


def process_message(user_identifier, message_text: str, platform: str):
    """
    The main entry point for processing a message from any platform.
    """
    logger.info(f"Processing message from {platform} identifier: {user_identifier}")

    # 1. Identify the influencer
    influencer_data = get_influencer(user_identifier, platform)

    if not influencer_data:
        logger.warning(f"Could not find influencer for {platform} identifier: {user_identifier}")
        # For Telegram, we ask them to register. For others, we might just ignore.
        if platform == 'telegram' or platform == 'line':
            return "我還不認識您耶！請先用 `/register [您的名字]` 指令來綁定身份喔！"
        else:
            return None # Or some other generic response

    # 2. Log the incoming message
    log_conversation(influencer_data['id'], influencer_data['name'], 'user', message_text)

    # 3. Get a response from the AI (currently offline)
    ai_response = get_ai_response(influencer_data, message_text)

    # 4. Log the outgoing response
    if ai_response:
        log_conversation(influencer_data['id'], influencer_data['name'], 'assistant', ai_response)

    # 5. Return the response to the platform connector
    return ai_response

def get_business_case_recommendation(business_case_description: str):
    """
    Generates business case recommendations by analyzing influencer data and conversation logs.
    """
    logger.info("Generating business case recommendations with AI.")
    
    # 1. Fetch all influencers from the database
    influencers_data = []
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM influencers")
        influencers_data = [dict(row) for row in cursor.fetchall()]
    except sqlite3.Error as e:
        logger.error(f"Database error while fetching influencers for recommendation: {e}")
        return "無法獲取網紅資料進行推薦。"
    finally:
        if conn:
            conn.close()

    if not influencers_data:
        return "目前沒有網紅資料可供分析推薦。"

    # 2. Read conversation logs for all influencers
    conversation_logs = defaultdict(list)
    try:
        with open(LOG_FILE_PATH, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    log = json.loads(line)
                    inf_id = log.get('influencer_id')
                    if inf_id:
                        conversation_logs[inf_id].append(log)
    except FileNotFoundError:
        logger.warning("Conversation log file not found. Recommendations will not include conversation history.")
    except Exception as e:
        logger.error(f"Error reading conversation log file for recommendation: {e}")

    # 3. Construct a comprehensive prompt for the AI
    prompt_parts = []
    prompt_parts.append("請根據以下商案描述和網紅資料，分析並推薦最適合的網紅。請詳細說明推薦理由，並指出潛在的合作機會和注意事項。")
    prompt_parts.append(f"\n商案描述:\n{business_case_description}\n")
    prompt_parts.append("\n--- 網紅資料 ---\n")

    for influencer in influencers_data:
        prompt_parts.append(f"## 網紅名稱: {influencer.get('name', 'N/A')} (ID: {influencer.get('id', 'N/A')})")
        prompt_parts.append(f"  聯絡資訊: {influencer.get('contact_info', 'N/A')}")
        prompt_parts.append(f"  社群媒體: {influencer.get('social_media', 'N/A')}")
        prompt_parts.append(f"  語氣提示: {influencer.get('tone_prompt', 'N/A')}")
        prompt_parts.append(f"  個性分析: {influencer.get('personality_analysis', 'N/A')}")
        prompt_parts.append(f"  備註: {influencer.get('notes', 'N/A')}")
        
        inf_id = influencer.get('id')
        if inf_id and conversation_logs[inf_id]:
            prompt_parts.append("  近期對話紀錄:")
            for log in conversation_logs[inf_id]:
                role = log.get('role', 'unknown')
                content = log.get('content', '').replace('\n', ' ')
                timestamp = log.get('timestamp', '')
                prompt_parts.append(f"    - [{timestamp}] [{role}]: {content}")
        prompt_parts.append("-" * 30)

    full_prompt = "\n".join(prompt_parts)

    # 4. Get AI response
    # For this function, influencer_data is not directly used by get_ai_response for its internal logic,
    # but it's a required parameter. We can pass a dummy one.
    dummy_influencer_data = {"id": -1, "name": "AI_Analyst"}
    ai_recommendation = get_ai_response(dummy_influencer_data, full_prompt)
    
    return ai_recommendation

from typing import Optional

def analyze_post_content(post_text: str, image_url: Optional[str] = None) -> dict:
    """
    Analyzes post text and an optional image to determine sentiment,
    image description, and extract text from the image.

    Args:
        post_text: The text content of the post.
        image_url: The URL of the image to analyze.

    Returns:
        A dictionary with analysis results:
        {'description': str|None, 'extracted_text': str|None, 'sentiment': str|None}
    """
    logger.info(f"Analyzing post content... (Image URL: {image_url})")
    
    try:
        model = genai.GenerativeModel("models/gemini-2.5-pro")
        
        prompt_parts = [
            "You are an expert social media analyst. Analyze the following post content, which includes text and possibly an image.",
            f'Post Text: "{post_text}"',
            "\n---\n",
            "Your task is to return a single, raw JSON object with three keys:",
            "1. 'description': A concise, one-sentence neutral description of the image's visual content and mood. If there is no image, this should be null.",
            "2. 'extracted_text': A string containing all text extracted from the image. If there is no image or no text, this should be null.",
            "3. 'sentiment': Your analysis of the overall sentiment of the post, considering both the text and the image. Choose one of the following options: 'Positive', 'Negative', 'Neutral', 'Mixed'.",
            "\n---\n",
            'Example Response: {"description": "A person smiling on a sunny beach.", "extracted_text": "Live, Laugh, Love", "sentiment": "Positive"}',
            "Do not wrap the JSON in markdown backticks or any other formatting."
        ]

        # Download and add image if URL is provided
        if image_url:
            try:
                response = requests.get(image_url, timeout=15)
                response.raise_for_status()
                img = Image.open(io.BytesIO(response.content))
                prompt_parts.insert(2, img) # Insert image after the context
            except requests.exceptions.RequestException as e:
                logger.warning(f"Could not download image from {image_url}: {e}. Analyzing text only.")
            except Exception as e:
                logger.warning(f"Could not process image from {image_url}: {e}. Analyzing text only.")

        # Generate content
        ai_response = model.generate_content(prompt_parts)
        
        # Parse the JSON response
        raw_text = ai_response.text
        logger.debug(f"Raw AI response text: {raw_text}")

        clean_text = raw_text.strip()
        if clean_text.startswith("```json"):
            clean_text = clean_text[7:]
        if clean_text.endswith("```"):
            clean_text = clean_text[:-3]
        clean_text = clean_text.strip()

        response_json = json.loads(clean_text)
        
        # Validate and return the result
        result = {
            "description": response_json.get("description"),
            "extracted_text": response_json.get("extracted_text"),
            "sentiment": response_json.get("sentiment")
        }
        logger.info(f"Successfully analyzed post content. Sentiment: {result['sentiment']}")
        return result

    except Exception as e:
        logger.error(f"An error occurred during post content analysis: {e}")
        return {}
