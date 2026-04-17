const BASE_URL = "http://127.0.0.1:5000";

let currentRules = [];
let currentEditingRule = null;
let relatedColumnCount = 0;

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    loadRules();
    loadColumns();
});

// 加载所有关系验证规则
async function loadRules() {
    try {
        const res = await fetch(`${BASE_URL}/relationship_rules`);
        const rules = await res.json();
        currentRules = rules;
        renderRules(rules);
    } catch (error) {
        console.error('加载规则失败:', error);
        alert('加载规则失败');
    }
}

// 加载所有列信息
async function loadColumns() {
    try {
        const res = await fetch(`${BASE_URL}/data?page=1&page_size=1`);
        const result = await res.json();
        
        if (!result.error) {
            const primaryKeySelect = document.getElementById('primaryKey');
            const columns = result.columns;
            
            columns.forEach(column => {
                const option = document.createElement('option');
                option.value = column;
                option.textContent = column;
                primaryKeySelect.appendChild(option);
            });
        }
    } catch (error) {
        console.error('加载列信息失败:', error);
    }
}

// 渲染规则卡片
function renderRules(rules) {
    const container = document.getElementById('rulesContainer');
    container.innerHTML = '';
    
    if (rules.length === 0) {
        container.innerHTML = '<div style="grid-column: 1 / -1; text-align: center; padding: 40px; color: #999;">暂无关系验证规则</div>';
        return;
    }
    
    rules.forEach(rule => {
        const card = createRuleCard(rule);
        container.appendChild(card);
    });
}

// 创建规则卡片
function createRuleCard(rule) {
    const card = document.createElement('div');
    card.className = 'rule-card';
    
    // 生成关联列HTML
    let relatedColumnsHtml = '';
    if (rule.related_columns) {
        Object.entries(rule.related_columns).forEach(([column, comparison]) => {
            relatedColumnsHtml += `
                <div class="related-column-item">
                    <span>${column}</span>
                    <span>${getComparisonText(comparison)}</span>
                </div>
            `;
        });
    }
    
    card.innerHTML = `
        <div class="rule-header">
            <div>
                <div class="rule-title">${rule.name}</div>
                <div class="rule-id">${rule.rule_id}</div>
            </div>
        </div>
        <div class="rule-description">${rule.description}</div>
        <div class="rule-info">
            <div class="rule-info-item">
                <span class="rule-info-label">主键列:</span>
                <span class="rule-info-value">${rule.primary_key}</span>
            </div>
            <div class="rule-info-item">
                <span class="rule-info-label">验证类型:</span>
                <span class="rule-info-value">${getValidationTypeText(rule.validation_type)}</span>
            </div>
        </div>
        ${relatedColumnsHtml ? `
            <div class="related-columns">
                <div class="related-columns-title">关联列:</div>
                ${relatedColumnsHtml}
            </div>
        ` : ''}
        <div class="rule-meta">
            <span class="rule-badge validation-type">${getValidationTypeText(rule.validation_type)}</span>
            <span class="rule-badge severity-${rule.severity}">${getSeverityText(rule.severity)}</span>
        </div>
        <div class="rule-actions">
            <button class="btn-edit" onclick="editRule('${rule.rule_id}')">编辑</button>
            <button class="btn-delete" onclick="deleteRule('${rule.rule_id}')">删除</button>
            <button class="btn-toggle" onclick="toggleRule('${rule.rule_id}', ${rule.enabled ? 'false' : 'true'})")">
                ${rule.enabled ? '禁用' : '启用'}
            </button>
        </div>
    `;
    
    return card;
}

// 获取验证类型文本
function getValidationTypeText(type) {
    const types = {
        'date_comparison': '日期比较',
        'numeric_comparison': '数值比较',
        'custom': '自定义验证',
        'id_card': '身份证验证'
    };
    return types[type] || type;
}

// 获取比较操作文本
function getComparisonText(comparison) {
    const comparisons = {
        'after': '之后',
        'before': '之前',
        'equal': '等于',
        'after_or_equal': '之后或等于',
        'before_or_equal': '之前或等于',
        'greater': '大于',
        'less': '小于',
        'greater_or_equal': '大于或等于',
        'less_or_equal': '小于或等于',
        'contains': '包含',
        'not_contains': '不包含',
        'equals': '等于',
        'not_equals': '不等于',
        'date': '日期',
        'gender': '性别'
    };
    return comparisons[comparison] || comparison;
}

