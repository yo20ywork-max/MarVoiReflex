# 教授要求：白話調整清單與逐項對照

先記五件事：**先選一種人、做好一件事、先給人看才動檔、用真的測試證明、每週留下進度。**

1. 把名字和介紹改成「協助小型商家行銷人員整理素材」，不要說什麼人、什麼電腦操作都能做。
2. 先完成「找圖片和文案→列分類清單→人按確認→搬檔→核對」這一整條。
3. 訪談6–8人，查清楚最常遇到哪三個麻煩；沒有訪談就先寫待驗證。
4. 用50題和12–16位使用者測試，量是否成功、花多久、好不好用、會不會沒同意就動檔。
5. 補架構圖、BMC、分工、16週計畫、會議紀錄與修訂簡報；聯絡資料由本人補，不亂猜。

下面60項全部已有對應文件；「文件已補」**不等於功能已做完或研究已執行**。未完成工作由GitHub Issues追蹤。教授原信是使用者提供的來源；未公開私人信箱或轉寄全文。

| 條目 | 要改什麼（白話） | 對應文件 | 實際進度 |
|---|---|---|---|
| 1.1.1 | 改成MarVoiReflex正式題名 | [project-positioning](project-positioning.md) | 定位已寫入；待全組確認 |
| 1.1.2 | 只先服務小型商家社群行銷人員 | [project-positioning](project-positioning.md) | 定位已寫入；待全組確認 |
| 1.1.3 | 先做每週行銷素材整理 | [project-positioning](project-positioning.md) | 定位已寫入；待全組確認 |
| 1.2.1 | 訪談6–8位真的做行銷的人 | [interviews](interviews.md) | 規劃／待執行 |
| 1.2.2 | 整理前三大問題、頻率與花費時間 | [interviews](interviews.md) | 規劃／待執行 |
| 1.2.3 | 公平比較Voice Access與Power Automate Desktop，核對中文與規劃能力 | [project-positioning](project-positioning.md) | 官方文件比較已補；競品實測待做 |
| 1.3.1 | 目標是Windows中文語音素材整理原型 | [mvp-spec](mvp-spec.md) | 部分原型已有；App啟動與正式研究待補 |
| 1.3.2 | 只保留開工具、找分類、預覽確認三核心 | [mvp-spec](mvp-spec.md) | 部分原型已有；App啟動與正式研究待補 |
| 1.3.3 | 用完成率、時間、滿意度驗證 | [mvp-spec](mvp-spec.md) | 部分原型已有；App啟動與正式研究待補 |
| 2.1.1 | 把大任務拆成找檔、分類、預覽、執行 | [architecture](architecture.md) | 已有受限流程；非自由完整工具庫 |
| 2.1.2 | 只用預先允許工具，不下任意系統命令 | [architecture](architecture.md) | 已有受限流程；非自由完整工具庫 |
| 2.1.3 | 做完核對去向、同名檔與失敗 | [architecture](architecture.md) | 已有受限流程；非自由完整工具庫 |
| 2.1.4 | 以多步驟規劃及結果驗證說明創新 | [architecture](architecture.md) | 已有受限流程；非自由完整工具庫 |
| 2.2.1 | 畫清楚六個系統模組 | [architecture](architecture.md) | 已有CPU原型；實體8GB未驗證 |
| 2.2.2 | 先跑通文字，再接語音 | [architecture](architecture.md) | 已有CPU原型；實體8GB未驗證 |
| 2.2.3 | 用llama.cpp與本機模型量硬體負載 | [architecture](architecture.md) | 已有CPU原型；實體8GB未驗證 |
| 2.2.4 | 限制工具與路徑，搬移批次先確認並留紀錄 | [architecture](architecture.md) | 已有CPU原型；實體8GB未驗證 |
| 2.3.1 | 第一階段做開App、找資料夾、列檔案 | [mvp-spec](mvp-spec.md) | 分階段規格已補；各項完成度分列 |
| 2.3.2 | 第二階段做分類、預覽、確認、回報 | [mvp-spec](mvp-spec.md) | 分階段規格已補；各項完成度分列 |
| 2.3.3 | 第三階段整合中文語音、任務規劃、錯誤處理 | [mvp-spec](mvp-spec.md) | 分階段規格已補；各項完成度分列 |
| 2.3.4 | 自動發文、文案生成、跨帳號先放未來 | [mvp-spec](mvp-spec.md) | 分階段規格已補；各項完成度分列 |
| 3.1.1 | 重新排成BMC九格 | [business-model](business-model.md) | 規劃／待執行 |
| 3.1.2 | 價值是省整理時間、少分錯檔 | [business-model](business-model.md) | 規劃／待執行 |
| 3.1.3 | 先問使用與付費意願，不預設訂閱成功 | [business-model](business-model.md) | 規劃／待執行 |
| 3.2.1 | 用每週貼文圖片、文案、成效截圖當場景 | [mvp-spec](mvp-spec.md) | 已有檔名篩選；活動多層目錄／成效驗證待補 |
| 3.2.2 | 依活動、檔型、日期選素材並給摘要 | [mvp-spec](mvp-spec.md) | 已有檔名篩選；活動多層目錄／成效驗證待補 |
| 3.2.3 | 量整理時間、分類正確率、操作步驟 | [mvp-spec](mvp-spec.md) | 已有檔名篩選；活動多層目錄／成效驗證待補 |
| 4.1.1 | Demo A語音開瀏覽器和活動資料夾 | [demo](demo.md) | A待開發；B/C部分已有；影片待錄 |
| 4.1.2 | Demo B拆任務、預覽、確認、回報 | [demo](demo.md) | A待開發；B/C部分已有；影片待錄 |
| 4.1.3 | Demo C測缺資料夾、同名檔、取消 | [demo](demo.md) | A待開發；B/C部分已有；影片待錄 |
| 4.1.4 | 準備固定素材、展示腳本和備用影片 | [demo](demo.md) | A待開發；B/C部分已有；影片待錄 |
| 4.2.1 | 50題分基本10、行銷20、多步驟10、安全10 | [50-cases](testing/50-cases.md) | 規劃／待執行 |
| 4.2.2 | 招募12–16人比較人工和Agent | [user-study](testing/user-study.md) | 規劃／待執行 |
| 4.2.3 | 每次記成功、時間、重試、錯誤、確認 | [user-study](testing/user-study.md) | 規劃／待執行 |
| 4.2.4 | 交換人工和Agent順序，減少越做越熟的影響 | [user-study](testing/user-study.md) | 規劃／待執行 |
| 4.3.1 | 任務完成率目標80%以上 | [user-study](testing/user-study.md) | 規劃／待執行 |
| 4.3.2 | 同難度任務節省時間20%以上 | [user-study](testing/user-study.md) | 規劃／待執行 |
| 4.3.3 | 五分問卷平均4分以上 | [user-study](testing/user-study.md) | 規劃／待執行 |
| 4.3.4 | 未授權移動／覆寫次數為0 | [user-study](testing/user-study.md) | 規劃／待執行 |
| 4.3.5 | 用真實表格圖表解釋結果和未達標原因 | [user-study](testing/user-study.md) | 規劃／待執行 |
| 5.1.1 | 每週開會記完成、問題、決議和下週目標 | [TEMPLATE](meetings/TEMPLATE.md) | 範本已補；沒有代造小組會議 |
| 5.1.2 | 用GitHub管程式、需求、問題與里程碑 | [CONTRIBUTING](../CONTRIBUTING.md) | 本輪建立新公開倉庫與Issue／milestone |
| 5.1.3 | 每兩週交一次可展示成果 | [roadmap](roadmap.md) | 規劃／待執行 |
| 6.1.1 | 封面補題名、教授、系、日期、組員照片、五關鍵字和網站 | [outline](presentation/outline.md) | 簡報草稿已補；Email／學程已核對；照片／個人網站待提供 |
| 6.1.2 | 結尾用完整Q&A頁，不只寫謝謝 | [outline](presentation/outline.md) | 簡報草稿已補；Email／學程已核對；照片／個人網站待提供 |
| 6.1.3 | 參考文獻獨立一頁並統一格式 | [outline](presentation/outline.md) | 簡報草稿已補；Email／學程已核對；照片／個人網站待提供 |
| 6.2.1 | 每頁只說一件主要事情 | [outline](presentation/outline.md) | 採既有UI預覽與真實去識別證據；未冒充真人測試 |
| 6.2.2 | 架構、流程、BMC、方法優先用圖 | [outline](presentation/outline.md) | 採既有UI預覽與真實去識別證據；未冒充真人測試 |
| 6.2.3 | 加真實介面、輸入輸出與工程測試證據 | [outline](presentation/outline.md) | 採既有UI預覽與真實去識別證據；未冒充真人測試 |
| 6.2.4 | 統一中英字體、標題、頁碼與術語 | [outline](presentation/outline.md) | 採既有UI預覽與真實去識別證據；未冒充真人測試 |
| 7.1 | 交修訂簡報：定位、目標、貢獻、Agent創新 | [outline](presentation/outline.md) | 修訂草稿已補；缺資料待全組補 |
| 7.2 | 交具體情境與MVP規格 | [mvp-spec](mvp-spec.md) | 規格已補；團隊核定待做 |
| 7.3 | 交架構、工作流程與技術可行性結果 | [architecture](architecture.md) | 架構已補；可行性引用既有17項，8GB未驗證 |
| 7.4 | 至少展示一個真的能操作的功能 | [demo](demo.md) | 既有原型有預覽確認分類；現場重現待做 |
| 7.5 | 交50題、使用者方法與量化指標 | [50-cases](testing/50-cases.md) | 規劃／待執行 |
| 7.6 | 交分工、16週計畫和會議紀錄 | [roadmap](roadmap.md) | 草案／範本已補；正式分工與真會議待完成 |
| 8.1 | 保留中文語音，定位行銷工作流程Agent | [next-review-checklist](next-review-checklist.md) | 方向已寫入；實作／研究成果依證據逐項驗收 |
| 8.2 | 先做好一個完整可靠的整理情境 | [next-review-checklist](next-review-checklist.md) | 方向已寫入；實作／研究成果依證據逐項驗收 |
| 8.3 | 以需求、價值、創新、展示、可驗證成果評分 | [next-review-checklist](next-review-checklist.md) | 方向已寫入；實作／研究成果依證據逐項驗收 |
| 8.4 | 下次帶可執行原型、架構與測試，不只講概念 | [next-review-checklist](next-review-checklist.md) | 方向已寫入；實作／研究成果依證據逐項驗收 |

## 另外四項行政要求

| 編號 | 事情 | 狀態 |
|---|---|---|
| A1 | Email同步所有組員 | 四人Email已齊；教授地址待確認，未寄信；有草稿 |
| A2 | 四人完整資料（Email、github.io、照片） | 姓名學號、Email與學程已核對；個人網站／照片待提供 |
| A3 | 修訂簡報上Google Drive，分享教授和全組 | 本輪交GitHub與PPTX；未代上傳、未分享權限 |
| A4 | 回覆並預約討論時段 | 2026-10-31 16:10–16:30只是教授建議，未確認／未建立邀請 |

詳見[下次指導清單](next-review-checklist.md)、[組員資料](team.md)及[信件草稿](sharing-draft.md)。
