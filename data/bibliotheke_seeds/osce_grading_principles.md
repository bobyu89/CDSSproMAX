# OSCE 評分原則

OSCE（Objective Structured Clinical Examination）評分強調可觀察、可量化、可重複的標準。評分者應依預先設定的 rubric 評估每個項目，避免主觀印象式評分（Harden et al., 1975；Boursicot et al., 2011）。

評分者間信度（interrater reliability）是 OSCE 心理計量品質的核心。研究顯示即使受過訓練的評分者，個體判斷仍可解釋 16.8%-32.8% 的分數變異（Bouzid et al., 2022）。這是 DUAT 多代理人評分架構設計的學術動機。

LQQOPERA 評分的關鍵原則：每個維度獨立評估，避免暈輪效應（halo effect）。學員在 Location 表現優秀不應影響 Quality 的評分。每個維度需逐條對照 rubric criteria 找最符合的層級。

評分證據必須可追溯：每個給分都應能引用學員話語中的具體片段作為依據。「印象」、「感覺」、「我覺得」不構成合理評分理由。E-Agent 萃取的 Evidence Bundle 即為此目的設計。

對抗審查（adversarial review）的價值：第二個獨立評估者對同一份證據提出不同詮釋，能揭露原始評分者未察覺的盲點。A-Agent 在 DUAT 中扮演此角色（Du et al., 2023；Yuan et al., 2026）。

人工最終裁決原則：所有 AI 評分結果均為建議性質，最終分數由人類評分者裁決並對結果負責（human-in-the-loop, Kubota et al., 2026）。Consensus Arbiter 的「force_human」決策即為此設計。

過度寬鬆偏誤（leniency bias）是 LLM 評分者的已知問題（Zheng et al., 2023）：LLM 傾向給予偏高評分而難以區分優秀與及格。評分者應特別警惕學員問診不充分時的給分是否仍然偏高。
