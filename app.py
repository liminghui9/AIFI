"""
AIFI智能财报系统 - Flask主应用
"""

from flask import Flask, render_template, request, jsonify, send_file, session, redirect, url_for, flash
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import os
import json
from datetime import datetime
from config import Config
from modules.report_generator import ReportGenerator
from modules.export_generator import ExportGenerator

app = Flask(__name__)
app.config.from_object(Config)

# 初始化目录
Config.init_app()

# 存储报告数据（实际生产环境应使用数据库）
report_storage = {}

# 操作记录
operation_logs = []

# 下载记录
download_records = []

# 报告持久化存储文件
REPORTS_STORAGE_FILE = os.path.join(Config.DATA_FOLDER, 'reports_storage.json')
USERS_STORAGE_FILE = os.path.join(Config.DATA_FOLDER, 'users.json')
DOWNLOAD_RECORDS_FILE = os.path.join(Config.DATA_FOLDER, 'download_records.json')

# 加载历史报告
def load_reports():
    """从文件加载历史报告"""
    global report_storage
    if os.path.exists(REPORTS_STORAGE_FILE):
        try:
            with open(REPORTS_STORAGE_FILE, 'r', encoding='utf-8') as f:
                report_storage = json.load(f)
            print(f"✓ 已加载 {len(report_storage)} 个历史报告")
        except Exception as e:
            print(f"✗ 加载历史报告失败: {str(e)}")
            report_storage = {}

