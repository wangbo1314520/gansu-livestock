# -*- coding: utf-8 -*-
"""
手动触发预警巡检（与 utils/scheduler.py 的 alert_check_job 同一逻辑）
用法（backend 目录下）：
  set DB_PASSWORD=***
  venv\\Scripts\\python.exe scripts\\run_alert_check.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from model import SessionLocal                    # noqa: E402
from service.alert_service import check_all_rules  # noqa: E402
from utils.logger import get_logger               # noqa: E402

logger = get_logger("alert_check")


def main():
    db = SessionLocal()
    try:
        result = check_all_rules(db)
        print("巡检完成: 规则 %d 条, 触发 %d 条" % (result["total_rules"], result["triggered"]))
        return result
    finally:
        db.close()


if __name__ == "__main__":
    main()
