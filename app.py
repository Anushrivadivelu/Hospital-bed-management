from flask import Flask, render_template, request, jsonify, session, send_from_directory
import sqlite3
import os
from datetime import datetime, timedelta

# Create Flask app
app = Flask(__name__)
app.secret_key = 'cura_hospital_secret_key'

# Serve static files
@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('static', filename)

# Database setup
def init_db():
    """Create database and tables if they don't exist"""
    conn = sqlite3.connect('hospital.db')
    cursor = conn.cursor()
    
    # Create hospitals table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS hospitals (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            address TEXT NOT NULL,
            contact TEXT NOT NULL,
            total_beds INTEGER NOT NULL,
            icu_beds INTEGER NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    
    # Create patients table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS patients (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            age INTEGER NOT NULL,
            blood_group TEXT NOT NULL,
            condition TEXT NOT NULL,
            severity TEXT NOT NULL,
            health_risk TEXT NOT NULL,
            doctor_recommendation TEXT NOT NULL,
            priority_score INTEGER NOT NULL,
            status TEXT NOT NULL,
            bed_id TEXT,
            admission_date TEXT,
            discharge_date TEXT,
            expected_stay_days INTEGER,
            hospital_id TEXT,
            extended_stay INTEGER DEFAULT 0
        )
    ''')
    
    # Create beds table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS beds (
            id TEXT PRIMARY KEY,
            hospital_id TEXT NOT NULL,
            type TEXT NOT NULL,
            ward TEXT,
            status TEXT NOT NULL,
            patient_id TEXT,
            last_occupied_date TEXT
        )
    ''')
    
    # Add sample hospital if none exists
    cursor.execute("SELECT COUNT(*) FROM hospitals")
    if cursor.fetchone()[0] == 0:
        cursor.execute('''
            INSERT INTO hospitals (id, name, address, contact, total_beds, icu_beds, password)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            'HOSP001',
            'Apollo Hospital, Chennai',
            '21, Greams Lane, Chennai',
            '044-28293333',
            150,
            20,
            'password123'
        ))
        
        # Create sample beds
        create_sample_beds(conn, 'HOSP001', 150, 20)
        
        # Add some sample patients
        create_sample_patients(conn, 'HOSP001')
    
    conn.commit()
    conn.close()

def create_sample_beds(conn, hospital_id, total_beds, icu_beds):
    """Create sample beds for a hospital"""
    cursor = conn.cursor()
    
    # Create general beds
    for i in range(1, total_beds - icu_beds + 1):
        bed_id = f"{hospital_id}_BED{i:03d}"
        cursor.execute('''
            INSERT OR IGNORE INTO beds (id, hospital_id, type, ward, status)
            VALUES (?, ?, 'general', ?, 'available')
        ''', (bed_id, hospital_id, 'Ward A' if i % 2 == 0 else 'Ward B'))
    
    # Create ICU beds
    for i in range(1, icu_beds + 1):
        bed_id = f"{hospital_id}_ICU{i:03d}"
        cursor.execute('''
            INSERT OR IGNORE INTO beds (id, hospital_id, type, ward, status)
            VALUES (?, ?, 'icu', ?, 'available')
        ''', (bed_id, hospital_id, 'ICU Unit 1'))
    
    # Create flexible beds (20% of total beds)
    flexible_beds = int(total_beds * 0.2)
    for i in range(1, flexible_beds + 1):
        bed_id = f"{hospital_id}_FLEX{i:03d}"
        cursor.execute('''
            INSERT OR IGNORE INTO beds (id, hospital_id, type, ward, status)
            VALUES (?, ?, 'flexible', ?, 'available')
        ''', (bed_id, hospital_id, 'Flex Care Unit'))

def create_sample_patients(conn, hospital_id):
    """Create some sample patients for demonstration"""
    cursor = conn.cursor()
    
    sample_patients = [
        {
            'name': 'Ramesh Kumar',
            'age': 67,
            'blood_group': 'B+',
            'condition': 'Cardiac Arrest',
            'severity': 'high',
            'health_risk': 'critical',
            'doctor_recommendation': 'icu',
            'bed_id': f"{hospital_id}_ICU001",
            'admission_date': (datetime.now() - timedelta(days=2)).strftime('%Y-%m-%d'),
            'expected_stay': 7
        },
        {
            'name': 'Priya Sharma',
            'age': 34,
            'blood_group': 'A-',
            'condition': 'Fractured Leg',
            'severity': 'medium',
            'health_risk': 'moderate',
            'doctor_recommendation': 'general',
            'bed_id': f"{hospital_id}_BED001",
            'admission_date': (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d'),
            'expected_stay': 5
        },
        {
            'name': 'Anjali Gupta',
            'age': 25,
            'blood_group': 'O-',
            'condition': 'Asthma Management',
            'severity': 'low',
            'health_risk': 'stable',
            'doctor_recommendation': 'flexible',
            'bed_id': f"{hospital_id}_FLEX001",
            'admission_date': datetime.now().strftime('%Y-%m-%d'),
            'expected_stay': 2,
            'extended_stay': 1  # Already extended once
        }
    ]
    
    for i, patient_data in enumerate(sample_patients, 1):
        patient_id = f"PAT{i:03d}"
        
        # Calculate priority score
        priority_score = calculate_priority_score(
            patient_data['severity'],
            patient_data['health_risk'],
            patient_data['doctor_recommendation']
        )
        
        # Insert patient
        cursor.execute('''
            INSERT INTO patients (id, name, age, blood_group, condition, severity, 
                                health_risk, doctor_recommendation, priority_score, 
                                status, bed_id, admission_date, expected_stay_days, hospital_id, extended_stay)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'allocated', ?, ?, ?, ?, ?)
        ''', (
            patient_id,
            patient_data['name'],
            patient_data['age'],
            patient_data['blood_group'],
            patient_data['condition'],
            patient_data['severity'],
            patient_data['health_risk'],
            patient_data['doctor_recommendation'],
            priority_score,
            patient_data['bed_id'],
            patient_data['admission_date'],
            patient_data['expected_stay'],
            hospital_id,
            patient_data.get('extended_stay', 0)
        ))
        
        # Update bed status
        cursor.execute('''
            UPDATE beds 
            SET status = 'occupied', patient_id = ?, last_occupied_date = ?
            WHERE id = ?
        ''', (patient_id, patient_data['admission_date'], patient_data['bed_id']))

def calculate_priority_score(severity, health_risk, doctor_recommendation):
    """Calculate priority score for patient"""
    score = 0
    if severity == 'high': score += 40
    elif severity == 'medium': score += 20
    
    if health_risk == 'critical': score += 40
    elif health_risk == 'moderate': score += 20
    
    if doctor_recommendation == 'icu': score += 20
    
    return score

# Routes
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    """Handle hospital login"""
    data = request.json
    hospital_id = data.get('hospital_id')
    password = data.get('password')
    
    conn = sqlite3.connect('hospital.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM hospitals WHERE id = ? AND password = ?', (hospital_id, password))
    hospital = cursor.fetchone()
    conn.close()
    
    if hospital:
        session['hospital_id'] = hospital_id
        session['hospital_name'] = hospital[1]
        return jsonify({
            'success': True,
            'message': 'Login successful',
            'hospital_name': hospital[1]
        })
    else:
        return jsonify({
            'success': False,
            'message': 'Invalid Hospital ID or Password'
        })

@app.route('/register', methods=['POST'])
def register():
    """Handle hospital registration"""
    data = request.json
    
    conn = sqlite3.connect('hospital.db')
    cursor = conn.cursor()
    
    # Check if hospital ID already exists
    cursor.execute('SELECT id FROM hospitals WHERE id = ?', (data.get('hospital_id'),))
    if cursor.fetchone():
        conn.close()
        return jsonify({
            'success': False,
            'message': 'Hospital ID already exists'
        })
    
    try:
        # Insert new hospital
        cursor.execute('''
            INSERT INTO hospitals (id, name, address, contact, total_beds, icu_beds, password)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['hospital_id'],
            data['name'],
            data['address'],
            data['contact'],
            data['total_beds'],
            data['icu_beds'],
            data['password']
        ))
        
        # Create beds for the hospital with unique IDs
        create_sample_beds(conn, data['hospital_id'], data['total_beds'], data['icu_beds'])
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': f'Hospital registered successfully!',
            'hospital_id': data['hospital_id']
        })
        
    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({
            'success': False,
            'message': f'Registration failed: {str(e)}'
        })

