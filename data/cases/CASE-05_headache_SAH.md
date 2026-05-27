# CASE-05：劇烈頭痛 — 蜘蛛膜下腔出血疑似案例

> **來源：LLM 生成案例**

## 基本資訊

| 欄位 | 內容 |
|------|------|
| 案例編號 | CASE-05 |
| 症狀 ID | headache |
| 難度 | intermediate（中級） |
| 類別 | 神經 |
| 類型 | **正式案例** |
| 案例類型（雙歷程理論） | 熟悉情境（系統一）— typical |

## 臨床情境

一位 45 歲女性，會計師，因突發性劇烈頭痛至急診就醫。病人主訴約 3 小時前在辦公室工作時，突然感到「這輩子最嚴重的頭痛」（thunderclap headache），疼痛自後枕部開始，迅速擴展至整個頭部，疼痛程度 10/10。伴隨噁心及一次嘔吐，頸部僵硬感，畏光。否認外傷史。到院時意識清楚但極度不適。過去病史：偏頭痛病史（約每月 1-2 次，通常為單側搏動性頭痛，此次型態完全不同），高血壓（服用 losartan 50mg QD，控制尚可），無抽菸。家族史：母親 50 歲時因腦出血過世。

## 標準答案

### 一、應評估系統

| 系統 | 重要性 | 理由 |
|------|--------|------|
| 神經系統 | core | 突發性劇烈頭痛（thunderclap headache）為神經科急症，需優先排除蜘蛛膜下腔出血（SAH）、腦出血等致命性疾病。 |
| 心血管系統 | important | 高血壓為出血性腦血管疾病的危險因子，需評估血壓控制狀況及血流動力學。 |
| 感染科 | important | 頸部僵硬需鑑別腦膜炎，但本案例為突發性而非漸進性發作。 |
| 眼科 | optional | 畏光及視乳頭水腫評估，可輔助判斷顱內壓升高。 |

### 二、身體評估項目

| 項目 ID | 項目名稱 | 預期結果 | 異常 | 關鍵 | 臨床意義 |
|---------|---------|---------|:----:|:----:|---------|
| vs_bp | 血壓測量 | BP 178/102 mmHg | Y | Y | 血壓明顯升高，可能為 SAH 導致的交感神經風暴或原有高血壓控制不佳。 |
| vs_hr | 心率/脈搏 | HR 88 bpm，regular rhythm | Y | N | 輕度心搏過速，疼痛及焦慮所致。 |
| vs_temp | 體溫 | BT 36.8°C | N | N | 體溫正常，不支持感染性病因。 |
| ga_consciousness | 意識狀態 | GCS 14/15（E4V4M6），自發性睜眼，言語略混亂，可遵從指令 | Y | Y | GCS 14 分，輕度意識障礙。Hunt-Hess Grade II。 |
| neuro_cranial | 腦神經檢查 | 瞳孔等大等圓 3mm，光反射靈敏。第 III 對腦神經功能正常。無顏面不對稱。 | N | Y | 瞳孔正常排除動眼神經壓迫（後交通動脈瘤破裂常見表現），但不能完全排除 SAH。 |
| neck_rom | 頸部活動度 | 頸部僵硬（nuchal rigidity），被動屈頸時明顯抗拒，Kernig's sign (+)，Brudzinski's sign (+) | Y | Y | 腦膜刺激徵（meningeal signs）陽性，強烈提示蜘蛛膜下腔出血或腦膜炎。 |
| neuro_motor | 運動功能 | 四肢肌力 5/5，無明顯偏癱 | N | Y | 無局灶性神經學缺損，排除大範圍腦實質出血或梗塞。 |
| neuro_reflex | 深層腱反射 | 雙側對稱，2+/4+ | N | N | 反射正常，無上運動神經元病變證據。 |
| heent_eye | 眼睛檢查 | 畏光明顯，眼底鏡：左眼視網膜前出血（subhyaloid hemorrhage）| Y | Y | 視網膜前出血（Terson syndrome）見於 SAH 患者，因顱內壓突然升高導致。高度支持 SAH 診斷。 |
| neuro_mental | 精神狀態評估 | 焦慮、煩躁，注意力下降，定向力完整 | Y | N | 精神狀態改變可能為疼痛反應或早期腦功能受損表現。 |

### 三、鑑別診斷

| 排名 | 診斷 | 嚴重度 | Must-not-miss | 理由 |
|:----:|------|:------:|:------------:|------|
| 1 | 蜘蛛膜下腔出血 (Subarachnoid Hemorrhage, SAH) | critical | Y | Thunderclap headache（此生最嚴重頭痛）、腦膜刺激徵陽性、視網膜前出血、家族史（母親腦出血），臨床高度懷疑動脈瘤破裂導致 SAH。需緊急 CT 確認。 |
| 2 | 腦膜炎 (Meningitis) | critical | Y | 頭痛 + 頸部僵硬 + Kernig's/Brudzinski's sign 陽性。但本案例為突發性（數秒內達峰）而非漸進性，且無發燒，腦膜炎可能性較低，但仍需排除。 |
| 3 | 腦出血 (Intracerebral Hemorrhage) | critical | Y | 高血壓患者突發劇烈頭痛需考慮高血壓性腦出血。但無明顯局灶性神經學缺損，腦實質出血可能性較 SAH 低。 |
| 4 | 偏頭痛急性發作 (Severe Migraine) | moderate | N | 病人有偏頭痛病史，但此次型態完全不同（突發、全頭、伴腦膜刺激徵），「first or worst headache」原則下不可僅以偏頭痛解釋。 |
| 5 | 腦靜脈竇栓塞 (Cerebral Venous Sinus Thrombosis, CVST) | high | N | 可表現為劇烈頭痛伴顱內壓升高，好發於年輕女性。通常為漸進性，但急性發作亦有報告。需 CT venography 排除。 |

## 學習目標

學習突發性劇烈頭痛（thunderclap headache）的系統性鑑別診斷，掌握蜘蛛膜下腔出血的臨床特徵與 Hunt-Hess 分級，理解「first or worst headache」的臨床處理原則，熟悉腦膜刺激徵的檢查方法。

## 標籤

`neurology` `emergency` `SAH` `thunderclap_headache`
