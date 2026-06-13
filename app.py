from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import mysql.connector
from mysql.connector import Error
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Database configuration (Update with your MySQL credentials)
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '1234',
    'database': 'payroll_management'
}

def get_db_connection():
    try:
        connection = mysql.connector.connect(**db_config)
        return connection
    except Error as e:
        print(f"Database connection error: {e}")
        return None

@app.route('/')
def index():
    return render_template('index.html')

# ==========================================
# EMPLOYEE CRUD OPERATIONS
# ==========================================

@app.route('/api/employees', methods=['GET'])
def get_employees():
    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'error': 'Database connection failed'}), 500
    
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT e.employee_id, e.name, e.designation, e.department_id, 
                   d.department_name,
                   s.basic_salary, s.net_salary
            FROM Employee e
            LEFT JOIN Department d ON e.department_id = d.department_id
            LEFT JOIN Salary s ON e.employee_id = s.employee_id
            ORDER BY e.employee_id
        """)
        employees = cursor.fetchall()
        conn.close()
        return jsonify({'success': True, 'data': employees})
    except Error as e:
        conn.close()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/employees', methods=['POST'])
def create_employee():
    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'error': 'Database connection failed'}), 500
    
    cursor = conn.cursor()
    data = request.json
    
    try:
        cursor.execute("""
            INSERT INTO Employee (name, department_id, designation) 
            VALUES (%s, %s, %s)
        """, (data['name'], data.get('department_id'), data.get('designation')))
        conn.commit()
        new_id = cursor.lastrowid
        conn.close()
        return jsonify({'success': True, 'message': 'Employee added successfully', 'employee_id': new_id})
    except Error as e:
        conn.close()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/employees/<int:emp_id>', methods=['PUT'])
def update_employee(emp_id):
    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'error': 'Database connection failed'}), 500
    
    cursor = conn.cursor()
    data = request.json
    
    try:
        updates = []
        values = []
        
        if 'name' in data:
            updates.append("name = %s")
            values.append(data['name'])
        if 'department_id' in data:
            updates.append("department_id = %s")
            values.append(data['department_id'])
        if 'designation' in data:
            updates.append("designation = %s")
            values.append(data['designation'])
        
        if updates:
            values.append(emp_id)
            cursor.execute(f"UPDATE Employee SET {', '.join(updates)} WHERE employee_id = %s", values)
            conn.commit()
        
        conn.close()
        return jsonify({'success': True, 'message': 'Employee updated successfully'})
    except Error as e:
        conn.close()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/employees/<int:emp_id>', methods=['DELETE'])
def delete_employee(emp_id):
    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'error': 'Database connection failed'}), 500
    
    cursor = conn.cursor()
    
    try:
        # Check if employee exists
        cursor.execute("SELECT employee_id FROM Employee WHERE employee_id = %s", (emp_id,))
        if not cursor.fetchone():
            conn.close()
            return jsonify({'success': False, 'error': 'Employee not found'}), 404
        
        cursor.execute("DELETE FROM Employee WHERE employee_id = %s", (emp_id,))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Employee deleted successfully'})
    except Error as e:
        conn.close()
        return jsonify({'success': False, 'error': str(e)}), 500

# ==========================================
# DEPARTMENT OPERATIONS
# ==========================================

@app.route('/api/departments', methods=['GET'])
def get_departments():
    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'error': 'Database connection failed'}), 500
    
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT department_id, department_name FROM Department ORDER BY department_name")
        departments = cursor.fetchall()
        conn.close()
        return jsonify({'success': True, 'data': departments})
    except Error as e:
        conn.close()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/departments', methods=['POST'])
def create_department():
    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'error': 'Database connection failed'}), 500
    
    cursor = conn.cursor()
    data = request.json
    
    try:
        cursor.execute("INSERT INTO Department (department_name) VALUES (%s)", (data['department_name'],))
        conn.commit()
        new_id = cursor.lastrowid
        conn.close()
        return jsonify({'success': True, 'message': 'Department added successfully', 'department_id': new_id})
    except Error as e:
        conn.close()
        return jsonify({'success': False, 'error': str(e)}), 500

# ==========================================
# SALARY OPERATIONS
# ==========================================

@app.route('/api/salary/<int:emp_id>', methods=['GET'])
def get_salary(emp_id):
    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'error': 'Database connection failed'}), 500
    
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT salary_id, employee_id, basic_salary, allowances, deductions, net_salary 
            FROM Salary WHERE employee_id = %s
        """, (emp_id,))
        salary = cursor.fetchone()
        conn.close()
        return jsonify({'success': True, 'data': salary})
    except Error as e:
        conn.close()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/salary', methods=['POST'])
