# -*- coding: utf-8 -*-
"""
Excel 家庭记录导入：解析家庭牧场记录模板.xlsx 的三个 Sheet

- 卖牛羊记录  -> ledger（type=income，金额=数量×体重×2×单价）
- 买饲料记录  -> ledger（type=expense，金额=数量×单价）
- 贩子报价记录 -> price_data（source='dealer'，source_detail=报价人）

返回 {success, skipped, errors: [{sheet, row, reason}]}
"""
import datetime

from sqlalchemy.orm import Session

from model.ledger import Ledger
from model.price import PriceData


def _to_date(v):
    s = str(v).strip()[:10]
    try:
        datetime.datetime.strptime(s, "%Y-%m-%d").date()
        return s
    except ValueError:
        return None


def _to_float(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def import_family_excel(db: Session, wb, farm_id, user_id=None):
    """wb 为已加载的 openpyxl Workbook；幂等不做（账本允许同额重复），dealer 按同日同分类去重"""
    result = {"success": 0, "skipped": 0, "errors": []}

    def rows_of(sheet_name):
        ws = wb[sheet_name]
        header = [c.value for c in ws[1]]
        for r in ws.iter_rows(min_row=2, values_only=True):
            if r[0] is None:
                continue
            # 跳过模板说明行（只有说明文字、其余列为空）
            if str(r[0]).lstrip().startswith("（") and all(v is None for v in r[1:]):
                continue
            yield dict(zip(header, r))

    # ---- Sheet1 卖牛羊 -> ledger income ----
    if "卖牛羊记录" in wb.sheetnames:
        for i, row in enumerate(rows_of("卖牛羊记录"), 2):
            try:
                d = _to_date(row.get("日期"))
                n = _to_float(row.get("数量")) or 1
                w = _to_float(row.get("平均体重(kg)")) or 0
                p = _to_float(row.get("单价(元/斤)"))
                if not d or p is None:
                    result["errors"].append(
                        {"sheet": "卖牛羊记录", "row": i, "reason": "日期或单价格式错误"})
                    continue
                amount = round(n * w * 2 * p, 2)
                breed = str(row.get("品种") or "").strip()
                db.add(Ledger(
                    farm_id=farm_id, type="income",
                    category="卖牛" if "牛" in breed else "卖羊",
                    amount=amount, quantity=int(n), unit_price=p, trade_date=d,
                    counterparty=str(row.get("买家") or "")[:100] or None,
                    remark="%s %skg %s元/斤" % (breed or "?", w, p)))
                result["success"] += 1
            except Exception as e:
                result["errors"].append({"sheet": "卖牛羊记录", "row": i,
                                         "reason": str(e)[:60]})

    # ---- Sheet2 买饲料 -> ledger expense ----
    if "买饲料记录" in wb.sheetnames:
        for i, row in enumerate(rows_of("买饲料记录"), 2):
            try:
                d = _to_date(row.get("日期"))
                q = _to_float(row.get("数量(kg)"))
                p = _to_float(row.get("单价(元/kg)"))
                if not d or q is None or p is None:
                    result["errors"].append(
                        {"sheet": "买饲料记录", "row": i, "reason": "日期/数量/单价格式错误"})
                    continue
                db.add(Ledger(
                    farm_id=farm_id, type="expense",
                    category="买饲料",
                    amount=round(q * p, 2), trade_date=d,
                    counterparty=str(row.get("供应商") or "")[:100] or None,
                    remark="%s %skg×%s元/kg" % (
                        row.get("饲料种类") or "?", q, p)))
                result["success"] += 1
            except Exception as e:
                result["errors"].append({"sheet": "买饲料记录", "row": i,
                                         "reason": str(e)[:60]})

    # ---- Sheet3 贩子报价 -> price_data(source=dealer) ----
    if "贩子报价记录" in wb.sheetnames:
        for i, row in enumerate(rows_of("贩子报价记录"), 2):
            try:
                d = _to_date(row.get("日期"))
                p = _to_float(row.get("报价(元/斤)"))
                breed = str(row.get("品种") or "").strip()
                if not d or p is None or not breed:
                    result["errors"].append(
                        {"sheet": "贩子报价记录", "row": i, "reason": "日期/品种/报价缺失或格式错误"})
                    continue
                # 分类：品种名含"牛"->活牛，含"羊"->活羊（贩子报价口径为活畜）
                cid = 1 if "牛" in breed else (3 if "羊" in breed else None)
                if cid is None:
                    result["skipped"] += 1
                    result["errors"].append(
                        {"sheet": "贩子报价记录", "row": i, "reason": "品种'%s'无法映射到活牛/活羊" % breed})
                    continue
                exists = db.query(PriceData).filter_by(
                    category_id=cid, record_date=d, source="dealer",
                    source_detail=str(row.get("报价人") or "")[:100]).count()
                if exists:
                    result["skipped"] += 1
                    continue
                db.add(PriceData(
                    region_id=12,                 # 定西（家庭牧场所在，dealer 报价为本地实际价）
                    category_id=cid,
                    price=p, unit="元/斤",
                    source="dealer",
                    source_detail=str(row.get("报价人") or "贩子")[:100],
                    record_date=d, is_sample=0,
                    remark="%s-%s 报价" % (breed, row.get("阶段") or ""),
                    user_id=user_id))
                result["success"] += 1
            except Exception as e:
                result["errors"].append({"sheet": "贩子报价记录", "row": i,
                                         "reason": str(e)[:60]})

    db.commit()
    return result
