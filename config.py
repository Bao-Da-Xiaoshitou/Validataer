#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置文件 - 管理项目的所有配置项
"""

import os
from typing import Dict, List, Any

# 项目根目录
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

# 规则文件路径
RULES_DIR = os.path.join(PROJECT_ROOT, "rules")

# 确保规则目录存在
os.makedirs(RULES_DIR, exist_ok=True)

# 规则文件配置
RULES_CONFIG = {
    "dlp_rules_file": os.path.join(RULES_DIR, "dlp_rules.json"),
    "validation_rules_file": os.path.join(RULES_DIR, "validation_rules.json"),
    "relationship_rules_file": os.path.join(RULES_DIR, "relationship_rules.json")
}

# 默认规则配置
DEFAULT_RULES = {
    "dlp_rules": [
        {
            'rule_id': 'phone_cn',
            'name': '中国手机号',
            'description': '检测中国大陆手机号码',
            'pattern': r'1[3-9]\d{9}',
            'rule_type': 'regex',
            'severity': 'medium',
            'enabled': True
        },
        {
            'rule_id': 'id_card_cn',
            'name': '中国身份证号',
            'description': '检测中国身份证号码',
            'pattern': r'\d{17}[\dXx]',
            'rule_type': 'regex',
            'severity': 'high',
            'enabled': True
        },
        {
            'rule_id': 'email',
            'name': '邮箱地址',
            'description': '检测邮箱地址',
            'pattern': r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
            'rule_type': 'regex',
            'severity': 'low',
            'enabled': True
        },
        {
            'rule_id': 'credit_card',
            'name': '信用卡号',
            'description': '检测信用卡号',
            'pattern': r'\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13}|3(?:0[0-5]|[68][0-9])[0-9]{11}|6(?:011|5[0-9]{2})[0-9]{12})\b',
            'rule_type': 'regex',
            'severity': 'high',
            'enabled': True
        },
        {
            'rule_id': 'ip_address',
            'name': 'IP地址',
            'description': '检测IP地址',
            'pattern': r'\b(?:\d{1,3}\.){3}\d{1,3}\b',
            'rule_type': 'regex',
            'severity': 'low',
            'enabled': True
        },
        {
            'rule_id': 'bank_card',
            'name': '银行卡号',
            'description': '检测银行卡号（16-19位数字）',
            'pattern': r'\b\d{16,19}\b',
            'rule_type': 'regex',
            'severity': 'high',
            'enabled': True
        },
        {
            'rule_id': 'password',
            'name': '密码字段',
            'description': '检测密码相关字段',
            'pattern': r'password|pwd|passwd',
            'rule_type': 'regex',
            'severity': 'high',
            'enabled': True
        }
    ],
    "validation_rules": [
        {
            'rule_id': 'phone_cn',
            'name': '中国手机号',
            'description': '验证中国大陆手机号码格式',
            'column_name': '手机号',
            'pattern': r'^1[3-9]\d{9}$',
            'severity': 'medium',
            'enabled': True
        },
        {
            'rule_id': 'id_card_cn',
            'name': '中国身份证号',
            'description': '验证中国身份证号码格式',
            'column_name': '身份证号',
            'pattern': r'^\d{17}[\dXx]$',
            'severity': 'high',
            'enabled': True
        },
        {
            'rule_id': 'email',
            'name': '邮箱地址',
            'description': '验证邮箱地址格式',
            'column_name': '邮箱',
            'pattern': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
            'severity': 'low',
            'enabled': True
        },
        {
            'rule_id': 'date',
            'name': '日期格式',
            'description': '验证日期格式 (YYYY-MM-DD)',
            'column_name': '出生日期',
            'pattern': r'^\d{4}-\d{2}-\d{2}$',
            'severity': 'medium',
            'enabled': True
        }
    ],
    "relationship_rules": [
        {
            'rule_id': 'id_card_relationships',
            'name': '身份证关系验证',
            'description': '基于身份证号验证出生日期和性别',
            'primary_key': '身份证号',
            'related_columns': {
                '出生日期': 'date',
                '性别': 'gender'
            },
            'validation_type': 'id_card',
            'validation_config': {},
            'severity': 'high',
            'enabled': True
        },
        {
            'rule_id': 'birth_date_comparison',
            'name': '出生日期比较验证',
            'description': '验证注册日期和最后登录日期应该在出生日期之后',
            'primary_key': '出生日期',
            'related_columns': {
                '注册日期': 'after',
                '最后登录日期': 'after'
            },
            'validation_type': 'date_comparison',
            'validation_config': {},
            'severity': 'medium',
            'enabled': True
        },
        {
            'rule_id': 'registration_order',
            'name': '注册顺序验证',
            'description': '验证最后登录日期应该在注册日期之后',
            'primary_key': '注册日期',
            'related_columns': {
                '最后登录日期': 'after'
            },
            'validation_type': 'date_comparison',
            'validation_config': {},
            'severity': 'medium',
            'enabled': True
        }
    ]
}

# 日期格式配置
DATE_FORMATS = [
    '%Y-%m-%d',
    '%Y/%m/%d',
    '%Y.%m.%d',
    '%Y-%m-%d %H:%M:%S',
    '%Y/%m/%d %H:%M:%S',
    '%Y%m%d'
]

# 验证类型配置
VALIDATION_TYPES = {
    "id_card": "身份证验证",
    "date_comparison": "日期比较",
    "numeric_comparison": "数值比较",
    "custom": "自定义验证"
}

# 比较类型配置
COMPARISON_TYPES = {
    "date_comparison": [
        {"value": "after", "label": "之后"},
        {"value": "before", "label": "之前"},
        {"value": "equal", "label": "等于"},
        {"value": "after_or_equal", "label": "之后或等于"},
        {"value": "before_or_equal", "label": "之前或等于"}
    ],
    "numeric_comparison": [
        {"value": "greater", "label": "大于"},
        {"value": "less", "label": "小于"},
        {"value": "equal", "label": "等于"},
        {"value": "greater_or_equal", "label": "大于或等于"},
        {"value": "less_or_equal", "label": "小于或等于"}
    ],
    "custom": [
        {"value": "contains", "label": "包含"},
        {"value": "not_contains", "label": "不包含"},
        {"value": "equals", "label": "等于"},
        {"value": "not_equals", "label": "不等于"}
    ],
    "id_card": [
        {"value": "date", "label": "日期"},
        {"value": "gender", "label": "性别"}
    ]
}

# 严重程度配置
SEVERITY_LEVELS = [
    {"value": "low", "label": "低"},
    {"value": "medium", "label": "中"},
    {"value": "high", "label": "高"}
]

# 关系验证配置
RELATIONSHIP_VALIDATION = {
    "id_card": {
        "columns": {
            "date": "出生日期",
            "gender": "性别"
        },
        "gender_map": {
            "male": "男",
            "female": "女"
        }
    }
}

# 错误消息模板配置
ERROR_MESSAGES = {
    "id_card_birthdate_mismatch": "出生日期与身份证号不符，身份证号显示出生日期为{}",
    "id_card_gender_mismatch": "性别与身份证号不符，身份证号显示性别为{}",
    "date_comparison_after": "{column_name}应该在{primary_key}之后",
    "date_comparison_before": "{column_name}应该在{primary_key}之前",
    "date_comparison_equal": "{column_name}应该等于{primary_key}",
    "date_comparison_after_or_equal": "{column_name}应该在{primary_key}之后或等于",
    "date_comparison_before_or_equal": "{column_name}应该在{primary_key}之前或等于",
    "numeric_comparison_greater": "{column_name}应该大于{primary_key}",
    "numeric_comparison_less": "{column_name}应该小于{primary_key}",
    "numeric_comparison_equal": "{column_name}应该等于{primary_key}",
    "numeric_comparison_greater_or_equal": "{column_name}应该大于或等于{primary_key}",
    "numeric_comparison_less_or_equal": "{column_name}应该小于或等于{primary_key}",
    "custom_contains": "{column_name}应该包含{primary_key}",
    "custom_not_contains": "{column_name}不应该包含{primary_key}",
    "custom_equals": "{column_name}应该等于{primary_key}",
    "custom_not_equals": "{column_name}不应该等于{primary_key}"
}

# API 响应消息配置
MESSAGES = {
    "no_file_uploaded": "No file uploaded",
    "file_loaded_successfully": "File loaded successfully",
    "no_data_loaded": "No data loaded",
    "rule_added_successfully": "Rule added successfully",
    "rule_updated_successfully": "Rule updated successfully",
    "rule_deleted_successfully": "Rule deleted successfully",
    "rule_not_found": "Rule not found",
    "no_valid_data_found": "No valid data found",
    "invalid_regex_pattern": "Invalid regex pattern: {}",
    "column_not_found": "Column {} not found",
    "no_violations_found": "No violations found"
}

# 分页默认配置
PAGINATION = {
    "default_page": 1,
    "default_page_size": 20,
    "max_page_size": 1000
}

# 应用配置
APP_CONFIG = {
    "debug": True,
    "host": "127.0.0.1",
    "port": 5000
}
