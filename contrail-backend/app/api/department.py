"""
部门相关 API
用于创建/查询部门信息，供注册时传入 department_id 绑定用户
"""

from flask import request, jsonify
from app.api import api_bp
from app.extensions import db
from app.models import Department


def _norm(v):
    if v is None:
        return None
    v = str(v).strip()
    return v if v else None


@api_bp.route("/departments", methods=["POST"])
def create_department():
    """
    创建部门（若已存在则返回已有记录）
    请求体: { "college": "...", "grade": "...", "major": "...", "class_name": "..." }
    返回: { "department": {...} }
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "请求体不能为空"}), 400

    college = _norm(data.get("college"))
    grade = _norm(data.get("grade"))
    major = _norm(data.get("major"))
    class_name = _norm(data.get("class_name"))

    if not all([college, grade, major, class_name]):
        return jsonify({"error": "college/grade/major/class_name 均不能为空"}), 400

    department = Department.query.filter_by(
        college=college,
        grade=grade,
        major=major,
        class_name=class_name,
    ).first()

    if department:
        return jsonify({"department": department.to_dict()}), 200

    department = Department(
        college=college,
        grade=grade,
        major=major,
        class_name=class_name,
    )
    try:
        db.session.add(department)
        db.session.commit()
        return jsonify({"department": department.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"创建部门失败: {str(e)}"}), 500


@api_bp.route("/departments", methods=["GET"])
def list_departments():
    """
    获取部门列表（简单全量返回）
    返回: { "items": [...], "total": n }
    """
    departments = Department.query.order_by(Department.id.desc()).all()
    return jsonify(
        {
            "total": len(departments),
            "items": [d.to_dict() for d in departments],
        }
    ), 200


