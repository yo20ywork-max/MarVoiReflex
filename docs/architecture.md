# 系統架構與完整工作流程

系統依序完成語音辨識、意圖理解、任務規劃、授權確認、工具執行及結果驗證。

```mermaid
flowchart LR
    U[文字／麥克風] --> A[1 語音辨識
faster-whisper small INT8 CPU]
    U --> B[2 意圖理解
聊天／任務分流]
    A --> B
    B -->|聊天| CHAT[MiniCPM5-2B 回答
沒有檔案工具]
    B -->|任務| C[3 任務規劃
小模型 JSON + 條件檢查]
    C --> D[5 安全確認
路徑／類型／日期／同名檔]
    D --> PRE[檔案計畫與預覽]
    PRE -->|畫面確認| E[4 工具執行
MCP 白名單 + 固定搬移器]
    PRE -->|取消| STOP[停止，不搬檔]
    E --> VERIFY[結果驗證
檔案存在／去向／SHA-256]
    VERIFY --> F[6 結果回報
文字／SAPI 語音／紀錄]
    CHAT --> F
```

系統包含六個模組；授權範圍與檔案狀態在計畫建立及確認執行時重新檢查。

| 模組 | 現有檔案 | 實際工作 |
|---|---|---|
| 語音辨識 | src/voice_engine.py、web/voice/audio-worklet.js | 收音、短句辨識、繁體轉換；採短句辨識 |
| 意圖理解 | src/runtime.py、assistant_modes.py、semantics.py | 聊天不執行；任務保留類型、日期、活動及否定條件 |
| 任務規劃 | src/intent.py、flow.py | MiniCPM5-2B 產生結構化 JSON，由控制器驗證操作條件 |
| 工具執行 | src/backend.py、flow.py、atomic_move.py、runtime/bridge.mjs | 本機 MCP stdio，固定 Windows 搬移 helper |
| 安全確認 | src/flow.py、atomic_move.py、main.py | 授權路徑、禁止連結越界、預覽計畫、按鍵確認、再驗證來源與同名檔 |
| 結果回報 | src/runtime.py、voice_engine.py、web/voice/live.js | 成功／失敗、分類摘要、語音、分段延遲及操作紀錄 |

## 一件任務從頭到尾

```mermaid
flowchart TD
    A[收到中文需求] --> B{任務模式？}
    B -->|否| CHAT[純聊天，提示切到任務]
    B -->|是| C[找授權素材並列清單]
    C --> D[理解活動／類型／日期]
    D --> E{條件明確且在範圍內？}
    E -->|否| ASK[拒絕或請使用者補充]
    E -->|是| F[選檔／計算固定分類去向]
    F --> G{存在同名檔？}
    G -->|是| ERR[停止，不覆寫]
    G -->|否| H[顯示來源、目的、數量與計畫]
    H --> I{畫面確認？}
    I -->|取消| END[取消並保留原檔]
    I -->|未確認| WAIT[等待，不修改]
    I -->|確認| J[重新核對計畫／來源／授權範圍]
    J --> K{仍與預覽一致？}
    K -->|否| NEW[停止，要求重新預覽]
    K -->|是| L[固定 helper 執行不覆寫搬移]
    L --> M[逐檔核對路徑、來源消失與內容雜湊]
    M --> N[回報成功或實際部分失敗，保留紀錄]
```

## 工具到底怎麼接

`MiniCPM5-2B → 受限 JSON → Python 安全控制器 → 本機 HTTP bridge → MCP stdio → Desktop Commander`。

目前使用 `@wonderwhy-er/desktop-commander@0.3.1` 的本機 stdio 連線。只開放 list_directory、read_file、get_file_info、start_search、get_more_search_results、stop_search、start_process、read_process_output。`start_process` 僅接受控制器產生的固定搬移命令。

本版本採限定工作流程與工具白名單，提供任務規劃與結果驗證。指定 App／瀏覽器啟動列於開發規劃，將使用獨立的授權工具。

## 資料與執行限制

模型 llama.cpp：CPU、4 執行緒、4096 context、單一並行、GPU layers 0。語音 faster-whisper small INT8 CPU，Windows SAPI 回覆。工作區、錄音、聊天及操作紀錄只留在使用者本機資料目錄，不放 GitHub。應用服務綁 127.0.0.1，前端／bridge 使用每次啟動產生的憑證；服務範圍限定於本機。
