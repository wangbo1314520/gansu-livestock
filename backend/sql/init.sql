-- ============================================================
-- 甘肃牛羊价格统计预测与趋势分析平台 数据库初始化脚本
-- 版本: v1.1
-- 数据库: gansu_livestock
-- 字符集: utf8mb4 / utf8mb4_unicode_ci
-- 引擎:   InnoDB
-- 说明:   在 Navicat 或 mysql 客户端中按顺序执行本文件与 init_data.sql
-- ============================================================

CREATE DATABASE IF NOT EXISTS gansu_livestock
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_unicode_ci;

USE gansu_livestock;

SET NAMES utf8mb4;

-- ============================================================
-- 1. 基础表
-- ============================================================

-- 地区表：甘肃省(id=1, level=1) + 14 个市州(level=2)
CREATE TABLE IF NOT EXISTS region (
  id INT UNSIGNED PRIMARY KEY AUTO_INCREMENT COMMENT '地区ID',
  name VARCHAR(50) NOT NULL COMMENT '地区名称，如：兰州、平凉',
  city_code VARCHAR(20) DEFAULT NULL COMMENT '行政区划代码，如 620100',
  level TINYINT NOT NULL DEFAULT 2 COMMENT '层级：1=省级 2=市州',
  parent_id INT UNSIGNED NOT NULL DEFAULT 0 COMMENT '上级地区ID，市州指向省级(1)，省级为0',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  UNIQUE KEY uk_region_name (name),
  INDEX idx_parent (parent_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='地区表';

-- 品种表：牛/羊品种
CREATE TABLE IF NOT EXISTS breed (
  id INT UNSIGNED PRIMARY KEY AUTO_INCREMENT COMMENT '品种ID',
  name VARCHAR(50) NOT NULL COMMENT '品种名称，如：西门塔尔、小尾寒羊',
  category VARCHAR(20) NOT NULL COMMENT '类别：cattle=牛 sheep=羊',
  remark VARCHAR(200) DEFAULT NULL COMMENT '备注，如产地、特点',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  UNIQUE KEY uk_breed_name (name),
  INDEX idx_category (category)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='品种表';

-- 价格分类表：牛羊价格 + 饲料价格统一分类
CREATE TABLE IF NOT EXISTS price_category (
  id INT UNSIGNED PRIMARY KEY AUTO_INCREMENT COMMENT '分类ID',
  name VARCHAR(50) NOT NULL COMMENT '分类名称：活牛、牛肉、活羊、羊肉、玉米、豆粕、麸皮、苜蓿草',
  type VARCHAR(20) NOT NULL COMMENT '类型：livestock=牲畜 feed=饲料',
  unit VARCHAR(20) NOT NULL DEFAULT '元/斤' COMMENT '计价单位',
  sort_order INT NOT NULL DEFAULT 0 COMMENT '显示排序，越小越靠前',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  UNIQUE KEY uk_category_name (name),
  INDEX idx_type (type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='价格分类表';

-- ============================================================
-- 2. 核心价格数据表
-- ============================================================

-- 价格数据表：牛羊价格与饲料价格共用
CREATE TABLE IF NOT EXISTS price_data (
  id BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT COMMENT '记录ID',
  region_id INT UNSIGNED NOT NULL COMMENT '地区ID，关联 region.id',
  breed_id INT UNSIGNED DEFAULT NULL COMMENT '品种ID，关联 breed.id，饲料类为NULL',
  category_id INT UNSIGNED NOT NULL COMMENT '价格分类ID，关联 price_category.id',
  price DECIMAL(10,2) NOT NULL COMMENT '价格（元/斤）',
  unit VARCHAR(20) NOT NULL DEFAULT '元/斤' COMMENT '计价单位',
  source VARCHAR(50) NOT NULL COMMENT '数据来源：gov=政府 manual=手工 dealer=贩子 market=市场 self=自家',
  source_detail VARCHAR(100) DEFAULT NULL COMMENT '来源明细，如：甘肃省发改委2026年第40周监测',
  record_date DATE NOT NULL COMMENT '价格所属日期',
  user_id INT UNSIGNED DEFAULT NULL COMMENT '录入用户ID（手工数据）',
  farm_id INT UNSIGNED DEFAULT NULL COMMENT '牧场ID（自家数据）',
  remark TEXT COMMENT '备注',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  CONSTRAINT fk_price_region FOREIGN KEY (region_id) REFERENCES region(id),
  CONSTRAINT fk_price_breed FOREIGN KEY (breed_id) REFERENCES breed(id) ON DELETE SET NULL,
  CONSTRAINT fk_price_category FOREIGN KEY (category_id) REFERENCES price_category(id),
  INDEX idx_region_date (region_id, record_date),
  INDEX idx_category_date (category_id, record_date),
  INDEX idx_source (source),
  INDEX idx_record_date (record_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='价格数据表（牛羊+饲料共用）';

-- ============================================================
-- 3. 用户与登录日志
-- ============================================================

-- 用户表（user 为常用表名，统一用反引号）
CREATE TABLE IF NOT EXISTS `user` (
  id INT UNSIGNED PRIMARY KEY AUTO_INCREMENT COMMENT '用户ID',
  username VARCHAR(50) NOT NULL COMMENT '登录用户名',
  password_hash VARCHAR(200) NOT NULL COMMENT 'bcrypt 密码哈希',
  real_name VARCHAR(50) DEFAULT NULL COMMENT '真实姓名',
  phone VARCHAR(20) DEFAULT NULL COMMENT '手机号',
  role VARCHAR(20) NOT NULL DEFAULT 'viewer' COMMENT '角色：admin=管理员 editor=录入员 viewer=只读',
  farm_id INT UNSIGNED DEFAULT NULL COMMENT '关联牧场ID（家用版家庭账号）',
  status TINYINT NOT NULL DEFAULT 1 COMMENT '状态：1=正常 0=禁用',
  last_login DATETIME DEFAULT NULL COMMENT '最后登录时间',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  UNIQUE KEY uk_username (username),
  INDEX idx_role (role)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户表';

-- 登录日志表
CREATE TABLE IF NOT EXISTS login_log (
  id BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT COMMENT '日志ID',
  user_id INT UNSIGNED NOT NULL COMMENT '用户ID，关联 user.id',
  ip VARCHAR(50) DEFAULT NULL COMMENT '登录IP',
  user_agent VARCHAR(200) DEFAULT NULL COMMENT '浏览器标识',
  login_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '登录时间',
  success TINYINT NOT NULL DEFAULT 1 COMMENT '是否成功：1=成功 0=失败',
  CONSTRAINT fk_loginlog_user FOREIGN KEY (user_id) REFERENCES `user`(id) ON DELETE CASCADE,
  INDEX idx_user_time (user_id, login_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='登录日志表';

-- ============================================================
-- 4. 预测与预警
-- ============================================================

-- 预测结果表
CREATE TABLE IF NOT EXISTS predict_result (
  id BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT COMMENT '记录ID',
  category_id INT UNSIGNED NOT NULL COMMENT '价格分类ID，关联 price_category.id',
  region_id INT UNSIGNED NOT NULL COMMENT '地区ID，关联 region.id',
  model VARCHAR(20) NOT NULL COMMENT '模型：arima arimax lstm',
  predict_date DATE NOT NULL COMMENT '预测日期',
  predict_value DECIMAL(10,2) NOT NULL COMMENT '预测值（元/斤）',
  lower_bound DECIMAL(10,2) DEFAULT NULL COMMENT '置信下界',
  upper_bound DECIMAL(10,2) DEFAULT NULL COMMENT '置信上界',
  confidence DECIMAL(5,2) NOT NULL DEFAULT 95.00 COMMENT '置信度（%）',
  mae DECIMAL(10,4) DEFAULT NULL COMMENT '平均绝对误差',
  rmse DECIMAL(10,4) DEFAULT NULL COMMENT '均方根误差',
  mape DECIMAL(10,4) DEFAULT NULL COMMENT '平均绝对百分比误差（%）',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  CONSTRAINT fk_predict_category FOREIGN KEY (category_id) REFERENCES price_category(id),
  CONSTRAINT fk_predict_region FOREIGN KEY (region_id) REFERENCES region(id),
  INDEX idx_category_region (category_id, region_id, predict_date),
  INDEX idx_model (model)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='预测结果表';

-- 预警规则表
CREATE TABLE IF NOT EXISTS alert_rule (
  id INT UNSIGNED PRIMARY KEY AUTO_INCREMENT COMMENT '规则ID',
  name VARCHAR(100) NOT NULL COMMENT '规则名称',
  category_id INT UNSIGNED NOT NULL COMMENT '价格分类ID，关联 price_category.id',
  region_id INT UNSIGNED DEFAULT NULL COMMENT '地区ID，NULL表示全部地区',
  rule_type VARCHAR(30) NOT NULL COMMENT '规则类型：below_cost=跌破成本线 above_price=高于阈值 continuous_rise=连续上涨 continuous_fall=连续下跌 feed_rise=饲料涨价',
  threshold DECIMAL(10,2) DEFAULT NULL COMMENT '阈值价格（元/斤）',
  continuous_days INT NOT NULL DEFAULT 3 COMMENT '连续天数（连续涨跌类规则用）',
  enabled TINYINT NOT NULL DEFAULT 1 COMMENT '是否启用：1=启用 0=停用',
  user_id INT UNSIGNED DEFAULT NULL COMMENT '创建用户ID',
  farm_id INT UNSIGNED DEFAULT NULL COMMENT '牧场ID（家用版）',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  CONSTRAINT fk_rule_category FOREIGN KEY (category_id) REFERENCES price_category(id),
  CONSTRAINT fk_rule_region FOREIGN KEY (region_id) REFERENCES region(id) ON DELETE SET NULL,
  CONSTRAINT fk_rule_user FOREIGN KEY (user_id) REFERENCES `user`(id) ON DELETE SET NULL,
  INDEX idx_enabled (enabled)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='预警规则表';

-- 预警记录表
CREATE TABLE IF NOT EXISTS alert_record (
  id BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT COMMENT '记录ID',
  rule_id INT UNSIGNED NOT NULL COMMENT '触发规则ID，关联 alert_rule.id',
  category_id INT UNSIGNED DEFAULT NULL COMMENT '价格分类ID',
  region_id INT UNSIGNED DEFAULT NULL COMMENT '地区ID',
  trigger_value DECIMAL(10,2) DEFAULT NULL COMMENT '触发时的价格（元/斤）',
  message VARCHAR(500) DEFAULT NULL COMMENT '预警消息内容',
  trigger_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '触发时间',
  is_read TINYINT NOT NULL DEFAULT 0 COMMENT '是否已读：1=已读 0=未读',
  user_id INT UNSIGNED DEFAULT NULL COMMENT '通知用户ID',
  push_status TINYINT NOT NULL DEFAULT 0 COMMENT '推送状态：0=未推送 1=已推送 2=推送失败',
  CONSTRAINT fk_record_rule FOREIGN KEY (rule_id) REFERENCES alert_rule(id) ON DELETE CASCADE,
  CONSTRAINT fk_record_category FOREIGN KEY (category_id) REFERENCES price_category(id) ON DELETE SET NULL,
  CONSTRAINT fk_record_region FOREIGN KEY (region_id) REFERENCES region(id) ON DELETE SET NULL,
  INDEX idx_trigger_time (trigger_time),
  INDEX idx_user_read (user_id, is_read)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='预警记录表';

-- 关联分析表：饲料价与牛羊价的相关性
CREATE TABLE IF NOT EXISTS input_correlation (
  id BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT COMMENT '记录ID',
  livestock_category_id INT UNSIGNED NOT NULL COMMENT '牛羊价格分类ID，如：活牛',
  input_category_id INT UNSIGNED NOT NULL COMMENT '饲料价格分类ID，如：玉米',
  region_id INT UNSIGNED DEFAULT NULL COMMENT '地区ID，NULL表示全省',
  correlation DECIMAL(6,4) DEFAULT NULL COMMENT '皮尔逊相关系数，-1~1',
  lag_days INT DEFAULT NULL COMMENT '最优滞后天数（饲料价先行）',
  calc_date DATE DEFAULT NULL COMMENT '计算日期',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  CONSTRAINT fk_corr_livestock FOREIGN KEY (livestock_category_id) REFERENCES price_category(id),
  CONSTRAINT fk_corr_input FOREIGN KEY (input_category_id) REFERENCES price_category(id),
  CONSTRAINT fk_corr_region FOREIGN KEY (region_id) REFERENCES region(id) ON DELETE SET NULL,
  INDEX idx_livestock_input (livestock_category_id, input_category_id),
  INDEX idx_calc_date (calc_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='投入品与牛羊价格关联分析表';

-- ============================================================
-- 5. 家用版：牧场、存栏、成本配置
-- ============================================================

-- 牧场表
CREATE TABLE IF NOT EXISTS farm (
  id INT UNSIGNED PRIMARY KEY AUTO_INCREMENT COMMENT '牧场ID',
  name VARCHAR(100) NOT NULL COMMENT '牧场名称，如：王家牧场',
  owner_id INT UNSIGNED NOT NULL COMMENT '归属用户ID，关联 user.id',
  region_id INT UNSIGNED DEFAULT NULL COMMENT '所在地区ID',
  address VARCHAR(200) DEFAULT NULL COMMENT '详细地址',
  cattle_count INT NOT NULL DEFAULT 0 COMMENT '牛存栏数（冗余统计）',
  sheep_count INT NOT NULL DEFAULT 0 COMMENT '羊存栏数（冗余统计）',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  CONSTRAINT fk_farm_owner FOREIGN KEY (owner_id) REFERENCES `user`(id),
  CONSTRAINT fk_farm_region FOREIGN KEY (region_id) REFERENCES region(id) ON DELETE SET NULL,
  INDEX idx_owner (owner_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='牧场表';

-- 存栏牲畜表
CREATE TABLE IF NOT EXISTS livestock (
  id BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT COMMENT '牲畜ID',
  farm_id INT UNSIGNED NOT NULL COMMENT '牧场ID，关联 farm.id',
  category VARCHAR(20) NOT NULL COMMENT '类别：cattle=牛 sheep=羊',
  breed_id INT UNSIGNED DEFAULT NULL COMMENT '品种ID，关联 breed.id',
  ear_tag VARCHAR(50) DEFAULT NULL COMMENT '耳标号',
  birth_date DATE DEFAULT NULL COMMENT '出生日期',
  weight DECIMAL(8,2) DEFAULT NULL COMMENT '当前体重（kg）',
  status VARCHAR(20) NOT NULL DEFAULT 'raising' COMMENT '状态：raising=在养 sold=已出栏 dead=死亡',
  purchase_price DECIMAL(10,2) DEFAULT NULL COMMENT '购入价（元/头）',
  purchase_date DATE DEFAULT NULL COMMENT '购入日期',
  remark TEXT COMMENT '备注',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  CONSTRAINT fk_livestock_farm FOREIGN KEY (farm_id) REFERENCES farm(id) ON DELETE CASCADE,
  CONSTRAINT fk_livestock_breed FOREIGN KEY (breed_id) REFERENCES breed(id) ON DELETE SET NULL,
  INDEX idx_farm_status (farm_id, status),
  INDEX idx_category (category)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='存栏牲畜表';

-- 成本配置表：日饲料量、日增重等参数，用于利润计算
CREATE TABLE IF NOT EXISTS cost_config (
  id INT UNSIGNED PRIMARY KEY AUTO_INCREMENT COMMENT '配置ID',
  farm_id INT UNSIGNED NOT NULL COMMENT '牧场ID，关联 farm.id',
  category VARCHAR(20) NOT NULL COMMENT '类别：cattle=牛 sheep=羊',
  daily_feed_amount DECIMAL(8,2) DEFAULT NULL COMMENT '日饲料量（kg/头）',
  daily_labor_cost DECIMAL(8,2) DEFAULT NULL COMMENT '日人工成本（元/头）',
  daily_other_cost DECIMAL(8,2) DEFAULT NULL COMMENT '日其他成本（元/头），水电等',
  daily_gain DECIMAL(6,3) DEFAULT NULL COMMENT '日增重（kg/头）',
  feed_detail JSON DEFAULT NULL COMMENT '饲料配比，如 {"玉米":0.6,"豆粕":0.2,"麸皮":0.1,"苜蓿草":0.1}',
  effective_date DATE DEFAULT NULL COMMENT '生效日期',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  CONSTRAINT fk_cost_farm FOREIGN KEY (farm_id) REFERENCES farm(id) ON DELETE CASCADE,
  INDEX idx_farm_category (farm_id, category)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='成本配置表';

-- ============================================================
-- 6. 家用版：账本、饲料库存
-- ============================================================

-- 家庭账本表
CREATE TABLE IF NOT EXISTS ledger (
  id BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT COMMENT '账目ID',
  farm_id INT UNSIGNED NOT NULL COMMENT '牧场ID，关联 farm.id',
  type VARCHAR(20) NOT NULL COMMENT '类型：income=收入 expense=支出',
  category VARCHAR(30) NOT NULL COMMENT '收支分类，如：卖牛、卖羊、购饲料、兽药',
  amount DECIMAL(10,2) NOT NULL COMMENT '金额（元）',
  livestock_id BIGINT UNSIGNED DEFAULT NULL COMMENT '关联牲畜ID（卖牲畜时）',
  quantity INT NOT NULL DEFAULT 1 COMMENT '数量（头/只/袋）',
  unit_price DECIMAL(10,2) DEFAULT NULL COMMENT '单价（元）',
  trade_date DATE NOT NULL COMMENT '交易日期',
  counterparty VARCHAR(100) DEFAULT NULL COMMENT '交易对方，如：贩子老李',
  remark TEXT COMMENT '备注',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  CONSTRAINT fk_ledger_farm FOREIGN KEY (farm_id) REFERENCES farm(id) ON DELETE CASCADE,
  CONSTRAINT fk_ledger_livestock FOREIGN KEY (livestock_id) REFERENCES livestock(id) ON DELETE SET NULL,
  INDEX idx_farm_date (farm_id, trade_date),
  INDEX idx_type (type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='家庭账本表';

-- 饲料库存表
CREATE TABLE IF NOT EXISTS feed_stock (
  id INT UNSIGNED PRIMARY KEY AUTO_INCREMENT COMMENT '库存ID',
  farm_id INT UNSIGNED NOT NULL COMMENT '牧场ID，关联 farm.id',
  feed_name VARCHAR(50) NOT NULL COMMENT '饲料名称：玉米 豆粕 麸皮 苜蓿草',
  quantity DECIMAL(10,2) NOT NULL DEFAULT 0 COMMENT '当前库存（kg）',
  unit VARCHAR(20) NOT NULL DEFAULT 'kg' COMMENT '库存单位',
  unit_price DECIMAL(8,2) DEFAULT NULL COMMENT '最近入库单价（元/kg）',
  warn_threshold DECIMAL(10,2) DEFAULT NULL COMMENT '库存预警阈值（kg），低于则提醒',
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  CONSTRAINT fk_stock_farm FOREIGN KEY (farm_id) REFERENCES farm(id) ON DELETE CASCADE,
  UNIQUE KEY uk_farm_feed (farm_id, feed_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='饲料库存表';

-- 饲料出入库记录表
CREATE TABLE IF NOT EXISTS feed_record (
  id BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT COMMENT '记录ID',
  farm_id INT UNSIGNED NOT NULL COMMENT '牧场ID，关联 farm.id',
  feed_name VARCHAR(50) NOT NULL COMMENT '饲料名称：玉米 豆粕 麸皮 苜蓿草',
  type VARCHAR(10) NOT NULL COMMENT '类型：in=入库（买入） out=出库（喂养）',
  quantity DECIMAL(10,2) NOT NULL COMMENT '数量（kg）',
  unit_price DECIMAL(8,2) DEFAULT NULL COMMENT '单价（元/kg）',
  total_price DECIMAL(10,2) DEFAULT NULL COMMENT '总金额（元）',
  record_date DATE NOT NULL COMMENT '记录日期',
  supplier VARCHAR(100) DEFAULT NULL COMMENT '供应商',
  remark TEXT COMMENT '备注',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  CONSTRAINT fk_record_farm FOREIGN KEY (farm_id) REFERENCES farm(id) ON DELETE CASCADE,
  INDEX idx_farm_feed_date (farm_id, feed_name, record_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='饲料出入库记录表';

-- 推送日志表：预警消息推送记录
CREATE TABLE IF NOT EXISTS push_log (
  id BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT COMMENT '推送ID',
  user_id INT UNSIGNED NOT NULL COMMENT '接收用户ID，关联 user.id',
  channel VARCHAR(20) DEFAULT NULL COMMENT '推送渠道：wechat=微信 bark=Bark sms=短信',
  title VARCHAR(200) DEFAULT NULL COMMENT '推送标题',
  content TEXT COMMENT '推送内容',
  send_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '发送时间',
  status TINYINT NOT NULL DEFAULT 0 COMMENT '状态：0=待发送 1=成功 2=失败',
  CONSTRAINT fk_push_user FOREIGN KEY (user_id) REFERENCES `user`(id) ON DELETE CASCADE,
  INDEX idx_user_time (user_id, send_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='推送日志表';

-- ============================================================
-- 初始化完成
-- ============================================================
