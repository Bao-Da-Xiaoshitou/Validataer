const BASE_URL = "http://127.0.0.1:5000";

// 全局状态
let currentPage = 1;
let totalPages = 1;
let totalRows = 0;

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    initDragAndDrop();
});

// 初始化拖放功能
function initDragAndDrop() {
    const dropArea = document.getElementById('dropArea');
    const fileInput = document.getElementById('fileInput');

    // 点击上传区域触发文件选择
    dropArea.addEventListener('click', function(e) {
        if (e.target !== fileInput) {
            fileInput.click();
        }
    });

    // 文件选择变化时自动上传
    fileInput.addEventListener('change', function() {
        if (fileInput.files.length > 0) {
            uploadFile();
        }
    });

    // 拖放事件
    dropArea.addEventListener('dragover', function(e) {
        e.preventDefault();
        dropArea.classList.add('dragover');
    });

    dropArea.addEventListener('dragleave', function(e) {
        e.preventDefault();
        dropArea.classList.remove('dragover');
    });

    dropArea.addEventListener('drop', function(e) {
        e.preventDefault();
        dropArea.classList.remove('dragover');

        const files = e.dataTransfer.files;
        if (files.length > 0) {
            // 检查是否是CSV文件
            const file = files[0];
            if (file.name.toLowerCase().endsWith('.csv')) {
                fileInput.files = files;
                uploadFile();
            } else {
                alert('请上传CSV文件');
            }
        }
    });
}

// 上传CSV
async function uploadFile() {
    const fileInput = document.getElementById("fileInput");
    const file = fileInput.files[0];

    if (!file) {
        alert("请选择文件");
        return;
    }

    const formData = new FormData();
    formData.append("file", file);

    try {
        const res = await fetch(`${BASE_URL}/upload`, {
            method: "POST",
            body: formData
        });

        const data = await res.json();
        if (data.error) {
            alert(`上传失败: ${data.error}`);
            return;
        }

        // 更新数据信息
        totalRows = data.rows;
        document.getElementById('dataStats').textContent = `共 ${data.rows} 行 / ${data.columns.length} 列`;

        // 重置到第一页
        currentPage = 1;

        // 自动加载数据
        await loadData();

        // 隐藏上传区域，显示数据区域
        document.querySelector('.upload-section').style.display = 'none';
        document.querySelector('.data-info').style.display = 'flex';

    } catch (error) {
        alert(`上传失败: ${error.message}`);
    }
}

// 重新上传
function resetUpload() {
    document.getElementById('fileInput').value = '';
    document.querySelector('.upload-section').style.display = 'block';
    document.querySelector('.data-info').style.display = 'none';
    document.getElementById('dataTable').querySelector('thead').innerHTML = '';
    document.getElementById('dataTable').querySelector('tbody').innerHTML = '';
    document.getElementById('dataStats').textContent = '共 0 行 / 0 列';
    currentPage = 1;
    totalPages = 1;
    totalRows = 0;
    updatePaginationInfo();
}

// 加载数据
async function loadData() {
    const pageSize = parseInt(document.getElementById("pageSize").value);

    try {
        const url = `${BASE_URL}/data?page=${currentPage}&page_size=${pageSize}`;

        const res = await fetch(url);
        const result = await res.json();

        if (result.error) {
            alert(`加载失败: ${result.error}`);
            return;
        }

        // 更新总页数
        totalRows = result.total_rows;
        totalPages = Math.ceil(totalRows / pageSize);

        // 渲染表格
        renderTable(result.columns, result.data);

        // 更新分页信息
        updatePaginationInfo();

    } catch (error) {
        alert(`加载失败: ${error.message}`);
    }
}

// 更新分页信息
function updatePaginationInfo() {
    const pageSize = parseInt(document.getElementById("pageSize").value);
    const startRow = (currentPage - 1) * pageSize + 1;
    const endRow = Math.min(currentPage * pageSize, totalRows);

    document.getElementById('startRow').textContent = totalRows > 0 ? startRow : 0;
    document.getElementById('endRow').textContent = endRow;
    document.getElementById('totalRows').textContent = totalRows;

    // 更新按钮状态
    document.getElementById('prevBtn').disabled = currentPage <= 1;
    document.getElementById('nextBtn').disabled = currentPage >= totalPages;

    // 生成页码索引
    generatePageNumbers();
}

