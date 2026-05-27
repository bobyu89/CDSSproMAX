# CASE-09：黃疸 — 急性膽管炎案例【保留案例】

> **來源：LLM 生成案例**
> **本案例為保留案例（withheld），僅用於後測，前測期間完全封存。**

## 基本資訊

| 欄位 | 內容 |
|------|------|
| 案例編號 | CASE-09 |
| 症狀 ID | jaundice |
| 難度 | intermediate（中級） |
| 類別 | 消化/肝膽 |
| 類型 | **保留案例 (withheld)** |
| 案例類型（雙歷程理論） | 熟悉情境（系統一）— typical |

## 臨床情境

一位 68 歲女性，退休護理師，因眼白及皮膚變黃伴右上腹痛 3 天至急診就醫。病人主訴 3 天前晚餐後（油膩飲食）突然出現右上腹絞痛，疼痛放射至右肩背部，伴噁心及嘔吐 2 次。隔日發現眼白變黃，小便顏色深如茶色，大便顏色變淡。今日畏寒後高燒 39.2°C，疼痛未緩解。過去病史：膽結石（2 年前超音波發現，因無症狀未處理），高血脂症，骨質疏鬆症（服用鈣片及維生素 D）。無菸酒。

## 標準答案

### 一、應評估系統

| 系統 | 重要性 | 理由 |
|------|--------|------|
| 消化/肝膽系統 | core | 黃疸 + 右上腹痛 + 膽結石病史，Charcot's triad（黃疸、發燒、右上腹痛）高度懷疑急性膽管炎。 |
| 感染科 | core | 高燒 + 畏寒提示膽道感染，需評估是否進展至 Reynolds' pentad（敗血性膽管炎）。 |
| 心血管系統 | important | 老年感染患者需評估血流動力學穩定性，排除感染性休克。 |
| 血液系統 | optional | 黃疸需鑑別溶血性貧血，雖此案例為阻塞性黃疸可能性較高。 |

### 二、身體評估項目

| 項目 ID | 項目名稱 | 預期結果 | 異常 | 關鍵 | 臨床意義 |
|---------|---------|---------|:----:|:----:|---------|
| vs_temp | 體溫 | BT 39.4°C (tympanic) | Y | Y | 高燒為 Charcot's triad 之一，提示膽道感染。 |
| vs_hr | 心率/脈搏 | HR 106 bpm，regular rhythm | Y | Y | 心搏過速，發燒及感染所致，需警覺敗血症可能。 |
| vs_bp | 血壓測量 | BP 108/68 mmHg | Y | Y | 血壓偏低，可能為早期敗血症或脫水所致。需密切監測是否進展為休克。 |
| vs_rr | 呼吸速率 | RR 22 次/分 | Y | N | 輕度呼吸急促，發燒及疼痛所致。 |
| heent_eye | 眼睛檢查 | 鞏膜明顯黃染（scleral icterus） | Y | Y | 鞏膜黃染為黃疸最早及最敏感的體徵，膽紅素 >2.5 mg/dL 時可見。 |
| skin_inspection | 皮膚視診 | 全身皮膚黃染，搔癢痕跡（+） | Y | Y | 皮膚黃疸及搔癢提示膽汁鬱積（cholestasis），直接膽紅素升高刺激皮膚神經末梢。 |
| abd_palpation | 腹部觸診 | 右上腹明顯壓痛，Murphy's sign positive（深吸氣時觸診膽囊區引起劇痛並中斷吸氣），無反彈痛 | Y | Y | Murphy's sign 陽性為急性膽囊炎特徵性體徵，結合黃疸及發燒提示結石滑入總膽管導致膽管炎。 |
| abd_murphy | Murphy's sign | Murphy's sign 強陽性，觸診時病人痛苦表情明顯 | Y | Y | 與上一項互為佐證，膽囊區發炎的直接證據。 |
| abd_auscultation | 腹部聽診 | 腸音減弱 | Y | N | 腸蠕動因發炎及疼痛而減緩。 |
| ga_consciousness | 意識狀態 | GCS 15/15，意識清楚但疲倦 | N | Y | 意識清楚排除 Reynolds' pentad（意識改變 + 休克 = 敗血性膽管炎），目前為 Charcot's triad 階段。 |

### 三、鑑別診斷

| 排名 | 診斷 | 嚴重度 | Must-not-miss | 理由 |
|:----:|------|:------:|:------------:|------|
| 1 | 急性膽管炎 (Acute Cholangitis) | critical | Y | 完整 Charcot's triad：發燒 39.4°C + 右上腹痛 + 黃疸。膽結石病史為明確危險因子。結石阻塞總膽管導致膽汁鬱積合併細菌感染。若進展為 Reynolds' pentad 則危及生命。 |
| 2 | 急性膽囊炎 (Acute Cholecystitis) | high | Y | Murphy's sign 陽性 + 膽結石病史 + 油膩飲食誘因。急性膽囊炎常與膽管炎並存，但單純膽囊炎通常無黃疸。 |
| 3 | 胰頭癌 (Pancreatic Head Cancer) | high | Y | 68 歲女性無痛性黃疸（painless jaundice）需排除胰頭癌。但此案例有明顯疼痛及發燒，惡性阻塞可能性較低。仍需影像學排除。 |
| 4 | 總膽管結石 (Choledocholithiasis) | moderate | N | 為急性膽管炎的直接病因，膽結石滑入或形成於總膽管。可單獨表現為黃疸而無感染。 |
| 5 | 急性肝炎 (Acute Hepatitis) | moderate | N | 病毒性或藥物性肝炎可導致黃疸。但右上腹絞痛及 Murphy's sign 更指向膽道疾病。需肝功能檢查鑑別。 |

## 學習目標

學習黃疸的三大分類（肝前性、肝性、肝後性）鑑別，掌握 Charcot's triad 與 Reynolds' pentad 的臨床意義，理解膽道急症的病理生理機轉及緊急處置原則，熟悉 Murphy's sign 的正確執行方法。

## 標籤

`gastroenterology` `hepatobiliary` `cholangitis` `jaundice` `emergency`
