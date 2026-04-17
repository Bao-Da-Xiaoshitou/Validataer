#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DLP Lite - 规则驱动的数据泄露检测系统
"""

import re
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
import os
from config import RULES_CONFIG, DEFAULT_RULES

class DLPRule:
    """DLP规则类"""
    
    def __init__(self, rule_id: str, name: str, description: str, 
                 pattern: str, rule_type: str = "regex", 
                 severity: str = "medium", enabled: bool = True):
        self.rule_id = rule_id
        self.name = name
        self.description = description
        self.pattern = pattern
        self.rule_type = rule_type
        self.severity = severity
        self.enabled = enabled
        self.created_at = datetime.now().isoformat()
        
        # 编译正则表达式
        if rule_type == "regex":
            try:
                self.compiled_pattern = re.compile(pattern, re.IGNORECASE)
            except re.error as e:
                raise ValueError(f"Invalid regex pattern: {e}")
        else:
            self.compiled_pattern = None
    
    def match(self, text: str) -> bool:
        """检查文本是否匹配规则"""
        if not self.enabled or not text:
            return False
            
        if self.rule_type == "regex":
            return bool(self.compiled_pattern.search(str(text)))
        elif self.rule_type == "exact":
            return str(text).lower() == self.pattern.lower()
        elif self.rule_type == "contains":
            return self.pattern.lower() in str(text).lower()
        return False
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'rule_id': self.rule_id,
            'name': self.name,
            'description': self.description,
            'pattern': self.pattern,
            'rule_type': self.rule_type,
            'severity': self.severity,
            'enabled': self.enabled,
            'created_at': self.created_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DLPRule':
        """从字典创建规则"""
        return cls(
            rule_id=data['rule_id'],
            name=data['name'],
            description=data['description'],
            pattern=data['pattern'],
            rule_type=data['rule_type'],
            severity=data['severity'],
            enabled=data['enabled']
        )


class DLPRuleManager:
    """DLP规则管理器"""
    
    def __init__(self, rules_file: str = None):
        self.rules_file = rules_file or RULES_CONFIG["dlp_rules_file"]
        self.rules: List[DLPRule] = []
        self.load_rules()
        
        # 如果没有规则，加载默认规则
        if not self.rules:
            self.load_default_rules()
    
    def load_default_rules(self):
        """加载默认的DLP规则"""
        for rule_data in DEFAULT_RULES["dlp_rules"]:
            self.add_rule(DLPRule.from_dict(rule_data))
        
        self.save_rules()
    
    def load_rules(self):
        """从文件加载规则"""
        if os.path.exists(self.rules_file):
            try:
                with open(self.rules_file, 'r', encoding='utf-8') as f:
                    rules_data = json.load(f)
                    self.rules = [DLPRule.from_dict(data) for data in rules_data]
            except Exception as e:
                print(f"加载规则失败: {e}")
                self.rules = []
    
    def save_rules(self):
        """保存规则到文件"""
        try:
            with open(self.rules_file, 'w', encoding='utf-8') as f:
                json.dump([rule.to_dict() for rule in self.rules], f, 
                         indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"保存规则失败: {e}")
    
    def add_rule(self, rule: DLPRule):
        """添加规则"""
        self.rules.append(rule)
        self.save_rules()
    
    def update_rule(self, rule_id: str, rule_data: Dict[str, Any]) -> bool:
        """更新规则"""
        for i, rule in enumerate(self.rules):
            if rule.rule_id == rule_id:
                updated_rule = DLPRule(
                    rule_id=rule_id,
                    name=rule_data.get('name', rule.name),
                    description=rule_data.get('description', rule.description),
                    pattern=rule_data.get('pattern', rule.pattern),
                    rule_type=rule_data.get('rule_type', rule.rule_type),
                    severity=rule_data.get('severity', rule.severity),
                    enabled=rule_data.get('enabled', rule.enabled)
                )
                self.rules[i] = updated_rule
                self.save_rules()
                return True
        return False
    
    def delete_rule(self, rule_id: str) -> bool:
        """删除规则"""
        for i, rule in enumerate(self.rules):
            if rule.rule_id == rule_id:
                del self.rules[i]
                self.save_rules()
                return True
        return False
    
    def get_rule(self, rule_id: str) -> Optional[DLPRule]:
        """获取规则"""
        for rule in self.rules:
            if rule.rule_id == rule_id:
                return rule
        return None
    
    def get_all_rules(self) -> List[Dict[str, Any]]:
        """获取所有规则"""
        return [rule.to_dict() for rule in self.rules]
    
    def get_enabled_rules(self) -> List[DLPRule]:
        """获取启用的规则"""
        return [rule for rule in self.rules if rule.enabled]


class DLPDetector:
    
    def __init__(self, rule_manager: DLPRuleManager):
        self.rule_manager = rule_manager
    
    def detect_data(self, data: List[Dict[str, Any]], 
                    columns: List[str]) -> Dict[str, Any]:
        """检测数据中的敏感信息"""
        violations = []
        enabled_rules = self.rule_manager.get_enabled_rules()
        
        for row_idx, row in enumerate(data):
            for col in columns:
                cell_value = row.get(col, "")
                if not cell_value:
                    continue
                
                for rule in enabled_rules:
                    if rule.match(cell_value):
                        violation = {
                            'row_index': row_idx + 1,
                            'column': col,
                            'value': str(cell_value)[:100],
                            'rule_id': rule.rule_id,
                            'rule_name': rule.name,
                            'severity': rule.severity,
                            'description': rule.description
                        }
                        violations.append(violation)
        
        # 统计信息
        severity_count = {
            'high': 0,
            'medium': 0,
            'low': 0
        }
        
        for v in violations:
            severity_count[v['severity']] += 1
        
        return {
            'total_violations': len(violations),
            'severity_count': severity_count,
            'violations': violations,
            'scan_time': datetime.now().isoformat()
        }
    
    def extract_violations(self, data: List[Dict[str, Any]], 
                          violations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """提取违规数据"""
        extracted = []
        seen = set()
        
        for violation in violations:
            row_idx = violation['row_index'] - 1
            if row_idx < len(data) and row_idx not in seen:
                extracted.append({
                    'row_index': violation['row_index'],
                    'data': data[row_idx],
                    'violations': [v for v in violations if v['row_index'] == violation['row_index']]
                })
                seen.add(row_idx)
        
        return extracted


rule_manager = DLPRuleManager()
dlp_detector = DLPDetector(rule_manager)