def create_salary():
    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'error': 'Database connection failed'}), 500
    
    cursor = conn.cursor()
    data = request.json
    
    try:
        net_salary = float(data['basic_salary']) + float(data.get('allowances', 0)) - float(data.get('deductions', 0))
        cursor.execute("""
            INSERT INTO Salary (employee_id, basic_salary, allowances, deductions, net_salary) 
            VALUES (%s, %s, %s, %s, %s)
        """, (data['employee_id'], data['basic_salary'], data.get('allowances', 0), 
              data.get('deductions', 0), net_salary))
        conn.commit()
        new_id = cursor.lastrowid
        conn.close()
        return jsonify({'success': True, 'message': 'Salary record created successfully', 'salary_id': new_id})
    except Error as e:
        conn.close()
        return jsonify({'success': False, 'error': str(e)}), 500

# ==========================================
# ATTENDANCE OPERATIONS
# ==========================================

@app.route('/api/attendance', methods=['GET'])
def get_attendance():
    emp_id = request.args.get('employee_id')
    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'error': 'Database connection failed'}), 500
    
    cursor = conn.cursor(dictionary=True)
    try:
        if emp_id:
            cursor.execute("SELECT * FROM Attendance WHERE employee_id = %s ORDER BY month DESC", (emp_id,))
        else:
            cursor.execute("SELECT a.*, e.name FROM Attendance a JOIN Employee e ON a.employee_id = e.employee_id ORDER BY a.month DESC")
        attendance = cursor.fetchall()
        conn.close()
        return jsonify({'success': True, 'data': attendance})
    except Error as e:
        conn.close()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/attendance', methods=['POST'])
def add_attendance():
    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'error': 'Database connection failed'}), 500
    
    cursor = conn.cursor()
    data = request.json
    
    try:
        cursor.execute("""
            INSERT INTO Attendance (employee_id, month, days_present) 
            VALUES (%s, %s, %s)
        """, (data['employee_id'], data['month'], data['days_present']))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Attendance recorded successfully'})
    except Error as e:
        conn.close()
        return jsonify({'success': False, 'error': str(e)}), 500

# ==========================================
# LEAVE OPERATIONS
# ==========================================

@app.route('/api/leave', methods=['GET'])
def get_leave():
    emp_id = request.args.get('employee_id')
    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'error': 'Database connection failed'}), 500
    
    cursor = conn.cursor(dictionary=True)
    try:
        if emp_id:
            cursor.execute("SELECT * FROM `Leave` WHERE employee_id = %s ORDER BY leave_id DESC", (emp_id,))
        else:
            cursor.execute("SELECT l.*, e.name FROM `Leave` l JOIN Employee e ON l.employee_id = e.employee_id ORDER BY l.leave_id DESC")
        leaves = cursor.fetchall()
        conn.close()
        return jsonify({'success': True, 'data': leaves})
    except Error as e:
        conn.close()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/leave', methods=['POST'])
def add_leave():
    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'error': 'Database connection failed'}), 500
    
    cursor = conn.cursor()
    data = request.json
    
    try:
        cursor.execute("""
            INSERT INTO `Leave` (employee_id, leave_days, leave_type) 
            VALUES (%s, %s, %s)
        """, (data['employee_id'], data['leave_days'], data['leave_type']))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Leave request submitted successfully'})
    except mysql.connector.Error as err:
        conn.close()
        if "Exceed maximum allowed" in str(err.msg):
            return jsonify({'success': False, 'error': 'Cannot exceed maximum allowed 20 leave days per year'}), 400
        return jsonify({'success': False, 'error': str(err.msg)}), 500

# ==========================================
# BONUS OPERATIONS
# ==========================================

@app.route('/api/bonus', methods=['POST'])
def add_bonus():
    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'error': 'Database connection failed'}), 500
    
    cursor = conn.cursor()
    data = request.json
    
    try:
        cursor.execute("INSERT INTO Bonus (employee_id, bonus_amount) VALUES (%s, %s)", 
                       (data['employee_id'], data['bonus_amount']))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Bonus awarded successfully'})
    except Error as e:
        conn.close()
        return jsonify({'success': False, 'error': str(e)}), 500

# ==========================================
# STORED PROCEDURE EXECUTION
# ==========================================

