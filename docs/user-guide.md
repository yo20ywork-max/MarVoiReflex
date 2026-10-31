# Windows App 使用指南

## 下載

[下載 Windows 自動下載工具](https://github.com/yo20ywork-max/MarVoiReflex/releases/download/v0.1.0-preview-20261031/MarVoiReflex-Download-Windows.cmd) ／ [發行頁面](https://github.com/yo20ywork-max/MarVoiReflex/releases/tag/v0.1.0-preview-20261031)

雙擊 `MarVoiReflex-Download-Windows.cmd`，工具會從本專案 GitHub Release 下載 App ZIP（約 693MB）與模型（約 1.56GB），核對 SHA-256 並解壓縮。完成後開啟使用者的 `Downloads\MarVoiReflex-20261031\MarVoiReflex\MarVoiReflex.exe`。

這是免安裝 App。完整下載包含 MiniCPM5-2B Q4_K_M、CPU 推論工具、語音辨識模型及相關執行元件。下載工具原始碼見 [download_app.cmd](../scripts/download_app.cmd)。

## 手動下載

也可下載以下兩個檔案：

1. [App 本體 ZIP](https://github.com/yo20ywork-max/MarVoiReflex/releases/download/v0.1.0-preview-20261031/MarVoiReflex-App-CPU-Windows-x64-20261031.zip)。
2. [MiniCPM5-2B-Q4_K_M.gguf 模型](https://github.com/yo20ywork-max/MarVoiReflex/releases/download/v0.1.0-preview-20261031/MiniCPM5-2B-Q4_K_M.gguf)。

完整 App 超過 GitHub 單檔上限，因此分開提供。兩個檔案都可公開下載，無需 GitHub 帳號。

## 電腦準備

- Windows 10/11，64 位元 x64。
- 至少 6GB 可用磁碟空間，供下載、解壓縮及操作資料使用。
- [Microsoft Edge WebView2 Runtime](https://developer.microsoft.com/microsoft-edge/webview2/) 與 .NET Framework 4.8。
- 使用語音對話時，需有可用的麥克風與 Windows 中文朗讀語音；建議配戴耳機。

App 以 CPU 執行，不需獨立顯示卡，也不需另外安裝 Python、Node 或 CUDA。8GB 記憶體是設計目標；現有驗證主機約 32GB，8GB 實機與其他電腦的相容性測試尚未完成。

## 第一次開啟

使用自動下載工具時，已完成解壓縮與模型放置。手動下載時，依序操作：

1. 在 App ZIP 上按右鍵，選「全部解壓縮」，放到自己的可寫入位置，例如桌面或文件資料夾。
2. 在解壓縮後的 `MarVoiReflex\assets` 裡建立 `models` 資料夾，將模型放入，完整相對路徑為 `MarVoiReflex\assets\models\MiniCPM5-2B-Q4_K_M.gguf`。
3. 開啟 `MarVoiReflex` 資料夾，雙擊 `MarVoiReflex.exe`。
4. 等待本機模型與工具啟動，再開始輸入訊息。

請保留 `assets`、`voice_runtime`、`web`、`第三方授權` 等資料夾與 App 放在一起。啟動說明也收錄在包內的 `MarVoiReflex-使用說明.txt`。

## 試做一次素材整理

1. 點左側資料夾圖示，開啟任務畫面。
2. 按「示範」建立測試素材；也可按「匯入」複製自己的圖片、TXT 或 Markdown 文案到 App 工作區。
3. 輸入「整理本週圖片與文案，先預覽」。
4. 檢查檔案名稱與分類去向，按畫面的「確認」後才會搬移；按「取消」則保留原位。
5. 查看結果摘要。App 會逐檔核對搬移後的 SHA-256。

素材操作範圍限於 App 的工作區。聊天與任務分開；語音說「確認」仍需在畫面按確認，才會執行檔案搬移。

## 語音對話

點電話或輸入框旁的聲波按鈕進入通話，選擇聊天或交辦任務，再開始並允許麥克風。語音回覆使用 Windows 中文朗讀語音，回覆速度可在語音選單查看。此功能為 AI 語音對話。

## 資料儲存

App 會在程式旁建立 `Data-MarVoiVoice`，存放匯入素材、操作紀錄及視窗設定。公開下載包不含開發電腦上的素材、聊天紀錄或連線權杖。關閉 App 會停止本 App 啟動的模型與工具服務。

## 下載檔案校驗

發行頁面的 `SHA256SUMS.txt` 提供 App ZIP、模型及下載工具的校驗碼。可在 PowerShell 執行下列指令，與清單比對：

```powershell
Get-FileHash -Algorithm SHA256 -LiteralPath '.\MarVoiReflex-App-CPU-Windows-x64-20261031.zip'
Get-FileHash -Algorithm SHA256 -LiteralPath '.\MiniCPM5-2B-Q4_K_M.gguf'
```

版本、已完成驗證及測試限制見[發行紀錄](releases/2026-10-31.md)。