# 保存报告到文件
def save_reports():
    """保存报告到文件"""
    try:
        # 自定义JSON编码器，处理numpy类型
        import numpy as np
        
        class NumpyEncoder(json.JSONEncoder):
            def default(self, obj):
                if isinstance(obj, (np.int_, np.intc, np.intp, np.int8,
                    np.int16, np.int32, np.int64, np.uint8,
                    np.uint16, np.uint32, np.uint64)):
                    return int(obj)
                elif isinstance(obj, (np.float_, np.float16, np.float32, np.float64)):
                    return float(obj)
                elif isinstance(obj, (np.ndarray,)):
                    return obj.tolist()
                return super(NumpyEncoder, self).default(obj)
        
        with open(REPORTS_STORAGE_FILE, 'w', encoding='utf-8') as f:
            json.dump(report_storage, f, ensure_ascii=False, indent=2, cls=NumpyEncoder)
        return True
    except Exception as e:
        print(f"✗ 保存报告失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

# 加载下载记录
def load_download_records():
    """从文件加载下载记录"""
    global download_records
    if os.path.exists(DOWNLOAD_RECORDS_FILE):
        try:
            with open(DOWNLOAD_RECORDS_FILE, 'r', encoding='utf-8') as f:
                download_records = json.load(f)
            print(f"✓ 已加载 {len(download_records)} 条下载记录")
        except Exception as e:
            print(f"✗ 加载下载记录失败: {str(e)}")
            download_records = []

# 保存下载记录
def save_download_records():
    """保存下载记录到文件"""
    try:
        with open(DOWNLOAD_RECORDS_FILE, 'w', encoding='utf-8') as f:
            json.dump(download_records, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"✗ 保存下载记录失败: {str(e)}")
        return False

# 用户数据存储（实际生产环境应使用数据库）
users_db = {
    'admin': {
        'username': 'admin',
        'password': generate_password_hash('admin123'),
        'email': 'admin@aifi.com',
        'fullname': '系统管理员',
        'role': 'admin',
        'status': 'active',
        'created_at': '2024-01-01 00:00:00'
    },
    'user': {
        'username': 'user',
        'password': generate_password_hash('user123'),
        'email': 'user@aifi.com',
        'fullname': '普通用户',
        'role': 'user',
        'status': 'active',
        'created_at': '2024-01-01 00:00:00'
    },
    'analyst': {
        'username': 'analyst',
        'password': generate_password_hash('analyst123'),
        'email': 'analyst@aifi.com',
        'fullname': '财务分析师',
        'role': 'user',
        'status': 'active',
        'created_at': '2024-01-01 00:00:00'
    }
}

# 加载用户数据
def load_users():
    """从文件加载用户数据"""
    global users_db
    if os.path.exists(USERS_STORAGE_FILE):
        try:
            with open(USERS_STORAGE_FILE, 'r', encoding='utf-8') as f:
                users_db = json.load(f)
            print(f"✓ 已加载 {len(users_db)} 个用户")
        except Exception as e:
            print(f"✗ 加载用户数据失败: {str(e)}")
    else:
        # 如果文件不存在，保存默认用户
        save_users()

# 保存用户数据
def save_users():
    """保存用户数据到文件"""
    try:
        with open(USERS_STORAGE_FILE, 'w', encoding='utf-8') as f:
            json.dump(users_db, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"✗ 保存用户数据失败: {str(e)}")
        return False


# 登录装饰器
def login_required(f):
    """要求用户登录的装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


# 管理员权限装饰器
def admin_required(f):
    """要求管理员权限的装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        if session.get('role') != 'admin':
            return jsonify({'success': False, 'error': '需要管理员权限'}), 403
        return f(*args, **kwargs)
    return decorated_function


def allowed_file(filename):
    """检查文件扩展名是否允许"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS


# ========== 认证相关路由 ==========

@app.route('/login', methods=['GET', 'POST'])
def login():
    """用户登录"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = request.form.get('remember')
        
        # 验证用户
        if username in users_db:
            user = users_db[username]
            # 检查用户状态
            if user.get('status') == 'inactive':
                return render_template('login.html', error='账号已被禁用，请联系管理员')
            
            if check_password_hash(user['password'], password):
                # 登录成功
                session['username'] = username
                session['fullname'] = user['fullname']
                session['role'] = user['role']
                session['email'] = user['email']
                
                # 记录登录日志
                operation_logs.append({
                    'type': '用户登录',
                    'username': username,
                    'fullname': user['fullname'],
                    'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                })
                
                return redirect(url_for('index'))
            else:
                return render_template('login.html', error='密码错误')
        else:
            return render_template('login.html', error='用户名不存在')
    
    # 如果已登录，直接跳转到首页
    if 'username' in session:
        return redirect(url_for('index'))
    
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    """用户注册"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        email = request.form.get('email')
        fullname = request.form.get('fullname')
        
        # 验证输入
        if not all([username, password, email, fullname]):
            return render_template('register.html', error='请填写所有必填项')
        
        if password != confirm_password:
            return render_template('register.html', error='两次输入的密码不一致')
        
        if len(password) < 6:
            return render_template('register.html', error='密码长度至少为6位')
        
        if username in users_db:
            return render_template('register.html', error='用户名已存在')
        
        # 检查邮箱是否已被使用
        for user in users_db.values():
            if user['email'] == email:
                return render_template('register.html', error='该邮箱已被注册')
        
        # 创建新用户
        users_db[username] = {
            'username': username,
            'password': generate_password_hash(password),
            'email': email,
            'fullname': fullname,
            'role': 'user',  # 默认角色为普通用户
            'status': 'active',
            'ai_model': 'gpt-4-turbo',  # 默认AI模型
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # 保存用户数据
        save_users()
        
        # 记录注册日志
        operation_logs.append({
            'type': '用户注册',
            'username': username,
            'fullname': fullname,
            'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
        
        # 注册成功，跳转到登录页
        return render_template('login.html', message='注册成功！请登录')
    
    # 如果已登录，直接跳转到首页
    if 'username' in session:
        return redirect(url_for('index'))
    
    return render_template('register.html')


@app.route('/logout')
def logout():
    """用户登出"""
    username = session.get('username', '未知用户')
    
    # 记录登出日志
    operation_logs.append({
        'type': '用户登出',
        'username': username,
        'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })
    
    # 清除session
    session.clear()
    
    return redirect(url_for('login'))


# ========== 主要功能路由 ==========

@app.route('/')
def landing():
    """着陆页 - 公开访问"""
    # 如果用户已登录，重定向到仪表板
    if 'username' in session:
        return redirect(url_for('index'))
    return render_template('landing.html')


@app.route('/index')
@app.route('/dashboard')
@login_required
def index():
    """仪表板首页"""
    # 统计已生成的报告数量
    reports_count = 0
    companies_count = 0
    
    try:
        if os.path.exists(REPORTS_STORAGE_FILE):
            with open(REPORTS_STORAGE_FILE, 'r', encoding='utf-8') as f:
                reports_data = json.load(f)
                reports_count = len(reports_data)
                # 统计不同企业数量
                companies = set()
                for report in reports_data.values():
                    company_name = report.get('basic_info', {}).get('企业名称', '')
                    if company_name:
                        companies.add(company_name)
                companies_count = len(companies)
    except Exception as e:
        print(f"读取报告统计失败: {str(e)}")
    
    return render_template('index.html', 
                         user=session,
                         reports_count=reports_count,
                         companies_count=companies_count)


@app.route('/upload', methods=['POST'])
@login_required
def upload_file():
    """处理文件上传"""
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': '没有文件上传'})
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'success': False, 'error': '没有选择文件'})
    
    if file and allowed_file(file.filename):
        try:
            # 保存文件
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            filename = f"{timestamp}_{filename}"
            filepath = os.path.join(Config.UPLOAD_FOLDER, filename)
            file.save(filepath)
            
            # 生成报告ID
            report_id = timestamp
            
            # 获取用户的AI模型设置
            username = session.get('username')
            user_ai_model = users_db.get(username, {}).get('ai_model', None)
            
            # 生成报告
            generator = ReportGenerator(ai_model=user_ai_model)
            report_data = generator.generate_report(filepath)
            
            if 'error' in report_data:
                return jsonify({'success': False, 'error': report_data['error']})
            
            # 存储报告数据（添加用户信息和元数据）
            report_data['report_id'] = report_id
            report_data['created_by'] = session.get('username')
            report_data['created_by_name'] = session.get('fullname')
            report_data['filename'] = file.filename
            report_storage[report_id] = report_data
            
            # 持久化保存
            save_reports()
            
            # 记录操作
            operation_logs.append({
                'type': '报告生成',
                'report_id': report_id,
                'company': report_data['basic_info'].get('企业名称', '未知'),
                'username': session.get('username'),
                'fullname': session.get('fullname'),
                'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
            
            return jsonify({
                'success': True,
                'report_id': report_id,
                'message': '报告生成成功'
            })
            
        except Exception as e:
            return jsonify({'success': False, 'error': f'处理失败: {str(e)}'})
    
    return jsonify({'success': False, 'error': '不支持的文件格式'})


def normalize_report_data(report_data):
    """
    规范化报告数据，确保兼容性
    修复旧报告的数据格式问题
    """
    # 确保years是列表
    if 'years' in report_data and report_data['years']:
        # 转换为整数列表
        report_data['years'] = [int(y) if isinstance(y, str) else y for y in report_data['years']]
    
    # 确保indicators字典的键是字符串
    if 'indicators' in report_data:
        new_indicators = {}
        for year, data in report_data['indicators'].items():
            # 将年份键统一转为字符串
            year_str = str(year)
            new_indicators[year_str] = data
        report_data['indicators'] = new_indicators
    
    # 确保financial_data字典的键是字符串
    if 'financial_data' in report_data:
        new_financial_data = {}
        for year, data in report_data['financial_data'].items():
            # 将年份键统一转为字符串
            year_str = str(year)
            new_financial_data[year_str] = data
        report_data['financial_data'] = new_financial_data
    
    return report_data


@app.route('/report/<report_id>')
@login_required
def view_report(report_id):
    """查看报告"""
    if report_id not in report_storage:
        return "报告不存在", 404
    
    report_data = report_storage[report_id]
    
    # 规范化报告数据，确保兼容性
    report_data = normalize_report_data(report_data)
    
    # 检查权限：管理员可以查看所有报告，普通用户只能查看自己的报告
    if session.get('role') != 'admin' and report_data.get('created_by') != session.get('username'):
        return "无权访问此报告", 403
    
    return render_template('report.html', report_id=report_id, report=report_data, user=session)


@app.route('/api/report/<report_id>')
@login_required
def get_report_data(report_id):
    """获取报告数据API"""
    if report_id not in report_storage:
        return jsonify({'success': False, 'error': '报告不存在'})
    
    report_data = report_storage[report_id]
    
    # 检查权限
    if session.get('role') != 'admin' and report_data.get('created_by') != session.get('username'):
        return jsonify({'success': False, 'error': '无权访问此报告'})
    
    return jsonify({
        'success': True,
        'data': report_storage[report_id]
    })


@app.route('/export/<report_id>/<format>')
@login_required
def export_report(report_id, format):
    """导出报告"""
    if report_id not in report_storage:
        return "报告不存在", 404
    
    report_data = report_storage[report_id]
    
    # 规范化报告数据，确保兼容性
    report_data = normalize_report_data(report_data)
    
    # 检查权限
    if session.get('role') != 'admin' and report_data.get('created_by') != session.get('username'):
        return "无权导出此报告", 403
    
    if format not in ['word', 'pdf', 'pdf_html']:
        return "不支持的导出格式", 400
    
    try:
        company_name = report_data['basic_info'].get('企业名称', '企业')
        
        # 生成文件名
        if format == 'word':
            filename = f"{company_name}_财务分析报告_{report_id}.docx"
            filepath = os.path.join(Config.EXPORT_FOLDER, filename)
            
            # 导出Word
            exporter = ExportGenerator()
            success = exporter.export_to_word(report_data, filepath)
            
        elif format == 'pdf_html':
            # 新方案：基于HTML的PDF导出
            from modules.pdf_export import PDFExporter
            
            pdf_exporter = PDFExporter()
            filename = pdf_exporter.get_pdf_filename(report_data, report_id)
            filepath = os.path.join(Config.EXPORT_FOLDER, filename)
            
            # 导出PDF
            success = pdf_exporter.export_to_pdf(report_data, filepath)
            
        else:  # PDF（旧方案，使用ReportLab）
            filename = f"{company_name}_财务分析报告_{report_id}.pdf"
            filepath = os.path.join(Config.EXPORT_FOLDER, filename)
            
            # 导出PDF
            exporter = ExportGenerator()
            success = exporter.export_to_pdf(report_data, filepath)
        
        if not success:
            return "导出失败", 500
        
        # 记录操作日志
        operation_logs.append({
            'type': f'报告导出({format.upper()})',
            'report_id': report_id,
            'company': company_name,
            'username': session.get('username'),
            'fullname': session.get('fullname'),
            'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
        
        # 记录下载记录
        download_records.append({
            'report_id': report_id,
            'company_name': company_name,
            'format': format.upper(),
            'filename': filename,
            'username': session.get('username'),
            'fullname': session.get('fullname'),
            'download_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'file_size': os.path.getsize(filepath) if os.path.exists(filepath) else 0
        })
        
        # 保存下载记录到文件
        save_download_records()
        
        # 发送文件
        return send_file(
            filepath,
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return f"导出失败: {str(e)}", 500


@app.route('/api/logs')
@login_required
def get_logs():
    """获取操作日志"""
    return jsonify({
        'success': True,
        'logs': operation_logs[-20:]  # 返回最近20条
    })


@app.route('/api/system_info')
@login_required
def get_system_info():
    """获取系统信息"""
    # 统计当前用户的报告数量
    username = session.get('username')
    role = session.get('role')
    
    if role == 'admin':
        # 管理员可以看到所有数据
        user_report_count = len(report_storage)
        active_users = sum(1 for u in users_db.values() if u.get('status') == 'active')
    else:
        # 普通用户只能看到自己的报告
        user_report_count = sum(1 for r in report_storage.values() if r.get('created_by') == username)
        active_users = 1
    
    return jsonify({
        'success': True,
        'info': {
            'version': 'v1.0（演示版）',
            'ai_enabled': bool(Config.OPENAI_API_KEY),
            'report_count': user_report_count,
            'log_count': len(operation_logs),
            'current_user': session.get('fullname', '未知'),
            'user_role': role,
            'active_users': active_users
        }
    })


@app.route('/reports')
@login_required
def reports_list():
    """报告列表页面"""
    # 获取当前用户
    username = session.get('username')
    role = session.get('role')
    
    # 准备报告列表数据
    reports = []
    for report_id, report_data in report_storage.items():
        # 管理员可以看到所有报告，普通用户只能看到自己的报告
        if role == 'admin' or report_data.get('created_by') == username:
            reports.append({
                'report_id': report_id,
                'company_name': report_data.get('basic_info', {}).get('企业名称', '未知企业'),
                'generated_at': report_data.get('generated_at', '未知时间'),
                'created_by': report_data.get('created_by', '未知'),
                'created_by_name': report_data.get('created_by_name', '未知用户'),
                'filename': report_data.get('filename', '未知文件'),
                'years': report_data.get('years', [])
            })
    
    # 按生成时间倒序排序
    reports.sort(key=lambda x: x['generated_at'], reverse=True)
    
    return render_template('reports_list.html', reports=reports, user=session)


@app.route('/api/reports/delete/<report_id>', methods=['POST'])
@login_required
def delete_report(report_id):
    """删除报告"""
    username = session.get('username')
    role = session.get('role')
    
    if report_id not in report_storage:
        return jsonify({'success': False, 'error': '报告不存在'})
    
    report = report_storage[report_id]
    
    # 检查权限：管理员或报告创建者可以删除
    if role != 'admin' and report.get('created_by') != username:
        return jsonify({'success': False, 'error': '无权删除此报告'})
    
    # 删除报告
    company_name = report.get('basic_info', {}).get('企业名称', '未知企业')
    del report_storage[report_id]
    
    # 持久化保存
    save_reports()
    
    # 记录操作
    operation_logs.append({
        'type': '删除报告',
        'report_id': report_id,
        'company': company_name,
        'username': username,
        'fullname': session.get('fullname'),
        'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })
    
    return jsonify({'success': True, 'message': '报告已删除'})


@app.route('/downloads')
@login_required
def download_records_page():
    """下载记录页面"""
    return render_template('download_records.html', user=session)


@app.route('/api/downloads')
@login_required
def get_download_records():
    """获取下载记录API"""
    username = session.get('username')
    role = session.get('role')
    
    # 管理员可以看到所有下载记录，普通用户只能看到自己的
    if role == 'admin':
        filtered_records = download_records
    else:
        filtered_records = [r for r in download_records if r.get('username') == username]
    
    return jsonify({
        'success': True,
        'data': filtered_records
    })


# ========== 管理员功能路由 ==========

@app.route('/api/admin/clear_uploads', methods=['POST'])
@login_required
@admin_required
def clear_uploads():
    """清理上传文件夹（仅管理员）"""
    try:
        import glob
        
        # 获取所有上传文件
        upload_files = glob.glob(os.path.join(Config.UPLOAD_FOLDER, '*'))
        
        # 删除所有文件
        deleted_count = 0
        for file_path in upload_files:
            if os.path.isfile(file_path):
                try:
                    os.remove(file_path)
                    deleted_count += 1
                except Exception as e:
                    print(f"删除文件失败: {file_path}, 错误: {str(e)}")
        
        # 记录操作
        operation_logs.append({
            'type': '清理上传文件',
            'operator': session.get('username'),
            'count': deleted_count,
            'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
        
        return jsonify({
            'success': True,
            'message': f'成功删除 {deleted_count} 个文件',
            'count': deleted_count
        })
        
    except Exception as e:
        print(f"清理上传文件失败: {str(e)}")
        return jsonify({'success': False, 'error': f'操作失败: {str(e)}'})


@app.route('/api/admin/upload_file_count')
@login_required
@admin_required
def get_upload_file_count():
    """获取上传文件数量（仅管理员）"""
    try:
        import glob
        
        # 获取所有上传文件
        upload_files = glob.glob(os.path.join(Config.UPLOAD_FOLDER, '*'))
        
        # 只统计文件，不包括文件夹
        file_count = sum(1 for f in upload_files if os.path.isfile(f))
        
        return jsonify({
            'success': True,
            'count': file_count
        })
        
    except Exception as e:
        print(f"获取文件数量失败: {str(e)}")
        return jsonify({'success': False, 'error': f'获取失败: {str(e)}'})


# ========== 用户设置路由 ==========
# 已删除系统设置功能
# 已删除 MySQL 企业数据功能

@app.route('/api/chat', methods=['POST'])
@login_required
def ai_chat():
    """AI对话接口 - 回答用户关于报告的问题"""
    try:
        data = request.get_json()
        report_id = data.get('report_id')
        question = data.get('question')
        
        # 验证输入
        if not report_id or not question:
            return jsonify({'success': False, 'error': '缺少必要参数'})
        
        # 获取报告数据
        report_data = report_storage.get(report_id)
        if not report_data:
            return jsonify({'success': False, 'error': '报告不存在'})
        
        # 检查权限 - 用户只能查看自己的报告（管理员可以查看所有报告）
        username = session.get('username')
        role = session.get('role')
        if role != 'admin' and report_data.get('created_by') != username:
            return jsonify({'success': False, 'error': '无权访问此报告'})
        
        # 导入AI分析器
        from modules.ai_analyzer import AIAnalyzer
        ai_analyzer = AIAnalyzer()
        
        # 获取企业基本信息
        company_info = report_data.get('basic_info', {})
        
        # 调用AI回答问题
        answer = ai_analyzer.answer_question(
            question=question,
            report_data=report_data,
            company_info=company_info
        )
        
        # 记录操作
        operation_logs.append({
            'type': 'AI对话',
            'username': username,
            'report_id': report_id,
            'question': question[:50] + ('...' if len(question) > 50 else ''),
            'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
        
        return jsonify({
            'success': True,
            'answer': answer
        })
        
    except Exception as e:
        print(f"AI对话处理失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': f'处理失败: {str(e)}'
        })


@app.errorhandler(404)
def not_found(error):
    """404错误处理"""
    return "页面不存在", 404


@app.errorhandler(500)
def internal_error(error):
    """500错误处理"""
    return "服务器内部错误", 500


if __name__ == '__main__':
    # 加载历史报告和用户数据
    load_reports()
    load_users()
    load_download_records()
    
    print("=" * 50)
    print("AIFI 智能财报系统启动中...")
    print("=" * 50)
    print(f"访问地址: http://localhost:5000")
    print(f"AI功能状态: {'已启用' if Config.OPENAI_API_KEY else '未配置（将使用默认分析）'}")
    print(f"历史报告: {len(report_storage)} 个")
    print(f"系统用户: {len(users_db)} 个")
    print(f"下载记录: {len(download_records)} 条")
    print("=" * 50)
    app.run(debug=True, host='0.0.0.0', port=5000)
