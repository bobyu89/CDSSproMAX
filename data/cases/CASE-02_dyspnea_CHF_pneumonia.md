# CASE-02：漸進性呼吸困難 — 心衰竭合併肺炎案例

> **來源：原始種子案例 (seed_cases.json)**

## 基本資訊

| 欄位 | 內容 |
|------|------|
| 案例編號 | CASE-02 |
| 症狀 ID | dyspnea |
| 難度 | advanced（高級） |
| 類別 | 心血管/呼吸 |
| 類型 | **正式案例** |
| 案例類型（雙歷程理論） | 熟悉情境（系統一）— typical |

## 臨床情境

一位 75 歲女性，退休教師，由家屬送至急診。主訴近一週呼吸越來越喘，尤其夜間無法平躺睡覺（需墊 3 個枕頭），昨晚更出現端坐呼吸（orthopnea）。同時有低度發燒（37.8°C）已 3 天，伴咳嗽及少量黃綠色痰液。過去病史：充血性心衰竭（CHF, EF 35%, 去年 echo 結果），心房顫動（服用 warfarin），高血壓，慢性腎臟病第三期。兩週前曾因感冒就醫，自行停服 furosemide 因擔心脫水。近三天雙腳腫脹加劇。

## 標準答案

### 一、應評估系統

| 系統 | 重要性 | 理由 |
|------|--------|------|
| 心血管系統 | core | 已知 CHF 病史，出現典型心衰竭急性惡化症狀（端坐呼吸、陣發性夜間呼吸困難、下肢水腫），且自行停藥為明確誘因。 |
| 呼吸系統 | core | 發燒伴黃綠色痰液提示可能合併肺炎，肺炎本身也可加重心衰竭。 |
| 腎臟系統 | important | CKD Stage III 患者停用 furosemide 後容量過負荷，需評估腎功能惡化。 |
| 感染科 | important | 低度發燒及咳痰提示感染性病因，需排除肺炎或其他感染源。 |

### 二、身體評估項目

| 項目 ID | 項目名稱 | 預期結果 | 異常 | 關鍵 | 臨床意義 |
|---------|---------|---------|:----:|:----:|---------|
| vs_bp | 血壓測量 | BP 148/92 mmHg | Y | Y | 血壓偏高，容量過負荷及交感神經活化。 |
| vs_hr | 心率/脈搏 | HR 112 bpm，irregularly irregular（心房顫動） | Y | Y | 心搏過速且不規則，快速心室率心房顫動，可加重心衰竭。 |
| vs_rr | 呼吸速率 | RR 28 次/分，使用輔助呼吸肌 | Y | Y | 明顯呼吸急促，提示呼吸功增加。 |
| vs_spo2 | 血氧飽和度 | SpO2 89% (room air)，給予鼻導管 O2 3L/min 後升至 93% | Y | Y | 低血氧，肺水腫及/或肺炎導致氣體交換障礙。 |
| vs_temp | 體溫 | BT 37.9°C (tympanic) | Y | N | 低度發燒，支持感染性病因。 |
| neck_jvp | 頸靜脈壓 | JVP 明顯升高（約 8 cm above sternal angle），45度時可見頸靜脈怒張 | Y | Y | JVP 升高為右心壓力升高的直接證據，支持心衰竭急性失代償。 |
| lung_auscultation | 肺部聽診 | 雙下肺野可聞及 bibasilar crackles（濕囉音），右下肺後段呼吸音減弱伴 bronchial breathing | Y | Y | 雙下肺 crackles 提示肺水腫；右下肺局部實質化改變提示肺炎。 |
| cv_auscultation | 心臟聽診 | Irregularly irregular rhythm，可聞及 S3 gallop，無明顯 murmur | Y | Y | S3 gallop 為容量過負荷的典型發現，支持失代償性心衰竭。 |
| ext_edema | 四肢水腫 | 雙下肢 3+ pitting edema 至小腿中段 | Y | Y | 嚴重下肢水腫為容量過負荷的體徵，與停用利尿劑相關。 |
| abd_palpation | 腹部觸診 | 肝臟觸診腫大（肋緣下 3 cm），有壓痛，hepatojugular reflux positive | Y | N | 肝臟鬱血為右心衰竭體徵，hepatojugular reflux 支持容量過負荷。 |

### 三、鑑別診斷

| 排名 | 診斷 | 嚴重度 | Must-not-miss | 理由 |
|:----:|------|:------:|:------------:|------|
| 1 | 急性失代償性心衰竭 (ADHF) | critical | Y | 已知 CHF (EF 35%)，自行停用 furosemide 為明確誘因。端坐呼吸、PND、JVP 升高、S3 gallop、雙下肢水腫 3+、肺部 crackles 均為典型表現。Killip Class III。 |
| 2 | 社區型肺炎 (CAP) | high | Y | 低度發燒 3 天、黃綠色痰液、右下肺實質化改變。肺炎可為心衰竭惡化的誘因，兩者可能同時存在。需 CXR 及血液培養確認。 |
| 3 | 肺栓塞 (Pulmonary Embolism) | critical | Y | 心房顫動、心衰竭、臥床活動減少均為 PE 風險因子。雖有其他更合理解釋，但仍不可完全排除。 |
| 4 | 急性腎損傷 (AKI) | high | N | CKD Stage III 基礎上，心衰竭惡化可導致腎前性 AKI（心腎症候群），需監測 BUN/Cr 變化。 |
| 5 | 肋膜積液 (Pleural Effusion) | moderate | N | 心衰竭常伴有肋膜積液，可加重呼吸困難。右下肺呼吸音減弱部分可能為積液而非僅肺炎。需 CXR 鑑別。 |

## 學習目標

學習心衰竭急性惡化的評估與處理，理解多重共病症的交互影響，掌握 Killip 分級與容量狀態評估。

## 標籤

`cardiology` `pulmonology` `heart_failure` `pneumonia`
