# AI 網紅經紀助理 (Project FameFlow) - 操作說明書 (v3.1)

## 1. 專案簡介

本專案旨在建立一個自動化的 AI 助理，協助網紅經紀人管理旗下網紅的日常事務。系統核心功能包含：網紅資料庫管理、網頁版儀表板、多平台通訊（Telegram, LINE, Email）、由 AI 驅動的網路動態自動收集與分析功能。

---

## 2. 系統元件

*   `influencers.db`: **核心資料庫**。儲存所有網紅、社群帳號、貼文、產品和客戶的資料。
*   `main.py`: **網頁儀表板後端**。使用 FastAPI 框架。
*   `templates/index.html`: **網頁儀表板前端**。
*   `manager_cli.py`: **經紀人命令列介面**。用於管理資料庫和執行後端任務。
*   `core_logic.py`: **核心商業邏輯**。封裝了呼叫 Gemini LLM 進行文字與視覺分析的功能。
*   `scraper.py`: **AI 網路爬蟲**。使用 Playwright 框架，可設定抓取目標網站，並使用 AI 分析圖片。
*   `*_bot.py`, `email_checker.py`: 各平台的通訊連接器。
*   `add_*.py`, `migrate_*.py`: 用於建立和修改資料庫結構的**輔助腳本**。
*   `venv/`: **Python 虛擬環境**資料夾。

---

## 3. 環境設定 (從零開始)

1.  **安裝 Python**: 確保系統已安裝 Python 3 (建議 3.10+)。
2.  **建立虛擬環境**: `python3 -m venv venv`。
3.  **啟用虛擬環境**: `source venv/bin/activate`。
4.  **安裝必要函式庫**:
    ```bash
    pip install python-telegram-bot beautifulsoup4 fastapi uvicorn jinja2 requests google-generativeai python-line-bot-sdk playwright Pillow
    ```
5.  **安裝 Playwright 瀏覽器核心**: `playwright install`。
6.  **設定 AI 大腦金鑰 (Gemini LLM)**: 
    ```bash
    export GOOGLE_API_KEY='您的_實際_API_金鑰'
    ```

---

## 4. 系統操作流程

**重要：** 在執行任何 Python 腳本前，請務必先啟用虛擬環境 (`source venv/bin/activate`)。

### 4.1 網頁儀表板 (主要管理工具)

這是您最主要的管理後台。

1.  **啟動伺服器**:
    ```bash
    uvicorn main:app --reload
    ```
2.  **開啟介面**: 在您的瀏覽器中打開網址 **http://127.0.0.1:8000**。
3.  **操作功能**:
    *   **CRUD 功能完整**: 您現在可以透過儀表板介面，完整地對網紅、產品、客戶進行新增、刪除、修改、查詢等所有操作。
    *   **查看 AI 分析**: 點擊任一網紅查看詳情時，彈出視窗下方會自動載入該網紅的近期貼文，並顯示 AI 對每篇貼文的**情緒分析 (AI Sentiment)** 結果。

### 4.2 經紀人命令列介面 (Manager CLI)

`manager_cli.py` 是功能最完整的管理工具，適合後端開發與批次處理。

1.  **列出所有網紅**:
    ```bash
    python manager_cli.py list
    ```

2.  **新增網紅 (互動式)**:
    ```bash
    python manager_cli.py add
    ```
    *   程式會引導您輸入網紅的主要資訊，並可選擇性地循環新增多個社群帳號。

3.  **查看網紅詳情**:
    ```bash
    python manager_cli.py view "網紅的真實姓名"
    ```
    *   將會顯示該網紅的所有主要資訊，並列出她所有已連結的社群帳號。

4.  **查看爬取的貼文 (含 AI 分析)**:
    ```bash
    python manager_cli.py show_posts [網紅ID]
    ```
    *   將會顯示指定 ID 的網紅所有被爬取的貼文，包含 AI 對圖片的描述、文字提取，以及最新的**情緒分析**結果。

5.  **獲取 AI 商案推薦**:
    ```bash
    python manager_cli.py recommend "您的商案描述..."
    ```

### 4.3 AI 網路爬蟲

`scraper.py` 已被升級為使用 Playwright 和 AI 視覺分析的進階爬蟲。

1.  **配置爬蟲**: 
    *   打開 `scraper.py` 檔案，在底部的 `if __name__ == '__main__':` 區塊中，修改 `TARGET_CONFIG` 來定義爬蟲目標。

2.  **執行爬蟲**:
    ```bash
    python scraper.py
    ```
    *   腳本會根據設定，抓取目標網站的貼文，對其文字和圖片進行綜合性的 AI 分析（包含情緒分析），並將所有結果存入資料庫。

---

## 5. 未來展望 (待辦事項)

本系統的下一步開發將專注於以下目標：

1.  **適配真實社群平台**: 為爬蟲撰寫針對特定平台（如 Instagram, Threads, Facebook）的爬取設定，並實作 Cookie 登入機制。
