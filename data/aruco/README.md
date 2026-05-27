# ArUco 標籤系統

半身假人上貼附 15 個 ArUco 標籤，攝影機透過 `DICT_4X4_50` 字典偵測。

## 對應表

| ArUco ID | 解剖位置 (region) | 標籤 | 貼附位置 |
|---------:|------------------|------|----------|
| 1  | pmi              | 心尖搏動點   | 左鎖骨中線 × 第五肋間 |
| 2  | aortic_area      | 主動脈瓣區   | 右胸骨第二肋間 |
| 3  | pulmonic_area    | 肺動脈瓣區   | 左胸骨第二肋間 |
| 4  | erbs_point       | Erb's point  | 左胸骨第三肋間 |
| 5  | tricuspid_area   | 三尖瓣區     | 左胸骨下緣（劍突旁） |
| 6  | jvp              | 頸靜脈壓     | 右側胸鎖乳突肌中段 |
| 7  | carotid_right    | 右頸動脈     | 右胸鎖乳突肌前緣 |
| 8  | carotid_left     | 左頸動脈     | 左胸鎖乳突肌前緣 |
| 9  | right_upper_lung | 右上肺葉     | 右鎖骨下方第二肋間 |
| 10 | left_upper_lung  | 左上肺葉     | 左鎖骨下方第二肋間 |
| 11 | right_lower_lung | 右下肺葉     | 右側第八肋間腋中線 |
| 12 | left_lower_lung  | 左下肺葉     | 左側第八肋間腋中線 |
| 13 | abdomen_ruq      | 腹部右上象限 | 肋緣下右鎖骨中線 |
| 14 | abdomen_luq      | 腹部左上象限 | 肋緣下左鎖骨中線 |
| 15 | abdomen_rlq      | 腹部右下象限 | McBurney point |
| 16 | abdomen_llq      | 腹部左下象限 | 左下腹 |

對應表是程式碼裡定義的（不是查表）：`apps/api/src/vision/anatomy_map.py`。

## 列印步驟

1. 安裝依賴（如尚未安裝）：
   ```bash
   cd apps/api
   uv pip install opencv-python reportlab
   ```

2. 產生 PDF：
   ```bash
   uv run python ../../scripts/generate_aruco_pdf.py \
       --out ../../data/aruco/anatomy_markers.pdf
   ```

3. 用 A4 紙列印（**1:1 比例，不要縮放**）。每個 marker 約 5×5 cm。

4. 剪下後依「貼附位置」欄貼到半身假人上。

## 偵測原理

- 攝影機每 0.5 秒（預設）擷取一張 frame
- OpenCV `cv2.aruco.detectMarkers` 找出畫面中可見的標籤 ID
- 後端 `marker_tracker` 紀錄每個 marker 最後被看到的時間戳
- 若某 marker 連續 **1.5 秒** 沒被偵測到 → 視為該位置被學員「觸碰」
- V-Agent 進一步用 Gemini Vision 判斷觸碰時的「動作品質」

## 校準

如果要改 `aruco_id ↔ region` 對應，只改 `anatomy_map.py`，前端會透過
`GET /vision/anatomy-map` 自動取得最新對應表。

`occlusion_threshold_s = 1.5` 可在 `apps/api/src/routers/vision.py` 調整。

## 目前狀態

- ✅ 對應表已定義（15 個 marker）
- ✅ 後端偵測程式（lazy OpenCV）
- ✅ 前端 CameraCapture + MarkerOverlay 元件
- 🚧 V-Agent 為 stub（待接 Gemini 3.5 Flash Vision multimodal API）
- 🚧 與 DUAT pipeline 的整合（V-Agent 結果寫入 duat_scores）
- ⏳ 校準工具（後台調整 marker → region 映射）