@app.route('/api/dashboard-data')
def dashboard_data():
    """Get dashboard data for logged-in hospital"""
    if 'hospital_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    hospital_id = session['hospital_id']
    conn = sqlite3.connect('hospital.db')
    cursor = conn.cursor()
    
    # Get bed statistics
    cursor.execute('''
        SELECT 
            COUNT(*) as total_beds,
            SUM(CASE WHEN status = 'available' THEN 1 ELSE 0 END) as available_beds,
            SUM(CASE WHEN type = 'icu' THEN 1 ELSE 0 END) as icu_beds,
            SUM(CASE WHEN type = 'flexible' THEN 1 ELSE 0 END) as flexible_beds,
            SUM(CASE WHEN status = 'occupied' THEN 1 ELSE 0 END) as occupied_beds
        FROM beds 
        WHERE hospital_id = ?
    ''', (hospital_id,))
    stats = cursor.fetchone()
    
    # Get recent patients (last 10)
    cursor.execute('''
        SELECT name, age, condition, severity, doctor_recommendation, admission_date, bed_id
        FROM patients 
        WHERE hospital_id = ? AND status = 'allocated'
        ORDER BY admission_date DESC 
        LIMIT 10
    ''', (hospital_id,))
    patients = cursor.fetchall()
    
    conn.close()
    
    return jsonify({
        'stats': {
            'total_beds': stats[0],
            'available_beds': stats[1],
            'icu_beds': stats[2],
            'flexible_beds': stats[3],
            'occupied_beds': stats[4]
        },
        'recent_patients': [
            {
                'name': patient[0],
                'age': patient[1],
                'condition': patient[2],
                'severity': patient[3],
                'bed_type': patient[4],
                'admission_date': patient[5],
                'bed_id': patient[6]
            } for patient in patients
        ]
    })

