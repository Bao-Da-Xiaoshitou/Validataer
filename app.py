from flask import Flask, request, jsonify, render_template, make_response
from flask_cors import CORS
import pandas as pd
from data_validator import validation_rule_manager, data_validator, ColumnValidationRule, RelationshipValidationRule
from config import MESSAGES, PAGINATION, APP_CONFIG
import io
import os
import uuid
import shutil

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'
CORS(app)

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
os.makedirs(UPLOAD_DIR, exist_ok=True)

def get_session_id():
    session_id = request.headers.get('X-Session-ID')
    if not session_id:
        session_id = str(uuid.uuid4())
    return session_id

def get_session_dir(session_id):
    session_dir = os.path.join(UPLOAD_DIR, session_id)
    os.makedirs(session_dir, exist_ok=True)
    return session_dir

def cleanup_session(session_id):
    session_dir = os.path.join(UPLOAD_DIR, session_id)
    if os.path.exists(session_dir):
        shutil.rmtree(session_dir)

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
    file = request.files.get('file')
    if not file:
        return jsonify({'error': MESSAGES["no_file_uploaded"]}), 400

    session_id = get_session_id()
    session_dir = get_session_dir(session_id)

    try:
        original_path = os.path.join(session_dir, 'original.csv')
        df = pd.read_csv(file)
        df.to_csv(original_path, index=False, encoding='utf-8-sig')

        return jsonify({
            'message': MESSAGES["file_loaded_successfully"],
            'rows': len(df),
            'columns': list(df.columns),
            'session_id': session_id
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/data', methods=['GET'])
def get_data():
    session_id = request.args.get('session_id')
    if not session_id:
        return jsonify({'error': 'Missing session ID'}), 400

    data_type = request.args.get('data_type', 'original')
    session_dir = get_session_dir(session_id)

    file_path = None
    if data_type == 'processed':
        file_path = os.path.join(session_dir, 'processed.csv')
    elif data_type == 'rejected':
        file_path = os.path.join(session_dir, 'rejected.csv')
    else:
        file_path = os.path.join(session_dir, 'original.csv')

    if not os.path.exists(file_path):
        if data_type == 'rejected':
            return jsonify({
                'page': 1,
                'page_size': PAGINATION["default_page_size"],
                'total_rows': 0,
                'total_columns': 1,
                'columns': ['剔除原因'],
                'data': []
            })
        return jsonify({'error': MESSAGES["no_data_loaded"]}), 400

    try:
        df = pd.read_csv(file_path)

        if df.empty:
            if data_type == 'rejected':
                columns = ['剔除原因']
            else:
                columns = []
            data = []
        else:
            columns = list(df.columns)
            data = df.to_dict(orient='records')

        page = int(request.args.get('page', PAGINATION["default_page"]))
        page_size = int(request.args.get('page_size', PAGINATION["default_page_size"]))

        start_row = (page - 1) * page_size
        end_row = start_row + page_size

        df_slice = data[start_row:end_row]

        return jsonify({
            'page': page,
            'page_size': page_size,
            'total_rows': len(data),
            'total_columns': len(columns),
            'columns': columns,
            'data': df_slice
        })
    except pd.errors.EmptyDataError:
        if data_type == 'rejected':
            return jsonify({
                'page': 1,
                'page_size': PAGINATION["default_page_size"],
                'total_rows': 0,
                'total_columns': 1,
                'columns': ['剔除原因'],
                'data': []
            })
        return jsonify({'error': MESSAGES["no_data_loaded"]}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/validate', methods=['POST'])
def validate_data():
    session_id = request.form.get('session_id') or request.json.get('session_id') if request.is_json and request.json else request.form.get('session_id')
    if not session_id:
        session_id = request.args.get('session_id')

    if not session_id:
        return jsonify({'error': 'Missing session ID'}), 400

    session_dir = get_session_dir(session_id)
    original_path = os.path.join(session_dir, 'original.csv')

    if not os.path.exists(original_path):
        return jsonify({'error': MESSAGES["no_data_loaded"]}), 400

    try:
        df = pd.read_csv(original_path)
        original_data = df.to_dict(orient='records')
        original_columns = list(df.columns)

        result = data_validator.validate_data(original_data, original_columns)

        valid_records = []
        rejected_records = []

        for row in original_data:
            valid_records.append(row.copy())

        invalid_row_indices = [record['row_index'] - 1 for record in result['invalid_records']]
        for i in sorted(invalid_row_indices, reverse=True):
            if i < len(valid_records):
                rejected_data = valid_records.pop(i)
                for record in result['invalid_records']:
                    if record['row_index'] - 1 == i:
                        rejected_data['剔除原因'] = '; '.join([err['description'] for err in record['errors']])
                        break
                rejected_records.append(rejected_data)

        processed_path = os.path.join(session_dir, 'processed.csv')
        rejected_path = os.path.join(session_dir, 'rejected.csv')

        pd.DataFrame(valid_records).to_csv(processed_path, index=False, encoding='utf-8-sig')

        if rejected_records:
            pd.DataFrame(rejected_records).to_csv(rejected_path, index=False, encoding='utf-8-sig')
        else:
            pd.DataFrame(columns=['剔除原因']).to_csv(rejected_path, index=False, encoding='utf-8-sig')

        return jsonify({
            'total_rows': len(original_data),
            'valid_rows': len(valid_records),
            'rejected_rows': len(rejected_records),
            'message': f'数据验证完成！有效数据 {len(valid_records)} 条，剔除数据 {len(rejected_records)} 条'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/download_processed', methods=['GET'])
def download_processed():
    session_id = request.args.get('session_id')
    if not session_id:
        return jsonify({'error': 'Missing session ID'}), 400

    session_dir = get_session_dir(session_id)
    processed_path = os.path.join(session_dir, 'processed.csv')

    if not os.path.exists(processed_path):
        return jsonify({'error': '没有可下载的处理后数据'}), 400

    try:
        with open(processed_path, 'rb') as f:
            csv_data = f.read()

        response = make_response(csv_data)
        response.headers['Content-Type'] = 'text/csv; charset=utf-8-sig'
        response.headers['Content-Disposition'] = 'attachment; filename=processed_data.csv'
        return response
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/download_rejected', methods=['GET'])
def download_rejected():
    session_id = request.args.get('session_id')
    if not session_id:
        return jsonify({'error': 'Missing session ID'}), 400

    session_dir = get_session_dir(session_id)
    rejected_path = os.path.join(session_dir, 'rejected.csv')

    if not os.path.exists(rejected_path):
        return jsonify({'error': '没有可下载的剔除数据'}), 400

    try:
        with open(rejected_path, 'rb') as f:
            csv_data = f.read()

        response = make_response(csv_data)
        response.headers['Content-Type'] = 'text/csv; charset=utf-8-sig'
        response.headers['Content-Disposition'] = 'attachment; filename=rejected_data.csv'
        return response
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/reset', methods=['POST'])
def reset_data():
    session_id = request.form.get('session_id') or (request.json.get('session_id') if request.is_json and request.json else None)
    if not session_id:
        session_id = request.args.get('session_id')

    if session_id:
        cleanup_session(session_id)

    return jsonify({'message': '数据已重置'})

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
    session_id = request.form.get('session_id') or request.json.get('session_id') if request.is_json and request.json else request.form.get('session_id')
    if not session_id:
        session_id = request.args.get('session_id')

    if not session_id:
        return jsonify({'error': 'Missing session ID'}), 400

    session_dir = get_session_dir(session_id)
    original_path = os.path.join(session_dir, 'original.csv')

    if not os.path.exists(original_path):
        return jsonify({'error': MESSAGES["no_data_loaded"]}), 400

    try:
        df = pd.read_csv(original_path)
        data = df.fillna("").to_dict(orient='records')
        result = data_validator.validate_relationships(data)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(
        debug=APP_CONFIG["debug"],
        host=APP_CONFIG["host"],
        port=APP_CONFIG["port"]
    )