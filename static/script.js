// Global variable to store current hospital
let currentHospital = null;

// Page navigation
function showPage(pageName) {
    // Hide all pages
    document.querySelectorAll('.page-content').forEach(page => {
        page.classList.remove('active');
    });
    
    // Remove active class from all menu items
    document.querySelectorAll('.sidebar-menu a').forEach(item => {
        item.classList.remove('active');
    });
    
    // Show selected page
    const pageElement = document.getElementById(pageName + 'Content');
    if (pageElement) {
        pageElement.classList.add('active');
    }
    
    // Add active class to clicked menu item
    event.target.classList.add('active');
    
    // Load page data
    if (pageName === 'dashboard') {
        loadDashboardData();
    } else if (pageName === 'availableBeds') {
        loadAvailableBeds();
    } else if (pageName === 'allocatedPatients') {
        loadAllocatedPatients();
    }
}

// Authentication functions
function showRegister() {
    document.getElementById('loginForm').style.display = 'none';
    document.getElementById('registerForm').style.display = 'block';
}

function showLogin() {
    document.getElementById('registerForm').style.display = 'none';
    document.getElementById('loginForm').style.display = 'block';
}

async function login() {
    const hospitalId = document.getElementById('hospitalId').value;
    const password = document.getElementById('password').value;
    
    if (!hospitalId || !password) {
        alert('Please enter both Hospital ID and Password');
        return;
    }
    
    try {
        const response = await fetch('/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                hospital_id: hospitalId,
                password: password
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            currentHospital = {
                id: hospitalId,
                name: data.hospital_name
            };
            showDashboard();
        } else {
            alert(data.message);
        }
    } catch (error) {
        alert('Login failed. Please try again.');
        console.error('Login error:', error);
    }
}

async function registerHospital() {
    const hospitalData = {
        hospital_id: document.getElementById('regHospitalId').value,
        name: document.getElementById('regHospitalName').value,
        address: document.getElementById('regAddress').value,
        contact: document.getElementById('regContact').value,
        total_beds: parseInt(document.getElementById('regBeds').value),
        icu_beds: parseInt(document.getElementById('regIcuBeds').value),
        password: document.getElementById('regPassword').value
    };
    
    // Simple validation
    if (!hospitalData.hospital_id || !hospitalData.name || !hospitalData.address || !hospitalData.contact) {
        alert('Please fill all required fields');
        return;
    }
    
    if (hospitalData.total_beds <= hospitalData.icu_beds) {
        alert('Total beds must be greater than ICU beds');
        return;
    }
    
    try {
        const response = await fetch('/register', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(hospitalData)
        });
        
        const data = await response.json();
        
        if (data.success) {
            alert(data.message);
            showLogin();
            // Pre-fill the login form with new hospital ID
            document.getElementById('hospitalId').value = hospitalData.hospital_id;
            // Clear registration form
            document.getElementById('regHospitalId').value = '';
            document.getElementById('regHospitalName').value = '';
            document.getElementById('regAddress').value = '';
            document.getElementById('regContact').value = '';
            document.getElementById('regBeds').value = '';
            document.getElementById('regIcuBeds').value = '';
            document.getElementById('regPassword').value = '';
        } else {
            alert(data.message);
        }
    } catch (error) {
        alert('Registration failed. Please try again.');
        console.error('Registration error:', error);
    }
}

async function logout() {
    try {
        await fetch('/logout');
        currentHospital = null;
        showLoginPage();
    } catch (error) {
        console.error('Logout error:', error);
        showLoginPage();
    }
}

function showLoginPage() {
    document.getElementById('loginPage').classList.add('active');
    document.getElementById('dashboardPage').classList.remove('active');
}

function showDashboard() {
    document.getElementById('loginPage').classList.remove('active');
    document.getElementById('dashboardPage').classList.add('active');
    document.getElementById('hospitalNameDisplay').textContent = currentHospital.name;
    loadDashboardData();
}

