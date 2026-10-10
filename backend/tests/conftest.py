# -*- coding: utf-8 -*-
"""pytest 公共配置：把 backend 和项目根加入 sys.path"""
import os
import sys

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(BACKEND)
for p in (BACKEND, ROOT):
    if p not in sys.path:
        sys.path.insert(0, p)
