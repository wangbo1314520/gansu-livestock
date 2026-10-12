# GitHub 提交前安全审计报告

- 审计时间：2026-10-12
- 审计范围：`E:\Program\gansu-livestock`（10 个提交）、`E:\Program\gansu-home`（3 个提交）
- 审计方式：git 跟踪清单 / 全历史文件名+内容扫描 / 工作区明文扫描 / .gitignore 比对
- 报告中所有密码值已打码，不出现明文

---

## 一、工作区敏感文件清单（1.1）

两项目 `git ls-files` 按 密码/password/secret/token/key/env/家庭账号 过滤：

- gansu-livestock：**无匹配**
- gansu-home：**无匹配**

（家庭账号文件 `docs/家庭账号.md` 存在于 home 工作区，但**未被 git 跟踪**，且从未提交过历史。）

## 二、git 历史敏感信息清单（重点，1.2 + 深扫）

### 2.1 文件名层面

两项目全部历史的文件名过滤（家庭账号/password/secret/.env/key）：**无匹配**。

### 2.2 内容层面（git grep 全部提交）

**【高危】gansu-home：MySQL root 密码明文进入了全部历史**

| 文件 | 出现提交 | 内容 |
|---|---|---|
| `start.bat` 第 6 行 | `9744582`（init）、`e82cf66`、`da08f21`（共 2 个含此文件的提交） | `set DB_PASSWORD=【6 位数字，已打码】`（即本机 MySQL root 密码） |

工作区当前文件仍是明文。**该密码随历史一旦推送即公开。**

**【中危】admin/admin123 默认口令出现在历史内容**

gansu-livestock（10 个提交中反复出现，共 9 个文件）：
- 代码类：`backend/sql/init_data.sql`（建库脚本注释与数据）、`backend/tests/test_api.py`、`backend/tests/test_export.py`、`scripts/test_api_smoke.py`、`scripts/test_mape_all.py`（测试登录用）
- 文档类：`README.md`、`docs/开发计划.md`、`docs/数据库设计.md`、`docs/晨报.md`

gansu-home（3 个文件）：
- `backend/sql/init_base.sql`（注释）、`docs/交接清单.md`（账号表）

说明：admin123 是**初始化演示口令**（文档均注明"首次登录后必须修改"），非真实生产口令，但公开仓库中明文默认口令仍属应处理项。

**家庭账号密码（jiaren01/jiaren02 的口令）：未进入任何 git 历史** ✓

## 三、硬编码密码清单（工作区，1.3）

| 位置 | 内容 | 级别 |
|---|---|---|
| `gansu-home/start.bat:6` | `set DB_PASSWORD=【明文，已打码】`（root 密码） | 高 |
| `gansu-livestock/backend/config.py:32` | `JWT_SECRET = os.getenv("JWT_SECRET", "gansu-livestock-dev-secret")` 开发默认值 | 低 |
| `gansu-home/backend/config.py:31` | 同上（同一默认值） | 低 |
| 两项目 `backend/sql/init_*.sql`、测试脚本、部分文档 | admin123 默认口令（见 2.2 清单） | 中 |

其余检查项结果：
- `DB_PASSWORD`：代码中全部走环境变量读取（`os.getenv("DB_PASSWORD", "")`），无硬编码 ✓
- `123456` 字面量：仅命中 home/start.bat 第 6 行（同上高危项）；livestock 无 ✓
- `.env` 文件：两项目均不存在 ✓
- `gansu-livestock/backend/start_bg.bat`：明确注释"Password NOT stored here"，从环境变量继承 ✓
- app.py：无密码相关内容 ✓

## 四、真实家庭数据文件清单（1.4）

| 文件 | 工作区 | git 跟踪 | 历史提交 | 敏感度 |
|---|---|---|---|---|
| `home/docs/家庭账号.md`（家人登录口令） | 有 | **否** | 无 | 高（但未泄露） |
| `home/data/snapshot/20261010/farm.json` | 有 | **是** | `da08f21` 提交过 | 中（牧场名/地区/规模） |
| `home/data/snapshot/20261010/price_data.csv`（231 行真实价格） | 有 | **是** | `da08f21` 提交过 | 中（真实数据快照，含定西 gov 明细） |
| `home/data/snapshot/20261010/alert_records.csv` | 有 | **是**（仅表头） | `da08f21` | 低 |
| `home/data/backup/*.sql`（全库备份含用户哈希） | 有（83KB+0KB） | 否 | 无 | 高（但未泄露） |
| `home/backend/logs/app.log` | 有 | 否 | 无 | 低 |
| `*.db / *.sqlite` | 无 | — | — | — |

另：`gansu-livestock` 跟踪了 `deploy/html/`（62 个前端构建产物）——非敏感，但会增大仓库体积，可选清理。

## 五、.gitignore 缺口（1.5）

对照要求清单：

| 条目 | livestock | home |
|---|---|---|
| venv/ | ✓ | ✓ |
| __pycache__/ | ✓ | ✓ |
| *.pyc | ✓ | **缺** |
| node_modules/ | ✓ | ✓ |
| dist/ | ✓ | ✓ |
| .env | ✓ | **缺** |
| *.log | ✓ | ✓ |
| logs/ | 部分（仅 `logs/*.out`、`backend/logs/*.out`） | **缺** |
| data/backup/ | ✓ | ✓ |
| data/snapshot/ | 缺（本项目无此目录） | **缺（且 3 个文件已被跟踪）** |
| docs/家庭账号.md | 不适用 | ✓ |
| *.out | 部分 | **缺** |
| data/*.csv | 不适用 | ✓（但对已跟踪文件不生效） |
| data/*.json | ✓ | 缺（farm.json 因此被跟踪） |

## 六、未提交的工作区变更

- gansu-home：`docs/任务执行日志.md`（修改）、`docs/日报-20261012.md`（新增）
- gansu-livestock：干净

---

## 七、结论

**两项目均不可直接推送 GitHub，需先清理。**

| # | 问题 | 项目 | 处理建议（阶段2，待确认后执行） |
|---|---|---|---|
| 1 | 【高】MySQL root 密码明文在 `start.bat` 且已进全部历史 | home | 方案 A：`git rm --cached` + 改为读环境变量 + **git filter-repo 清洗历史**（改写历史，需你确认）；方案 B：清洗或直接**修改 MySQL root 密码**（旧密码作废即无害）+ 移除文件跟踪 |
| 2 | 【中】data/snapshot 3 个真实数据文件被跟踪且在历史 | home | `git rm --cached -r data/snapshot/` + .gitignore 补条目（未来不再跟踪）；历史中是否清洗随问题1一并决策 |
| 3 | 【中】admin123 出现在 11 个文件（测试/建库/文档/README） | 两项目 | 测试脚本改环境变量读取；文档中打码为 `admin/<初始口令>`；init.sql 注释打码 |
| 4 | 【低】JWT_SECRET 开发默认值硬编码 | 两项目 | 保留 env 覆盖逻辑即可（默认值仅开发态）；可选改为启动时随机生成并提示 |
| 5 | 【低】.gitignore 缺口（home 4 项、livestock 2 项） | 两项目 | 补齐条目清单见第五节 |
| 6 | 【可选】deploy/html 构建产物 62 文件入库 | livestock | 可保留（部署便利）或改为发布包，由你定 |

**优先级顺序：先决 1（含是否改写历史）→ 2 → 3 → 5 → 4 → 6。**

> 提醒：问题 1 的两种方案里，"改写历史"（filter-repo）会变更全部 commit hash；"改密码"不动历史但旧密码必须立即作废。两方案都需要处理 start.bat 的明文本身。
