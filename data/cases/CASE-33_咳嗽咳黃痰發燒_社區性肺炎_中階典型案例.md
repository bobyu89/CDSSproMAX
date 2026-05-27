# CASE-33：咳嗽咳黃痰發燒 — 社區性肺炎（中階典型案例）

> **來源：理論示範案例（seed_cases_theory_examples.json）**

## 基本資訊

| 欄位 | 內容 |
|------|------|
| 案例編號 | CASE-33 |
| 症狀 ID | `cough` |
| 難度（心流理論分級） | 中級 (intermediate) |
| 類別 | 內科/呼吸/感染 |
| 案例類型（雙歷程理論） | 熟悉情境（系統一） |
| 狀態 | 正式案例 |

## 臨床情境

一位 68 歲女性退休教師，因咳嗽咳黃痰合併發燒 5 天至門診就醫。病人 5 天前開始感冒症狀（流鼻水、微咳），3 天前開始咳黃痰，咳嗽加劇，昨日起出現寒顫、高燒（自測耳溫 39.1°C）、左側胸痛（深呼吸或咳嗽時加劇），今早出現喘，平常走 30 分鐘沒問題，今天走 5 分鐘就喘。過去病史：高血壓（amlodipine 控制）、骨質疏鬆。否認糖尿病。30 年前有抽菸 10 年但已戒。未接種肺炎鏈球菌疫苗或流感疫苗。無近期住院或抗生素使用。無旅遊史。

## 標準答案

### 一、應評估系統

| 系統 | 重要性 | 理由 |
|------|--------|------|
| 呼吸系統 | core | 咳嗽、咳痰、胸痛與喘均為呼吸系統症狀，須完整聽診與評估氧合。 |
| 感染/全身系統 | core | 高燒、寒顫、黃痰指向細菌性感染，須評估 qSOFA / CURB-65 判斷嚴重度。 |
| 心血管系統 | important | 老人胸痛需鑑別心臟病因，同時評估是否有敗血性心肌損傷。 |
| 一般外觀與生命徵象 | important | 脫水、精神狀態改變為肺炎嚴重度指標。 |

### 二、身體評估項目

| 項目 | 預期結果 | 異常 | 關鍵 | 臨床意義 |
|------|---------|:----:|:----:|---------|
| 體溫測量 | BT 39.0°C | Y | Y | 高燒符合細菌性肺炎；≥ 39°C 增加菌血症風險。 |
| 呼吸速率與血氧 | RR 26 次/分, SpO2 92% (room air) | Y | Y | RR ≥ 22 為 qSOFA 陽性指標；SpO2 92% 提示低氧血症，可能需補充氧氣。 |
| 血壓與心率 | BP 118/70 mmHg, HR 108 bpm | Y | Y | 輕度心搏過速，血壓尚穩定；須警覺敗血性休克進展。 |
| 肺部聽診 | 左下肺野可聞及局部吸氣末濕囉音（crackles），右肺清晰，無哮鳴音 | Y | Y | 局部性濕囉音支持肺泡填充病變，典型肺炎表現。 |
| 肺部叩診 | 左下肺野輕度濁音（dullness） | Y | N | 叩診濁音支持肺實質化（consolidation）或合併少量胸水。 |
| 觸覺震顫 | 左下肺野觸覺震顫增強 | Y | N | 震顫增強支持實質化；若減弱則考慮胸水或氣胸。 |
| Egophony（羊音） | 左下肺野 E→A 變化陽性 | Y | N | Egophony 陽性為肺實質化敏感指標。 |
| 意識與認知評估 | 意識清醒，GCS E4V5M6，時地人定向正常 | N | Y | 意識狀態為 CURB-65 指標之一。 |
| 心臟聽診 | S1/S2 正常，無雜音，無 S3/S4 | N | N | 排除合併心臟病因。 |
| 脫水評估 | 口腔黏膜稍乾，皮膚 turgor 尚可 | Y | N | 輕度脫水，需補充水分。 |

### 三、鑑別診斷

| 排名 | 診斷 | 嚴重度 | Must-not-miss | 理由 |
|:----:|------|:------:|:------------:|------|
| 1 | 社區性肺炎 (Community-Acquired Pneumonia, CAP) | high | N | 典型三聯徵（發燒、咳嗽咳痰、胸痛）+ 局部濕囉音 + egophony 陽性，高度懷疑。CURB-65 初估：年齡 ≥ 65 = 1 分、RR ≥ 30? 未達、BP 穩定、意識正常、BUN 未知 → 至少 1 分，門診治療可評估。 |
| 2 | 急性支氣管炎 (Acute Bronchitis) | low | N | 常見上呼吸道後咳嗽原因，但通常無高燒、無局部濕囉音及實質化證據，此案例不支持。 |
| 3 | 肺栓塞 (Pulmonary Embolism) | critical | Y | 老年人突發呼吸困難合併胸痛須警覺。然此案例有明確感染表現與局部濕囉音，PE 可能性較低。可用 Wells score 輔助判斷。 |
| 4 | 肺結核 (Pulmonary Tuberculosis) | high | Y | 咳嗽 > 3 週、體重減輕、盜汗為典型，此案例時程 5 天較短、無盜汗，可能性較低。但台灣為流行區域須考量。 |
| 5 | 心衰竭急性惡化 (Acute Decompensated Heart Failure) | high | Y | 老人呼吸困難加劇須排除。然此案例無頸靜脈怒張、無下肢水腫、濕囉音為單側局部而非雙側，HF 可能性較低。 |

### 四、LQQOPERA 結構化問診標準

| 維度 | 名稱 | 權重 | 關鍵概念 | 雙語關鍵字 | 示例回答 |
|:---:|------|:----:|---------|-----------|---------|
| L | Location（位置） | 3 | left-sided chest localization | left chest、lower lobe、左胸、左側、左下肺 | 左邊胸口痛，特別是深呼吸的時候。 |
| Q | Quality（型態） | 3 | pleuritic sharp pain | pleuritic、sharp、stabbing、肋膜性、刺痛 | 像被刀刺一樣的刺痛，跟呼吸相關。 |
| Q2 | Quantity / time course | 2 | 5-day progressive course | 5 days、progressive、5 天、漸進惡化 | 5 天了，這 3 天越來越嚴重。 |
| O | Onset mode | 2 | gradual onset after URI | gradual、URI preceded、漸進、上呼吸道感染後 | 先是普通感冒，後來變成咳痰發燒。 |
| P | Precipitation factors | 2 | unvaccinated elderly | no vaccine、未接種疫苗、elderly | 沒打肺炎疫苗和流感疫苗。 |
| E | Exaggerating factors | 2 | deep breath and cough worsen pain | deep breath、cough、exertion、深呼吸、咳嗽、活動 | 深呼吸和咳嗽時痛加劇，走路也會喘。 |
| R | Relieving factors | 2 | shallow breathing helps | shallow breath、rest、淺呼吸、休息 | 淺呼吸比較好，休息時也比較不痛。 |
| A | Accompanying symptoms | 3 | productive cough + fever + chills + dyspnea | yellow sputum、fever、chills、dyspnea、黃痰、發燒、寒顫、喘 | 咳黃痰、高燒、寒顫、走幾步就喘。 |

## 學習目標

掌握肺炎典型臨床表現、練習 CURB-65 嚴重度評估、熟悉肺實質化的身體評估徵兆（crackles、egophony、fremitus、percussion）。

## 目標學員

NP 中階學員，鞏固呼吸系統評估技巧（雙歷程理論系統一熟悉情境，中階典型）。

## 標籤

`pulmonology` `pneumonia` `CAP` `intermediate`
