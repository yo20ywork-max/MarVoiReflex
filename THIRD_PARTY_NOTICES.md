# 第三方來源與授權

原始程式授權條款見 LICENSE；第三方元件及識別素材依各自授權使用。

| 元件 | 本次用途 | 來源／授權紀錄 |
|---|---|---|
| Noto Sans TC | 中英共用字型 | ui/NotoSansTC-OFL.txt；SIL OFL 1.1 |
| 國立臺北大學識別圖 | 專題展示識別 | https://new.ntpu.edu.tw/assets/logo/ntpu.svg；原始圖形；商標及識別權利屬校方 |
| MiniCPM5-2B | Windows 發行包隨附 Q4_K_M 本機模型 | https://huggingface.co/openbmb/MiniCPM5-2B；保留發行包內該版本模型卡、Apache-2.0 與來源紀錄 |
| llama.cpp | Windows 發行包隨附 CPU 推論程式 | https://github.com/ggml-org/llama.cpp/blob/master/LICENSE |
| Desktop Commander | Windows 發行包隨附本機 MCP 0.3.1 | https://github.com/wonderwhy-er/DesktopCommanderMCP；依安裝版本 LICENSE，與 remote-desktop-commander 分開記錄 |
| faster-whisper / CTranslate2 | Windows 發行包隨附 CPU 語音辨識元件及模型 | https://github.com/SYSTRAN/faster-whisper / https://github.com/OpenNMT/CTranslate2；MIT |
| pywebview / pythonnet | 原生視窗橋接 | https://github.com/r0x0r/pywebview / https://github.com/pythonnet/pythonnet；依固定版本 LICENSE |
| Windows SAPI / WebView2 | Windows 安裝環境 | 使用者電腦提供；本倉庫未重新分發語音包／WebView2 runtime |

完整 App 的第三方授權資料夾應與程式一同保留。runtime/manifest.json 記錄固定版本。模型與 Windows App ZIP 隨 GitHub Release 分開提供，Node 及 Python 執行元件包含在 ZIP 內，未放入 Git 原始碼歷史；發行包不含真人錄音、聊天紀錄或連線權杖。
