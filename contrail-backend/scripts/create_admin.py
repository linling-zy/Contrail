"""
创建管理员账号脚本
用于向数据库中写入管理员账号
"""
import sys
import os
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
from app import create_app
from app.extensions import db
from app.models import AdminUser

# 加载环境变量
load_dotenv()


def create_admin(username, password, name, role='normal'):
    """
    创建管理员账号
    
    Args:
        username: 登录账号（唯一）
        password: 密码（明文，会自动哈希）
        name: 真实姓名
        role: 角色，'super' 或 'normal'（默认 'normal'）
    """
    # 创建 Flask 应用实例
    config_name = os.environ.get('FLASK_ENV', 'development')
    app = create_app(config_name)
    
    with app.app_context():
        # 检查账号是否已存在
        existing_admin = AdminUser.query.filter_by(username=username).first()
        if existing_admin:
            print(f"❌ 错误：账号 '{username}' 已存在！")
            return False
        
        # 创建管理员账号
        admin = AdminUser(
            username=username,
            name=name,
            role=role
        )
        admin.set_password(password)  # 自动哈希密码
        
        # 保存到数据库
        try:
            db.session.add(admin)
            db.session.commit()
            print(f"✅ 成功创建管理员账号：")
            print(f"   账号：{username}")
            print(f"   姓名：{name}")
            print(f"   角色：{role}")
            return True
        except Exception as e:
            db.session.rollback()
            print(f"❌ 创建失败：{str(e)}")
            return False


def get_input(prompt, required=True, default=None, password=False):
    """
    获取用户输入
    
    Args:
        prompt: 提示信息
        required: 是否必填
        default: 默认值
        password: 是否为密码输入（隐藏输入）
    """
    import getpass
    
    # 检查是否是交互式终端
    if not sys.stdin.isatty():
        if default:
            print(f"{prompt}：使用默认值 '{default}'")
            return default
        elif not required:
            return None
        else:
            print(f"❌ 错误：在非交互式环境中，'{prompt}' 为必填项但未提供默认值")
            sys.exit(1)
    
    while True:
        if default:
            full_prompt = f"{prompt}（默认：{default}）"
        else:
            full_prompt = prompt
        
        try:
            if password:
                value = getpass.getpass(f"{full_prompt}：")
            else:
                value = input(f"{full_prompt}：").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\n操作已取消")
            sys.exit(0)
        
        if value:
            return value
        elif default:
            return default
        elif not required:
            return None
        else:
            print("❌ 此项为必填项，请输入！")


def main():
    """主函数"""
    print("=" * 50)
    print("创建管理员账号")
    print("=" * 50)
    print()
    
    # 如果提供了命令行参数，则直接使用参数（非交互模式）
    if len(sys.argv) >= 5:
        username = sys.argv[1]
        password = sys.argv[2]
        name = sys.argv[3]
        role = sys.argv[4] if sys.argv[4] in [AdminUser.ROLE_SUPER, AdminUser.ROLE_NORMAL] else AdminUser.ROLE_NORMAL
        print("使用命令行参数创建管理员账号...")
        print(f"   账号：{username}")
        print(f"   姓名：{name}")
        print(f"   角色：{role}")
    else:
        # 检查是否是交互式环境
        if not sys.stdin.isatty():
            print("❌ 错误：当前环境不支持交互式输入")
            print("请使用命令行参数方式创建管理员账号：")
            print("   python scripts/create_admin.py <账号> <密码> <姓名> <角色>")
            print("   角色可选：super（超级管理员）或 normal（普通管理员）")
            sys.exit(1)
        
        # 交互式输入
        print("请按提示输入管理员信息：")
        print()
        
        # 获取账号
        username = get_input("请输入管理员账号", required=True)
        
        # 获取密码（需要确认）
        while True:
            password = get_input("请输入密码", required=True, password=True)
            if len(password) < 6:
                print("❌ 密码长度至少为6位，请重新输入！")
                continue
            
            password_confirm = get_input("请再次输入密码确认", required=True, password=True)
            if password != password_confirm:
                print("❌ 两次输入的密码不一致，请重新输入！")
                continue
            break
        
        # 获取姓名
        name = get_input("请输入真实姓名", required=True)
        
        # 获取角色
        while True:
            role_choice = get_input("请选择角色（1-普通管理员，2-超级管理员）", required=True, default="1")
            if role_choice == '1':
                role = AdminUser.ROLE_NORMAL
                break
            elif role_choice == '2':
                role = AdminUser.ROLE_SUPER
                break
            else:
                print("❌ 请输入 1 或 2！")
        
        # 确认信息
        print()
        print("=" * 50)
        print("请确认以下信息：")
        print("=" * 50)
        print(f"账号：{username}")
        print(f"姓名：{name}")
        print(f"角色：{'超级管理员' if role == AdminUser.ROLE_SUPER else '普通管理员'}")
        print("=" * 50)
        
        confirm = get_input("确认创建？(y/n)", required=True, default="y")
        if confirm.lower() not in ['y', 'yes', '是']:
            print("\n操作已取消")
            sys.exit(0)
    
    print()
    print("正在创建管理员账号...")
    success = create_admin(username, password, name, role)
    
    if success:
        print("\n✅ 管理员账号创建成功！")
        print(f"\n可以使用以下信息登录：")
        print(f"   账号：{username}")
        print(f"   密码：{'*' * len(password)}")
    else:
        print("\n❌ 管理员账号创建失败！")
        sys.exit(1)


if __name__ == '__main__':
    main()

