-- ============================================================
-- breed 表品种+阶段细分扩展（配合 2026-10-10 的 ALTER：ADD COLUMN stage）
-- 设计：执行一次。前置唯一索引已改为 (name, stage) 复合
--      （同名不同阶段合法共存，同名同阶段仍拒绝，防重复插入）
-- 注意：如重复执行本文件，INSERT IGNORE 幂等（已存在的同名同阶段跳过）
-- 历史文件 init.sql / init_data.sql 不受影响，保留原样
-- ============================================================

USE gansu_livestock;
SET NAMES utf8mb4;

-- 牛类细分（黄牛=家里实际养殖；牦牛=对比参考价；西门塔尔=常见改良品种）
INSERT IGNORE INTO breed (name, category, stage, remark) VALUES
('黄牛',     'cattle', 'bull',      '种公牛'),
('黄牛',     'cattle', 'cow',       '繁殖母牛'),
('黄牛',     'cattle', 'calf',      '牛犊'),
('黄牛',     'cattle', 'fattening', '育肥牛'),
('牦牛',     'cattle', 'bull',      '种公牛-参考价'),
('牦牛',     'cattle', 'cow',       '母牦牛-参考价'),
('牦牛',     'cattle', 'calf',      '牦牛犊-参考价'),
('西门塔尔', 'cattle', 'bull',      '种公牛'),
('西门塔尔', 'cattle', 'cow',       '繁殖母牛'),
('西门塔尔', 'cattle', 'calf',      '牛犊'),
('西门塔尔', 'cattle', 'fattening', '育肥牛');

-- 羊类细分（小尾寒羊/湖羊/滩羊/藏羊/杜泊羊）
INSERT IGNORE INTO breed (name, category, stage, remark) VALUES
('小尾寒羊', 'sheep', 'ram',       '种公羊'),
('小尾寒羊', 'sheep', 'ewe',       '繁殖母羊'),
('小尾寒羊', 'sheep', 'lamb',      '羊羔'),
('小尾寒羊', 'sheep', 'fattening', '育肥羊'),
('湖羊',     'sheep', 'ewe',       '繁殖母羊'),
('湖羊',     'sheep', 'lamb',      '羊羔'),
('滩羊',     'sheep', 'fattening', '育肥羊'),
('藏羊',     'sheep', 'ewe',       '繁殖母羊'),
('藏羊',     'sheep', 'lamb',      '羊羔'),
('杜泊羊',   'sheep', 'ram',       '种公羊');
