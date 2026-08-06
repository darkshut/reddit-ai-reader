# Reddit AI Reader

一個供個人使用的非商業 Reddit 閱讀器雛形。它透過 Reddit Data API 唯讀擷取少量 AI 社群的新文章，並保留原始文章連結供人工閱讀。

## 使用範圍

- 僅供單一使用者在自己的電腦執行。
- 僅讀取公開文章，不發文、留言、投票、傳訊或執行管理操作。
- 不建立或散布 Reddit 資料集。
- 不使用 Reddit 內容訓練或微調 AI 模型。
- 程式不把 Reddit 內容寫入磁碟；資料只存在於當次程序的記憶體。
- 遵守 OAuth、可識別的 User-Agent 與 Reddit API 流量限制。

## 目前狀態

這是提供 Reddit 審查的最小安全雛形。必須先獲得 Reddit Data API 核准並建立 OAuth Client，才能實際連線。

## 設定

把憑證放在環境變數。不要把憑證寫進檔案或提交到 GitHub。

```bash
export REDDIT_CLIENT_ID="..."
export REDDIT_CLIENT_SECRET="..."
export REDDIT_USERNAME="darkshutor"
```

## 執行

預設讀取 `LocalLLaMA`、`MachineLearning` 與 `artificial` 的最新文章：

```bash
python3 reddit_ai_reader.py
```

也可以自行指定社群與每個社群的篇數：

```bash
python3 reddit_ai_reader.py --subreddit OpenAI --subreddit ClaudeAI --limit 5
```

## 驗證

```bash
python3 -m unittest -v
```

## 資料處理

程式只把 API 回應保留在執行期間，結束後即消失。如果未來加入暫存功能，會在 48 小時內清除內容，並同步移除已在 Reddit 刪除的內容。

