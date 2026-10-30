# 開發與打包說明

本專案提供Windows原生介面、CPU推論服務、語音模組與素材操作控制器。Python模組位於 `src/`，前端來源位於 `ui/`，以 `scripts/build_ui.py` 產生 `web/voice/index.html`。

## 開發環境

Windows 11 x64、Python 3.12、WebView2，以及完整App的執行資產。語言模型、ASR模型、llama-server、Node與MCP套件依 `runtime/manifest.json` 準備，並保留第三方授權文件。

依README建立虛擬環境與安裝依賴後，執行 `configure_runtime.py` 指定完整App目錄。設定儲存於本機 `app-link.json`，也可透過 `MARVOI_ASSETS_ROOT` 覆蓋。開發網頁讀取本倉庫；資料預設儲存於 `.local-data/`，可用 `CROSSGEN_DATA_DIR` 設定獨立目錄。

同一資料目錄供單一App實例使用。`--no-browser` 啟動本機服務供API測試；`--stop` 搭配相同 `--data-dir` 關閉對應實例。服務限定127.0.0.1。

## Windows 原生殼打包

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-build.txt
.\.venv\Scripts\python.exe scripts/build_windows.py
```

輸出包含 `dist/MarVoiReflex/MarVoiReflex.exe`、`voice_runtime` 與 `web`。完整發行版需另加入驗證過的 `assets` 與第三方授權，並執行啟動、聊天、素材操作、語音及關閉流程驗證。

## MCP 執行資產

`runtime/node/package.json` 固定MCP與SDK版本。完整App的bridge位於 `assets/bridge.mjs`，Node套件位於 `assets/node/node_modules`。目前使用本機stdio連線。

目前已記錄直接依賴版本；乾淨環境重建與完整傳遞依賴校驗列於後續工作。

## 原始碼與文件檢查

執行 `python scripts/check_project.py`，檢查文件連結、50題分類、60項研究需求、Python語法與來源路徑設定。模型推論、原生介面操作與8GB實機效能另行驗證。

Issue重現資料應先去識別。錄音、對話、工作區、session憑證與執行紀錄依 `.gitignore` 留存於本機。