// Data loading functions
async function loadDashboardData() {
    try {
        showLoading('recentAllocationsTable', 'Loading recent allocations...');
        
        const response = await fetch('/api/dashboard-data');
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (data.error) {
            alert('Please login again');
            showLoginPage();
            return;
        }
        
        // Update stats
        document.getElementById('totalBeds').textContent = data.stats?.total_beds || 0;
        document.getElementById('availableBeds').textContent = data.stats?.available_beds || 0;
        document.getElementById('icuBeds').textContent = data.stats?.icu_beds || 0;
        document.getElementById('flexibleBeds').textContent = data.stats?.flexible_beds || 0;
        document.getElementById('occupiedBeds').textContent = data.stats?.occupied_beds || 0;
        
        // Update recent allocations table
        const table = document.getElementById('recentAllocationsTable');
        if (data.recent_patients && data.recent_patients.length > 0) {
            table.innerHTML = data.recent_patients.map(patient => `
                <tr>
                    <td>${patient.name}</td>
                    <td>${patient.age}</td>
                    <td>${patient.condition}</td>
                    <td><span class="badge ${patient.severity}">${patient.severity}</span></td>
                    <td>${patient.bed_type}</td>
                    <td>${patient.admission_date}</td>
                    <td>${patient.bed_id || 'N/A'}</td>
                </tr>
            `).join('');
        } else {
            table.innerHTML = `
                <tr>
                    <td colspan="7" class="empty-state">
                        <i class="fas fa-user-injured"></i>
                        <p>No recent allocations</p>
                    </td>
                </tr>
            `;
        }
    } catch (error) {
        console.error('Error loading dashboard data:', error);
        showError('recentAllocationsTable', 'Error loading dashboard data');
    }
}

async function loadAvailableBeds() {
    try {
        showLoading('bedsTable', 'Loading beds...');
        
        const response = await fetch('/api/available-beds');
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (data.error) {
            alert('Please login again');
            showLoginPage();
            return;
        }
        
        const table = document.getElementById('bedsTable');
        if (data.beds && data.beds.length > 0) {
            table.innerHTML = data.beds.map(bed => `
                <tr>
                    <td>${bed.id}</td>
                    <td>${bed.type}</td>
                    <td>${bed.ward}</td>
                    <td><span class="badge ${bed.status === 'available' ? 'low' : 'high'}">${bed.status}</span></td>
                    <td>${bed.last_occupied || 'Never'}</td>
                </tr>
            `).join('');
        } else {
            table.innerHTML = `
                <tr>
                    <td colspan="5" class="empty-state">
                        <i class="fas fa-bed"></i>
                        <p>No beds found</p>
                    </td>
                </tr>
            `;
        }
    } catch (error) {
        console.error('Error loading beds:', error);
        showError('bedsTable', 'Error loading bed data');
    }
}

async function loadAllocatedPatients() {
    try {
        showLoading('patientsTable', 'Loading patients...');
        
        const response = await fetch('/api/allocated-patients');
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (data.error) {
            alert('Please login again');
            showLoginPage();
            return;
        }
        
        const table = document.getElementById('patientsTable');
        if (data.patients && data.patients.length > 0) {
            table.innerHTML = data.patients.map(patient => `
                <tr>
                    <td>${patient.name}</td>
                    <td>${patient.age}</td>
                    <td>${patient.blood_group}</td>
                    <td>${patient.condition}</td>
                    <td><span class="badge ${patient.severity}">${patient.severity}</span></td>
                    <td>${patient.bed_id}</td>
                    <td>${patient.admission_date}</td>
                    <td>${patient.expected_discharge || 'N/A'}</td>
                    <td>
                        ${patient.can_extend ? 
                            `<button class="btn btn-sm btn-success" onclick="extendStay('${patient.id}', '${patient.name}')" style="margin-bottom: 5px;">
                                Extend 2 Days
                            </button><br>` : ''
                        }
                        <button class="btn btn-sm btn-warning" onclick="dischargePatient('${patient.id}', '${patient.name}')">
                            Discharge
                        </button>
                    </td>
                </tr>
            `).join('');
        } else {
            table.innerHTML = `
                <tr>
                    <td colspan="9" class="empty-state">
                        <i class="fas fa-user-injured"></i>
                        <p>No patients currently allocated</p>
                    </td>
                </tr>
            `;
        }
    } catch (error) {
        console.error('Error loading patients:', error);
        showError('patientsTable', 'Error loading patient data');
    }
}

