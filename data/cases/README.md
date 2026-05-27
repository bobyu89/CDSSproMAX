# CDSS 標準化臨床案例總覽

本資料夾包含 AI 臨床決策學習系統的所有標準化 OSCE 案例。

> **三大理論實作說明**：請先參閱 [THEORIES_IN_CODE.md](THEORIES_IN_CODE.md)，了解心流、雙歷程、反脆弱三大理論如何潛移默化於系統之中。CASE-31 ~ CASE-36 為依三大理論設計之示範案例。

## 案例清單

### 正式案例（20 個）— 前測與後測使用

| 編號 | 檔案 | 主訴 | 難度 | 類別 | 來源 |
|:----:|------|------|:----:|------|:----:|
| 01 | [CASE-01](CASE-01_chest_pain_ACS.md) | 急性胸痛 — ACS | 中級 | 內科/心血管 | 種子案例 |
| 02 | [CASE-02](CASE-02_dyspnea_CHF_pneumonia.md) | 呼吸困難 — CHF+肺炎 | 高級 | 內科/心血管/呼吸 | 種子案例 |
| 03 | [CASE-03](CASE-03_fever_endocarditis.md) | 持續高燒 — IE | 高級 | 內科/感染/心血管 | 種子案例 |
| 04 | [CASE-04](CASE-04_abdominal_pain_appendicitis.md) | 急性腹痛 — 闌尾炎 | 初級 | 外科/消化 | LLM 生成 |
| 05 | [CASE-05](CASE-05_headache_SAH.md) | 劇烈頭痛 — SAH | 中級 | 內科/神經 | LLM 生成 |
| 06 | [CASE-06](CASE-06_leg_edema_nephrotic.md) | 下肢水腫 — 腎病症候群 | 中級 | 內科/腎臟 | LLM 生成 |
| 07 | [CASE-07](CASE-07_hemoptysis_lung_cancer.md) | 咳血 — 肺癌 | 高級 | 內科/呼吸/腫瘤 | LLM 生成 |
| 08 | [CASE-08](CASE-08_altered_consciousness_DKA.md) | 意識改變 — DKA | 高級 | 內科/代謝 | LLM 生成 |
| 12 | [CASE-12](CASE-12_palpitation_atrial_fibrillation.md) | 心悸 — 心房顫動 | 中級 | 內科/心血管 | LLM 生成 |
| 13 | [CASE-13](CASE-13_back_pain_hematuria_nephrolithiasis.md) | 背痛合併血尿 — 腎結石 | 初級 | 外科/泌尿 | LLM 生成 |
| 14 | [CASE-14](CASE-14_fever_skin_redness_cellulitis.md) | 發燒合併皮膚紅腫 — 蜂窩性組織炎 | 初級 | 外科/感染/皮膚 | LLM 生成 |
| 15 | [CASE-15](CASE-15_dysphagia_esophageal_cancer.md) | 漸進性吞嚥困難 — 食道癌 | 高級 | 外科/消化/腫瘤 | LLM 生成 |
| 16 | [CASE-16](CASE-16_polyuria_polydipsia_T2DM.md) | 多尿多渴體重減輕 — 新診斷 T2DM | 中級 | 內科/代謝/內分泌 | LLM 生成 |
| 17 | [CASE-17](CASE-17_seizure_epilepsy.md) | 抽搐 — 癲癇 | 高級 | 內科/神經 | LLM 生成 |
| 18 | [CASE-18](CASE-18_wheezing_asthma.md) | 呼吸喘合併哮鳴音 — 氣喘急性發作 | 中級 | 內科/呼吸 | LLM 生成 |
| 19 | [CASE-19](CASE-19_melena_upper_GI_bleeding.md) | 解黑色柏油便 — 上消化道出血 | 高級 | 內科/消化 | LLM 生成 |
| 20 | [CASE-20](CASE-20_neck_mass_lymphoma.md) | 頸部腫塊 — 淋巴瘤 | 中級 | 內科/血液/腫瘤 | LLM 生成 |
| 21 | [CASE-21](CASE-21_back_pain_cauda_equina.md) | 急性腰痛合併下肢無力 — 馬尾症候群 | 高級 | 外科/神經/骨科 | LLM 生成 |
| 22 | [CASE-22](CASE-22_fever_dysuria_pyelonephritis.md) | 發燒合併頻尿灼熱 — 急性腎盂腎炎 | 初級 | 內科/泌尿/感染 | LLM 生成 |
| 23 | [CASE-23](CASE-23_edema_nephrotic_syndrome.md) | 全身水腫加劇合併泡沫尿 — 腎病症候群急性惡化 | 中級 | 內科/腎臟 | LLM 生成 |

### 理論示範案例（6 個）— 雙歷程／心流／反脆弱三大理論對照

> 來源：[data/seed_cases_theory_examples.json](../data/seed_cases_theory_examples.json)
> 設計矩陣：2 × 3（case_type × difficulty），每個組合 1 個案例，供專家審查三大理論之信效度。

