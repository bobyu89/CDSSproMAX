# Sub-Agent: roles-access — 角色權限系統

> **權重:基礎設施層(橫跨全系統的存取控制)。**
> 三種角色:學員 / 審核者 / 管理者。一帳號一角色。權限最小化。

---

## 版本控管

| 欄位 | 內容 |
|------|------|
| 模組名稱 | roles-access |
| 模組版本 | v1.0 |
| 契約版本 | contract-v1.0 |
| 最後更新 | 2026-05-29 |
| 相依模組 | core、persistence |
| 被依賴模組 | 所有需要存取控制的端點 |

> GitHub 路徑:`ticdss/auth/`。Notion:「TICDSS / roles-access / v1.0」。

---

## 三種角色

| 角色 | 職責 | 設計考量 |
|------|------|---------|
| 學員 Student | 訓練、看自己的成績與成長 | 系統主要使用者 |
| 審核者 Reviewer | 只審核案例(draft→approved) | 權限極窄,碰不到任何學生隱私 |
| 管理者 Admin | 管系統、管帳號、看去識別化研究資料 | 看研究層,非學員可識別資料 |

> 一帳號一角色,不允許多重角色(系統乾淨好維護)。
> 測試時多開帳號(admin/student/reviewer 各一)。
> **教師角色不做**——「只看自己班」價值不足以獨立成角色;
> 未來需要再擴充,角色系統可擴充。

---

## 權限矩陣

| 權限 | 學員 | 審核者 | 管理者 |
|------|:---:|:---:|:---:|
| 進行訓練 | ✅ | — | — |
| 看自己的成績/卡片/歷程 | ✅ | — | — |
| 審核案例(draft→approved/rejected) | — | ✅ | ✅ |
| 看待審佇列 | — | ✅ | ✅ |
| 管理帳號(建立/停用/改角色) | — | — | ✅ |
| 看去識別化研究資料 | — | — | ✅ |
| 系統設定(成本上限、保留期等) | — | — | ✅ |
| 看案例庫統計 | — | ✅(限案例) | ✅ |

關鍵設計:
- **審核者權限極窄**:只碰案例審核,碰不到學生隱私。臨床專家可來審案例,
  不需也不該能看所有人資料。權限最小化。
- **管理者看去識別化**:研究資料來自 persistence 的 research_sessions 視圖
  (md5 去識別化),管理者看不到學員姓名/email。
- **學員只看自己**:嚴格限縮在自己的 student_id。

---

## 產出檔案

### 1. `auth/roles.py` — 角色與權限定義

```python
"""
角色權限定義
============
三種角色 + 權限列舉。一帳號一角色。
(TEACHER 不實作,未來擴充時於此新增即可。)
"""

from enum import Enum


class Role(str, Enum):
    STUDENT  = "student"
    REVIEWER = "reviewer"
    ADMIN    = "admin"
    # TEACHER = "teacher"   # 未來擴充位,目前不做


class Permission(str, Enum):
    DO_TRAINING       = "do_training"
    VIEW_OWN_DATA     = "view_own_data"
    REVIEW_CASES      = "review_cases"
    VIEW_REVIEW_QUEUE = "view_review_queue"
    MANAGE_ACCOUNTS   = "manage_accounts"
    VIEW_RESEARCH     = "view_research"
    SYSTEM_SETTINGS   = "system_settings"
    VIEW_CASE_STATS   = "view_case_stats"


# 角色 → 權限集合
ROLE_PERMISSIONS = {
    Role.STUDENT: {
        Permission.DO_TRAINING,
        Permission.VIEW_OWN_DATA,
    },
    Role.REVIEWER: {
        Permission.REVIEW_CASES,
        Permission.VIEW_REVIEW_QUEUE,
        Permission.VIEW_CASE_STATS,
    },
    Role.ADMIN: {
        Permission.REVIEW_CASES,
        Permission.VIEW_REVIEW_QUEUE,
        Permission.MANAGE_ACCOUNTS,
        Permission.VIEW_RESEARCH,
        Permission.SYSTEM_SETTINGS,
        Permission.VIEW_CASE_STATS,
    },
}


def has_permission(role: Role, perm: Permission) -> bool:
    return perm in ROLE_PERMISSIONS.get(role, set())
```

### 2. `auth/guard.py` — 權限檢查

