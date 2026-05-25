-- ----------------------------
-- 家庭成员上下文记录表
-- ----------------------------
CREATE TABLE `member_context` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '上下文ID',
  `member_nickname` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '' COMMENT '成员昵称',
  `member_name` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '' COMMENT '成员名称',
  `context_type_level_one` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '' COMMENT '上下文1级分类：学习/健康/生活等',
  `context_type_level_two` varchar(128) COLLATE utf8mb4_unicode_ci DEFAULT '' COMMENT '上下文2级分类：如数学、英语、体检报告等',
  `context_type_level_three` varchar(128) COLLATE utf8mb4_unicode_ci DEFAULT '' COMMENT '上下文3级分类',
  `context_type_level_four` varchar(128) COLLATE utf8mb4_unicode_ci DEFAULT '' COMMENT '上下文4级分类',
  `content_format` tinyint(4) NOT NULL DEFAULT '1' COMMENT '内容格式：1-文字，2-图片，3-文件',
  `content` text COLLATE utf8mb4_unicode_ci COMMENT '文字内容',
  `cos_url` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT 'COS资源URL（content_format=2,3时使用）',
  `cos_key` varchar(300) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT 'COS对象Key',
  `file_name` varchar(200) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '原始文件名（content_format=2,3时使用）',
  `file_size` bigint(20) unsigned DEFAULT '0' COMMENT '文件大小字节',
  `status` tinyint(4) NOT NULL DEFAULT '1' COMMENT '状态：1-正常，2-已删除（软删除），3-已归档',
  `permission` tinyint(4) NOT NULL DEFAULT '1' COMMENT '访问权限：1-私有（仅自己），2-家庭成员可见，3-全部成员可编辑',
  `remark` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '' COMMENT '备注说明',
  `tags` varchar(500) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '' COMMENT '标签，多个用逗号分隔',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_member_nickname` (`member_nickname`) COMMENT '按昵称查询索引',
  KEY `idx_member_name` (`member_name`) COMMENT '按名称查询索引',
  KEY `idx_context_type` (`context_type_level_one`,`context_type_level_two`,`context_type_level_three`,`context_type_level_four`) COMMENT '按上下文类型查询索引',
  KEY `idx_status` (`status`) COMMENT '按状态过滤索引',
  KEY `idx_created_at` (`created_at`) COMMENT '按时间排序索引'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='家庭成员上下文记录表';