| 編號 | 檔案 | 主訴 | 難度 | 類型（雙歷程） | 偏誤 | 對應診斷 |
|:----:|------|------|:----:|:----:|:----:|------|
| 31 | [CASE-31](CASE-31_急性喉嚨痛發燒_鏈球菌性咽炎_初階典型案例.md) | 喉嚨痛發燒 | 初階 | typical | — | 鏈球菌性咽炎 |
| 32 | [CASE-32](CASE-32_單側劇烈喉嚨痛_看似扁桃腺炎的扁桃腺周圍膿瘍_初階陷阱案例.md) | 單側喉嚨痛惡化 | 初階 | atypical_trap | anchoring | 扁桃腺周圍膿瘍 |
| 33 | [CASE-33](CASE-33_咳嗽咳黃痰發燒_社區性肺炎_中階典型案例.md) | 咳嗽咳痰發燒 | 中階 | typical | — | 社區性肺炎 |
| 34 | [CASE-34](CASE-34_年輕女性反覆胸痛_看似焦慮症的_Prinzmetal_變異性心絞痛_中階陷阱案例.md) | 年輕女性夜間胸痛 | 中階 | atypical_trap | confirmation | Prinzmetal 變異性心絞痛 |
| 35 | [CASE-35](CASE-35_高燒合併低血壓意識改變_敗血性休克_進階典型案例.md) | 高燒+意識改變 | 進階 | typical | — | 敗血性休克合併壞死性筋膜炎 |
| 36 | [CASE-36](CASE-36_老年意識改變_看似_UTI_譫妄的後循環中風_進階陷阱案例.md) | 老年意識改變 | 進階 | atypical_trap | anchoring | 後循環中風 |

### 保留案例（10 個）— 僅用於後測

| 編號 | 檔案 | 主訴 | 難度 | 類別 | 來源 |
|:----:|------|------|:----:|------|:----:|
| 09 | [CASE-09](CASE-09_jaundice_cholangitis_WITHHELD.md) | 黃疸 — 急性膽管炎 | 中級 | 內科/消化/肝膽 | LLM 生成 |
| 10 | [CASE-10](CASE-10_joint_pain_gout_WITHHELD.md) | 關節痛 — 痛風 | 中級 | 內科/風濕/代謝 | LLM 生成 |
| 11 | [CASE-11](CASE-11_nausea_vomiting_pancreatitis_WITHHELD.md) | 噁心嘔吐 — 胰臟炎 | 中級 | 內科/消化/代謝 | LLM 生成 |
| 24 | [CASE-24](CASE-24_purpura_ITP_WITHHELD.md) | 胸悶合併皮膚紫斑 — ITP | 中級 | 內科/血液 | LLM 生成 |
| 25 | [CASE-25](CASE-25_fever_joint_SLE_WITHHELD.md) | 發燒合併關節痛及蝴蝶斑 — SLE | 高級 | 內科/風濕/免疫 | LLM 生成 |
| 26 | [CASE-26](CASE-26_hemiparesis_stroke_WITHHELD.md) | 突發單側肢體無力 — 急性腦中風 | 高級 | 內科/神經 | LLM 生成 |
| 27 | [CASE-27](CASE-27_ascites_liver_cirrhosis_WITHHELD.md) | 腹脹合併移動性濁音 — 肝硬化腹水 | 中級 | 內科/消化/肝膽 | LLM 生成 |
| 28 | [CASE-28](CASE-28_chest_pain_pneumothorax_WITHHELD.md) | 突發胸痛合併呼吸困難 — 自發性氣胸 | 中級 | 外科/呼吸 | LLM 生成 |
| 29 | [CASE-29](CASE-29_fever_meningitis_WITHHELD.md) | 高燒合併頸部僵硬 — 細菌性腦膜炎 | 高級 | 內科/感染/神經 | LLM 生成 |
| 30 | [CASE-30](CASE-30_goiter_Graves_WITHHELD.md) | 甲狀腺腫大合併心悸手抖 — Graves 病 | 中級 | 內科/內分泌 | LLM 生成 |

## 難度分布

| 難度 | 數量 | 案例 |
|------|:----:|------|
| 初級 (beginner) | 4 | CASE-04, 13, 14, 22 |
| 中級 (intermediate) | 14 | CASE-01, 05, 06, 09, 10, 11, 12, 16, 18, 20, 23, 24, 27, 28, 30 |
| 高級 (advanced) | 12 | CASE-02, 03, 07, 08, 15, 17, 19, 21, 25, 26, 29 |

## 科別分布

| 科別方向 | 數量 | 案例 |
|---------|:----:|------|
| 內科為主 | 22 | CASE-01, 02, 03, 05, 06, 07, 08, 09, 10, 11, 12, 16, 17, 18, 19, 20, 22, 23, 24, 25, 26, 27, 29, 30 |
| 外科為主 | 6 | CASE-04, 13, 14, 15, 21, 28 |

## 標記說明

- **來源**欄位標示「種子案例」表示來自原始 `seed_cases.json`，「LLM 生成」表示由 Claude 根據臨床知識生成
- **保留案例 (withheld)** 於前測期間完全封存，受試者從未接觸，後測才開放
- **類別**欄位以「內科/」或「外科/」前綴標示科別方向
- 所有案例均需經臨床專家審核後定稿
