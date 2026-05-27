# CASE-26：突發單側肢體無力 — 急性缺血性腦中風案例【保留案例】

> **來源：LLM 生成案例**
> **本案例為保留案例（withheld），僅用於後測，前測期間完全封存。**

## 基本資訊

| 欄位 | 內容 |
|------|------|
| 案例編號 | CASE-26 |
| 症狀 ID | acute_hemiparesis |
| 難度 | advanced（高級） |
| 類別 | 內科/神經 |
| 類型 | **保留案例 (withheld)** |
| 案例類型（雙歷程理論） | 熟悉情境（系統一）— typical |

## 臨床情境

一位 72 歲男性，退休教師，由太太撥打 119 送至急診。太太描述今晨 7:00 發現先生起床時右側肢體無力，無法自行站立，說話口齒不清且語句不完整。昨晚 23:00 就寢時一切正常（last known well time: 23:00）。過去病史：心房顫動（atrial fibrillation）診斷 3 年，醫師開立 warfarin 但病人自述常忘記服藥或自行停藥；高血壓（amlodipine 5 mg QD）；第二型糖尿病（metformin 500 mg BID）。菸史 40 年（每日一包），5 年前戒菸。飲酒偶爾。家族史：父親曾中風。

## 標準答案

### 一、應評估系統

| 系統 | 重要性 | 理由 |
|------|--------|------|
| 神經系統 | core | 突發單側肢體無力合併言語障礙，高度懷疑急性腦中風，需立即執行 NIHSS 評估嚴重度及決定治療策略。 |
| 心血管系統 | core | AF 病史未規則抗凝血為心源性栓塞之高危因子，需評估心律及血流動力學穩定性。 |
| 呼吸系統 | important | 需評估呼吸道保護能力（GCS、吞嚥功能），嚴重中風可能影響呼吸中樞。 |
| 代謝/內分泌系統 | important | 低血糖可模擬中風表現（stroke mimic），糖尿病患者需立即檢測血糖。 |

### 二、身體評估項目

| 項目 ID | 項目名稱 | 預期結果 | 異常 | 關鍵 | 臨床意義 |
|---------|---------|---------|:----:|:----:|---------|
| neuro_gcs | 意識狀態 GCS | GCS E4V4M6 = 14/15（V4：語句混亂但可辨識詞彙） | Y | Y | 意識輕度受損，言語障礙明顯，提示左側大腦半球病變影響語言區。 |
| neuro_facial | 顏面神經 | 右側鼻唇溝變淺，右嘴角下垂，露齒時右側明顯不對稱（central facial palsy） | Y | Y | 中樞型顏面神經麻痺（上下臉不對稱），額紋保留，與周邊型 Bell's palsy 不同。為 NIHSS 評估項目。 |
| neuro_arm_drift | 上肢肌力/漂移 | 右上肢抬起後 10 秒內向下漂移並落至床面（NIHSS arm drift score 3），左上肢正常 | Y | Y | 右上肢嚴重無力，提示左側大腦中動脈（MCA）供血區梗塞。 |
| neuro_leg_drift | 下肢肌力/漂移 | 右下肢抬起後 5 秒內向下漂移但未落至床面（NIHSS leg drift score 2），左下肢正常 | Y | Y | 右下肢中度無力，與上肢無力合併為典型 MCA territory stroke 表現（上肢>下肢）。 |
| neuro_speech | 言語評估 | 言語不流利，可說出單字但組句困難，理解力部分保留（Broca's aphasia 特徵） | Y | Y | 運動性失語症（Broca's aphasia）提示左側額下回（Broca's area）受損。為 NIHSS 語言項目。 |
| neuro_gaze | 眼球運動/凝視 | 雙眼共軛偏向左側（conjugate gaze deviation to the left），可被動矯正 | Y | Y | 眼球偏向病灶同側為大面積大腦半球中風之重要徵兆（"eyes look at the lesion"）。 |
| vs_bp | 血壓測量 | BP 178/96 mmHg | Y | Y | 急性中風期血壓偏高為常見反應（Cushing response），靜脈溶栓前需控制 <185/110 mmHg。 |
| vs_hr | 心率/脈搏 | HR 88 bpm，irregularly irregular rhythm | Y | Y | 不規則脈搏證實心房顫動，為心源性栓塞之直接證據。CHA₂DS₂-VASc score 需重新評估。 |
| vs_spo2 | 血氧飽和度 | SpO2 95% (room air) | N | Y | 血氧尚可，但需持續監測。嚴重中風患者可能因意識障礙或吸入而導致低血氧。 |
| neuro_sensory | 感覺測試 | 右側肢體輕觸覺及針刺覺明顯減退，左側正常 | Y | N | 右側感覺減退與運動障礙一致，進一步支持左側大腦半球病變。 |

### 三、鑑別診斷

| 排名 | 診斷 | 嚴重度 | Must-not-miss | 理由 |
|:----:|------|:------:|:------------:|------|
| 1 | 急性缺血性腦中風 (Acute Ischemic Stroke) | critical | Y | 72 歲男性，AF 未規則抗凝血，突發右側肢體無力合併失語症及眼球偏向，病程符合急性中風。AF 為心源性栓塞之最常見原因。需緊急影像學確認並評估溶栓/取栓適應症。 |
| 2 | 出血性腦中風 (Hemorrhagic Stroke) | critical | Y | 高血壓病史患者突發神經學缺損，腦出血不能僅憑臨床排除。warfarin 使用（即使不規則）增加出血風險。需 CT 排除，因溶栓治療前必須排除出血。 |
| 3 | 暫時性腦缺血發作 (Transient Ischemic Attack, TIA) | high | Y | 若症狀在 24 小時內完全緩解則為 TIA，但目前症狀仍持續。TIA 為未來中風之強烈預測因子，即使緩解仍需積極處理。 |
| 4 | Todd's paralysis（癲癇後麻痺） | moderate | N | 癲癇發作後可出現暫時性局部神經缺損（Todd's paralysis），但通常有癲癇發作之目擊史。此案例無抽搐描述，可能性較低。 |
| 5 | 低血糖 (Hypoglycemia) | moderate | Y | 糖尿病使用 metformin 患者，低血糖可模擬中風表現（stroke mimic）。需立即檢測血糖。治療簡單但若遺漏可致腦損傷。 |

## 學習目標

學習急性腦中風之快速辨識與 NIHSS 評估要點，掌握中風急性期之時間窗概念（last known well time）與溶栓/取栓適應症，了解心房顫動與心源性栓塞之關係及 CHA₂DS₂-VASc 評分，熟悉 stroke mimics 之鑑別（低血糖、Todd's paralysis）。

## 標籤

`neurology` `stroke` `emergency` `atrial_fibrillation` `NIHSS`
