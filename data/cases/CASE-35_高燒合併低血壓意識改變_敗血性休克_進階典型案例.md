# CASE-35：高燒合併低血壓意識改變 — 敗血性休克（進階典型案例）

> **來源：理論示範案例（seed_cases_theory_examples.json）**

## 基本資訊

| 欄位 | 內容 |
|------|------|
| 案例編號 | CASE-35 |
| 症狀 ID | `fever` |
| 難度（心流理論分級） | 進階 (advanced) |
| 類別 | 內科/感染/急重症 |
| 案例類型（雙歷程理論） | 熟悉情境（系統一） |
| 狀態 | 正式案例 |

## 臨床情境

一位 74 歲男性，退休農夫，因發燒 3 天合併意識改變 6 小時由家屬送至急診。病人 3 天前出現畏寒、發燒（自測 38.5°C），家屬以為一般感冒未就醫。今晨發現病人躺在床上叫不醒，反應遲鈍，無法正確回答姓名與地點。皮膚摸起來又熱又潮，四肢末梢冰冷。家屬發現病人左大腿前側有一處皮膚紅腫，約 10×15 cm，病人回憶 4 天前在田裡被樹枝刮傷。過去病史：第二型糖尿病（長期口服降血糖藥，但 HbA1c 9.8%）、慢性腎病第 3 期、曾中風 2 次。長期臥床時間增加。

## 標準答案

### 一、應評估系統

| 系統 | 重要性 | 理由 |
|------|--------|------|
| 感染/全身系統 | core | 發燒 + 皮膚感染灶 + 意識改變為感染全身性反應的典型表現，須評估敗血症嚴重度與病原來源。 |
| 心血管系統 | core | 低血壓、末梢灌流不良提示敗血性休克，須立即液體復甦並評估是否需 vasopressor。 |
| 神經系統 | core | 意識改變為 qSOFA 指標之一；須鑑別敗血症腦病（septic encephalopathy）與腦膜炎、腦中風。 |
| 皮膚系統 | core | 皮膚紅腫為感染源線索，須評估蜂窩性組織炎、壞死性筋膜炎或深部膿瘍。 |
| 呼吸系統 | important | 評估 RR（qSOFA）及排除合併肺炎。 |
| 泌尿/腎臟系統 | important | 既有 CKD，須評估急性腎損傷；並排除泌尿道感染為第二來源。 |

### 二、身體評估項目

| 項目 | 預期結果 | 異常 | 關鍵 | 臨床意義 |
|------|---------|:----:|:----:|---------|
| 體溫測量 | BT 39.2°C（耳溫） | Y | Y | 高燒符合敗血症 SIRS / Sepsis-3 發燒指標。 |
| 血壓與心率 | BP 82/48 mmHg, MAP 59 mmHg, HR 128 bpm | Y | Y | MAP < 65 mmHg 即符合敗血性休克；心搏過速為代償性反應。 |
| 呼吸速率與血氧 | RR 28 次/分, SpO2 93% (room air) | Y | Y | RR ≥ 22 為 qSOFA 陽性；低氧提示器官功能障礙。 |
| 意識評估（GCS） | GCS E3V3M5 (11 分)，對疼痛有反應，言語混亂 | Y | Y | GCS < 15 + 基線改變，qSOFA 陽性，敗血症腦病表現。 |
| 皮膚感染灶評估 | 左大腿前側 10×15 cm 紅腫熱痛區域，邊緣模糊，局部可見出血性水泡（hemorrhagic bullae）與皮膚壞死斑，皮下捻髮音陽性（crepitus） | Y | Y | 出血性水泡、皮下捻髮音、與臨床不成比例的疼痛強烈提示壞死性筋膜炎（necrotizing fasciitis），須緊急手術清創。 |
| 末梢微血管充填時間 | Capillary refill > 4 秒 | Y | Y | 末梢灌流不良為休克代償失調的指標。 |
| 膝部皮膚花斑評估 | 雙膝部 mottling score 3-4 分（花斑範圍超過膝蓋至大腿） | Y | Y | Mottling score 高度預測敗血性休克死亡率。 |
| 腦膜刺激徵 | Kernig's sign 陰性、Brudzinski's sign 陰性、頸部柔軟 | N | Y | 初步排除腦膜炎作為意識改變原因。 |
| 肺部聽診 | 雙側呼吸音對稱，無顯著囉音或哮鳴 | N | N | 排除肺炎為第二感染源。 |
| 腹部檢查 | 腹部柔軟，無壓痛，無肌衛 | N | Y | 排除腹腔感染來源。 |
| 尿量評估（插尿管） | 過去 6 小時尿量 80 mL（< 0.5 mL/kg/hr） | Y | Y | 少尿為敗血症器官功能障礙指標。 |
| 四肢動脈搏動 | 四肢動脈可觸及但微弱；下肢較上肢為弱 | Y | N | 休克時末梢灌流下降，脈搏微弱。 |