// 获取严重程度文本
function getSeverityText(severity) {
    const severities = {
        'low': '低',
        'medium': '中',
        'high': '高'
    };
    return severities[severity] || severity;
}

// 打开添加/编辑模态框
function openModal(ruleId = null) {
    const modal = document.getElementById('ruleModal');
    const modalTitle = document.getElementById('modalTitle');
    const ruleForm = document.getElementById('ruleForm');
    
    // 重置表单
    ruleForm.reset();
    document.getElementById('relatedColumnsContainer').innerHTML = '';
    relatedColumnCount = 0;
    
    if (ruleId) {
        // 编辑模式
        const rule = currentRules.find(r => r.rule_id === ruleId);
        if (rule) {
            currentEditingRule = rule;
            modalTitle.textContent = '编辑规则';
            document.getElementById('ruleId').value = rule.rule_id;
            document.getElementById('ruleId').disabled = true;
            document.getElementById('ruleName').value = rule.name;
            document.getElementById('ruleDescription').value = rule.description;
            document.getElementById('primaryKey').value = rule.primary_key;
            document.getElementById('validationType').value = rule.validation_type;
            document.getElementById('ruleSeverity').value = rule.severity;
            document.getElementById('ruleEnabled').checked = rule.enabled;
            
            // 加载关联列
            if (rule.related_columns) {
                Object.entries(rule.related_columns).forEach(([column, comparison]) => {
                    addRelatedColumn(column, comparison);
                });
            }
        }
    } else {
        // 添加模式
        currentEditingRule = null;
        modalTitle.textContent = '添加规则';
        document.getElementById('ruleId').disabled = false;
    }
    
    // 更新验证类型UI
    updateValidationTypeUI();
    
    modal.classList.add('active');
}

// 关闭模态框
function closeModal() {
    const modal = document.getElementById('ruleModal');
    modal.classList.remove('active');
    currentEditingRule = null;
}


function updateValidationTypeUI() {
    const validationType = document.getElementById('validationType').value;
    const relatedColumnsContainer = document.getElementById('relatedColumnsContainer');
    
    relatedColumnsContainer.innerHTML = '';
    relatedColumnCount = 0;
    
    // 根据验证类型添加默认关联列
    if (validationType === 'date_comparison') {
        addRelatedColumn('', 'after');
    } else if (validationType === 'numeric_comparison') {
        addRelatedColumn('', 'greater');
    } else if (validationType === 'custom') {
        addRelatedColumn('', 'contains');
    } else if (validationType === 'id_card') {
        addRelatedColumn('出生日期', 'date');
        addRelatedColumn('性别', 'gender');
    }
}

// 添加关联列
function addRelatedColumn(column = '', comparison = 'after') {
    const container = document.getElementById('relatedColumnsContainer');
    const validationType = document.getElementById('validationType').value;
    
    const item = document.createElement('div');
    item.className = 'related-column-form';
    item.dataset.index = relatedColumnCount;
    
    // 获取可用的列
    const primaryKeySelect = document.getElementById('primaryKey');
    const availableColumns = Array.from(primaryKeySelect.options).map(opt => opt.value);
    
    let comparisonOptions = '';
    
    if (validationType === 'date_comparison') {
        comparisonOptions = `
            <option value="after" ${comparison === 'after' ? 'selected' : ''}>之后</option>
            <option value="before" ${comparison === 'before' ? 'selected' : ''}>之前</option>
            <option value="equal" ${comparison === 'equal' ? 'selected' : ''}>等于</option>
            <option value="after_or_equal" ${comparison === 'after_or_equal' ? 'selected' : ''}>之后或等于</option>
            <option value="before_or_equal" ${comparison === 'before_or_equal' ? 'selected' : ''}>之前或等于</option>
        `;
    } else if (validationType === 'numeric_comparison') {
        comparisonOptions = `
            <option value="greater" ${comparison === 'greater' ? 'selected' : ''}>大于</option>
            <option value="less" ${comparison === 'less' ? 'selected' : ''}>小于</option>
            <option value="equal" ${comparison === 'equal' ? 'selected' : ''}>等于</option>
            <option value="greater_or_equal" ${comparison === 'greater_or_equal' ? 'selected' : ''}>大于或等于</option>
            <option value="less_or_equal" ${comparison === 'less_or_equal' ? 'selected' : ''}>小于或等于</option>
        `;
    } else if (validationType === 'custom') {
        comparisonOptions = `
            <option value="contains" ${comparison === 'contains' ? 'selected' : ''}>包含</option>
            <option value="not_contains" ${comparison === 'not_contains' ? 'selected' : ''}>不包含</option>
            <option value="equals" ${comparison === 'equals' ? 'selected' : ''}>等于</option>
            <option value="not_equals" ${comparison === 'not_equals' ? 'selected' : ''}>不等于</option>
        `;
    } else if (validationType === 'id_card') {
        comparisonOptions = `
            <option value="date" ${comparison === 'date' ? 'selected' : ''}>日期</option>
            <option value="gender" ${comparison === 'gender' ? 'selected' : ''}>性别</option>
        `;
    }
    
    let columnOptions = '';
    availableColumns.forEach(col => {
        columnOptions += `<option value="${col}" ${column === col ? 'selected' : ''}>${col}</option>`;
    });
    
    item.innerHTML = `
        <select class="related-column-select">
            ${columnOptions}
        </select>
        <select class="comparison-type-select">
            ${comparisonOptions}
        </select>
        <button type="button" class="btn-remove-column" onclick="removeRelatedColumn(this)">删除</button>
    `;
    
    container.appendChild(item);
    relatedColumnCount++;
}