// Helper functions for loading states
function showLoading(tableId, message) {
    const table = document.getElementById(tableId);
    table.innerHTML = `
        <tr>
            <td colspan="9" class="loading">
                <i class="fas fa-spinner fa-spin"></i>
                <p>${message}</p>
            </td>
        </tr>
    `;
}

function showError(tableId, message) {
    const table = document.getElementById(tableId);
    table.innerHTML = `
        <tr>
            <td colspan="9" class="empty-state">
                <i class="fas fa-exclamation-triangle"></i>
                <p>${message}</p>
            </td>
        </tr>
    `;
}

// Bed allocation function
async function allocateBed(event) {
    event.preventDefault();
    
    const patientData = {
        patient_name: document.getElementById('patientName').value,
        age: parseInt(document.getElementById('patientAge').value),
        blood_group: document.getElementById('patientBlood').value,
        admission_cause: document.getElementById('admissionCause').value,
        severity: document.getElementById('severity').value,
        health_risk: document.getElementById('healthRisk').value,
        doctor_recommendation: document.getElementById('doctorRecommendation').value
    };
    
    // Simple validation
    if (!patientData.patient_name || !patientData.age || !patientData.admission_cause) {
        alert('Please fill all required fields');
        return;
    }
    
    try {
        const response = await fetch('/api/allocate-bed', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(patientData)
        });
        
        const data = await response.json();
        
        if (data.success) {
            showNotification(`Bed allocated successfully! Patient: ${patientData.patient_name}, Bed: ${data.bed_id}, Admission: ${data.admission_date}`, 'success');
            // Reset form
            event.target.reset();
            // Refresh all data
            loadDashboardData();
            loadAvailableBeds();
            loadAllocatedPatients();
        } else {
            showNotification(data.message, 'error');
        }
    } catch (error) {
        showNotification('Error allocating bed. Please try again.', 'error');
        console.error('Allocation error:', error);
    }
}

// Extend stay function
async function extendStay(patientId, patientName) {
    if (!confirm(`Extend stay for ${patientName} by 2 days?`)) {
        return;
    }
    
    try {
        const response = await fetch('/api/extend-stay', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                patient_id: patientId
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showNotification(data.message, 'success');
            // Refresh all data
            loadDashboardData();
            loadAvailableBeds();
            loadAllocatedPatients();
        } else {
            showNotification(data.message, 'error');
        }
    } catch (error) {
        showNotification('Error extending stay. Please try again.', 'error');
        console.error('Extend stay error:', error);
    }
}

// Discharge patient function
async function dischargePatient(patientId, patientName) {
    if (!confirm(`Are you sure you want to discharge ${patientName}? This will free up their bed.`)) {
        return;
    }
    
    try {
        const response = await fetch('/api/discharge-patient', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                patient_id: patientId
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showNotification(data.message, 'success');
            // Refresh all data
            loadDashboardData();
            loadAvailableBeds();
            loadAllocatedPatients();
        } else {
            showNotification(data.message, 'error');
        }
    } catch (error) {
        showNotification('Error discharging patient. Please try again.', 'error');
        console.error('Discharge error:', error);
    }
}

// Notification function
function showNotification(message, type) {
    // Remove existing notifications
    document.querySelectorAll('.notification').forEach(notification => {
        notification.remove();
    });
    
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.innerHTML = `
        <span>${message}</span>
        <button onclick="this.parentElement.remove()">&times;</button>
    `;
    
    document.body.appendChild(notification);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        if (notification.parentElement) {
            notification.remove();
        }
    }, 5000);
}