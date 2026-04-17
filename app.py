from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import pandas as pd
from matcher import rule_manager, dlp_detector, DLPRule
from data_validator import validation_rule_manager, data_validator, ColumnValidationRule, RelationshipValidationRule
from config import MESSAGES, PAGINATION, APP_CONFIG

app = Flask(__name__)
CORS(app)

DATA = None
VIOLATIONS = None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/rules_page')
def rules_page():
    return render_template('rules.html')

@app.route('/relationship_rules_page')
def relationship_rules_page():
    return render_template('relationship_rules.html')

@app.route('/upload', methods=['POST'])
def upload_csv():
    global DATA

    file = request.files.get('file')
    if not file:
        return jsonify({'error': MESSAGES["no_file_uploaded"]}), 400

    try:
        DATA = pd.read_csv(file)
        return jsonify({
            'message': MESSAGES["file_loaded_successfully"],
            'rows': DATA.shape[0],
            'columns': list(DATA.columns)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/data', methods=['GET'])
def get_data():
    global DATA

    if DATA is None:
        return jsonify({'error': MESSAGES["no_data_loaded"]}), 400

    page = int(request.args.get('page', PAGINATION["default_page"]))
    page_size = int(request.args.get('page_size', PAGINATION["default_page_size"]))

    start_row = (page - 1) * page_size
    end_row = start_row + page_size

    df_slice = DATA.iloc[start_row:end_row]

    return jsonify({
        'page': page,
        'page_size': page_size,
        'total_rows': DATA.shape[0],
        'total_columns': len(DATA.columns),
        'columns': list(DATA.columns),
        'data': df_slice.fillna("").to_dict(orient='records')
    })

# DLP规则管理API
@app.route('/rules', methods=['GET'])
def get_rules():
    """获取所有DLP规则"""
    return jsonify(rule_manager.get_all_rules())

@app.route('/rules', methods=['POST'])
def add_rule():
    """添加DLP规则"""
    try:
        data = request.json
        rule = DLPRule(
            rule_id=data['rule_id'],
            name=data['name'],
            description=data['description'],
            pattern=data['pattern'],
            rule_type=data.get('rule_type', 'regex'),
            severity=data.get('severity', 'medium'),
            enabled=data.get('enabled', True)
        )
        rule_manager.add_rule(rule)
        return jsonify({'message': MESSAGES["rule_added_successfully"], 'rule': rule.to_dict()})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/rules/<rule_id>', methods=['PUT'])
def update_rule(rule_id):
    """更新DLP规则"""
    try:
        data = request.json
        success = rule_manager.update_rule(rule_id, data)
        if success:
            return jsonify({'message': MESSAGES["rule_updated_successfully"]})
        else:
            return jsonify({'error': MESSAGES["rule_not_found"]}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/rules/<rule_id>', methods=['DELETE'])
def delete_rule(rule_id):
    """删除DLP规则"""
    success = rule_manager.delete_rule(rule_id)
    if success:
        return jsonify({'message': MESSAGES["rule_deleted_successfully"]})
    else:
        return jsonify({'error': MESSAGES["rule_not_found"]}), 404

@app.route('/scan', methods=['POST'])
def scan_data():
    global DATA, VIOLATIONS

    if DATA is None:
        return jsonify({'error': MESSAGES["no_data_loaded"]}), 400

    try:
        columns = list(DATA.columns)
        data = DATA.fillna("").to_dict(orient='records')
        
        result = dlp_detector.detect_data(data, columns)
        VIOLATIONS = result['violations']
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/violations', methods=['GET'])
def get_violations():
    """获取违规数据"""
    global DATA, VIOLATIONS

    if DATA is None or VIOLATIONS is None:
        return jsonify({'error': MESSAGES["no_violations_found"]}), 400

    try:
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 20))

        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size

        extracted = dlp_detector.extract_violations(
            DATA.fillna("").to_dict(orient='records'),
            VIOLATIONS
        )

        paginated = extracted[start_idx:end_idx]

        return jsonify({
            'page': page,
            'page_size': page_size,
            'total': len(extracted),
            'violations': paginated
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== 数据验证 API ====================

@app.route('/validate', methods=['POST'])
def validate_data():
    """
    验证数据
    """
    global DATA

    if DATA is None:
        return jsonify({'error': MESSAGES["no_data_loaded"]}), 400

    try:
        columns = list(DATA.columns)
        data = DATA.fillna("").to_dict(orient='records')
        result = data_validator.validate_data(data, columns)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/invalid_data', methods=['GET'])
def get_invalid_data():
    """
    获取验证失败的数据
    """
    global DATA

    if DATA is None:
        return jsonify({'error': MESSAGES["no_data_loaded"]}), 400

    try:
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 20))

        columns = list(DATA.columns)
        data = DATA.fillna("").to_dict(orient='records')
        result = data_validator.validate_data(data, columns)

        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated = result['invalid_records'][start_idx:end_idx]

        return jsonify({
            'page': page,
            'page_size': page_size,
            'total': len(result['invalid_records']),
            'invalid_records': paginated
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/validate_column', methods=['POST'])
def validate_column():
    """
    验证指定列
    """
    global DATA

    if DATA is None:
        return jsonify({'error': MESSAGES["no_data_loaded"]}), 400

    try:
        data = request.json
        column_name = data['column_name']
        pattern = data['pattern']

        if column_name not in DATA.columns:
            return jsonify({'error': MESSAGES["column_not_found"].format(column_name)}), 400

        data = DATA.fillna("").to_dict(orient='records')
        result = data_validator.validate_column(data, column_name, pattern)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/validation_rules', methods=['GET'])
def get_validation_rules():
    """获取所有验证规则"""
    return jsonify(validation_rule_manager.get_all_column_rules())


@app.route('/validation_rules', methods=['POST'])
def add_validation_rule():
    """添加验证规则"""
    try:
        data = request.json
        rule = ColumnValidationRule(
            rule_id=data['rule_id'],
            name=data['name'],
            description=data['description'],
            column_name=data['column_name'],
            pattern=data['pattern'],
            severity=data.get('severity', 'medium'),
            enabled=data.get('enabled', True)
        )
        validation_rule_manager.add_column_rule(rule)
        return jsonify({'message': 'Validation rule added successfully', 'rule': rule.to_dict()})
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/validation_rules/<rule_id>', methods=['PUT'])
def update_validation_rule(rule_id):
    """更新验证规则"""
    try:
        data = request.json
        success = validation_rule_manager.update_column_rule(rule_id, data)
        if success:
            return jsonify({'message': 'Validation rule updated successfully'})
        else:
            return jsonify({'error': MESSAGES["rule_not_found"]}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/validation_rules/<rule_id>', methods=['DELETE'])
def delete_validation_rule(rule_id):
    """删除验证规则"""
    success = validation_rule_manager.delete_column_rule(rule_id)
    if success:
        return jsonify({'message': 'Validation rule deleted successfully'})
    else:
        return jsonify({'error': MESSAGES["rule_not_found"]}), 404


@app.route('/relationship_rules', methods=['GET'])
def get_relationship_rules():
    """获取所有关系验证规则"""
    return jsonify(validation_rule_manager.get_all_relationship_rules())


@app.route('/relationship_rules', methods=['POST'])
def add_relationship_rule():
    """添加关系验证规则"""
    try:
        data = request.json
        rule = RelationshipValidationRule(
            rule_id=data['rule_id'],
            name=data['name'],
            description=data['description'],
            primary_key=data['primary_key'],
            related_columns=data['related_columns'],
            validation_type=data.get('validation_type', 'id_card'),
            validation_config=data.get('validation_config', {}),
            severity=data.get('severity', 'high'),
            enabled=data.get('enabled', True)
        )
        validation_rule_manager.add_relationship_rule(rule)
        return jsonify({'message': 'Relationship rule added successfully', 'rule': rule.to_dict()})
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/relationship_rules/<rule_id>', methods=['PUT'])
def update_relationship_rule(rule_id):
    """更新关系验证规则"""
    try:
        data = request.json
        success = validation_rule_manager.update_relationship_rule(rule_id, data)
        if success:
            return jsonify({'message': 'Relationship rule updated successfully'})
        else:
            return jsonify({'error': MESSAGES["rule_not_found"]}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/relationship_rules/<rule_id>', methods=['DELETE'])
def delete_relationship_rule(rule_id):
    """删除关系验证规则"""
    success = validation_rule_manager.delete_relationship_rule(rule_id)
    if success:
        return jsonify({'message': 'Relationship rule deleted successfully'})
    else:
        return jsonify({'error': MESSAGES["rule_not_found"]}), 404


@app.route('/validate_relationships', methods=['POST'])
def validate_relationships():
    """
    验证数据中的关系规则
    """
    global DATA

    if DATA is None:
        return jsonify({'error': MESSAGES["no_data_loaded"]}), 400

    try:
        data = DATA.fillna("").to_dict(orient='records')
        result = data_validator.validate_relationships(data)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/process_csv', methods=['POST'])
def process_csv():
    """
    处理CSV文件，剔除违规数据，返回处理后的CSV文件
    """
    global DATA

    if DATA is None:
        return jsonify({'error': MESSAGES["no_data_loaded"]}), 400

    try:
        # 验证并过滤数据（包含关系验证）
        columns = list(DATA.columns)
        data = DATA.fillna("").to_dict(orient='records')
        
        # 过滤出有效数据
        valid_data = data_validator.filter_valid_data(data, columns, include_relationships=True)
        
        if not valid_data:
            return jsonify({'error': MESSAGES["no_valid_data_found"]}), 400

        valid_df = pd.DataFrame(valid_data)

        import io
        output = io.StringIO()
        valid_df.to_csv(output, index=False, encoding='utf-8-sig')
        csv_data = output.getvalue()

        from flask import make_response
        response = make_response(csv_data)
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = 'attachment; filename=processed_data.csv'
        
        return response
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/process_csv_quick', methods=['POST'])
def process_csv_quick():
    """
    快速清洗CSV文件，只使用列级验证，不包含关系验证
    """
    global DATA

    if DATA is None:
        return jsonify({'error': MESSAGES["no_data_loaded"]}), 400

    try:
        # 验证并过滤数据（只使用列级验证）
        columns = list(DATA.columns)
        data = DATA.fillna("").to_dict(orient='records')
        
        # 过滤出有效数据（不包含关系验证）
        valid_data = data_validator.filter_valid_data(data, columns, include_relationships=False)
        
        if not valid_data:
            return jsonify({'error': MESSAGES["no_valid_data_found"]}), 400
        
        # 转换为DataFrame
        valid_df = pd.DataFrame(valid_data)
        
        # 生成CSV数据
        import io
        output = io.StringIO()
        valid_df.to_csv(output, index=False, encoding='utf-8-sig')
        csv_data = output.getvalue()
        
        # 设置响应头
        from flask import make_response
        response = make_response(csv_data)
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = 'attachment; filename=processed_data_quick.csv'
        
        return response
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(
        debug=APP_CONFIG["debug"],
        host=APP_CONFIG["host"],
        port=APP_CONFIG["port"]
    )