from flask import Blueprint, jsonify, request
from sqlalchemy.exc import IntegrityError

from .database import db
from .models import Employee

api = Blueprint("api", __name__)


@api.get("/health")
def health():
    return (
        jsonify(
            {
                "status": "healthy",
                "service": "employee-api",
            }
        ),
        200,
    )


@api.post("/employees")
def create_employee():
    data = request.get_json()

    employee = Employee(
        name=data["name"],
        email=data["email"],
        department=data["department"],
        salary=data["salary"],
    )

    try:
        db.session.add(employee)
        db.session.commit()

        return (
            jsonify(
                {
                    "message": "Employee created successfully",
                    "id": employee.id,
                }
            ),
            201,
        )

    except IntegrityError:
        db.session.rollback()

        return jsonify({"error": "Employee with this email already exists"}), 409


@api.get("/employees")
def get_employees():
    employees = Employee.query.all()

    result = []

    for employee in employees:
        result.append(
            {
                "id": employee.id,
                "name": employee.name,
                "email": employee.email,
                "department": employee.department,
                "salary": employee.salary,
            }
        )

    return jsonify(result), 200


@api.get("/employees/<int:id>")
def get_employee(id):

    employee = db.session.get(Employee, id)

    if employee is None:
        return jsonify({"error": "Employee not found"}), 404

    return (
        jsonify(
            {
                "id": employee.id,
                "name": employee.name,
                "email": employee.email,
                "department": employee.department,
                "salary": employee.salary,
            }
        ),
        200,
    )


@api.put("/employees/<int:id>")
def update_employee(id):

    employee = db.session.get(Employee, id)

    if employee is None:
        return jsonify({"error": "Employee not found"}), 404

    data = request.get_json()

    employee.name = data.get("name", employee.name)
    employee.email = data.get("email", employee.email)
    employee.department = data.get("department", employee.department)
    employee.salary = data.get("salary", employee.salary)

    try:
        db.session.commit()

        return jsonify({"message": "Employee updated successfully"}), 200

    except IntegrityError:
        db.session.rollback()

        return jsonify({"error": "Email already exists"}), 409


@api.delete("/employees/<int:id>")
def delete_employee(id):

    employee = db.session.get(Employee, id)

    if employee is None:
        return jsonify({"error": "Employee not found"}), 404

    db.session.delete(employee)
    db.session.commit()

    return jsonify({"message": "Employee deleted successfully"}), 200