// 生成页码索引
function generatePageNumbers() {
    const pageNumbersContainer = document.getElementById('pageNumbers');
    pageNumbersContainer.innerHTML = '';

    if (totalPages <= 1) {
        return;
    }

    const maxVisiblePages = 7; // 最多显示的页码数
    let startPage, endPage;

    if (totalPages <= maxVisiblePages) {
        // 页数较少，全部显示
        startPage = 1;
        endPage = totalPages;
    } else {
        // 页数较多，显示部分页码
        if (currentPage <= 4) {
            startPage = 1;
            endPage = maxVisiblePages - 2;
        } else if (currentPage >= totalPages - 3) {
            startPage = totalPages - (maxVisiblePages - 3);
            endPage = totalPages;
        } else {
            startPage = currentPage - 2;
            endPage = currentPage + 2;
        }
    }

    // 添加第一页
    if (startPage > 1) {
        addPageNumber(1);
        if (startPage > 2) {
            addEllipsis();
        }
    }

    // 添加中间页码
    for (let i = startPage; i <= endPage; i++) {
        addPageNumber(i);
    }

    // 添加最后一页
    if (endPage < totalPages) {
        if (endPage < totalPages - 1) {
            addEllipsis();
        }
        addPageNumber(totalPages);
    }
}

// 添加页码按钮
function addPageNumber(page) {
    const pageNumbersContainer = document.getElementById('pageNumbers');
    const pageBtn = document.createElement('button');
    pageBtn.className = 'page-number';
    pageBtn.textContent = page;
    if (page === currentPage) {
        pageBtn.classList.add('active');
    }
    pageBtn.onclick = function() {
        currentPage = page;
        loadData();
    };
    pageNumbersContainer.appendChild(pageBtn);
}

// 添加省略号
function addEllipsis() {
    const pageNumbersContainer = document.getElementById('pageNumbers');
    const ellipsis = document.createElement('span');
    ellipsis.className = 'page-number ellipsis';
    ellipsis.textContent = '...';
    pageNumbersContainer.appendChild(ellipsis);
}

// 上一页
function prevPage() {
    if (currentPage > 1) {
        currentPage--;
        loadData();
    }
}

// 下一页
function nextPage() {
    if (currentPage < totalPages) {
        currentPage++;
        loadData();
    }
}

// 渲染表格
function renderTable(columns, data) {
    const thead = document.querySelector("#dataTable thead");
    const tbody = document.querySelector("#dataTable tbody");

    thead.innerHTML = "";
    tbody.innerHTML = "";

    if (columns.length === 0) {
        return;
    }

    // 表头
    let headerRow = "<tr>";
    columns.forEach(col => {
        headerRow += `<th>${escapeHtml(col)}</th>`;
    });
    headerRow += "</tr>";
    thead.innerHTML = headerRow;

    // 数据
    if (data.length === 0) {
        tbody.innerHTML = `<tr><td colspan="${columns.length}" style="text-align: center; color: #999;">暂无数据</td></tr>`;
        return;
    }

    data.forEach(row => {
        let rowHtml = "<tr>";
        columns.forEach(col => {
            const value = row[col] !== null && row[col] !== undefined ? row[col] : "";
            rowHtml += `<td>${escapeHtml(String(value))}</td>`;
        });
        rowHtml += "</tr>";
        tbody.innerHTML += rowHtml;
    });
}

// HTML转义，防止XSS攻击
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// DLP扫描功能
let violationsCurrentPage = 1;
let violationsTotalPages = 1;
let violationsTotal = 0;

// 扫描数据
async function scanData() {
    try {
        const res = await fetch(`${BASE_URL}/scan`, {
            method: 'POST'
        });

        const result = await res.json();

        if (result.error) {
            alert(`扫描失败: ${result.error}`);
            return;
        }

        // 显示扫描结果
        showScanResults(result);
    } catch (error) {
        alert(`扫描失败: ${error.message}`);
    }
}

// 显示扫描结果
function showScanResults(result) {
    const scanResults = document.getElementById('scanResults');
    const scanSummary = document.getElementById('scanSummary');

    // 显示摘要
    scanSummary.innerHTML = `
        <div class="summary-item">
            <div class="summary-count">${result.total_violations}</div>
            <div class="summary-label">总违规数</div>
        </div>
        <div class="summary-item">
            <div class="summary-count summary-high">${result.severity_count.high}</div>
            <div class="summary-label">高危</div>
        </div>
        <div class="summary-item">
            <div class="summary-count summary-medium">${result.severity_count.medium}</div>
            <div class="summary-label">中危</div>
        </div>
        <div class="summary-item">
            <div class="summary-count summary-low">${result.severity_count.low}</div>
            <div class="summary-label">低危</div>
        </div>
    `;

    violationsCurrentPage = 1;
    violationsTotal = result.total_violations;
    violationsTotalPages = Math.ceil(violationsTotal / 20);


    loadViolations();

    scanResults.style.display = 'flex';
    scanResults.classList.add('active');
}

