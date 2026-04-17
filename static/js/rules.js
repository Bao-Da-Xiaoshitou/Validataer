const BASE_URL = "http://127.0.0.1:5000";
let editingRuleId = null;

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    loadRules();
});

// 加载所有规则
async function loadRules() {
    try {
        const res = await fetch(`${BASE_URL}/rules`);
        const rules = await res.json();
        renderRules(rules);
    } catch (error) {
        alert(`加载规则失败: ${error.message}`);
    }
}

// 渲染规则卡片
function renderRules(rules) {
    const container = document.getElementById('rulesContainer');
    container.innerHTML = '';

    if (rules.length === 0) {
        container.innerHTML = '<p style="text-align: center; color: #999; grid-column: 1/-1;">暂无规则</p>';
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
    card.innerHTML = `
        <div class="rule-header">
            <div>
                <div class="rule-title">${escapeHtml(rule.name)}</div>
                <span class="rule-id">${escapeHtml(rule.rule_id)}</span>
            </div>
            <div class="switch-container">
                <label class="switch">
                    <input type="checkbox" ${rule.enabled ? 'checked' : ''} onchange="toggleRule('${rule.rule_id}', this.checked)">
                    <span class="slider"></span>
                </label>
            </div>
        </div>
        <div class="rule-description">${escapeHtml(rule.description)}</div>
        <div class="rule-pattern">${escapeHtml(rule.pattern)}</div>
        <div class="rule-meta">
            <span class="rule-badge severity-${rule.severity}">
                ${getSeverityText(rule.severity)}
            </span>
            <span class="rule-badge rule-type">
                ${getRuleTypeText(rule.rule_type)}
            </span>
        </div>
        <div class="rule-actions">
            <button class="btn-edit" onclick="editRule('${rule.rule_id}')">编辑</button>
            <button class="btn-delete" onclick="deleteRule('${rule.rule_id}')">删除</button>
        </div>
    `;
    return card;
}

// 获取严重程度文本
function getSeverityText(severity) {
    const map = {
        'high': '高危',
        'medium': '中危',
        'low': '低危'
    };
    return map[severity] || severity;
}

// 获取规则类型文本
function getRuleTypeText(type) {
    const map = {
        'regex': '正则表达式',
        'exact': '精确匹配',
        'contains': '包含匹配'
    };
    return map[type] || type;
}

// 打开模态框
function openModal(rule = null) {
    const modal = document.getElementById('ruleModal');
    const title = document.getElementById('modalTitle');
    const form = document.getElementById('ruleForm');

    if (rule) {
        editingRuleId = rule.rule_id;
        title.textContent = '编辑规则';
        document.getElementById('ruleId').value = rule.rule_id;
        document.getElementById('ruleId').disabled = true;
        document.getElementById('ruleName').value = rule.name;
        document.getElementById('ruleDescription').value = rule.description;
        document.getElementById('ruleType').value = rule.rule_type;
        document.getElementById('rulePattern').value = rule.pattern;
        document.getElementById('ruleSeverity').value = rule.severity;
        document.getElementById('ruleEnabled').checked = rule.enabled;
    } else {
        editingRuleId = null;
        title.textContent = '添加规则';
        form.reset();
        document.getElementById('ruleId').disabled = false;
        document.getElementById('ruleEnabled').checked = true;
    }

    modal.classList.add('active');
}

// 关闭模态框
function closeModal() {
    const modal = document.getElementById('ruleModal');
    modal.classList.remove('active');
    editingRuleId = null;
}

// 编辑规则
function editRule(ruleId) {
    const rule = findRule(ruleId);
    if (rule) {
        openModal(rule);
    }
}

// 查找规则
async function findRule(ruleId) {
    try {
        const res = await fetch(`${BASE_URL}/rules`);
        const rules = await res.json();
        return rules.find(r => r.rule_id === ruleId);
    } catch (error) {
        alert(`查找规则失败: ${error.message}`);
        return null;
    }
}

// 删除规则
async function deleteRule(ruleId) {
    if (!confirm('确定要删除这个规则吗？')) {
        return;
    }

    try {
        const res = await fetch(`${BASE_URL}/rules/${ruleId}`, {
            method: 'DELETE'
        });

        if (res.ok) {
            alert('规则删除成功');
            loadRules();
        } else {
            const error = await res.json();
            alert(`删除失败: ${error.error}`);
        }
    } catch (error) {
        alert(`删除失败: ${error.message}`);
    }
}

// 切换规则启用状态
async function toggleRule(ruleId, enabled) {
    try {
        const res = await fetch(`${BASE_URL}/rules/${ruleId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ enabled })
        });

        if (!res.ok) {
            const error = await res.json();
            alert(`更新失败: ${error.error}`);
            loadRules(); // 重新加载以恢复状态
        }
    } catch (error) {
        alert(`更新失败: ${error.message}`);
        loadRules(); // 重新加载以恢复状态
    }
}

// 表单提交
document.getElementById('ruleForm').addEventListener('submit', async function(e) {
    e.preventDefault();

    const ruleData = {
        rule_id: document.getElementById('ruleId').value,
        name: document.getElementById('ruleName').value,
        description: document.getElementById('ruleDescription').value,
        rule_type: document.getElementById('ruleType').value,
        pattern: document.getElementById('rulePattern').value,
        severity: document.getElementById('ruleSeverity').value,
        enabled: document.getElementById('ruleEnabled').checked
    };

    try {
        let res;
        if (editingRuleId) {
            // 更新规则
            res = await fetch(`${BASE_URL}/rules/${editingRuleId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(ruleData)
            });
        } else {
            // 添加规则
            res = await fetch(`${BASE_URL}/rules`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(ruleData)
            });
        }

        if (res.ok) {
            alert(editingRuleId ? '规则更新成功' : '规则添加成功');
            closeModal();
            loadRules();
        } else {
            const error = await res.json();
            alert(`${editingRuleId ? '更新' : '添加'}失败: ${error.error}`);
        }
    } catch (error) {
        alert(`${editingRuleId ? '更新' : '添加'}失败: ${error.message}`);
    }
});

// HTML转义
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// 点击模态框外部关闭
document.getElementById('ruleModal').addEventListener('click', function(e) {
    if (e.target === this) {
        closeModal();
    }
});