// 删除关联列
function removeRelatedColumn(button) {
    const item = button.parentElement;
    item.remove();
    relatedColumnCount--;
}

// 提交表单
document.getElementById('ruleForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const ruleId = document.getElementById('ruleId').value;
    const ruleName = document.getElementById('ruleName').value;
    const ruleDescription = document.getElementById('ruleDescription').value;
    const primaryKey = document.getElementById('primaryKey').value;
    const validationType = document.getElementById('validationType').value;
    const severity = document.getElementById('ruleSeverity').value;
    const enabled = document.getElementById('ruleEnabled').checked;
    
    // 收集关联列配置
    const relatedColumns = {};
    const container = document.getElementById('relatedColumnsContainer');
    const items = container.querySelectorAll('.related-column-form');
    
    items.forEach(item => {
        const columnSelect = item.querySelector('.related-column-select');
        const comparisonSelect = item.querySelector('.comparison-type-select');
        
        if (columnSelect && comparisonSelect) {
            relatedColumns[columnSelect.value] = comparisonSelect.value;
        }
    });
    
    if (Object.keys(relatedColumns).length === 0) {
        alert('请至少添加一个关联列配置');
        return;
    }
    
    const ruleData = {
        rule_id: ruleId,
        name: ruleName,
        description: ruleDescription,
        primary_key: primaryKey,
        related_columns: relatedColumns,
        validation_type: validationType,
        validation_config: {},
        severity: severity,
        enabled: enabled
    };
    
    try {
        let res;
        if (currentEditingRule) {
            // 更新规则
            res = await fetch(`${BASE_URL}/relationship_rules/${ruleId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(ruleData)
            });
        } else {
            // 添加规则
            res = await fetch(`${BASE_URL}/relationship_rules`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(ruleData)
            });
        }
        
        const result = await res.json();
        if (result.error) {
            alert(`保存规则失败: ${result.error}`);
            return;
        }
        
        alert('规则保存成功！');
        closeModal();
        loadRules();
    } catch (error) {
        console.error('保存规则失败:', error);
        alert('保存规则失败');
    }
});

// 编辑规则
function editRule(ruleId) {
    openModal(ruleId);
}

// 删除规则
async function deleteRule(ruleId) {
    if (!confirm('确定要删除这个规则吗？')) {
        return;
    }
    
    try {
        const res = await fetch(`${BASE_URL}/relationship_rules/${ruleId}`, {
            method: 'DELETE'
        });
        
        const result = await res.json();
        if (result.error) {
            alert(`删除规则失败: ${result.error}`);
            return;
        }
        
        alert('规则删除成功！');
        loadRules();
    } catch (error) {
        console.error('删除规则失败:', error);
        alert('删除规则失败');
    }
}

// 切换规则启用状态
async function toggleRule(ruleId, enabled) {
    try {
        const res = await fetch(`${BASE_URL}/relationship_rules/${ruleId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ enabled: enabled })
        });
        
        const result = await res.json();
        if (result.error) {
            alert(`更新规则状态失败: ${result.error}`);
            return;
        }
        
        loadRules();
    } catch (error) {
        console.error('更新规则状态失败:', error);
        alert('更新规则状态失败');
    }
}