function closeScanResults() {
    const scanResults = document.getElementById('scanResults');
    scanResults.style.display = 'none';
    scanResults.classList.remove('active');
}

// 加载违规数据
async function loadViolations() {
    try {
        const res = await fetch(`${BASE_URL}/violations?page=${violationsCurrentPage}&page_size=20`);
        const result = await res.json();

        if (result.error) {
            alert(`加载违规数据失败: ${result.error}`);
            return;
        }

        renderViolations(result.violations);
        renderViolationsPagination();
    } catch (error) {
        alert(`加载违规数据失败: ${error.message}`);
    }
}

// 渲染违规数据表格
function renderViolations(violations) {
    const tbody = document.getElementById('violationsTableBody');
    tbody.innerHTML = '';

    if (violations.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" style="text-align: center; color: #999;">暂无违规数据</td></tr>';
        return;
    }

    violations.forEach(v => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${v.row_index}</td>
            <td>${escapeHtml(v.column)}</td>
            <td>${escapeHtml(v.value)}</td>
            <td>${escapeHtml(v.rule_name)}</td>
            <td><span class="severity-badge severity-${v.severity}">${getSeverityText(v.severity)}</span></td>
        `;
        tbody.appendChild(row);
    });
}

// 渲染违规数据分页
function renderViolationsPagination() {
    const pagination = document.getElementById('violationsPagination');
    pagination.innerHTML = '';

    if (violationsTotalPages <= 1) {
        return;
    }

    // 上一页按钮
    const prevBtn = document.createElement('button');
    prevBtn.textContent = '上一页';
    prevBtn.disabled = violationsCurrentPage <= 1;
    prevBtn.onclick = function() {
        violationsCurrentPage--;
        loadViolations();
    };
    pagination.appendChild(prevBtn);

    // 页码
    const maxVisiblePages = 7;
    let startPage, endPage;

    if (violationsTotalPages <= maxVisiblePages) {
        startPage = 1;
        endPage = violationsTotalPages;
    } else {
        if (violationsCurrentPage <= 4) {
            startPage = 1;
            endPage = maxVisiblePages - 2;
        } else if (violationsCurrentPage >= violationsTotalPages - 3) {
            startPage = violationsTotalPages - (maxVisiblePages - 3);
            endPage = violationsTotalPages;
        } else {
            startPage = violationsCurrentPage - 2;
            endPage = violationsCurrentPage + 2;
        }
    }

    for (let i = startPage; i <= endPage; i++) {
        const pageBtn = document.createElement('button');
        pageBtn.className = 'page-number';
        pageBtn.textContent = i;
        if (i === violationsCurrentPage) {
            pageBtn.classList.add('active');
        }
        pageBtn.onclick = function() {
            violationsCurrentPage = i;
            loadViolations();
        };
        pagination.appendChild(pageBtn);
    }

    // 下一页按钮
    const nextBtn = document.createElement('button');
    nextBtn.textContent = '下一页';
    nextBtn.disabled = violationsCurrentPage >= violationsTotalPages;
    nextBtn.onclick = function() {
        violationsCurrentPage++;
        loadViolations();
    };
    pagination.appendChild(nextBtn);
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

// ==================== 数据验证功能 ====================

let validationCurrentPage = 1;
let validationTotalPages = 1;
let validationTotal = 0;

// 验证数据
async function validateData() {
    try {
        const res = await fetch(`${BASE_URL}/validate`, {
            method: 'POST'
        });

        const result = await res.json();

        if (result.error) {
            alert(`验证失败: ${result.error}`);
            return;
        }

        // 显示验证结果
        showValidationResults(result);
    } catch (error) {
        alert(`验证失败: ${error.message}`);
    }
}

// 显示验证结果
function showValidationResults(result) {
    const validationResults = document.getElementById('validationResults');
    const validationSummary = document.getElementById('validationSummary');

    // 显示摘要
    validationSummary.innerHTML = `
        <div class="summary-item">
            <div class="summary-count">${result.total_rows}</div>
            <div class="summary-label">总行数</div>
        </div>
        <div class="summary-item">
            <div class="summary-count summary-high">${result.invalid_rows}</div>
            <div class="summary-label">错误行数</div>
        </div>
        <div class="summary-item">
            <div class="summary-count summary-low">${result.valid_rows}</div>
            <div class="summary-label">有效行数</div>
        </div>
        <div class="summary-item">
            <div class="summary-count">${result.severity_count.high}</div>
            <div class="summary-label">高危错误</div>
        </div>
        <div class="summary-item">
            <div class="summary-count">${result.severity_count.medium}</div>
            <div class="summary-label">中危错误</div>
        </div>
        <div class="summary-item">
            <div class="summary-count">${result.severity_count.low}</div>
            <div class="summary-label">低危错误</div>
        </div>
    `;

    validationCurrentPage = 1;
    validationTotal = result.invalid_rows;
    validationTotalPages = Math.ceil(validationTotal / 20);

    loadInvalidData();

    validationResults.style.display = 'flex';
    validationResults.classList.add('active');
}

function closeValidationResults() {
    const validationResults = document.getElementById('validationResults');
    validationResults.style.display = 'none';
    validationResults.classList.remove('active');
}

// 加载验证失败的数据
async function loadInvalidData() {
    try {
        const res = await fetch(`${BASE_URL}/invalid_data?page=${validationCurrentPage}&page_size=20`);
        const result = await res.json();

        if (result.error) {
            alert(`加载验证数据失败: ${result.error}`);
            return;
        }

        renderInvalidData(result.invalid_records);
        renderValidationPagination();
    } catch (error) {
        alert(`加载验证数据失败: ${error.message}`);
    }
}

// 渲染验证失败数据表格
function renderInvalidData(invalidRecords) {
    const tbody = document.getElementById('invalidDataTableBody');
    tbody.innerHTML = '';

    if (invalidRecords.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; color: #999;">暂无验证失败数据</td></tr>';
        return;
    }

    invalidRecords.forEach(record => {
        record.errors.forEach(error => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${record.row_index}</td>
                <td>${escapeHtml(error.column)}</td>
                <td>${escapeHtml(error.value)}</td>
                <td>${escapeHtml(error.rule_name)}</td>
                <td><span class="severity-badge severity-${error.severity}">${getSeverityText(error.severity)}</span></td>
                <td>${escapeHtml(error.expected_pattern)}</td>
            `;
            tbody.appendChild(row);
        });
    });
}

