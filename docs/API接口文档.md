# API 接口文档

gansu-livestock 后端 · Base URL `http://<host>:5000/api`

## 0. 通用约定

**认证**：除登录与健康检查外，均需 Header `Authorization: Bearer <token>`（/api/auth/login 获取）

**统一返回格式**：

```json
{"code": 200, "msg": "success", "data": {}, "timestamp": 1760073600}
```

**分页返回**（data 内）：

```json
{"list": [], "total": 100, "page": 1, "page_size": 20}
```

**错误码**：400 参数错误 · 401 未登录/过期 · 403 无权限或功能未开放 · 404 资源不存在 · 500 服务器错误

**功能开关**：cost / advice / farm / ledger / push 为家用版功能，`APP_MODE=school` 时返回 403

## 1. 认证 /api/auth

| 方法 | 路径 | 参数 | 说明 |
|---|---|---|---|
| POST | /auth/login | body: `{username, password}` | 登录，返回 `{token, user}` |
| POST | /auth/logout | - | 登出（前端删 token） |
| GET | /auth/info | - | 当前用户信息 |
| POST | /auth/change-password | body: `{old_password, new_password}` | 改密码 |

## 2. 基础数据 /api/base

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | /base/regions | 地区列表（15 条） |
| GET | /base/breeds | 品种列表（10 条） |
| GET | /base/categories | 价格分类（8 条） |

## 3. 牛羊价格 /api/price

| 方法 | 路径 | 参数 | 说明 |
|---|---|---|---|
| GET | /price/list | query: region_id, category_id, breed_id, source, start_date, end_date, page, page_size | 分页查询 |
| GET | /price/trend | query: category_id*, region_id*, start_date, end_date | 日均价趋势 `[{date, price}]` |
| GET | /price/compare | query: category_id*, region_ids*（逗号分隔）, start_date, end_date | 地区均价对比 |
| GET | /price/latest | query: region_id, type(livestock/feed) | 每分类最新价 |
| GET | /price/yoy | query: category_id*, region_id*, ref_date | 同比环比 `{current, mom_pct, yoy_pct}` |
| POST | /price/add | body: `{region_id, category_id, price, record_date, ...}` | 新增（admin/editor） |
| PUT | /price/update | body: `{id, ...}` | 修改（admin/editor） |
| DELETE | /price/delete | query: id | 删除（admin/editor） |
| POST | /price/import | body: `[记录, ...]` JSON 数组 | 批量导入 |
| GET | /price/export | query: 同 list 筛选 | 导出 CSV（UTF-8 BOM） |

## 4. 饲料价格 /api/price/feed

| 方法 | 路径 | 参数 | 说明 |
|---|---|---|---|
| GET | /price/feed/list | query: feed_name, region_id, start/end_date, page | 列表 |
| GET | /price/feed/trend | query: feed_name*, region_id* | 趋势 |
| GET | /price/feed/latest | query: region_id | 四种饲料最新价（含 price_per_kg） |
| POST | /price/feed/add | body: `{feed_name, region_id, price, record_date}` | 录入自家采购价 |

## 5. 预测 /api/predict

| 方法 | 路径 | 参数 | 说明 |
|---|---|---|---|
| GET | /predict/arima | query: category_id*, region_id*, days(7-90, 默认30) | ARIMA 预测 |
| GET | /predict/arimax | query: 同上 + feed_category_id(默认5=玉米) | ARIMAX（含饲料变量） |
| GET | /predict/lstm | - | 预留（未实现） |
| GET | /predict/accuracy | query: category_id*, region_id*, model | 最近一次精度 `{mae, rmse, mape}` |
| POST | /predict/retrain | - | 全分类重跑 ARIMAX（admin/editor） |

预测返回结构：

```json
{
  "history":  [{"date": "2026-09-01", "value": 15.2}],
  "forecast": [{"date": "2026-10-01", "value": 15.6, "lower": 15.1, "upper": 16.1}],
  "metrics":  {"mae": 0.35, "rmse": 0.38, "mape": 2.16, "grade": "优秀"},
  "order":    [1, 1, 1],
  "adf":      {"statistic": -3.2, "pvalue": 0.02, "is_stationary": true}
}
```

## 6. 关联分析 /api/analysis

| 方法 | 路径 | 参数 | 说明 |
|---|---|---|---|
| GET | /analysis/correlation | query: region_id*；可选 livestock_category_id+input_category_id（单对）或留空（矩阵）；save=1 落库 | 相关性 |
| GET | /analysis/lag | query: livestock_category_id*, input_category_id*, region_id*, max_lag | 滞后曲线 |
| GET | /analysis/cost-impact | query: 前三者* + feed_ratio, daily_feed_amount, weight | 饲料涨价敏感性 |