@app.route('/api/payslip/<int:emp_id>', methods=['GET'])
def get_payslip(emp_id):
    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'error': 'Database connection failed'}), 500
    
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.callproc('GeneratePayslip', [emp_id])
        result = []
        for cur in cursor.stored_results():
            result.extend(cur.fetchall())
        conn.close()
        return jsonify({'success': True, 'data': result})
    except Error as e:
        conn.close()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/calculate-salary/<int:emp_id>', methods=['POST'])
def calculate_salary(emp_id):
    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'error': 'Database connection failed'}), 500
    
    cursor = conn.cursor()
    try:
        cursor.callproc('CalculateMonthlySalary', [emp_id])
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Salary calculated successfully'})
    except Error as e:
        conn.close()
        return jsonify({'success': False, 'error': str(e)}), 500

# ==========================================
# ANALYTICAL QUERIES
# ==========================================

@app.route('/api/queries/<int:query_id>', methods=['GET'])
def execute_query(query_id):
    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'error': 'Database connection failed'}), 500
    
    cursor = conn.cursor(dictionary=True)
    
    queries = {
        1: "SELECT * FROM Employee",
        2: "SELECT e.*, d.department_name FROM Employee e JOIN Department d ON e.department_id = d.department_id WHERE e.department_id = %s",
        3: "SELECT e.name, e.designation, s.basic_salary, s.net_salary FROM Employee e INNER JOIN Salary s ON e.employee_id = s.employee_id",
        4: "SELECT e.name, d.department_name, s.net_salary FROM Employee e JOIN Department d ON e.department_id = d.department_id JOIN Salary s ON e.employee_id = s.employee_id",
        5: "SELECT d.department_name, COUNT(e.employee_id) AS total_employees FROM Department d LEFT JOIN Employee e ON d.department_id = e.department_id GROUP BY d.department_id, d.department_name",
        6: "SELECT d.department_name, AVG(s.basic_salary) AS avg_salary FROM Department d JOIN Employee e ON d.department_id = e.department_id JOIN Salary s ON e.employee_id = s.employee_id GROUP BY d.department_name HAVING AVG(s.basic_salary) > 50000",
        7: "SELECT name FROM Employee WHERE employee_id IN (SELECT employee_id FROM Salary WHERE basic_salary > (SELECT AVG(basic_salary) FROM Salary))",
        8: "SELECT e1.name, s1.basic_salary FROM Employee e1 JOIN Salary s1 ON e1.employee_id = s1.employee_id WHERE e1.department_id = (SELECT department_id FROM Employee WHERE employee_id = %s) AND s1.basic_salary > (SELECT s2.basic_salary FROM Salary s2 WHERE s2.employee_id = %s)",
        9: "SELECT e.name, s.net_salary FROM Employee e LEFT JOIN Salary s ON e.employee_id = s.employee_id",
        10: "SELECT department_name FROM Department d WHERE NOT EXISTS (SELECT 1 FROM Employee e WHERE e.department_id = d.department_id)"
    }
    
    selected_query = queries.get(query_id)
    if not selected_query:
        conn.close()
        return jsonify({'success': False, 'error': 'Invalid query ID'}), 404
    
    try:
        if query_id == 2:
            dept_id = request.args.get('dept_id', 1)
            cursor.execute(selected_query, (dept_id,))
        elif query_id == 8:
            emp_id = request.args.get('emp_id', 1)
            cursor.execute(selected_query, (emp_id, emp_id))
        else:
            cursor.execute(selected_query)
        
        result = cursor.fetchall()
        conn.close()
        return jsonify({'success': True, 'data': result})
    except Error as e:
        conn.close()
        return jsonify({'success': False, 'error': str(e)}), 500

# ==========================================
# STATISTICS
# ==========================================

@app.route('/api/stats', methods=['GET'])
def get_stats():
    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'error': 'Database connection failed'}), 500
    
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT COUNT(*) as total FROM Employee")
        total_employees = cursor.fetchone()['total']
        
        cursor.execute("SELECT COUNT(*) as total FROM Department")
        total_departments = cursor.fetchone()['total']
        
        cursor.execute("SELECT SUM(net_salary) as total_payroll FROM Salary")
        total_payroll = cursor.fetchone()['total_payroll'] or 0
        
        cursor.execute("SELECT AVG(basic_salary) as avg_salary FROM Salary")
        avg_salary = cursor.fetchone()['avg_salary'] or 0
        
        conn.close()
        return jsonify({
            'success': True, 
            'data': {
                'total_employees': total_employees,
                'total_departments': total_departments,
                'total_payroll': float(total_payroll),
                'avg_salary': float(avg_salary)
            }
        })
    except Error as e:
        conn.close()
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)