// 渲染验证数据分页
function renderValidationPagination() {
    const pagination = document.getElementById('validationPagination');
    pagination.innerHTML = '';

    if (validationTotalPages <= 1) {
        return;
    }

    // 上一页按钮
    const prevBtn = document.createElement('button');
    prevBtn.textContent = '上一页';
    prevBtn.disabled = validationCurrentPage <= 1;
    prevBtn.onclick = function() {
        validationCurrentPage--;
        loadInvalidData();
    };
    pagination.appendChild(prevBtn);

    // 页码
    const maxVisiblePages = 7;
    let startPage, endPage;

    if (validationTotalPages <= maxVisiblePages) {
        startPage = 1;
        endPage = validationTotalPages;
    } else {
        if (validationCurrentPage <= 4) {
            startPage = 1;
            endPage = maxVisiblePages - 2;
        } else if (validationCurrentPage >= validationTotalPages - 3) {
            startPage = validationTotalPages - (maxVisiblePages - 3);
            endPage = validationTotalPages;
        } else {
            startPage = validationCurrentPage - 2;
            endPage = validationCurrentPage + 2;
        }
    }

    for (let i = startPage; i <= endPage; i++) {
        const pageBtn = document.createElement('button');
        pageBtn.className = 'page-number';
        pageBtn.textContent = i;
        if (i === validationCurrentPage) {
            pageBtn.classList.add('active');
        }
        pageBtn.onclick = function() {
            validationCurrentPage = i;
            loadInvalidData();
        };
        pagination.appendChild(pageBtn);
    }

    // 下一页按钮
    const nextBtn = document.createElement('button');
    nextBtn.textContent = '下一页';
    nextBtn.disabled = validationCurrentPage >= validationTotalPages;
    nextBtn.onclick = function() {
        validationCurrentPage++;
        loadInvalidData();
    };
    pagination.appendChild(nextBtn);
}