## 7. 预警 /api/alert

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | /alert/rules | query: enabled 可选 |
| POST | /alert/rule/add | body: `{name, category_id, rule_type, threshold?, continuous_days?}` |
| PUT | /alert/rule/update | body: `{id, ...}` |
| DELETE | /alert/rule/delete | query: id |
| GET | /alert/records | query: rule_id, is_read, page |
| POST | /alert/read | body: `{id}` |
| POST | /alert/push/test | 测试推送（家用版） |

## 8. 成本 /api/cost（家用版）

| 方法 | 路径 | 参数 | 说明 |
|---|---|---|---|
| POST | /cost/calculate | body: `{weight, current_price, total_cost, farm_id?, category?, region_id?}` | 出栏利润+盈亏平衡价+日成本 |
| POST | /cost/delay | body: `{weight, days, predicted_price, current_price, ...}` | 压栏 N 天对比 |
| GET | /cost/breakeven | query: total_cost*, weight* | 盈亏平衡价 |
| GET | /cost/config | query: farm_id, category | 成本参数 |
| POST | /cost/config/save | body: `{farm_id, category, daily_feed_amount?, feed_detail?...}` | 保存参数 |

## 9. 建议 /api/advice（家用版）

| 方法 | 路径 | 参数 | 说明 |
|---|---|---|---|
| GET | /advice/sell | query: weight*, current_price*, total_cost*, predicted_price* | 出栏建议（8.5 规则+压栏对比） |
| GET | /advice/reason | 同上 | 人话版理由与数字 |

## 10. 牧场 /api/farm（家用版）

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | /farm/info | query: farm_id |
| GET | /farm/livestock/list | query: farm_id, category, status, page |
| POST | /farm/livestock/add | body: `{category(cattle/sheep), ear_tag?, weight?...}` |
| PUT | /farm/livestock/update | body: `{id, ...}` |
| DELETE | /farm/livestock/delete | query: id, farm_id |
| GET | /farm/feed/list | 库存（附 warning 标记） |
| POST | /farm/feed/in | body: `{feed_name, quantity, unit_price?, supplier?}` |
| POST | /farm/feed/out | body: `{feed_name, quantity}`（库存不足报 400） |

## 11. 账本 /api/ledger（家用版）

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | /ledger/list | query: farm_id, type, category, start/end_date, page |
| POST | /ledger/add | body: `{farm_id, type(income/expense), category, amount, trade_date}` |
| PUT | /ledger/update | body: `{id, farm_id, ...}` |
| DELETE | /ledger/delete | query: id, farm_id |
| GET | /ledger/summary | query: farm_id, year? 收支汇总 |
| GET | /ledger/profit | query: farm_id, year? 按月利润 |

## 12. 管理 /api/admin

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | /admin/users | 用户列表（admin） |
| POST | /admin/user/add | 新增用户（admin） |
| POST | /admin/spider/run | body: `{spider: gov|feed|all}` 触发爬虫（admin/editor） |
| GET | /admin/spider/log | 爬虫日志 tail（admin/editor） |
| GET | /admin/system/info | 系统与库版本（admin） |

## 13. 其他

`GET /api/health`：健康检查（免认证），返回 `{"code":200,"data":{"mode":"school",...}}`


## 14. 第六轮变更记录（2026-10-10）

### 14.1 价格导出（原有接口补备注列）

`GET /api/price/export?category_id=&region_id=&start_date=&end_date=&format=csv`

- 返回 CSV 文件流（`text/csv; charset=utf-8`，带 UTF-8 BOM，Excel 直接打开不乱码）
- 字段：日期、地区、分类、品种、价格、单位、来源、来源明细、**备注**（新增）
- 默认排除示例数据；`include_sample=true` 包含

### 14.2 趋势接口结构升级（v2）

`GET /api/price/trend` 返回由数组升级为对象：

```json
{
  "points": [{"date": "2026-10-10", "price": 15.15, "source": "gov"}],
  "data_region_id": 12, "data_region_name": "定西市", "fallback": true
}
```

- 指定地区无数据时**动态回退**到该分类最近有数据的地区（不硬编码），`fallback=true` 标记
- 每点带 `source`（gov/derived/index/manual，多来源逗号分隔取首个），供前端区分观测/反推
- `GET /api/price/feed/latest` 同步升级为 `{items, data_region_id, data_region_name}`

### 14.3 报告生成脚本（非 HTTP）

- `backend/scripts/gen_weekly_report.py [YYYY-Wnn]`：周报 md（价格/环比/异常/下周预测）
- `backend/scripts/gen_monthly_report.py [YYYY-MM]`：月报 md + matplotlib 走势 png
- `backend/scripts/derive_livestock_price.py`：活牛/活羊反推补全（幂等）
- `backend/scripts/gen_thesis_materials.py`：论文统计表与图

### 14.4 登录态 URL 注入（截图/扫码场景）

两前端路由守卫支持 `?token=<JWT>` 自动写入 localStorage 后正常进入内页。