```python
"""
權限檢查
========
端點呼叫前檢查角色是否有權限。學員額外限縮在自己的資料。
"""

from auth.roles import Role, Permission, has_permission


class AccessDenied(Exception):
    pass


def require(user, perm: Permission):
    """檢查使用者角色是否有該權限,無則拒絕。"""
    if not has_permission(user.role, perm):
        raise AccessDenied(f"{user.role} 無權限:{perm}")


def require_own_data(user, target_student_id):
    """
    學員只能存取自己的資料。
    管理者看研究資料走另一條(去識別化),不經此檢查。
    """
    if user.role == Role.STUDENT and user.id != target_student_id:
        raise AccessDenied("學員只能存取自己的資料")
```

### 3. `auth/endpoints_map.py` — 各端點的權限需求

```python
"""
端點 → 所需權限對照(供 API 路由套用)。
"""

from auth.roles import Permission as P

ENDPOINT_PERMISSIONS = {
    # 學員端
    "POST /training/start":      P.DO_TRAINING,
    "GET  /me/results":          P.VIEW_OWN_DATA,
    "GET  /me/cards":            P.VIEW_OWN_DATA,
    "GET  /me/progress":         P.VIEW_OWN_DATA,
    # 審核者端
    "GET  /review/queue":        P.VIEW_REVIEW_QUEUE,
    "POST /review/approve":      P.REVIEW_CASES,
    "POST /review/reject":       P.REVIEW_CASES,
    # 管理者端
    "POST /admin/accounts":      P.MANAGE_ACCOUNTS,
    "GET  /admin/research":      P.VIEW_RESEARCH,
    "PUT  /admin/settings":      P.SYSTEM_SETTINGS,
}
```

---

## 資料表(接 persistence)

```sql
-- 在 students 表外,統一帳號表(三種角色共用)
CREATE TABLE accounts (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email       TEXT UNIQUE NOT NULL,
    role        TEXT NOT NULL,        -- student/reviewer/admin
    name        TEXT,                 -- 可識別,依角色與隱私規則存取
    active      BOOLEAN DEFAULT true,
    created_at  TIMESTAMPTZ DEFAULT now()
);

-- 學員的訓練資料仍以 student_id 關聯(= accounts.id 當 role=student)
-- 審核者的審核紀錄
CREATE TABLE review_logs (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    reviewer_id UUID REFERENCES accounts(id),
    scenario_id UUID REFERENCES scenarios(id),
    action      TEXT,                 -- approve/reject
    reason      TEXT,
    reviewed_at TIMESTAMPTZ DEFAULT now()
);
```

---

## 三種角色的介面範圍

```
學員模式
├── 開始訓練(選模式、主題、難度)
├── 訓練中互動(問診/身評/診斷)
└── 結果頁:Cornell 報告 + 雷達圖 + 卡片 + 成長歷程

審核者模式
├── 待審佇列(draft 案例列表)
├── 審單一案例(看 AI 自檢結果、內容)
└── 通過 / 退回(附理由)

管理者模式
├── 帳號管理(建立/停用/改角色)
├── 研究資料(去識別化的群體分析)
├── 系統設定(成本上限、訊號保留期)
└── 案例庫總覽(各狀態統計)
```

---

## 設計重點

- **權限最小化**:審核者只碰案例、學員只看自己、管理者看去識別化資料。
  每個角色只拿到完成職責所需的最小權限,降低隱私與安全風險。
- **一帳號一角色**:不允許多重角色,權限判斷單純(查一個角色的權限集),
  好維護。測試多開帳號即可。
- **接 persistence 雙層隱私**:管理者看 research_sessions 視圖(去識別化),
  學員看自己 student_id 的完整資料,審核者完全不碰學生資料。三者一致。
- **審核者 = case-generator 的專家**:case-generator 的 approve_case/
  reject_case 由審核者角色呼叫,審核紀錄存 review_logs。
- **教師可擴充**:Role 列舉留註解位,未來要做教師端,新增 TEACHER 與其
  權限集即可,不動現有三角色。

---

## 設計紀錄

| 日期 | 版本 | 變更 | 原因 |
|------|------|------|------|
| 2026-05-29 | v1.0 | 初版:三角色(學員/審核者/管理者)+ 權限矩陣 + 檢查 | 角色權限完整設計;教師不做(價值不足);一帳號一角色 |

---

## 驗證方式

1. 學員呼叫審核端點,確認 AccessDenied。
2. 學員存取他人 student_id,確認 require_own_data 拒絕。
3. 審核者呼叫 approve_case,確認通過且寫入 review_logs。
4. 審核者嘗試看研究資料,確認 AccessDenied(權限極窄)。
5. 管理者看研究資料,確認來自去識別化視圖,無姓名/email。
6. 確認新增 TEACHER 角色只需改 roles.py,不動既有檢查邏輯。
```