// 自定义验证
function validateColumn() {
    // 加载列信息
    loadColumns();
    
    const modal = document.getElementById('customValidationModal');
    modal.style.display = 'flex';
}

// 加载列信息
async function loadColumns() {
    try {
        const res = await fetch(`${BASE_URL}/data?page=1&page_size=1`);
        const result = await res.json();
        
        if (result.error) {
            alert(`加载列信息失败: ${result.error}`);
            return;
        }
        
        const columnSelect = document.getElementById('columnSelect');
        columnSelect.innerHTML = '';
        
        result.columns.forEach(column => {
            const option = document.createElement('option');
            option.value = column;
            option.textContent = column;
            columnSelect.appendChild(option);
        });
    } catch (error) {
        alert(`加载列信息失败: ${error.message}`);
    }
}

function closeCustomValidation() {
    const modal = document.getElementById('customValidationModal');
    modal.style.display = 'none';
}

// 执行自定义验证
async function runCustomValidation() {
    const columnSelect = document.getElementById('columnSelect');
    const regexPattern = document.getElementById('regexPattern');
    
    const columnName = columnSelect.value;
    const pattern = regexPattern.value;
    
    if (!columnName || !pattern) {
        alert('请选择列并输入正则表达式');
        return;
    }
    
    try {
        const res = await fetch(`${BASE_URL}/validate_column`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ column_name: columnName, pattern: pattern })
        });
        
        const result = await res.json();
        
        if (result.error) {
            alert(`验证失败: ${result.error}`);
            return;
        }
        
        // 关闭模态框
        closeCustomValidation();
        
        // 显示自定义验证结果
        showCustomValidationResults(result);
    } catch (error) {
        alert(`验证失败: ${error.message}`);
    }
}

// 显示自定义验证结果
function showCustomValidationResults(result) {
    const customValidationResults = document.getElementById('customValidationResults');
    const customValidationSummary = document.getElementById('customValidationSummary');
    
    // 显示摘要
    customValidationSummary.innerHTML = `
        <div class="summary-item">
            <div class="summary-count">${result.total_rows}</div>
            <div class="summary-label">总行数</div>
        </div>
        <div class="summary-item">
            <div class="summary-count summary-high">${result.invalid_count}</div>
            <div class="summary-label">验证失败数</div>
        </div>
        <div class="summary-item">
            <div class="summary-count">${result.column}</div>
            <div class="summary-label">验证列</div>
        </div>
        <div class="summary-item">
            <div class="summary-count">${result.pattern}</div>
            <div class="summary-label">正则表达式</div>
        </div>
    `;
    
    // 渲染验证失败数据
    const tbody = document.getElementById('customInvalidDataTableBody');
    tbody.innerHTML = '';
    
    if (result.invalid_records.length === 0) {
        tbody.innerHTML = '<tr><td colspan="4" style="text-align: center; color: #999;">所有数据都符合验证规则</td></tr>';
    } else {
        result.invalid_records.forEach(record => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${record.row_index}</td>
                <td>${escapeHtml(record.column)}</td>
                <td>${escapeHtml(record.value)}</td>
                <td>${escapeHtml(record.expected_pattern)}</td>
            `;
            tbody.appendChild(row);
        });
    }
    
    customValidationResults.style.display = 'flex';
    customValidationResults.classList.add('active');
}

function closeCustomValidationResults() {
    const customValidationResults = document.getElementById('customValidationResults');
    customValidationResults.style.display = 'none';
    customValidationResults.classList.remove('active');
}

// 处理CSV文件
async function processCsv() {
    try {
        const res = await fetch(`${BASE_URL}/process_csv`, {
            method: 'POST'
        });

        if (!res.ok) {
            const errorData = await res.json();
            alert(`处理失败: ${errorData.error || '未知错误'}`);
            return;
        }

        // 创建下载链接
        const blob = await res.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        a.download = 'processed_data.csv';
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);

        alert('智能处理完成！已下载包含关系验证的处理文件');
    } catch (error) {
        alert(`处理失败: ${error.message}`);
    }
}

// 快速清洗CSV文件
async function processCsvQuick() {
    try {
        const res = await fetch(`${BASE_URL}/process_csv_quick`, {
            method: 'POST'
        });

        if (!res.ok) {
            const errorData = await res.json();
            alert(`处理失败: ${errorData.error || '未知错误'}`);
            return;
        }

        // 创建下载链接
        const blob = await res.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        a.download = 'processed_data_quick.csv';
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);

        alert('快速清洗完成！已下载处理后的CSV文件');
    } catch (error) {
        alert(`处理失败: ${error.message}`);
    }
}

// 关系验证
async function validateRelationships() {
    try {
        const res = await fetch(`${BASE_URL}/validate_relationships`, {
            method: 'POST'
        });

        const result = await res.json();

        if (result.error) {
            alert(`验证失败: ${result.error}`);
            return;
        }

        // 显示关系验证结果
        showRelationshipResults(result);
    } catch (error) {
        alert(`验证失败: ${error.message}`);
    }
}

// 显示关系验证结果
function showRelationshipResults(result) {
    const relationshipResults = document.getElementById('relationshipResults');
    const relationshipSummary = document.getElementById('relationshipSummary');

    // 显示摘要
    relationshipSummary.innerHTML = `
        <div class="summary-item">
            <div class="summary-count">${result.total_errors}</div>
            <div class="summary-label">关系验证错误数</div>
        </div>
        <div class="summary-item">
            <div class="summary-count summary-high">${result.severity_count.high}</div>
            <div class="summary-label">高危错误</div>
        </div>
        <div class="summary-item">
            <div class="summary-count summary-medium">${result.severity_count.medium}</div>
            <div class="summary-label">中危错误</div>
        </div>
        <div class="summary-item">
            <div class="summary-count summary-low">${result.severity_count.low}</div>
            <div class="summary-label">低危错误</div>
        </div>
    `;

    // 渲染关系验证错误数据
    const tbody = document.getElementById('relationshipTableBody');
    tbody.innerHTML = '';

    if (result.errors.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; color: #999;">关系验证通过，无错误</td></tr>';
    } else {
        result.errors.forEach(error => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${error.row_index}</td>
                <td>${escapeHtml(error.column)}</td>
                <td>${escapeHtml(error.value)}</td>
                <td>${escapeHtml(error.expected_value)}</td>
                <td>${escapeHtml(error.rule_name)}</td>
                <td><span class="severity-badge severity-${error.severity}">${getSeverityText(error.severity)}</span></td>
                <td>${escapeHtml(error.description)}</td>
            `;
            tbody.appendChild(row);
        });
    }

    relationshipResults.style.display = 'flex';
    relationshipResults.classList.add('active');
}

