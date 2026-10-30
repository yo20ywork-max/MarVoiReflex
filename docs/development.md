# 開發、啟動與打包

本倉庫是2026-10-31既有原生App的來源整理。只在新倉庫調整來源路徑與建置腳本，既有安裝目錄不變。Python模組放src，編輯前端放ui；以scripts/build_ui.py重建web/voice/index.html。

## 原始碼啟動

按README建立Python3.12虛擬環境、安裝requirements，使用configure_runtime.py指向已有的完整App。模型、llama-server.exe、Node與node_modules、ASR必須在該App的assets中，並保留第三方授權。設定檔不進Git。設定可用MARVOI_ASSETS_ROOT環境變數覆蓋；src的網頁仍讀本倉庫，不讀外部舊UI。CROSSGEN_DATA_DIR可設定獨立D槽資料目錄。

啟動前先確定沒有把同一個資料目錄給兩個程序共用。預設原生視窗；--no-browser僅開本機服務供隔離API驗證，不可公開監聽到外網。--stop需搭配相同--data-dir，僅關閉該資料目錄的實例。

## Windows原生殼打包

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-build.txt
.\.venv\Scripts\python.exe scripts/build_windows.py
```

輸出dist/MarVoiReflex/MarVoiReflex.exe與voice_runtime及web。這只打包原生殼，**不是完整免安裝版**。完整發布還需加入校驗過的assets與第三方授權資料夾，另做啟動／聊天／確認操作／關閉及無GPU檢查；不可因PyInstaller完成就稱發版通過。本次沒有執行全量重新打包、下載模型或複製大型runtime。

runtime/node/package.json固定MCP與SDK版本。bridge.mjs應放完整發布的assets/bridge.mjs，套件在assets/node/node_modules。遠端OAuth專案不是本版使用的runtime。重裝依賴可能得到不同傳遞版本；本次只記錄既有直屬版本，尚未完成乾淨電腦重建驗證，不宣稱bit-for-bit可重現。

## 必要檢查

`python scripts/check_project.py`：文件鏈結、50題分類數、60項對照、Python語法、UI控制器與原始碼路徑隔離。這是無模型檢查；不能替代8GB實機或所有功能驗證。新功能請加對應實際案例，修正紀錄保留原始失敗。

程式記錄可能含使用者文字、檔名與本機路徑；回報Issue前先去識別。session token、connection.json、bridge-state.json、錄音與Data資料夾不應公開。
