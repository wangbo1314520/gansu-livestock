# -*- coding: utf-8 -*-
"""
预警业务：规则 CRUD、巡检（跌破成本线/高于阈值/连续涨跌/饲料涨价）、记录管理
"""
import datetime

from sqlalchemy import and_
from sqlalchemy.orm import Session

from model.alert import AlertRecord, AlertRule
from model.price import PriceCategory, PriceData
from utils.logger import get_logger

logger = get_logger("alert_service")

RULE_TYPE_CN = {
    "below_cost": "跌破成本线",
    "above_price": "高于阈值",
    "continuous_rise": "连续上涨",
    "continuous_fall": "连续下跌",
    "feed_rise": "饲料涨价",
}


def list_rules(db: Session, enabled=None):
    """规则列表"""
    q = db.query(AlertRule)
    if enabled is not None:
        q = q.filter(AlertRule.enabled == enabled)
    return [r.to_dict() for r in q.order_by(AlertRule.id.desc()).all()]


def add_rule(db: Session, data: dict, user_id=None):
    """新增规则"""
    rule = AlertRule(
        name=data["name"],
        category_id=data["category_id"],
        region_id=data.get("region_id"),
        rule_type=data["rule_type"],
        threshold=data.get("threshold"),
        continuous_days=data.get("continuous_days", 3),
        enabled=data.get("enabled", 1),
        user_id=user_id,
        farm_id=data.get("farm_id"),
    )
    db.add(rule)
    db.commit()
    return rule.id


def update_rule(db: Session, rule_id, data: dict):
    """修改规则"""
    rule = db.query(AlertRule).get(rule_id)
    if not rule:
        return False
    for f in ("name", "category_id", "region_id", "rule_type",
              "threshold", "continuous_days", "enabled"):
        if f in data and data[f] is not None:
            setattr(rule, f, data[f])
    db.commit()
    return True


def delete_rule(db: Session, rule_id):
    """删除规则（级联删除其预警记录）"""
    rule = db.query(AlertRule).get(rule_id)
    if not rule:
        return False
    db.delete(rule)
    db.commit()
    return True


def list_records(db: Session, rule_id=None, is_read=None, page=1, page_size=20):
    """预警记录分页"""
    q = db.query(AlertRecord)
    if rule_id:
        q = q.filter(AlertRecord.rule_id == rule_id)
    if is_read is not None:
        q = q.filter(AlertRecord.is_read == is_read)
    total = q.count()
    rows = (q.order_by(AlertRecord.trigger_time.desc())
            .offset((page - 1) * page_size).limit(page_size).all())
    return [r.to_dict() for r in rows], total


def mark_read(db: Session, record_id):
    """标记已读"""
    record = db.query(AlertRecord).get(record_id)
    if not record:
        return False
    record.is_read = 1
    db.commit()
    return True


# ------------------------------------------------------------------
# 巡检逻辑
# ------------------------------------------------------------------

def _recent_prices(db: Session, category_id, region_id, days):
    """最近 N 天价格序列（按日均价，升序）"""
    since = datetime.date.today() - datetime.timedelta(days=days)
    q = db.query(PriceData.record_date, PriceData.price).filter(
        PriceData.category_id == category_id,
        PriceData.record_date >= since,
    )
    if region_id:
        q = q.filter(PriceData.region_id == region_id)
    rows = q.order_by(PriceData.record_date).all()
    by_date = {}
    for d, p in rows:
        by_date.setdefault(d, []).append(float(p))
    return {d: sum(v) / len(v) for d, v in sorted(by_date.items())}


def check_rule(db: Session, rule: AlertRule):
    """检查单条规则，触发则写 alert_record，返回是否触发"""
    daily = _recent_prices(db, rule.category_id, rule.region_id, days=60)
    if not daily:
        return False
    latest_date = max(daily)
    latest_price = daily[latest_date]
    cat = db.query(PriceCategory).get(rule.category_id)
    cat_name = cat.name if cat else "分类%s" % rule.category_id
    type_cn = RULE_TYPE_CN.get(rule.rule_type, rule.rule_type)

    triggered, message = False, ""

    if rule.rule_type in ("below_cost", "above_price") and rule.threshold is not None:
        if rule.rule_type == "below_cost" and latest_price < float(rule.threshold):
            triggered = True
            message = "%s最新价 %.2f 元/斤，已跌破阈值 %.2f 元/斤（%s）" % (
                cat_name, latest_price, float(rule.threshold), type_cn)
        if rule.rule_type == "above_price" and latest_price > float(rule.threshold):
            triggered = True
            message = "%s最新价 %.2f 元/斤，高于阈值 %.2f 元/斤（%s）" % (
                cat_name, latest_price, float(rule.threshold), type_cn)

    elif rule.rule_type in ("continuous_rise", "continuous_fall"):
        prices = list(daily.values())[-(rule.continuous_days or 3):]
        if len(prices) >= (rule.continuous_days or 3):
            diffs = [prices[i + 1] - prices[i] for i in range(len(prices) - 1)]
            if rule.rule_type == "continuous_rise" and all(d > 0 for d in diffs):
                triggered = True
                message = "%s已连续 %d 天上涨：%.2f -> %.2f 元/斤" % (
                    cat_name, len(prices), prices[0], prices[-1])
            if rule.rule_type == "continuous_fall" and all(d < 0 for d in diffs):
                triggered = True
                message = "%s已连续 %d 天下跌：%.2f -> %.2f 元/斤" % (
                    cat_name, len(prices), prices[0], prices[-1])

    elif rule.rule_type == "feed_rise" and rule.threshold is not None:
        prices = list(daily.values())
        if len(prices) >= 2 and (prices[-1] - prices[0]) > float(rule.threshold):
            triggered = True
            message = "%s近%d天涨幅 %.2f 元/斤，超过 %.2f，注意养殖成本" % (
                cat_name, len(prices), prices[-1] - prices[0], float(rule.threshold))

    if not triggered:
        return False

    # 同一规则同一天不重复告警
    today_start = datetime.datetime.combine(datetime.date.today(), datetime.time.min)
    exists = db.query(AlertRecord).filter(
        AlertRecord.rule_id == rule.id,
        AlertRecord.trigger_time >= today_start,
    ).count()
    if exists:
        return False

    record = AlertRecord(
        rule_id=rule.id,
        category_id=rule.category_id,
        region_id=rule.region_id,
        trigger_value=round(latest_price, 2),
        message=message,
        user_id=rule.user_id,
    )
    db.add(record)
    db.commit()
    logger.info("预警触发: %s", message)
    return True


def check_all_rules(db: Session):
    """定时任务用：巡检所有启用规则"""
    rules = db.query(AlertRule).filter(AlertRule.enabled == 1).all()
    triggered = 0
    for rule in rules:
        try:
            if check_rule(db, rule):
                triggered += 1
        except Exception as e:
            db.rollback()
            logger.error("规则[%s]巡检失败: %s", rule.name, e)
    return {"total_rules": len(rules), "triggered": triggered}
