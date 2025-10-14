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

# 用户数据存储（实际生产环境应使用数据库）
users_db = {
    'admin': {
        'username': 'admin',
        'password': generate_password_hash('admin123'),
        'email': 'admin@aifi.com',
        'fullname': '系统管理员',
        'role': 'admin',
        'created_at': '2024-01-01 00:00:00'
    },
    'user': {
        'username': 'user',
        'password': generate_password_hash('user123'),
        'email': 'user@aifi.com',
        'fullname': '普通用户',
        'role': 'user',
        'created_at': '2024-01-01 00:00:00'
    },
    'analyst': {
        'username': 'analyst',
        'password': generate_password_hash('analyst123'),
        'email': 'analyst@aifi.com',
        'fullname': '财务分析师',
        'role': 'analyst',
        'created_at': '2024-01-01 00:00:00'
    }
}


# 登录装饰器
def login_required(f):
    """要求用户登录的装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
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
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
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
            
            # 存储报告数据（添加用户信息）
            report_data['created_by'] = session.get('username')
            report_data['created_by_name'] = session.get('fullname')
            report_storage[report_id] = report_data
            
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
    return render_template('report.html', report_id=report_id, report=report_data, user=session)


@app.route('/api/report/<report_id>')
@login_required
def get_report_data(report_id):
    """获取报告数据API"""
    if report_id not in report_storage:
        return jsonify({'success': False, 'error': '报告不存在'})
    
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
    
    if format not in ['word', 'pdf']:
        return "不支持的导出格式", 400
    
    try:
        report_data = report_storage[report_id]
        company_name = report_data['basic_info'].get('企业名称', '企业')
        
        # 生成文件名
        if format == 'word':
            filename = f"{company_name}_财务分析报告_{report_id}.docx"
            filepath = os.path.join(Config.EXPORT_FOLDER, filename)
            
            # 导出Word
            exporter = ExportGenerator()
            success = exporter.export_to_word(report_data, filepath)
            
        else:  # PDF
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
    return jsonify({
        'success': True,
        'info': {
            'version': 'v1.0（演示版）',
            'ai_enabled': bool(Config.OPENAI_API_KEY),
            'report_count': len(report_storage),
            'log_count': len(operation_logs),
            'current_user': session.get('fullname', '未知'),
            'user_role': session.get('role', 'user')
        }
    })


@app.errorhandler(404)
def not_found(error):
    """404错误处理"""
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_error(error):
    """500错误处理"""
    return render_template('500.html'), 500


if __name__ == '__main__':
    print("=" * 50)
    print("AIFI 智能财报系统启动中...")
    print("=" * 50)
    print(f"访问地址: http://localhost:5000")
    print(f"AI功能状态: {'已启用' if Config.OPENAI_API_KEY else '未配置（将使用默认分析）'}")
    print("=" * 50)
    app.run(debug=True, host='0.0.0.0', port=5000)

