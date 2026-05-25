-- 标签管理表（仅作标签字典）
CREATE TABLE `tag` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '标签ID',
  `name` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '' COMMENT '标签名称',
  `color` varchar(16) COLLATE utf8mb4_unicode_ci DEFAULT '' COMMENT '标签颜色（如 #FF5733）',
  `description` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT '' COMMENT '标签说明',
  `status` tinyint(4) NOT NULL DEFAULT '1' COMMENT '状态：1-正常，2-已禁用',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_name` (`name`),
  KEY `idx_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='标签管理表';