### 三、鑑別診斷

| 排名 | 診斷 | 嚴重度 | Must-not-miss | 理由 |
|:----:|------|:------:|:------------:|------|
| 1 | 敗血性休克合併壞死性筋膜炎 (Septic Shock with Necrotizing Fasciitis) | critical | Y | qSOFA ≥ 2（RR 28、GCS < 15、SBP ≤ 100）+ MAP < 65 + 明確感染灶（左大腿 hemorrhagic bullae、crepitus、pain-disproportion）。糖尿病 + CKD 為重要共病危險因子。需立即外科會診與廣效抗生素（含 clindamycin for toxin suppression）。 |
| 2 | 中毒性休克症候群 (Toxic Shock Syndrome) | critical | Y | Group A Streptococcus 或 Staphylococcus 毒素介導之全身性反應，與壞死性筋膜炎常並存。 |
| 3 | 糖尿病酮酸中毒 (DKA) 合併感染 | high | Y | HbA1c 9.8% 合併感染壓力，須查血糖、anion gap、ketone；可同時存在且複雜化敗血症。 |
| 4 | 細菌性腦膜炎 (Bacterial Meningitis) | critical | Y | 老人意識改變 + 發燒須排除；此案例無頸部僵硬、無腦膜刺激徵，可能性較低但經驗性治療時須涵蓋。 |
| 5 | 急性缺血性中風 (Acute Ischemic Stroke) | high | Y | 有過去中風病史，須影像排除新發梗塞。然敗血症腦病可模擬局部神經學表現，須整體判斷。 |

### 四、LQQOPERA 結構化問診標準

| 維度 | 名稱 | 權重 | 關鍵概念 | 雙語關鍵字 | 示例回答 |
|:---:|------|:----:|---------|-----------|---------|
| L | Location（位置） | 3 | localized skin infection + systemic | left thigh、systemic、左大腿、全身 | 左大腿有一塊紅腫，全身很燙。 |
| Q | Quality（型態） | 3 | pain out of proportion | severe、disproportionate、劇痛、不成比例 | 家屬說病人一碰到大腿就痛到大叫，但看起來只是紅腫。 |
| Q2 | Quantity / time course | 3 | 3-day rapid progression | 3 days、rapidly progressing、3 天、快速惡化 | 3 天內從小紅腫變成大片，今天意識就模糊了。 |
| O | Onset mode | 3 | preceding skin trauma | wound exposure、trauma、scratch、外傷、刮傷 | 4 天前在田裡被樹枝刮傷。 |
| P | Precipitation factors | 3 | diabetes + CKD + poor glycemic control | diabetes、CKD、immunocompromised、糖尿病、腎病、免疫力低 | 有糖尿病、腎功能不好，血糖控制不好。 |
| E | Exaggerating factors | 2 | pain on minimal stimulation | touch、movement、觸碰、移動 | 一摸就大叫。 |
| R | Relieving factors | 1 | no relief | none、無 | 無任何有效緩解。 |
| A | Accompanying symptoms | 3 | altered mental + mottled skin + oliguria | altered mental、oliguria、cold extremities、意識改變、少尿、四肢冰冷 | 叫不太醒、尿很少、四肢冰冷。 |

## 學習目標

熟練 qSOFA / Sepsis-3 診斷與分層、辨識壞死性筋膜炎警示徵兆（hemorrhagic bullae、crepitus、pain-disproportion）、掌握敗血性休克的第一小時復甦（Hour-1 bundle）。

## 目標學員

NP 進階學員，訓練急重症多系統整合判斷（雙歷程理論系統一熟悉情境，進階典型）。

## 標籤

`infectious_disease` `sepsis` `necrotizing_fasciitis` `advanced`