@app.route('/api/allocate-bed', methods=['POST'])
def allocate_bed():
    """Allocate bed to patient"""
    if 'hospital_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    data = request.json
    hospital_id = session['hospital_id']
    
    conn = sqlite3.connect('hospital.db')
    cursor = conn.cursor()
    
    try:
        # Calculate priority score
        priority_score = calculate_priority_score(
            data['severity'],
            data['health_risk'],
            data['doctor_recommendation']
        )
        
        # Calculate expected stay based on severity
        expected_stay = 3  # default for general
        if data['severity'] == 'high':
            expected_stay = 7
        elif data['severity'] == 'medium':
            expected_stay = 5
        elif data['doctor_recommendation'] == 'flexible':
            expected_stay = 2  # Flexible beds: 2 days initial
        
        # Generate patient ID
        cursor.execute("SELECT COUNT(*) FROM patients")
        count = cursor.fetchone()[0]
        patient_id = f"PAT{count + 1:03d}"
        
        # Find available bed
        bed = find_available_bed(cursor, hospital_id, data['doctor_recommendation'])
        
        if bed:
            # Allocate the bed
            cursor.execute('''
                UPDATE beds 
                SET status = "occupied", patient_id = ?, last_occupied_date = ?
                WHERE id = ?
            ''', (patient_id, datetime.now().strftime('%Y-%m-%d'), bed[0]))
            
            # Add patient
            cursor.execute('''
                INSERT INTO patients (id, name, age, blood_group, condition, severity, 
                                    health_risk, doctor_recommendation, priority_score, 
                                    status, bed_id, admission_date, expected_stay_days, hospital_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'allocated', ?, ?, ?, ?)
            ''', (
                patient_id,
                data['patient_name'],
                data['age'],
                data['blood_group'],
                data['admission_cause'],
                data['severity'],
                data['health_risk'],
                data['doctor_recommendation'],
                priority_score,
                bed[0],
                datetime.now().strftime('%Y-%m-%d'),
                expected_stay,
                hospital_id
            ))
            
            conn.commit()
            conn.close()
            
            return jsonify({
                'success': True,
                'message': f'Bed {bed[0]} allocated successfully!',
                'bed_id': bed[0],
                'patient_id': patient_id,
                'admission_date': datetime.now().strftime('%Y-%m-%d'),
                'expected_stay': expected_stay
            })
        else:
            # No bed available
            cursor.execute('''
                INSERT INTO patients (id, name, age, blood_group, condition, severity, 
                                    health_risk, doctor_recommendation, priority_score, 
                                    status, admission_date, expected_stay_days, hospital_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'waiting', ?, ?, ?)
            ''', (
                patient_id,
                data['patient_name'],
                data['age'],
                data['blood_group'],
                data['admission_cause'],
                data['severity'],
                data['health_risk'],
                data['doctor_recommendation'],
                priority_score,
                datetime.now().strftime('%Y-%m-%d'),
                expected_stay,
                hospital_id
            ))
            
            conn.commit()
            conn.close()
            
            return jsonify({
                'success': False,
                'message': 'No available beds. Patient added to waiting list.'
            })
            
    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        })

