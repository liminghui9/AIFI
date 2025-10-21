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

# MySQL数据库配置
DB_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': '123456',
    'database': 'simulated_data',
}

app = Flask(__name__)
app.config.from_object(Config)

# 初始化目录
Config.init_app()

# 存储报告数据（实际生产环境应使用数据库）
report_storage = {}

# 操作记录
operation_logs = []

# 报告持久化存储文件
REPORTS_STORAGE_FILE = os.path.join(Config.DATA_FOLDER, 'reports_storage.json')
USERS_STORAGE_FILE = os.path.join(Config.DATA_FOLDER, 'users.json')

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
@login_required
def index():
    """首页"""
    return render_template('index.html', user=session)


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
            
            # 生成报告
            generator = ReportGenerator()
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


@app.route('/report/<report_id>')
@login_required
def view_report(report_id):
    """查看报告"""
    if report_id not in report_storage:
        return "报告不存在", 404
    
    report_data = report_storage[report_id]
    
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
        
        # 记录操作
        operation_logs.append({
            'type': f'报告导出({format.upper()})',
            'report_id': report_id,
            'company': company_name,
            'username': session.get('username'),
            'fullname': session.get('fullname'),
            'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
        
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


# ========== 管理员功能路由 ==========

@app.route('/admin/users')
@login_required
@admin_required
def admin_users():
    """用户管理页面（仅管理员）"""
    return render_template('admin_users.html', user=session)


@app.route('/api/admin/users')
@login_required
@admin_required
def get_users():
    """获取用户列表（仅管理员）"""
    # 准备用户列表（不包含密码）
    users_list = []
    for username, user_data in users_db.items():
        user_info = user_data.copy()
        user_info.pop('password', None)  # 移除密码字段
        # 统计用户创建的报告数量
        report_count = sum(1 for r in report_storage.values() if r.get('created_by') == username)
        user_info['report_count'] = report_count
        users_list.append(user_info)
    
    # 按创建时间排序
    users_list.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    
    return jsonify({
        'success': True,
        'users': users_list
    })


@app.route('/api/admin/users/add', methods=['POST'])
@login_required
@admin_required
def add_user():
    """添加用户（仅管理员）"""
    data = request.get_json()
    
    username = data.get('username')
    password = data.get('password')
    email = data.get('email')
    fullname = data.get('fullname')
    role = data.get('role', 'user')
    
    # 验证输入
    if not all([username, password, email, fullname]):
        return jsonify({'success': False, 'error': '请填写所有必填项'})
    
    if username in users_db:
        return jsonify({'success': False, 'error': '用户名已存在'})
    
    # 检查邮箱是否已被使用
    for user in users_db.values():
        if user['email'] == email:
            return jsonify({'success': False, 'error': '该邮箱已被注册'})
    
    if len(password) < 6:
        return jsonify({'success': False, 'error': '密码长度至少为6位'})
    
    # 创建新用户
    users_db[username] = {
        'username': username,
        'password': generate_password_hash(password),
        'email': email,
        'fullname': fullname,
        'role': role,
        'status': 'active',
        'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    # 保存用户数据
    save_users()
    
    # 记录操作
    operation_logs.append({
        'type': '管理员添加用户',
        'target_user': username,
        'operator': session.get('username'),
        'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })
    
    return jsonify({'success': True, 'message': '用户添加成功'})


@app.route('/api/admin/users/edit/<username>', methods=['POST'])
@login_required
@admin_required
def edit_user(username):
    """编辑用户（仅管理员）"""
    if username not in users_db:
        return jsonify({'success': False, 'error': '用户不存在'})
    
    data = request.get_json()
    user = users_db[username]
    
    # 更新用户信息
    if 'email' in data and data['email'] != user['email']:
        # 检查新邮箱是否已被使用
        for u in users_db.values():
            if u['email'] == data['email'] and u['username'] != username:
                return jsonify({'success': False, 'error': '该邮箱已被使用'})
        user['email'] = data['email']
    
    if 'fullname' in data:
        user['fullname'] = data['fullname']
    
    if 'role' in data:
        user['role'] = data['role']
    
    if 'status' in data:
        user['status'] = data['status']
    
    # 如果提供了新密码，则更新密码
    if 'password' in data and data['password']:
        if len(data['password']) < 6:
            return jsonify({'success': False, 'error': '密码长度至少为6位'})
        user['password'] = generate_password_hash(data['password'])
    
    # 保存用户数据
    save_users()
    
    # 记录操作
    operation_logs.append({
        'type': '管理员编辑用户',
        'target_user': username,
        'operator': session.get('username'),
        'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })
    
    return jsonify({'success': True, 'message': '用户信息更新成功'})


@app.route('/api/admin/users/delete/<username>', methods=['POST'])
@login_required
@admin_required
def delete_user(username):
    """删除用户（仅管理员）"""
    if username not in users_db:
        return jsonify({'success': False, 'error': '用户不存在'})
    
    # 不能删除自己
    if username == session.get('username'):
        return jsonify({'success': False, 'error': '不能删除自己'})
    
    # 不能删除最后一个管理员
    admin_count = sum(1 for u in users_db.values() if u.get('role') == 'admin')
    if users_db[username].get('role') == 'admin' and admin_count <= 1:
        return jsonify({'success': False, 'error': '不能删除最后一个管理员账号'})
    
    # 删除用户
    del users_db[username]
    
    # 保存用户数据
    save_users()
    
    # 记录操作
    operation_logs.append({
        'type': '管理员删除用户',
        'target_user': username,
        'operator': session.get('username'),
        'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })
    
    return jsonify({'success': True, 'message': '用户已删除'})


@app.route('/api/admin/users/change_role/<username>', methods=['POST'])
@login_required
@admin_required
def change_user_role(username):
    """修改用户角色/权限（仅管理员）"""
    if username not in users_db:
        return jsonify({'success': False, 'error': '用户不存在'})
    
    data = request.get_json()
    new_role = data.get('role')
    
    if new_role not in ['admin', 'user']:
        return jsonify({'success': False, 'error': '无效的角色'})
    
    # 不能修改自己的角色
    if username == session.get('username'):
        return jsonify({'success': False, 'error': '不能修改自己的角色'})
    
    # 如果要将管理员降级为普通用户，检查是否还有其他管理员
    if users_db[username].get('role') == 'admin' and new_role == 'user':
        admin_count = sum(1 for u in users_db.values() if u.get('role') == 'admin')
        if admin_count <= 1:
            return jsonify({'success': False, 'error': '不能降级最后一个管理员'})
    
    # 修改角色
    old_role = users_db[username]['role']
    users_db[username]['role'] = new_role
    
    # 保存用户数据
    save_users()
    
    # 记录操作
    operation_logs.append({
        'type': '管理员修改用户权限',
        'target_user': username,
        'operator': session.get('username'),
        'details': f'{old_role} -> {new_role}',
        'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })
    
    return jsonify({'success': True, 'message': '用户权限修改成功'})


@app.route('/api/admin/users/toggle_status/<username>', methods=['POST'])
@login_required
@admin_required
def toggle_user_status(username):
    """启用/禁用用户（仅管理员）"""
    if username not in users_db:
        return jsonify({'success': False, 'error': '用户不存在'})
    
    # 不能禁用自己
    if username == session.get('username'):
        return jsonify({'success': False, 'error': '不能禁用自己'})
    
    # 切换状态
    current_status = users_db[username].get('status', 'active')
    new_status = 'inactive' if current_status == 'active' else 'active'
    users_db[username]['status'] = new_status
    
    # 保存用户数据
    save_users()
    
    # 记录操作
    operation_logs.append({
        'type': f'管理员{"禁用" if new_status == "inactive" else "启用"}用户',
        'target_user': username,
        'operator': session.get('username'),
        'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })
    
    return jsonify({'success': True, 'message': f'用户已{"禁用" if new_status == "inactive" else "启用"}'})


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

@app.route('/settings')
@login_required
def settings():
    """用户设置页面"""
    username = session.get('username')
    user_info = users_db.get(username, {}).copy()
    # 移除密码字段
    user_info.pop('password', None)
    return render_template('settings.html', user=session, user_info=user_info)


@app.route('/api/settings/change_password', methods=['POST'])
@login_required
def change_password():
    """修改密码"""
    data = request.get_json()
    username = session.get('username')
    
    old_password = data.get('old_password')
    new_password = data.get('new_password')
    confirm_password = data.get('confirm_password')
    
    # 验证输入
    if not all([old_password, new_password, confirm_password]):
        return jsonify({'success': False, 'error': '请填写所有必填项'})
    
    if new_password != confirm_password:
        return jsonify({'success': False, 'error': '两次输入的新密码不一致'})
    
    if len(new_password) < 6:
        return jsonify({'success': False, 'error': '新密码长度至少为6位'})
    
    # 验证旧密码
    user = users_db.get(username)
    if not user:
        return jsonify({'success': False, 'error': '用户不存在'})
    
    if not check_password_hash(user['password'], old_password):
        return jsonify({'success': False, 'error': '原密码错误'})
    
    # 更新密码
    users_db[username]['password'] = generate_password_hash(new_password)
    
    # 保存用户数据
    save_users()
    
    # 记录操作
    operation_logs.append({
        'type': '修改密码',
        'username': username,
        'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })
    
    return jsonify({'success': True, 'message': '密码修改成功'})


@app.route('/api/settings/update_profile', methods=['POST'])
@login_required
def update_profile():
    """更新个人资料"""
    data = request.get_json()
    username = session.get('username')
    
    fullname = data.get('fullname')
    email = data.get('email')
    
    # 验证输入
    if not all([fullname, email]):
        return jsonify({'success': False, 'error': '请填写所有必填项'})
    
    # 检查邮箱是否被其他用户使用
    for uname, user_data in users_db.items():
        if uname != username and user_data['email'] == email:
            return jsonify({'success': False, 'error': '该邮箱已被其他用户使用'})
    
    # 更新用户信息
    users_db[username]['fullname'] = fullname
    users_db[username]['email'] = email
    
    # 更新session
    session['fullname'] = fullname
    session['email'] = email
    
    # 保存用户数据
    save_users()
    
    # 记录操作
    operation_logs.append({
        'type': '更新个人资料',
        'username': username,
        'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })
    
    return jsonify({'success': True, 'message': '个人资料更新成功'})


@app.route('/mysql_enterprises')
@login_required
def mysql_enterprises():
    """MySQL企业列表页面"""
    return render_template('mysql_enterprises.html', user=session)


@app.route('/api/mysql/enterprises')
@login_required
def get_mysql_enterprises():
    """获取MySQL数据库中的企业列表"""
    try:
        import mysql.connector
        
        # 连接数据库
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        
        # 方案1：优先使用企业信息表关联（不过滤invalid_mark，因为数据中都不是NULL）
        sql_with_info = """
        SELECT DISTINCT 
            e.taxpayer_id,
            e.taxpayer_name,
            e.industry_type,
            e.register_capital,
            e.registered_date,
            COUNT(DISTINCT YEAR(b.end_date)) as years_count
        FROM syx_enterprise_info e
        INNER JOIN syx_tax_finance_balance_year b ON e.taxpayer_id = b.taxpayer_id
        GROUP BY e.taxpayer_id, e.taxpayer_name, e.industry_type, 
                 e.register_capital, e.registered_date
        HAVING years_count >= 2
        ORDER BY e.taxpayer_name
        LIMIT 100
        """
        
        cursor.execute(sql_with_info)
        results = cursor.fetchall()
        
        # 如果没有找到结果，尝试直接从财务表读取
        if not results:
            print("⚠️ 企业信息表关联失败，尝试直接从财务表读取...")
            sql_direct = """
            SELECT 
                b.taxpayer_id,
                b.taxpayer_id as taxpayer_name,
                '未知' as industry_type,
                NULL as register_capital,
                NULL as registered_date,
                COUNT(DISTINCT YEAR(b.end_date)) as years_count
            FROM syx_tax_finance_balance_year b
            GROUP BY b.taxpayer_id
            HAVING years_count >= 2
            ORDER BY b.taxpayer_id
            LIMIT 100
            """
            
            cursor.execute(sql_direct)
            results = cursor.fetchall()
            
            # 尝试从企业信息表补充名称
            for row in results:
                try:
                    cursor.execute(
                        "SELECT taxpayer_name, industry_type, register_capital, registered_date "
                        "FROM syx_enterprise_info WHERE taxpayer_id = %s",
                        (row['taxpayer_id'],)
                    )
                    info = cursor.fetchone()
                    if info:
                        row['taxpayer_name'] = info['taxpayer_name'] or row['taxpayer_id']
                        row['industry_type'] = info['industry_type'] or '未知'
                        row['register_capital'] = info['register_capital']
                        row['registered_date'] = info['registered_date']
                except:
                    pass
        
        # 处理日期格式
        for row in results:
            if row.get('registered_date'):
                row['registered_date'] = row['registered_date'].strftime('%Y-%m-%d')
            if row.get('register_capital'):
                row['register_capital'] = float(row['register_capital'])
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'enterprises': results,
            'count': len(results)
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': f'数据库查询失败: {str(e)}'
        })


@app.route('/api/mysql/generate_report/<taxpayer_id>', methods=['POST'])
@login_required
def generate_mysql_report(taxpayer_id):
    """从MySQL直接生成报告"""
    try:
        # 生成报告ID
        report_id = datetime.now().strftime('%Y%m%d%H%M%S')
        
        # 使用税务数据适配器读取MySQL数据
        import sys
        import os
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        
        # 动态导入快速开始脚本中的函数
        import mysql.connector
        
        # 连接数据库
        conn = mysql.connector.connect(**DB_CONFIG)
        
        # 获取企业基本信息
        basic_info = get_basic_info_from_db(conn, taxpayer_id)
        if not basic_info:
            conn.close()
            return jsonify({'success': False, 'error': '未找到该企业的数据'})
        
        # 获取财务数据
        years = [2023, 2022]
        financial_data = {}
        
        for year in years:
            balance_data = get_balance_sheet_from_db(conn, taxpayer_id, year)
            profit_data = get_profit_statement_from_db(conn, taxpayer_id, year)
            cashflow_data = get_cashflow_statement_from_db(conn, taxpayer_id, year)
            
            financial_data[year] = {
                '资产负债表': balance_data,
                '利润表': profit_data,
                '现金流量表': cashflow_data
            }
        
        conn.close()
        
        # 使用ReportGenerator生成分析报告
        from modules.indicator_calculator import IndicatorCalculator
        from modules.ai_analyzer import AIAnalyzer
        from modules.chart_generator import ChartGenerator
        
        # 计算财务指标
        indicator_calculator = IndicatorCalculator(financial_data)
        all_indicators = indicator_calculator.calculate_all_indicators()
        
        # 生成AI分析
        ai_analyzer = AIAnalyzer()
        dimension_analyses = {}
        dimensions = ['盈利风险', '偿债风险', '运营风险', '现金流风险']
        
        for dimension in dimensions:
            current_year = years[0]
            indicators = all_indicators.get(current_year, {}).get(dimension, {})
            
            year_data = {}
            for year in years:
                year_data[year] = all_indicators.get(year, {}).get(dimension, {})
            
            analysis = ai_analyzer.analyze_dimension_risk(
                dimension, indicators, year_data, basic_info
            )
            dimension_analyses[dimension] = analysis
        
        # 生成总体风险评估
        overall_assessment = ai_analyzer.generate_overall_risk_assessment(
            dimension_analyses, all_indicators.get(years[0], {}), basic_info
        )
        
        # 生成图表
        chart_generator = ChartGenerator()
        temp_report_data = {
            'years': years,
            'indicators': all_indicators,
            'dimension_analyses': dimension_analyses,
            'basic_info': basic_info
        }
        charts = chart_generator.generate_all_charts(temp_report_data)
        
        # 组装报告数据
        report_data = {
            'report_id': report_id,
            'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'basic_info': basic_info,
            'years': years,
            'financial_data': financial_data,
            'indicators': all_indicators,
            'dimension_analyses': dimension_analyses,
            'overall_assessment': overall_assessment,
            'charts': charts,
            'created_by': session.get('username'),
            'created_by_name': session.get('fullname'),
            'filename': f'MySQL直连_{taxpayer_id}',
            'data_source': 'mysql'
        }
        
        # 存储报告
        report_storage[report_id] = report_data
        save_reports()
        
        # 记录操作
        operation_logs.append({
            'type': 'MySQL直连报告',
            'report_id': report_id,
            'company': basic_info.get('企业名称', '未知'),
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
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': f'报告生成失败: {str(e)}'
        })


def get_basic_info_from_db(conn, taxpayer_id):
    """从数据库获取企业基本信息"""
    cursor = conn.cursor(dictionary=True)
    
    sql = """
    SELECT 
        taxpayer_name AS '企业名称',
        taxpayer_id AS '统一社会信用代码',
        tax_no AS '税号',
        legal_person_name AS '法定代表人',
        register_capital AS '注册资本（万元）',
        register_currencies AS '注册资本币种',
        COALESCE(registered_date, start_business_date) AS '成立日期',
        registered_date AS '注册日期',
        start_business_date AS '开业日期',
        registered_type AS '企业类型',
        industry_type AS '行业类别',
        taxpayer_type AS '纳税人类型',
        nsrztmc AS '登记状态',
        bureau AS '税务局',
        bureau_detail AS '登记机关',
        register_province AS '注册省份',
        register_city AS '注册城市',
        register_county AS '注册区县',
        register_address AS '注册地址',
        business_address AS '经营地址',
        business_scope AS '经营范围',
        employees_number AS '从业人数',
        hydm AS '行业代码'
    FROM syx_enterprise_info
    WHERE taxpayer_id = %s
    LIMIT 1
    """
    
    cursor.execute(sql, (taxpayer_id,))
    result = cursor.fetchone()
    cursor.close()
    
    if not result:
        return None
    
    # 处理注册资本
    if result.get('注册资本（万元）'):
        result['注册资本（万元）'] = float(result['注册资本（万元）'])
    
    # 处理日期格式
    date_fields = ['成立日期', '注册日期', '开业日期']
    for field in date_fields:
        if result.get(field):
            result[field] = result[field].strftime('%Y-%m-%d')
    
    # 处理None值
    for key in result:
        if result[key] is None:
            result[key] = "-"
    
    # 组合完整注册地址
    if result.get('注册省份') and result['注册省份'] != '-':
        address_parts = []
        if result.get('注册省份') and result['注册省份'] != '-':
            address_parts.append(result['注册省份'])
        if result.get('注册城市') and result['注册城市'] != '-':
            address_parts.append(result['注册城市'])
        if result.get('注册区县') and result['注册区县'] != '-':
            address_parts.append(result['注册区县'])
        if result.get('注册地址') and result['注册地址'] != '-':
            address_parts.append(result['注册地址'])
        
        if address_parts:
            result['完整注册地址'] = ''.join(address_parts)
        else:
            result['完整注册地址'] = result.get('注册地址', '-')
    else:
        result['完整注册地址'] = result.get('注册地址', '-')
    
    return result


def get_balance_sheet_from_db(conn, taxpayer_id, year):
    """从数据库获取资产负债表"""
    cursor = conn.cursor()
    
    sql = """
    SELECT 
        project_name,
        ending_balance
    FROM syx_tax_finance_balance_year
    WHERE taxpayer_id = %s
      AND YEAR(end_date) = %s
    ORDER BY sequence
    """
    
    cursor.execute(sql, (taxpayer_id, year))
    results = cursor.fetchall()
    cursor.close()
    
    # 项目映射
    BALANCE_SHEET_PROJECTS = {
        '总资产': '资产总计',
        '流动资产': '流动资产合计',
        '非流动资产': '非流动资产合计',
        '总负债': '负债合计',
        '流动负债': '流动负债合计',
        '非流动负债': '非流动负债合计',
        '所有者权益': '所有者权益合计',
        '应收账款': '应收账款',
        '存货': '存货',
    }
    
    data = {}
    for project_name, value in results:
        for std_name, tax_name in BALANCE_SHEET_PROJECTS.items():
            if project_name == tax_name:
                data[std_name] = float(value) if value else None
                break
    
    return data


def get_profit_statement_from_db(conn, taxpayer_id, year):
    """从数据库获取利润表"""
    cursor = conn.cursor()
    
    sql = """
    SELECT 
        project_name,
        current_year_accumulative_amount
    FROM syx_tax_finance_profit_year
    WHERE taxpayer_id = %s
      AND YEAR(end_date) = %s
    ORDER BY sequence
    """
    
    cursor.execute(sql, (taxpayer_id, year))
    results = cursor.fetchall()
    cursor.close()
    
    PROFIT_PROJECTS = {
        '营业收入': '营业收入',
        '营业成本': '营业成本',
        '营业利润': '营业利润',
        '利润总额': '利润总额',
        '净利润': '净利润',
    }
    
    data = {}
    for project_name, value in results:
        for std_name, tax_name in PROFIT_PROJECTS.items():
            if project_name == tax_name:
                data[std_name] = float(value) if value else None
                break
    
    return data


def get_cashflow_statement_from_db(conn, taxpayer_id, year):
    """从数据库获取现金流量表"""
    cursor = conn.cursor()
    
    sql = """
    SELECT 
        project_name,
        bnljje
    FROM syx_cash_flow
    WHERE taxpayer_id = %s
      AND YEAR(end_date) = %s
    ORDER BY sequence
    """
    
    cursor.execute(sql, (taxpayer_id, year))
    results = cursor.fetchall()
    cursor.close()
    
    CASHFLOW_PROJECTS = {
        '经营活动现金流量净额': '经营活动产生的现金流量净额',
        '投资活动现金流量净额': '投资活动产生的现金流量净额',
        '筹资活动现金流量净额': '筹资活动产生的现金流量净额',
        '现金及现金等价物净增加额': '现金及现金等价物净增加额',
    }
    
    data = {}
    for project_name, value in results:
        for std_name, tax_name in CASHFLOW_PROJECTS.items():
            if project_name == tax_name:
                data[std_name] = float(value) if value else None
                break
    
    return data


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
    
    print("=" * 50)
    print("AIFI 智能财报系统启动中...")
    print("=" * 50)
    print(f"访问地址: http://localhost:5000")
    print(f"AI功能状态: {'已启用' if Config.OPENAI_API_KEY else '未配置（将使用默认分析）'}")
    print(f"历史报告: {len(report_storage)} 个")
    print(f"系统用户: {len(users_db)} 个")
    print("=" * 50)
    app.run(debug=True, host='0.0.0.0', port=5000)



