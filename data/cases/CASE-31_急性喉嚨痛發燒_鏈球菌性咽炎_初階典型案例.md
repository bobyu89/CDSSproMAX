# CASE-31：急性喉嚨痛發燒 — 鏈球菌性咽炎（初階典型案例）

> **來源：理論示範案例（seed_cases_theory_examples.json）**

## 基本資訊

| 欄位 | 內容 |
|------|------|
| 案例編號 | CASE-31 |
| 症狀 ID | `sore_throat` |
| 難度（心流理論分級） | 初級 (basic) |
| 類別 | 內科/感染/耳鼻喉 |
| 案例類型（雙歷程理論） | 熟悉情境（系統一） |
| 狀態 | 正式案例 |

## 臨床情境

一位 22 歲男性大學生，因發燒合併喉嚨痛 2 天至診所就醫。病人主訴前天傍晚開始出現喉嚨刺痛感，伴隨吞嚥時明顯加劇，昨日起出現發燒（自測耳溫 38.5°C）、頭痛、倦怠。否認咳嗽、流鼻水。與室友共住，室友上週也有類似症狀且被診斷為鏈球菌性咽炎。過去病史無特殊，無藥物過敏，無抽菸、飲酒。

## 標準答案

### 一、應評估系統

| 系統 | 重要性 | 理由 |
|------|--------|------|
| 耳鼻喉系統 | core | 喉嚨痛為上呼吸道感染最直接的定位線索，需視診評估咽部與扁桃腺。 |
| 感染/全身系統 | core | 發燒提示全身性感染反應，須評估嚴重度與可能病原。 |
| 淋巴系統 | important | 頸部淋巴結腫大有助於鑑別細菌性或病毒性感染。 |
| 呼吸系統 | optional | 排除下呼吸道感染合併症，但此案例以咽部症狀為主。 |

### 二、身體評估項目

| 項目 | 預期結果 | 異常 | 關鍵 | 臨床意義 |
|------|---------|:----:|:----:|---------|
| 體溫測量 | BT 38.6°C（耳溫） | Y | Y | 中度發燒，支持細菌性感染可能。Centor criteria 計分之一。 |
| 咽喉視診 | 雙側扁桃腺紅腫對稱，扁桃腺上可見白色膿性滲出物（exudate），懸壅垂位置居中 | Y | Y | 對稱性扁桃腺滲出物為鏈球菌性咽炎典型表現，Centor criteria 計分之一。 |
| 頸部淋巴結觸診 | 雙側前頸淋巴結可觸及數個約 1-1.5 cm 腫大淋巴結，壓痛明顯 | Y | Y | 前頸淋巴結腫痛為 Centor criteria 計分之一，支持細菌性感染。 |
| 咳嗽評估 | 病人否認咳嗽 | N | Y | 無咳嗽為 Centor criteria 計分之一，有助於鑑別病毒性感染。 |
| 耳鏡檢查 | 雙側耳膜正常，無紅腫或滲出 | N | N | 排除中耳炎合併症。 |
| 肺部聽診 | 雙側呼吸音清晰，無囉音或哮鳴音 | N | N | 排除下呼吸道感染。 |
| 頸部僵硬度評估 | 頸部可自由轉動，無 Kernig's sign 或 Brudzinski's sign | N | Y | 排除腦膜炎。發燒頭痛時必做。 |

### 三、鑑別診斷

| 排名 | 診斷 | 嚴重度 | Must-not-miss | 理由 |
|:----:|------|:------:|:------------:|------|
| 1 | 鏈球菌性咽炎 (Group A Streptococcal Pharyngitis) | moderate | N | Centor criteria 滿足 4 項（發燒、無咳嗽、扁桃腺滲出物、前頸淋巴結腫大），加上接觸史，臨床高度懷疑。建議 rapid antigen test 或咽喉培養確診。 |
| 2 | 病毒性咽炎 (Viral Pharyngitis) | low | N | 為最常見的喉嚨痛原因，但此案例 Centor 4 分支持細菌性可能性較高。 |
| 3 | 傳染性單核球增多症 (Infectious Mononucleosis) | moderate | N | EBV 感染可類似表現，但典型有後頸淋巴結腫大及脾腫大，此案例無此特徵。若抗生素治療無效需考慮。 |
| 4 | 扁桃腺周圍膿瘍 (Peritonsillar Abscess) | high | Y | 需排除之併發症。典型有單側嚴重疼痛、懸壅垂偏移、含糊言語（hot potato voice），此案例雙側對稱不支持。 |

### 四、LQQOPERA 結構化問診標準

| 維度 | 名稱 | 權重 | 關鍵概念 | 雙語關鍵字 | 示例回答 |
|:---:|------|:----:|---------|-----------|---------|
| L | Location（位置） | 3 | bilateral pharyngeal pain | throat、pharynx、tonsil、喉嚨、咽部、扁桃腺 | 喉嚨深處兩側疼痛，吞嚥時最明顯。 |
| Q | Quality（型態） | 3 | sharp sore throat on swallowing | sore、sharp、scratchy、burning、刺痛、灼熱、刮痛 | 像被刮到一樣的刺痛感，吞口水會加劇。 |
| Q2 | Quantity / time course | 2 | 2-day progression | 2 days、progressive、2 天、漸進 | 2 天前開始，一天比一天嚴重。 |
| O | Onset mode（起病狀態） | 3 | acute onset | sudden、acute、突然、急性 | 前天傍晚突然開始喉嚨不舒服。 |
| P | Precipitation factors | 2 | close contact exposure | contact、roommate、exposure、接觸史、室友 | 室友上週被診斷為鏈球菌咽炎。 |
| E | Exaggerating factors | 1 | pain worsens with swallowing | swallow、drink、吞嚥、喝水 | 吞口水或喝水時最痛。 |
| R | Relieving factors | 2 | limited relief | none、painkiller、warm、無、止痛、溫 | 吃了 acetaminophen 稍微好一點。 |
| A | Accompanying symptoms | 2 | fever + malaise, no cough | fever、headache、fatigue、no cough、發燒、頭痛、倦怠、無咳嗽 | 有發燒、頭痛、倦怠，沒有咳嗽或流鼻水。 |

## 學習目標

掌握 Centor criteria 評估、區分細菌性與病毒性咽炎、識別典型鏈球菌咽炎的病史與身體評估表現。

## 目標學員

NP 初階學員，建立模式識別（雙歷程理論系統一熟悉情境）。

## 標籤

`ent` `pharyngitis` `strep_throat` `basic`
