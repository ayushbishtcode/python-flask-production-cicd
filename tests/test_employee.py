def test_create_employee(client):

    response = client.post(
        "/employees",
        json={
            "name": "Ayush",
            "email": "ayush@test.com",
            "department": "DevOps",
            "salary": 80000,
        },
    )

    assert response.status_code == 201

    data = response.get_json()

    assert data["message"] == "Employee created successfully"

    assert "id" in data


def test_duplicate_employee(client):

    employee = {
        "name": "Ayush",
        "email": "ayush@test.com",
        "department": "DevOps",
        "salary": 80000,
    }

    # First request should succeed
    client.post("/employees", json=employee)

    # Second request should fail
    response = client.post("/employees", json=employee)

    assert response.status_code == 409

    data = response.get_json()

    assert data["error"] == "Employee with this email already exists"


def test_get_employees(client):

    employee = {
        "name": "Rahul",
        "email": "rahul@test.com",
        "department": "HR",
        "salary": 60000,
    }

    create_response = client.post("/employees", json=employee)

    assert create_response.status_code == 201

    response = client.get("/employees")

    assert response.status_code == 200

    data = response.get_json()

    assert len(data) == 1
    assert data[0]["name"] == "Rahul"
    assert data[0]["email"] == "rahul@test.com"
    assert data[0]["department"] == "HR"
    assert data[0]["salary"] == 60000


def test_update_employee(client):

    employee = {
        "name": "Ayush",
        "email": "update@test.com",
        "department": "IT",
        "salary": 50000,
    }

    create_response = client.post("/employees", json=employee)

    assert create_response.status_code == 201

    employee_id = create_response.get_json()["id"]

    update_response = client.put(
        f"/employees/{employee_id}",
        json={
            "name": "Ayush Bisht",
            "email": "update@test.com",
            "department": "DevOps",
            "salary": 80000,
        },
    )

    assert update_response.status_code == 200

    data = update_response.get_json()

    assert data["message"] == "Employee updated successfully"

    # Verify the actual updated employee
    get_response = client.get(f"/employees/{employee_id}")

    assert get_response.status_code == 200

    employee_data = get_response.get_json()

    assert employee_data["name"] == "Ayush Bisht"
    assert employee_data["email"] == "update@test.com"
    assert employee_data["department"] == "DevOps"
    assert employee_data["salary"] == 80000


def test_delete_employee(client):

    employee = {
        "name": "Delete Me",
        "email": "delete@test.com",
        "department": "IT",
        "salary": 50000,
    }

    create_response = client.post("/employees", json=employee)

    assert create_response.status_code == 201

    employee_id = create_response.get_json()["id"]

    delete_response = client.delete(f"/employees/{employee_id}")

    assert delete_response.status_code == 200

    data = delete_response.get_json()

    assert data["message"] == "Employee deleted successfully"

    get_response = client.get(f"/employees/{employee_id}")

    assert get_response.status_code == 404


def test_update_employee_not_found(client):

    response = client.put(
        "/employees/99999",
        json={
            "name": "Nobody",
            "email": "nobody@test.com",
            "department": "IT",
            "salary": 50000,
        },
    )

    assert response.status_code == 404

    data = response.get_json()

    assert data["error"] == "Employee not found"


def test_update_duplicate_email(client):

    employee_one = {
        "name": "Ayush",
        "email": "ayush1@test.com",
        "department": "IT",
        "salary": 50000,
    }

    employee_two = {
        "name": "Rahul",
        "email": "rahul1@test.com",
        "department": "HR",
        "salary": 60000,
    }

    response_one = client.post("/employees", json=employee_one)
    response_two = client.post("/employees", json=employee_two)

    assert response_one.status_code == 201
    assert response_two.status_code == 201

    employee_two_id = response_two.get_json()["id"]

    update_response = client.put(
        f"/employees/{employee_two_id}",
        json={
            "email": "ayush1@test.com",
        },
    )

    assert update_response.status_code == 409

    data = update_response.get_json()

    assert data["error"] == "Email already exists"


def test_delete_employee_not_found(client):

    response = client.delete("/employees/99999")

    assert response.status_code == 404

    data = response.get_json()

    assert data["error"] == "Employee not found"
