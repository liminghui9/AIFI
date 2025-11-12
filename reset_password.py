"""重置用户密码"""
from werkzeug.security import generate_password_hash
import json

# 生成新密码哈希
admin_password = generate_password_hash('admin123')
user_password = generate_password_hash('user123')

users = {
    "admin": {
        "username": "admin",
        "password": admin_password,
        "email": "admin@aifi.com",
        "fullname": "系统管理员",
        "role": "admin",
        "status": "active",
        "created_at": "2024-01-01 00:00:00"
    },
    "user": {
        "username": "user",
        "password": user_password,
        "email": "user@aifi.com",
        "fullname": "普通用户",
        "role": "user",
        "status": "active",
        "created_at": "2024-01-01 00:00:00"
    }
}

# 保存
with open('data/users.json', 'w', encoding='utf-8') as f:
    json.dump(users, f, ensure_ascii=False, indent=2)

print("密码已重置！")
print("admin/admin123")
print("user/user123")



