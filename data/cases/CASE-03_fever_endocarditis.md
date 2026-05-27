# CASE-03：持續高燒 — 感染性心內膜炎疑似案例

> **來源：原始種子案例 (seed_cases.json)**

## 基本資訊

| 欄位 | 內容 |
|------|------|
| 案例編號 | CASE-03 |
| 症狀 ID | fever |
| 難度 | advanced（高級） |
| 類別 | 感染科/心血管 |
| 類型 | **正式案例** |
| 案例類型（雙歷程理論） | 熟悉情境（系統一）— typical |

## 臨床情境

一位 38 歲男性，軟體工程師，因持續高燒 10 天至門診就醫。病人主訴約 10 天前開始出現畏寒、發燒（自量最高 39.5°C），伴隨夜間盜汗及全身倦怠。曾至診所就醫，使用口服抗生素（amoxicillin）5 天無明顯改善。近 3 天新出現活動時呼吸困難及關節痠痛。追問病史，病人 6 個月前曾因嚴重齲齒接受牙科拔牙手術。過去病史：兒時曾被告知有心雜音，但從未追蹤。否認靜脈注射藥物使用。無其他慢性病史。

## 標準答案

### 一、應評估系統

| 系統 | 重要性 | 理由 |
|------|--------|------|
| 感染科 | core | 持續高燒 10 天且抗生素無效，需考慮深層感染或非典型感染源。 |
| 心血管系統 | core | 兒時心雜音病史 + 近期牙科手術 + 持續發燒 + 新發呼吸困難 = 感染性心內膜炎高度懷疑。 |
| 免疫系統 | important | 需排除自體免疫疾病（如 SLE、成人 Still's disease）造成的不明原因發燒。 |
| 血液腫瘤 | important | 持續發燒伴盜汗需排除淋巴瘤等血液惡性疾病。 |
| 肌肉骨骼系統 | optional | 關節痠痛可能為免疫複合體沉積所致（感染性心內膜炎的免疫相關表現），或為獨立的感染性關節炎。 |

### 二、身體評估項目

| 項目 ID | 項目名稱 | 預期結果 | 異常 | 關鍵 | 臨床意義 |
|---------|---------|---------|:----:|:----:|---------|
| vs_temp | 體溫 | BT 38.8°C (oral) | Y | Y | 持續高燒為感染性心內膜炎的主要表現（Duke criteria major criteria）。 |
| vs_hr | 心率/脈搏 | HR 108 bpm，regular rhythm | Y | Y | 心搏過速，可能為發燒反應或心衰竭早期徵象。 |
| vs_bp | 血壓測量 | BP 118/72 mmHg | N | N | 血壓正常範圍，暫無血流動力學不穩定。 |
| cv_auscultation | 心臟聽診 | Mitral area 可聞及 grade III/VI holosystolic murmur（全收縮期雜音），放射至左腋下。病人表示過去被告知的雜音沒有這麼大聲。 | Y | Y | 新出現或惡化的心雜音為感染性心內膜炎 Duke criteria 的 major criterion。提示二尖瓣逆流（MR），可能因贅生物導致瓣膜功能障礙。 |
| heent_eye | 眼睛檢查 | 結膜蒼白（+），眼底鏡檢查：左眼可見一處 Roth spot（視網膜出血伴白色中心） | Y | Y | Roth spot 為感染性心內膜炎的經典眼底發現（免疫複合體沉積導致），雖非 Duke criteria 但高度支持診斷。結膜蒼白提示貧血。 |
| skin_inspection | 皮膚視診 | 左手中指指腹可見一處 Osler node（疼痛性紅色結節），雙手指甲下可見 splinter hemorrhage（線狀出血） | Y | Y | Osler node（免疫複合體沉積）和 splinter hemorrhage 為感染性心內膜炎的周邊血管表現，屬 Duke minor criteria。 |
| ga_general | 一般外觀 | 急性病容，面色蒼白，精神萎靡但意識清楚 | Y | N | 慢性消耗性病程表現。 |
| abd_palpation | 腹部觸診 | 脾臟可觸及（肋緣下 2 cm），輕度壓痛 | Y | N | 脾腫大可見於感染性心內膜炎（約 15-50% 患者），可能因感染或脾梗塞。 |
| ext_joint | 關節檢查 | 雙膝關節輕度腫脹及壓痛，活動度稍受限，無紅熱 | Y | N | 關節症狀可能為免疫複合體沉積所致的反應性關節炎。 |
| neck_lymph | 頸部淋巴結 | 雙側頸部可觸及數顆 <1 cm 淋巴結，質軟，可移動，無壓痛 | Y | N | 輕度淋巴結腫大，為非特異性免疫反應。需追蹤排除淋巴瘤。 |

### 三、鑑別診斷

| 排名 | 診斷 | 嚴重度 | Must-not-miss | 理由 |
|:----:|------|:------:|:------------:|------|
| 1 | 感染性心內膜炎 (Infective Endocarditis, IE) | critical | Y | 符合多項 Modified Duke Criteria：Major — 持續發燒 >38°C、新出現心雜音惡化；Minor — 易感因素（既有心雜音 + 牙科手術）、血管現象（splinter hemorrhage）、免疫現象（Osler node, Roth spot）、脾腫大。 |
| 2 | 淋巴瘤 (Lymphoma) | high | Y | 持續發燒、夜間盜汗、倦怠及淋巴結腫大為淋巴瘤典型 B symptoms。雖然臨床表現更傾向 IE，但需透過血液檢查及影像排除。 |
| 3 | 全身性紅斑狼瘡 (SLE) | moderate | N | 發燒、關節痛、心雜音（Libman-Sacks endocarditis）及血管病變在 SLE 中可見。但 SLE 好發於年輕女性，且此案例有明確感染源。 |
| 4 | 成人 Still's disease | moderate | N | 高燒、關節痛、Ferritin 可能極高。但通常有典型鮭魚色皮疹及咽喉痛，此案例不典型。 |
| 5 | 深部膿瘍 (Deep Abscess) | high | N | 口服抗生素無效的持續發燒需考慮深部膿瘍（肝膿瘍、脾膿瘍等），需影像學排除。 |

## 學習目標

學習 Modified Duke Criteria 的應用，掌握感染性心內膜炎的周邊血管表現（Osler node, Janeway lesion, splinter hemorrhage, Roth spot），理解不明原因發燒（FUO）的系統性鑑別診斷。

## 標籤

`infectious_disease` `cardiology` `endocarditis` `FUO`
