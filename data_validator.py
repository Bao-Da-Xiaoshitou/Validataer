#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据验证器 - 用于验证CSV数据的格式和关系
"""

import re
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
import os
from config import RULES_CONFIG, DEFAULT_RULES, DATE_FORMATS, RELATIONSHIP_VALIDATION, ERROR_MESSAGES


class ColumnValidationRule:
    """列验证规则类"""
    
    def __init__(self, rule_id: str, name: str, description: str, 
                 column_name: str, pattern: str, 
                 severity: str = "medium", enabled: bool = True):
        self.rule_id = rule_id
        self.name = name
        self.description = description
        self.column_name = column_name
        self.pattern = pattern
        self.severity = severity
        self.enabled = enabled
        self.created_at = datetime.now().isoformat()
        
        # 编译正则表达式
        try:
            self.compiled_pattern = re.compile(pattern, re.IGNORECASE)
        except re.error as e:
            raise ValueError(f"Invalid regex pattern: {e}")
    
    def validate(self, value: Any) -> Dict[str, Any]:
        """验证值是否符合规则"""
        if not self.enabled:
            return None
        
        value_str = str(value)
        if not value_str:
            return None
        
        if not self.compiled_pattern.match(value_str):
            return {
                'column': self.column_name,
                'value': value_str,
                'rule_id': self.rule_id,
                'rule_name': self.name,
                'severity': self.severity,
                'expected_pattern': self.pattern,
                'description': self.description
            }
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'rule_id': self.rule_id,
            'name': self.name,
            'description': self.description,
            'column_name': self.column_name,
            'pattern': self.pattern,
            'severity': self.severity,
            'enabled': self.enabled,
            'created_at': self.created_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ColumnValidationRule':
        """从字典创建规则"""
        return cls(
            rule_id=data['rule_id'],
            name=data['name'],
            description=data['description'],
            column_name=data['column_name'],
            pattern=data['pattern'],
            severity=data['severity'],
            enabled=data['enabled']
        )


class RelationshipValidationRule:
    """关系验证规则类"""
    
    def __init__(self, rule_id: str, name: str, description: str, 
                 primary_key: str, related_columns: Dict[str, str], 
                 validation_type: str = "id_card", 
                 validation_config: Dict[str, Any] = None,
                 severity: str = "high", enabled: bool = True):
        self.rule_id = rule_id
        self.name = name
        self.description = description
        self.primary_key = primary_key
        self.related_columns = related_columns
        self.validation_type = validation_type
        self.validation_config = validation_config or {}
        self.severity = severity
        self.enabled = enabled
        self.created_at = datetime.now().isoformat()
    
    def validate(self, row: Dict[str, Any]) -> List[Dict[str, Any]]:
        """验证行数据中的关系"""
        errors = []
        if not self.enabled:
            return errors
        
        primary_value = row.get(self.primary_key, "")
        if not primary_value:
            return errors
        
        # 根据验证类型选择不同的验证逻辑
        if self.validation_type == "id_card":
            errors.extend(self._validate_id_card_relationships(row, primary_value))
        elif self.validation_type == "date_comparison":
            errors.extend(self._validate_date_comparison(row, primary_value))
        elif self.validation_type == "numeric_comparison":
            errors.extend(self._validate_numeric_comparison(row, primary_value))
        elif self.validation_type == "custom":
            errors.extend(self._validate_custom(row, primary_value))
        
        return errors
    
    def _validate_id_card_relationships(self, row: Dict[str, Any], id_card: str) -> List[Dict[str, Any]]:
        """验证身份证号相关的关系"""
        errors = []
        try:
            # 验证身份证号格式
            if not re.match(r'^\d{17}[\dXx]$', id_card):
                return errors
            
            # 提取出生日期
            birth_year = id_card[6:10]
            birth_month = id_card[10:12]
            birth_day = id_card[12:14]
            expected_birthdate = f"{birth_year}-{birth_month}-{birth_day}"
            
            # 提取性别
            gender_code = int(id_card[16])
            expected_gender = RELATIONSHIP_VALIDATION["id_card"]["gender_map"]["male"] if gender_code % 2 == 1 else RELATIONSHIP_VALIDATION["id_card"]["gender_map"]["female"]
            
            # 验证出生日期
            birthdate_column = RELATIONSHIP_VALIDATION["id_card"]["columns"]["date"]
            if birthdate_column in self.related_columns:
                actual_birthdate = str(row.get(birthdate_column, "")).strip()
                if actual_birthdate:
                    # 统一日期格式
                    actual_birthdate = actual_birthdate.replace("/", "-").replace(".", "-")
                    if actual_birthdate != expected_birthdate:
                        errors.append({
                            'column': birthdate_column,
                            'value': actual_birthdate,
                            'expected_value': expected_birthdate,
                            'rule_id': self.rule_id,
                            'rule_name': self.name,
                            'severity': self.severity,
                            'description': ERROR_MESSAGES["id_card_birthdate_mismatch"].format(expected_birthdate)
                        })
            
            # 验证性别
            gender_column = RELATIONSHIP_VALIDATION["id_card"]["columns"]["gender"]
            if gender_column in self.related_columns:
                actual_gender = str(row.get(gender_column, "")).strip()
                if actual_gender:
                    if actual_gender != expected_gender:
                        errors.append({
                            'column': gender_column,
                            'value': actual_gender,
                            'expected_value': expected_gender,
                            'rule_id': self.rule_id,
                            'rule_name': self.name,
                            'severity': self.severity,
                            'description': ERROR_MESSAGES["id_card_gender_mismatch"].format(expected_gender)
                        })
        except Exception as e:
            pass
        
        return errors
    
    def _validate_date_comparison(self, row: Dict[str, Any], primary_date: str) -> List[Dict[str, Any]]:
        """验证日期比较关系"""
        errors = []
        try:
            # 解析主日期
            primary_date_obj = self._parse_date(primary_date)
            if not primary_date_obj:
                return errors
            
            # 验证每个关联日期字段
            for column_name, comparison_type in self.related_columns.items():
                related_date = str(row.get(column_name, "")).strip()
                if not related_date:
                    continue
                
                related_date_obj = self._parse_date(related_date)
                if not related_date_obj:
                    continue
                
                # 根据比较类型进行验证
                is_valid = True
                error_msg = ""
                
                if comparison_type == "after" or comparison_type == ">":
                    is_valid = related_date_obj > primary_date_obj
                    error_msg = ERROR_MESSAGES["date_comparison_after"].format(column_name=column_name, primary_key=self.primary_key)
                elif comparison_type == "before" or comparison_type == "<":
                    is_valid = related_date_obj < primary_date_obj
                    error_msg = ERROR_MESSAGES["date_comparison_before"].format(column_name=column_name, primary_key=self.primary_key)
                elif comparison_type == "equal" or comparison_type == "==":
                    is_valid = related_date_obj == primary_date_obj
                    error_msg = ERROR_MESSAGES["date_comparison_equal"].format(column_name=column_name, primary_key=self.primary_key)
                elif comparison_type == "after_or_equal" or comparison_type == ">=":
                    is_valid = related_date_obj >= primary_date_obj
                    error_msg = ERROR_MESSAGES["date_comparison_after_or_equal"].format(column_name=column_name, primary_key=self.primary_key)
                elif comparison_type == "before_or_equal" or comparison_type == "<=":
                    is_valid = related_date_obj <= primary_date_obj
                    error_msg = ERROR_MESSAGES["date_comparison_before_or_equal"].format(column_name=column_name, primary_key=self.primary_key)
                
                if not is_valid:
                    errors.append({
                        'column': column_name,
                        'value': related_date,
                        'expected_value': f"{comparison_type} {primary_date}",
                        'rule_id': self.rule_id,
                        'rule_name': self.name,
                        'severity': self.severity,
                        'description': error_msg
                    })
        except Exception as e:
            pass
        
        return errors
    
    def _validate_numeric_comparison(self, row: Dict[str, Any], primary_value: str) -> List[Dict[str, Any]]:
        """验证数值比较关系"""
        errors = []
        try:
            # 解析主数值
            primary_num = float(primary_value)
            
            # 验证每个关联数值字段
            for column_name, comparison_type in self.related_columns.items():
                related_value = str(row.get(column_name, "")).strip()
                if not related_value:
                    continue
                
                try:
                    related_num = float(related_value)
                except ValueError:
                    continue
                
                # 根据比较类型进行验证
                is_valid = True
                error_msg = ""
                
                if comparison_type == "greater" or comparison_type == ">":
                    is_valid = related_num > primary_num
                    error_msg = ERROR_MESSAGES["numeric_comparison_greater"].format(column_name=column_name, primary_key=self.primary_key)
                elif comparison_type == "less" or comparison_type == "<":
                    is_valid = related_num < primary_num
                    error_msg = ERROR_MESSAGES["numeric_comparison_less"].format(column_name=column_name, primary_key=self.primary_key)
                elif comparison_type == "equal" or comparison_type == "==":
                    is_valid = related_num == primary_num
                    error_msg = ERROR_MESSAGES["numeric_comparison_equal"].format(column_name=column_name, primary_key=self.primary_key)
                elif comparison_type == "greater_or_equal" or comparison_type == ">=":
                    is_valid = related_num >= primary_num
                    error_msg = ERROR_MESSAGES["numeric_comparison_greater_or_equal"].format(column_name=column_name, primary_key=self.primary_key)
                elif comparison_type == "less_or_equal" or comparison_type == "<=":
                    is_valid = related_num <= primary_num
                    error_msg = ERROR_MESSAGES["numeric_comparison_less_or_equal"].format(column_name=column_name, primary_key=self.primary_key)
                
                if not is_valid:
                    errors.append({
                        'column': column_name,
                        'value': related_value,
                        'expected_value': f"{comparison_type} {primary_value}",
                        'rule_id': self.rule_id,
                        'rule_name': self.name,
                        'severity': self.severity,
                        'description': error_msg
                    })
        except Exception as e:
            pass
        
        return errors
    
    def _validate_custom(self, row: Dict[str, Any], primary_value: str) -> List[Dict[str, Any]]:
        """自定义验证逻辑"""
        errors = []
        try:
            # 从配置中获取自定义验证规则
            custom_rules = self.validation_config.get('custom_rules', [])
            
            for custom_rule in custom_rules:
                column_name = custom_rule.get('column')
                validation_func = custom_rule.get('validation_func')
                
                if not column_name or not validation_func:
                    continue
                
                related_value = str(row.get(column_name, "")).strip()
                if not related_value:
                    continue
                
                # 执行自定义验证函数
                is_valid = True
                error_msg = ""
                
                if validation_func == "contains":
                    is_valid = primary_value in related_value
                    error_msg = ERROR_MESSAGES["custom_contains"].format(column_name=column_name, primary_key=self.primary_key)
                elif validation_func == "not_contains":
                    is_valid = primary_value not in related_value
                    error_msg = ERROR_MESSAGES["custom_not_contains"].format(column_name=column_name, primary_key=self.primary_key)
                elif validation_func == "equals":
                    is_valid = primary_value == related_value
                    error_msg = ERROR_MESSAGES["custom_equals"].format(column_name=column_name, primary_key=self.primary_key)
                elif validation_func == "not_equals":
                    is_valid = primary_value != related_value
                    error_msg = ERROR_MESSAGES["custom_not_equals"].format(column_name=column_name, primary_key=self.primary_key)
                
                if not is_valid:
                    errors.append({
                        'column': column_name,
                        'value': related_value,
                        'expected_value': validation_func,
                        'rule_id': self.rule_id,
                        'rule_name': self.name,
                        'severity': self.severity,
                        'description': error_msg
                    })
        except Exception as e:
            pass
        
        return errors
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """解析日期字符串"""
        if not date_str:
            return None
        
        # 尝试不同的日期格式
        for fmt in DATE_FORMATS:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'rule_id': self.rule_id,
            'name': self.name,
            'description': self.description,
            'primary_key': self.primary_key,
            'related_columns': self.related_columns,
            'validation_type': self.validation_type,
            'validation_config': self.validation_config,
            'severity': self.severity,
            'enabled': self.enabled,
            'created_at': self.created_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RelationshipValidationRule':
        """从字典创建规则"""
        return cls(
            rule_id=data['rule_id'],
            name=data['name'],
            description=data['description'],
            primary_key=data['primary_key'],
            related_columns=data['related_columns'],
            validation_type=data.get('validation_type', 'id_card'),
            validation_config=data.get('validation_config', {}),
            severity=data['severity'],
            enabled=data['enabled']
        )


class ValidationRuleManager:
    """验证规则管理器"""
    
    def __init__(self, column_rules_file: str = None, 
                 relationship_rules_file: str = None):
        self.column_rules_file = column_rules_file or RULES_CONFIG["validation_rules_file"]
        self.relationship_rules_file = relationship_rules_file or RULES_CONFIG["relationship_rules_file"]
        self.column_rules: List[ColumnValidationRule] = []
        self.relationship_rules: List[RelationshipValidationRule] = []
        
        self.load_column_rules()
        self.load_relationship_rules()
        
        # 如果没有列验证规则，加载默认规则
        if not self.column_rules:
            self.load_default_column_rules()
        
        # 如果没有关系验证规则，加载默认规则
        if not self.relationship_rules:
            self.load_default_relationship_rules()
    
    def load_default_column_rules(self):
        """加载默认的列验证规则"""
        for rule_data in DEFAULT_RULES["validation_rules"]:
            self.add_column_rule(ColumnValidationRule.from_dict(rule_data))
        
        self.save_column_rules()
    
    def load_default_relationship_rules(self):
        """加载默认的关系验证规则"""
        for rule_data in DEFAULT_RULES["relationship_rules"]:
            self.add_relationship_rule(RelationshipValidationRule.from_dict(rule_data))
        
        self.save_relationship_rules()
    
    def load_column_rules(self):
        """从文件加载列验证规则"""
        if os.path.exists(self.column_rules_file):
            try:
                with open(self.column_rules_file, 'r', encoding='utf-8') as f:
                    rules_data = json.load(f)
                    self.column_rules = [ColumnValidationRule.from_dict(data) for data in rules_data]
            except Exception as e:
                print(f"加载列验证规则失败: {e}")
                self.column_rules = []
    
    def save_column_rules(self):
        """保存列验证规则到文件"""
        try:
            with open(self.column_rules_file, 'w', encoding='utf-8') as f:
                json.dump([rule.to_dict() for rule in self.column_rules], f, 
                         indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"保存列验证规则失败: {e}")
    
    def load_relationship_rules(self):
        """从文件加载关系验证规则"""
        if os.path.exists(self.relationship_rules_file):
            try:
                with open(self.relationship_rules_file, 'r', encoding='utf-8') as f:
                    rules_data = json.load(f)
                    self.relationship_rules = [RelationshipValidationRule.from_dict(data) for data in rules_data]
            except Exception as e:
                print(f"加载关系验证规则失败: {e}")
                self.relationship_rules = []
    
    def save_relationship_rules(self):
        """保存关系验证规则到文件"""
        try:
            with open(self.relationship_rules_file, 'w', encoding='utf-8') as f:
                json.dump([rule.to_dict() for rule in self.relationship_rules], f, 
                         indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"保存关系验证规则失败: {e}")
    
    def add_column_rule(self, rule: ColumnValidationRule):
        """添加列验证规则"""
        self.column_rules.append(rule)
        self.save_column_rules()
    
    def update_column_rule(self, rule_id: str, rule_data: Dict[str, Any]) -> bool:
        """更新列验证规则"""
        for i, rule in enumerate(self.column_rules):
            if rule.rule_id == rule_id:
                updated_rule = ColumnValidationRule(
                    rule_id=rule_id,
                    name=rule_data.get('name', rule.name),
                    description=rule_data.get('description', rule.description),
                    column_name=rule_data.get('column_name', rule.column_name),
                    pattern=rule_data.get('pattern', rule.pattern),
                    severity=rule_data.get('severity', rule.severity),
                    enabled=rule_data.get('enabled', rule.enabled)
                )
                self.column_rules[i] = updated_rule
                self.save_column_rules()
                return True
        return False
    
    def delete_column_rule(self, rule_id: str) -> bool:
        """删除列验证规则"""
        for i, rule in enumerate(self.column_rules):
            if rule.rule_id == rule_id:
                del self.column_rules[i]
                self.save_column_rules()
                return True
        return False
    
    def add_relationship_rule(self, rule: RelationshipValidationRule):
        """添加关系验证规则"""
        self.relationship_rules.append(rule)
        self.save_relationship_rules()
    
    def update_relationship_rule(self, rule_id: str, rule_data: Dict[str, Any]) -> bool:
        """更新关系验证规则"""
        for i, rule in enumerate(self.relationship_rules):
            if rule.rule_id == rule_id:
                updated_rule = RelationshipValidationRule(
                    rule_id=rule_id,
                    name=rule_data.get('name', rule.name),
                    description=rule_data.get('description', rule.description),
                    primary_key=rule_data.get('primary_key', rule.primary_key),
                    related_columns=rule_data.get('related_columns', rule.related_columns),
                    validation_type=rule_data.get('validation_type', rule.validation_type),
                    validation_config=rule_data.get('validation_config', rule.validation_config),
                    severity=rule_data.get('severity', rule.severity),
                    enabled=rule_data.get('enabled', rule.enabled)
                )
                self.relationship_rules[i] = updated_rule
                self.save_relationship_rules()
                return True
        return False
    
    def delete_relationship_rule(self, rule_id: str) -> bool:
        """删除关系验证规则"""
        for i, rule in enumerate(self.relationship_rules):
            if rule.rule_id == rule_id:
                del self.relationship_rules[i]
                self.save_relationship_rules()
                return True
        return False
    
    def get_all_column_rules(self) -> List[Dict[str, Any]]:
        """获取所有列验证规则"""
        return [rule.to_dict() for rule in self.column_rules]
    
    def get_all_relationship_rules(self) -> List[Dict[str, Any]]:
        """获取所有关系验证规则"""
        return [rule.to_dict() for rule in self.relationship_rules]
    
    def get_enabled_column_rules(self) -> List[ColumnValidationRule]:
        """获取启用的列验证规则"""
        return [rule for rule in self.column_rules if rule.enabled]
    
    def get_enabled_relationship_rules(self) -> List[RelationshipValidationRule]:
        """获取启用的关系验证规则"""
        return [rule for rule in self.relationship_rules if rule.enabled]


class DataValidator:
    """数据验证器"""
    
    def __init__(self, rule_manager: ValidationRuleManager):
        self.rule_manager = rule_manager
    
    def validate_data(self, data: List[Dict[str, Any]], 
                      columns: List[str]) -> Dict[str, Any]:
        """验证数据"""
        invalid_records = []
        severity_count = {
            'high': 0,
            'medium': 0,
            'low': 0
        }
        
        enabled_rules = self.rule_manager.get_enabled_column_rules()
        
        for row_idx, row in enumerate(data):
            errors = []
            
            for rule in enabled_rules:
                if rule.column_name in columns:
                    value = row.get(rule.column_name, "")
                    error = rule.validate(value)
                    if error:
                        errors.append(error)
                        severity_count[error['severity']] += 1
            
            if errors:
                invalid_records.append({
                    'row_index': row_idx + 1,
                    'data': row,
                    'errors': errors
                })
        
        total_rows = len(data)
        valid_rows = total_rows - len(invalid_records)
        
        return {
            'total_rows': total_rows,
            'valid_rows': valid_rows,
            'invalid_rows': len(invalid_records),
            'severity_count': severity_count,
            'invalid_records': invalid_records,
            'validation_time': datetime.now().isoformat()
        }
    
    def validate_relationships(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """验证数据中的关系"""
        errors = []
        severity_count = {
            'high': 0,
            'medium': 0,
            'low': 0
        }
        
        enabled_rules = self.rule_manager.get_enabled_relationship_rules()
        
        for row_idx, row in enumerate(data):
            for rule in enabled_rules:
                rule_errors = rule.validate(row)
                for error in rule_errors:
                    error['row_index'] = row_idx + 1
                    errors.append(error)
                    severity_count[error['severity']] += 1
        
        return {
            'total_errors': len(errors),
            'severity_count': severity_count,
            'errors': errors,
            'validation_time': datetime.now().isoformat()
        }
    
    def validate_column(self, data: List[Dict[str, Any]], 
                       column_name: str, pattern: str) -> Dict[str, Any]:
        """验证指定列"""
        invalid_records = []
        
        try:
            compiled_pattern = re.compile(pattern, re.IGNORECASE)
        except re.error as e:
            return {'error': f'Invalid regex pattern: {e}'}
        
        for row_idx, row in enumerate(data):
            value = row.get(column_name, "")
            value_str = str(value)
            
            if value_str and not compiled_pattern.match(value_str):
                invalid_records.append({
                    'row_index': row_idx + 1,
                    'column': column_name,
                    'value': value_str,
                    'expected_pattern': pattern
                })
        
        return {
            'total_rows': len(data),
            'invalid_count': len(invalid_records),
            'column': column_name,
            'pattern': pattern,
            'invalid_records': invalid_records
        }
    
    def filter_valid_data(self, data: List[Dict[str, Any]], 
                          columns: List[str], 
                          include_relationships: bool = True) -> List[Dict[str, Any]]:
        """过滤出有效数据"""
        valid_data = []
        
        enabled_column_rules = self.rule_manager.get_enabled_column_rules()
        enabled_relationship_rules = self.rule_manager.get_enabled_relationship_rules() if include_relationships else []
        
        for row in data:
            # 验证列规则
            column_valid = True
            for rule in enabled_column_rules:
                if rule.column_name in columns:
                    value = row.get(rule.column_name, "")
                    error = rule.validate(value)
                    if error:
                        column_valid = False
                        break
            
            if not column_valid:
                continue
            
            # 验证关系规则
            if include_relationships:
                relationship_valid = True
                for rule in enabled_relationship_rules:
                    errors = rule.validate(row)
                    if errors:
                        relationship_valid = False
                        break
                
                if not relationship_valid:
                    continue
            
            valid_data.append(row)
        
        return valid_data


validation_rule_manager = ValidationRuleManager()
data_validator = DataValidator(validation_rule_manager)