@app.route('/api/extend-stay', methods=['POST'])
def extend_stay():
    """Extend patient stay by 2 days (for flexible beds)"""
    if 'hospital_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    data = request.json
    patient_id = data.get('patient_id')
    
    conn = sqlite3.connect('hospital.db')
    cursor = conn.cursor()
    
    try:
        # Get patient details
        cursor.execute('''
            SELECT expected_stay_days, extended_stay, doctor_recommendation 
            FROM patients WHERE id = ?
        ''', (patient_id,))
        patient = cursor.fetchone()
        
        if not patient:
            conn.close()
            return jsonify({'success': False, 'message': 'Patient not found'})
        
        expected_stay, extended_count, bed_type = patient
        
        # Check if patient is in flexible bed and hasn't exceeded max extensions
        if bed_type == 'flexible' and extended_count < 2:  # Max 2 extensions (total 6 days)
            # Extend stay by 2 days
            new_expected_stay = expected_stay + 2
            new_extended_count = extended_count + 1
            
            cursor.execute('''
                UPDATE patients 
                SET expected_stay_days = ?, extended_stay = ?
                WHERE id = ?
            ''', (new_expected_stay, new_extended_count, patient_id))
            
            conn.commit()
            conn.close()
            
            return jsonify({
                'success': True,
                'message': f'Stay extended by 2 days. New expected discharge in {new_expected_stay} days total.',
                'new_stay_days': new_expected_stay,
                'extensions_used': new_extended_count
            })
        else:
            conn.close()
            if bed_type != 'flexible':
                return jsonify({
                    'success': False,
                    'message': 'Stay extension only available for flexible care patients'
                })
            else:
                return jsonify({
                    'success': False,
                    'message': 'Maximum extensions reached (2 extensions allowed). Please discharge or transfer patient.'
                })
        
    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({
            'success': False,
            'message': f'Error extending stay: {str(e)}'
        })