function closeRelationshipResults() {
    const relationshipResults = document.getElementById('relationshipResults');
    relationshipResults.style.display = 'none';
    relationshipResults.classList.remove('active');
}

// ==================== 自定义关系验证功能 ====================

let relatedColumnCount = 0;

// 打开自定义关系验证对话框
async function openRelationshipValidationModal() {
    // 加载列信息
    await loadColumnsForRelationshipValidation();
    
    // 初始化关联列配置
    updateRelatedColumnsUI();
    
    const modal = document.getElementById('relationshipValidationModal');
    modal.style.display = 'flex';
}

// 加载列信息到关系验证对话框
async function loadColumnsForRelationshipValidation() {
    try {
        const res = await fetch(`${BASE_URL}/data?page=1&page_size=1`);
        const result = await res.json();
        
        if (result.error) {
            alert(`加载列信息失败: ${result.error}`);
            return;
        }
        
        const primaryKeySelect = document.getElementById('primaryKey');
        primaryKeySelect.innerHTML = '';
        
        result.columns.forEach(column => {
            const option = document.createElement('option');
            option.value = column;
            option.textContent = column;
            primaryKeySelect.appendChild(option);
        });
    } catch (error) {
        alert(`加载列信息失败: ${error.message}`);
    }
}

// 更新关联列配置界面
function updateRelatedColumnsUI() {
    const validationType = document.getElementById('validationType').value;
    const container = document.getElementById('relatedColumnsContainer');
    
    // 清空现有内容
    container.innerHTML = '';
    relatedColumnCount = 0;
    
    // 根据验证类型显示不同的配置选项
    if (validationType === 'date_comparison') {
        addRelatedColumn('after');
        addRelatedColumn('after_or_equal');
    } else if (validationType === 'numeric_comparison') {
        addRelatedColumn('greater');
        addRelatedColumn('less');
    } else if (validationType === 'custom') {
        addRelatedColumn('contains');
        addRelatedColumn('equals');
    } else if (validationType === 'id_card') {
        addRelatedColumn('date');
        addRelatedColumn('gender');
    }
}

