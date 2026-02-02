"""
手动添加缺失的数据库列
用于修复 users 表中缺失的 credits, gpa, birthplace, phone 字段
"""
import os
import sqlite3
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

def get_database_path():
    """获取数据库文件路径"""
    # 从环境变量或默认配置获取数据库路径
    db_url = os.environ.get('DEV_DATABASE_URL', 'sqlite:///contrail_dev.db')
    
    # 解析 SQLite URL (格式: sqlite:///path/to/db.db)
    if db_url.startswith('sqlite:///'):
        db_path = db_url.replace('sqlite:///', '')
        # 如果是相对路径，转换为绝对路径
        if not os.path.isabs(db_path):
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            # SQLite 默认会在 instance/ 目录下查找数据库文件
            instance_path = os.path.join(project_root, 'instance', db_path)
            if os.path.exists(instance_path):
                db_path = instance_path
            else:
                db_path = os.path.join(project_root, db_path)
        return db_path
    else:
        raise ValueError(f"不支持的数据库 URL: {db_url}")

def add_missing_columns():
    """添加缺失的列到 users 表"""
    db_path = get_database_path()
    
    if not os.path.exists(db_path):
        print(f"错误: 数据库文件不存在: {db_path}")
        return
    
    print(f"连接到数据库: {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 检查列是否已存在
        cursor.execute("PRAGMA table_info(users)")
        columns = [row[1] for row in cursor.fetchall()]
        
        print(f"当前 users 表的列: {columns}")
        
        # 定义需要添加的列
        columns_to_add = [
            ('credits', 'REAL'),
            ('gpa', 'REAL'),
            ('birthplace', 'VARCHAR(100)'),
            ('phone', 'VARCHAR(20)')
        ]
        
        added_count = 0
        for col_name, col_type in columns_to_add:
            if col_name not in columns:
                print(f"正在添加列: {col_name} ({col_type})...")
                sql = f"ALTER TABLE users ADD COLUMN {col_name} {col_type}"
                cursor.execute(sql)
                added_count += 1
                print(f"✓ 成功添加列: {col_name}")
            else:
                print(f"列 {col_name} 已存在，跳过")
        
        conn.commit()
        
        if added_count > 0:
            print(f"\n成功添加了 {added_count} 个列！")
        else:
            print("\n所有列都已存在，无需添加")
            
    except Exception as e:
        conn.rollback()
        print(f"错误: {str(e)}")
        raise
    finally:
        conn.close()

if __name__ == '__main__':
    add_missing_columns()

