# -*- coding: utf-8 -*-
"""
APScheduler 定时任务：
  - 每日 07:00 爬饲料价格
  - 每周一 08:00 爬政府监测价格
  - 每日 07:30 跑预测并落库
  - 每日 08:00 巡检预警规则
  - 每周日 02:00 备份数据库
任务体延迟导入，避免循环依赖；爬虫/预测实现就位前只打日志
"""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from utils.logger import get_logger

logger = get_logger("scheduler")
_scheduler = None


def crawl_price_job():
    """每周一 08:00 爬取政府价格监测数据"""
    logger.info("[定时任务] 爬取政府价格监测数据开始")
    try:
        # TODO: 阶段3 爬虫就位后取消注释
        # import sys, os
        # sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        # from spider.gov_spider import GovSpider
        # GovSpider().run()
        logger.info("[定时任务] 爬取政府价格监测数据完成（爬虫未接入，跳过）")
    except Exception as e:
        logger.error("[定时任务] 爬取政府价格监测数据失败: %s", e)


def crawl_feed_job():
    """每日 07:00 爬取饲料价格"""
    logger.info("[定时任务] 爬取饲料价格开始")
    try:
        # TODO: from spider.feed_spider import FeedSpider; FeedSpider().run()
        logger.info("[定时任务] 爬取饲料价格完成（爬虫未接入，跳过）")
    except Exception as e:
        logger.error("[定时任务] 爬取饲料价格失败: %s", e)


def predict_job():
    """每日 07:30 对所有启用分类跑 ARIMAX 预测并写入 predict_result"""
    logger.info("[定时任务] 定时预测开始")
    try:
        # TODO: from service.predict_service import run_all_predict; run_all_predict()
        logger.info("[定时任务] 定时预测完成（预测服务未接入，跳过）")
    except Exception as e:
        logger.error("[定时任务] 定时预测失败: %s", e)


def alert_check_job():
    """每日 08:00 巡检预警规则，生成预警记录"""
    logger.info("[定时任务] 预警巡检开始")
    try:
        # TODO: from service.alert_service import check_all_rules; check_all_rules()
        logger.info("[定时任务] 预警巡检完成（预警服务未接入，跳过）")
    except Exception as e:
        logger.error("[定时任务] 预警巡检失败: %s", e)


def backup_job():
    """每周日 02:00 备份数据库到 data/backup/"""
    logger.info("[定时任务] 数据库备份开始")
    try:
        # TODO: mysqldump 导出至 data/backup/gansu_livestock_YYYYMMDD.sql
        logger.info("[定时任务] 数据库备份完成（备份命令未接入，跳过）")
    except Exception as e:
        logger.error("[定时任务] 数据库备份失败: %s", e)


def start_scheduler():
    """启动后台调度器（Flask 启动后调用一次）"""
    global _scheduler
    if _scheduler is not None:
        return _scheduler
    _scheduler = BackgroundScheduler(timezone="Asia/Shanghai")

    _scheduler.add_job(crawl_price_job, CronTrigger(day_of_week="mon", hour=8, minute=0),
                       id="crawl_price", replace_existing=True)
    _scheduler.add_job(crawl_feed_job, CronTrigger(hour=7, minute=0),
                       id="crawl_feed", replace_existing=True)
    _scheduler.add_job(predict_job, CronTrigger(hour=7, minute=30),
                       id="predict", replace_existing=True)
    _scheduler.add_job(alert_check_job, CronTrigger(hour=8, minute=0),
                       id="alert_check", replace_existing=True)
    _scheduler.add_job(backup_job, CronTrigger(day_of_week="sun", hour=2, minute=0),
                       id="backup", replace_existing=True)

    _scheduler.start()
    logger.info("定时调度器已启动（Asia/Shanghai）")
    return _scheduler


def shutdown_scheduler():
    """关闭调度器"""
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
        logger.info("定时调度器已停止")