// 添加关联列配置
function addRelatedColumn(defaultComparisonType = 'after') {
    const container = document.getElementById('relatedColumnsContainer');
    const validationType = document.getElementById('validationType').value;
    
    const item = document.createElement('div');
    item.className = 'related-column-item';
    
    // 获取可用的列
    const primaryKeySelect = document.getElementById('primaryKey');
    const availableColumns = Array.from(primaryKeySelect.options).map(opt => opt.value);
    
    let comparisonOptions = '';
    
    if (validationType === 'date_comparison') {
        comparisonOptions = `
            <option value="after">之后</option>
            <option value="before">之前</option>
            <option value="equal">等于</option>
            <option value="after_or_equal">之后或等于</option>
            <option value="before_or_equal">之前或等于</option>
        `;
    } else if (validationType === 'numeric_comparison') {
        comparisonOptions = `
            <option value="greater">大于</option>
            <option value="less">小于</option>
            <option value="equal">等于</option>
            <option value="greater_or_equal">大于或等于</option>
            <option value="less_or_equal">小于或等于</option>
        `;
    } else if (validationType === 'custom') {
        comparisonOptions = `
            <option value="contains">包含</option>
            <option value="not_contains">不包含</option>
            <option value="equals">等于</option>
            <option value="not_equals">不等于</option>
        `;
    } else if (validationType === 'id_card') {
        comparisonOptions = `
            <option value="date">日期</option>
            <option value="gender">性别</option>
        `;
    }
    
    let columnOptions = '';
    availableColumns.forEach(column => {
        columnOptions += `<option value="${column}">${column}</option>`;
    });
    
    item.innerHTML = `
        <select class="related-column-select">
            ${columnOptions}
        </select>
        <select class="comparison-type-select">
            ${comparisonOptions}
        </select>
        <button onclick="removeRelatedColumn(this)">删除</button>
    `;
    
    container.appendChild(item);
    relatedColumnCount++;
}

// 删除关联列配置
function removeRelatedColumn(button) {
    const item = button.parentElement;
    item.remove();
    relatedColumnCount--;
}

// 保存关系验证规则
async function saveRelationshipRule() {
    const ruleId = document.getElementById('ruleId').value.trim();
    const ruleName = document.getElementById('ruleName').value.trim();
    const ruleDescription = document.getElementById('ruleDescription').value.trim();
    const primaryKey = document.getElementById('primaryKey').value;
    const validationType = document.getElementById('validationType').value;
    const severity = document.getElementById('severity').value;
    
    if (!ruleId || !ruleName || !primaryKey) {
        alert('请填写规则ID、规则名称和主键列');
        return;
    }
    
    // 收集关联列配置
    const relatedColumns = {};
    const container = document.getElementById('relatedColumnsContainer');
    const items = container.querySelectorAll('.related-column-item');
    
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
    
    // 构建规则数据
    const ruleData = {
        rule_id: ruleId,
        name: ruleName,
        description: ruleDescription,
        primary_key: primaryKey,
        related_columns: relatedColumns,
        validation_type: validationType,
        validation_config: {},
        severity: severity,
        enabled: true
    };
    
    try {
        const res = await fetch(`${BASE_URL}/relationship_rules`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(ruleData)
        });
        
        const result = await res.json();
        
        if (result.error) {
            alert(`保存规则失败: ${result.error}`);
            return;
        }
        
        alert('规则保存成功！');
        
        // 关闭对话框并清空表单
        closeRelationshipValidationModal();
        clearRelationshipValidationForm();
        
        // 重新验证数据
        await validateRelationships();
    } catch (error) {
        alert(`保存规则失败: ${error.message}`);
    }
}

// 关闭自定义关系验证对话框
function closeRelationshipValidationModal() {
    const modal = document.getElementById('relationshipValidationModal');
    modal.style.display = 'none';
}

// 清空关系验证表单
function clearRelationshipValidationForm() {
    document.getElementById('ruleId').value = '';
    document.getElementById('ruleName').value = '';
    document.getElementById('ruleDescription').value = '';
    document.getElementById('primaryKey').selectedIndex = 0;
    document.getElementById('validationType').selectedIndex = 0;
    document.getElementById('severity').selectedIndex = 0;
    document.getElementById('relatedColumnsContainer').innerHTML = '';
    relatedColumnCount = 0;
}
