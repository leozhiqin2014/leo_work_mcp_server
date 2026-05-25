CREATE TABLE `member_info` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '成员ID',
  `member_nickname` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '' COMMENT '成员昵称（唯一标识）',
  `member_name` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '' COMMENT '成员中文名称',
  `avatar_url` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '' COMMENT '头像URL（COS存储）',
  `avatar_cos_key` varchar(300) COLLATE utf8mb4_unicode_ci DEFAULT '' COMMENT '头像COS对象Key',
  `gender` tinyint(4) NOT NULL DEFAULT '0' COMMENT '性别：0-未知，1-男，2-女',
  `birthday` date DEFAULT NULL COMMENT '生日',
  `relation` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT '' COMMENT '与户主关系：如爸爸、妈妈、儿子、女儿等',
  `phone` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT '' COMMENT '手机号',
  `remark` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '' COMMENT '备注',
  `status` tinyint(4) NOT NULL DEFAULT '1' COMMENT '状态：1-正常，2-已禁用',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_member_nickname` (`member_nickname`) COMMENT '昵称唯一索引',
  KEY `idx_member_name` (`member_name`) COMMENT '按名称查询索引',
  KEY `idx_status` (`status`) COMMENT '按状态过滤索引'
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='家庭成员信息表';
