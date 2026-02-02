"""
初始化证书类型脚本
用于在数据库中初始化5种固定的证书类型：
1. 英语四级
2. 英语六级
3. 雅思IELTS
4. 任职情况
5. 获奖情况
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
from app.models import CertificateType

# 加载环境变量
load_dotenv()

# 固定的证书类型配置
CERTIFICATE_TYPES = [
    {
        'name': '英语四级',
        'description': '大学英语四级考试证书，单次上传，需要存储分数'
    },
    {
        'name': '英语六级',
        'description': '大学英语六级考试证书，单次上传，需要存储分数'
    },
    {
        'name': '雅思IELTS',
        'description': '国际英语语言测试系统证书，单次上传，需要存储听力、阅读、写作、口语、总分'
    },
    {
        'name': '任职情况',
        'description': '学生任职情况证明，可多次上传，需要存储任职时间、职务、集体获奖情况'
    },
    {
        'name': '获奖情况',
        'description': '学生获奖情况证明，可多次上传，需要存储奖励时间、主办单位、奖励级别、获奖等次'
    }
]


def init_certificate_types():
    """
    初始化证书类型
    如果证书类型已存在，则跳过；如果不存在，则创建
    """
    # 创建 Flask 应用实例
    config_name = os.environ.get('FLASK_ENV', 'development')
    app = create_app(config_name)
    
    with app.app_context():
        created_count = 0
        skipped_count = 0
        
        print("=" * 50)
        print("初始化证书类型")
        print("=" * 50)
        print()
        
        for cert_type_data in CERTIFICATE_TYPES:
            name = cert_type_data['name']
            description = cert_type_data['description']
            
            # 检查是否已存在
            existing = CertificateType.query.filter_by(name=name).first()
            if existing:
                print(f"⏭️  跳过：'{name}' 已存在（ID: {existing.id}）")
                skipped_count += 1
                continue
            
            # 创建证书类型
            cert_type = CertificateType(
                name=name,
                description=description,
                is_required=True
            )
            
            try:
                db.session.add(cert_type)
                db.session.commit()
                print(f"✅ 创建：'{name}' (ID: {cert_type.id})")
                created_count += 1
            except Exception as e:
                db.session.rollback()
                print(f"❌ 创建失败：'{name}' - {str(e)}")
        
        print()
        print("=" * 50)
        print("初始化完成")
        print("=" * 50)
        print(f"✅ 创建：{created_count} 个")
        print(f"⏭️  跳过：{skipped_count} 个")
        print(f"📊 总计：{len(CERTIFICATE_TYPES)} 个")
        
        return created_count > 0 or skipped_count == len(CERTIFICATE_TYPES)


def main():
    """主函数"""
    success = init_certificate_types()
    
    if success:
        print("\n✅ 证书类型初始化成功！")
    else:
        print("\n❌ 证书类型初始化失败！")
        sys.exit(1)


if __name__ == '__main__':
    main()

