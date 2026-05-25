CREATE TABLE `context_category` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '分类ID',
  `level_one` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '' COMMENT '1级分类：如学习、健康、生活',
  `level_two` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '' COMMENT '2级分类',
  `level_three` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '' COMMENT '3级分类',
  `level_four` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '' COMMENT '4级分类',
  `description` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '' COMMENT '分类说明',
  `sort_order` int(11) NOT NULL DEFAULT '0' COMMENT '排序权重，数值越小越靠前',
  `status` tinyint(4) NOT NULL DEFAULT '1' COMMENT '状态：1-正常，2-已禁用',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_category_path` (`level_one`, `level_two`, `level_three`, `level_four`) COMMENT '分类路径唯一索引',
  KEY `idx_level_one` (`level_one`) COMMENT '按1级分类查询',
  KEY `idx_level_two` (`level_two`) COMMENT '按2级分类查询',
  KEY `idx_status` (`status`) COMMENT '按状态过滤'
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='上下文分类表';