@app.route('/api/discharge-patient', methods=['POST'])
def discharge_patient():
    """Discharge patient and free up bed"""
    if 'hospital_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    data = request.json
    patient_id = data.get('patient_id')
    
    conn = sqlite3.connect('hospital.db')
    cursor = conn.cursor()
    
    try:
        # Get patient details
        cursor.execute('SELECT bed_id FROM patients WHERE id = ?', (patient_id,))
        patient = cursor.fetchone()
        
        if not patient:
            conn.close()
            return jsonify({'success': False, 'message': 'Patient not found'})
        
        bed_id = patient[0]
        
        # Update patient status
        cursor.execute('''
            UPDATE patients 
            SET status = 'discharged', discharge_date = ?
            WHERE id = ?
        ''', (datetime.now().strftime('%Y-%m-%d'), patient_id))
        
        # Free up the bed
        if bed_id:
            cursor.execute('''
                UPDATE beds 
                SET status = 'available', patient_id = NULL
                WHERE id = ?
            ''', (bed_id,))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': f'Patient discharged successfully. Bed {bed_id} is now available.'
        })
        
    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({
            'success': False,
            'message': f'Error discharging patient: {str(e)}'
        })

def find_available_bed(cursor, hospital_id, bed_type):
    """Find an available bed of the recommended type"""
    cursor.execute('''
        SELECT id FROM beds 
        WHERE hospital_id = ? AND type = ? AND status = 'available' 
        LIMIT 1
    ''', (hospital_id, bed_type))
    bed = cursor.fetchone()
    
    if not bed:
        # Try general beds as fallback
        cursor.execute('''
            SELECT id FROM beds 
            WHERE hospital_id = ? AND type = 'general' AND status = 'available' 
            LIMIT 1
        ''', (hospital_id,))
        bed = cursor.fetchone()
    
    return bed

@app.route('/api/available-beds')
def available_beds():
    """Get available beds for hospital"""
    if 'hospital_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    hospital_id = session['hospital_id']
    conn = sqlite3.connect('hospital.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, type, ward, status, last_occupied_date
        FROM beds 
        WHERE hospital_id = ?
        ORDER BY type, id
    ''', (hospital_id,))
    beds = cursor.fetchall()
    conn.close()
    
    return jsonify({
        'beds': [
            {
                'id': bed[0],
                'type': bed[1],
                'ward': bed[2],
                'status': bed[3],
                'last_occupied': bed[4]
            } for bed in beds
        ]
    })

@app.route('/api/allocated-patients')
def allocated_patients():
    """Get allocated patients for hospital"""
    if 'hospital_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    hospital_id = session['hospital_id']
    conn = sqlite3.connect('hospital.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT p.id, p.name, p.age, p.blood_group, p.condition, p.bed_id, 
               p.admission_date, p.severity, p.expected_stay_days, p.extended_stay,
               p.doctor_recommendation
        FROM patients p
        WHERE p.hospital_id = ? AND p.status = 'allocated'
        ORDER BY p.admission_date DESC
    ''', (hospital_id,))
    patients = cursor.fetchall()
    conn.close()
    
    return jsonify({
        'patients': [
            {
                'id': patient[0],
                'name': patient[1],
                'age': patient[2],
                'blood_group': patient[3],
                'condition': patient[4],
                'bed_id': patient[5],
                'admission_date': patient[6],
                'severity': patient[7],
                'expected_stay': patient[8],
                'extended_stay': patient[9],
                'bed_type': patient[10],
                'expected_discharge': calculate_expected_discharge(patient[6], patient[8]),
                'can_extend': patient[10] == 'flexible' and patient[9] < 2
            } for patient in patients
        ]
    })

def calculate_expected_discharge(admission_date, expected_stay_days):
    """Calculate expected discharge date"""
    if admission_date and expected_stay_days:
        admission = datetime.strptime(admission_date, '%Y-%m-%d')
        discharge = admission + timedelta(days=expected_stay_days)
        return discharge.strftime('%Y-%m-%d')
    return None

@app.route('/logout')
def logout():
    """Logout user"""
    session.clear()
    return jsonify({'success': True, 'message': 'Logged out successfully'})

if __name__ == '__main__':
    # Initialize database
    init_db()
    print("Database initialized!")
    print("Sample hospital created: HOSP001 (password: password123)")
    print("Access the application at: http://127.0.0.1:5000")
    
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
