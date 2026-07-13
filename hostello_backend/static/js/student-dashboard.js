// HOSTELLO - Student Dashboard JavaScript

// Global variables
let currentUser = null;
let notifications = [];
let requests = [];
let attendanceData = [];
let paymentHistory = [];

// Initialize dashboard when page loads
document.addEventListener('DOMContentLoaded', function() {
    // Load user data from session storage
    currentUser = JSON.parse(sessionStorage.getItem('loggedInUser')) || {};

    // Initialize dashboard
    loadUserProfile();
    loadNotifications();
    loadRequests();
    loadAttendanceData();
    loadPaymentHistory();

    // Set default active section
    showSection('profile');
});

// Navigation functions
function showSection(sectionId) {
    // Hide all sections
    document.querySelectorAll('.content-section').forEach(section => {
        section.classList.remove('active');
    });

    // Remove active class from all menu items
    document.querySelectorAll('.menu-item').forEach(item => {
        item.classList.remove('active');
    });

    // Show selected section
    document.getElementById(sectionId).classList.add('active');

    // Add active class to corresponding menu item
    event.target.closest('.menu-item').classList.add('active');
}

function logout() {
    if (confirm('Are you sure you want to logout?')) {
        sessionStorage.clear();
        localStorage.clear();
        window.location.href = 'login.html';
    }
}

// Profile functions
function loadUserProfile() {
    if (currentUser) {
        // document.getElementById('studentName').textContent = currentUser.fullName || 'Student';
        // document.getElementById('profileAdmissionNo').textContent = currentUser.admissionNo || '-';
        // document.getElementById('profileFullName').textContent = currentUser.fullName || '-';
        // document.getElementById('profileEmail').textContent = currentUser.email || '-';
        // document.getElementById('profileGuardianName').textContent = currentUser.guardianName || '-';
        // document.getElementById('profileGuardianEmail').textContent = currentUser.guardianEmail || '-';
        // document.getElementById('profileAddress').textContent = currentUser.address || '-';
        // document.getElementById('profileMobile').textContent = currentUser.mobile || '-';
        // document.getElementById('profileDOB').textContent = currentUser.dob || '-';
        // document.getElementById('profileCity').textContent = currentUser.city || '-';
        // document.getElementById('profileProgram').textContent = currentUser.program || '-';
        // document.getElementById('profileDiscipline').textContent = currentUser.discipline || '-';
    }
}

function editProfile() {
    alert('Edit profile functionality will be implemented with Django backend integration.');
}

function showProfile() {
    showSection('profile');
}

// Notification functions
function loadNotifications() {
    // Sample notifications (will be loaded from Django backend)
    notifications = [
        {
            id: 1,
            title: 'Attendance Alert',
            content: 'You were marked absent on 03/07/2025 for room attendance.',
            date: '2025-07-03',
            type: 'attendance',
            read: false
        },
        {
            id: 2,
            title: 'Fee Reminder',
            content: 'Your monthly fee payment is due on 15th July 2025.',
            date: '2025-07-10',
            type: 'fee',
            read: false
        },
        {
            id: 3,
            title: 'Mess Closure Notice',
            content: 'Mess will be closed on 15th July for cleaning and maintenance.',
            date: '2025-07-12',
            type: 'general',
            read: true
        }
    ];

    updateNotificationCount();
    loadNotificationDropdown();
    loadAllNotifications();
}

function updateNotificationCount() {
    const unreadCount = notifications.filter(n => !n.read).length;
    document.getElementById('notificationCount').textContent = unreadCount;
    document.getElementById('notificationCount').style.display = unreadCount > 0 ? 'flex' : 'none';
}

function toggleNotifications() {
    const dropdown = document.getElementById('notificationDropdown');
    dropdown.style.display = dropdown.style.display === 'block' ? 'none' : 'block';
}

function loadNotificationDropdown() {
    const notificationList = document.getElementById('notificationList');
    const recentNotifications = notifications.slice(0, 3);

    notificationList.innerHTML = recentNotifications.map(notification => `
        <div class="notification-item ${notification.read ? 'read' : 'unread'}" onclick="markAsRead(${notification.id})">
            <div class="notification-title">${notification.title}</div>
            <div class="notification-content">${notification.content}</div>
            <div class="notification-date">${formatDate(notification.date)}</div>
        </div>
    `).join('');
}

function loadAllNotifications() {
    const allNotificationsList = document.getElementById('allNotificationsList');

    allNotificationsList.innerHTML = notifications.map(notification => `
        <div class="notification-item">
            <div class="notification-header">
                <div class="notification-title">${notification.title}</div>
                <div class="notification-date">${formatDate(notification.date)}</div>
            </div>
            <div class="notification-content">${notification.content}</div>
        </div>
    `).join('');
}

function viewAllNotifications() {
    showSection('notifications');
    document.getElementById('notificationDropdown').style.display = 'none';
}

function markAsRead(notificationId) {
    const notification = notifications.find(n => n.id === notificationId);
    if (notification) {
        notification.read = true;
        updateNotificationCount();
        loadNotificationDropdown();
    }
}

// Attendance functions
function loadAttendanceData() {
    // Sample attendance data (will be loaded from Django backend)
    attendanceData = [
        { date: '2025-07-01', roomAttendance: 'present', messAttendance: 'present' },
        { date: '2025-07-02', roomAttendance: 'present', messAttendance: 'absent' },
        { date: '2025-07-03', roomAttendance: 'absent', messAttendance: 'present' },
        // More attendance data...
    ];

    updateAttendanceStats();
    generateAttendanceCalendar();
    generateAttendanceList();
}

function updateAttendanceStats() {
    const roomPresent = attendanceData.filter(a => a.roomAttendance === 'present').length;
    const roomAbsent = attendanceData.filter(a => a.roomAttendance === 'absent').length;
    const messPresent = attendanceData.filter(a => a.messAttendance === 'present').length;
    const messAbsent = attendanceData.filter(a => a.messAttendance === 'absent').length;

    document.getElementById('roomPresent').textContent = roomPresent;
    document.getElementById('roomAbsent').textContent = roomAbsent;
    document.getElementById('messPresent').textContent = messPresent;
    document.getElementById('messAbsent').textContent = messAbsent;
}

function generateAttendanceCalendar() {
    const calendar = document.getElementById('attendanceCalendar');
    // This will be implemented with a proper calendar library or custom calendar
    calendar.innerHTML = `
        <div class="calendar-placeholder">
            <p>Calendar view will be implemented with proper calendar component</p>
            <p>Shows monthly view with color-coded attendance status</p>
        </div>
    `;
}

function generateAttendanceList() {
    const list = document.getElementById('attendanceList');
    list.innerHTML = `
        <div class="attendance-table">
            <table>
                <thead>
                    <tr>
                        <th>Date</th>
                        <th>Room Attendance</th>
                        <th>Mess Attendance</th>
                    </tr>
                </thead>
                <tbody>
                    ${attendanceData.map(record => `
                        <tr>
                            <td>${formatDate(record.date)}</td>
                            <td class="status-${record.roomAttendance}">${record.roomAttendance}</td>
                            <td class="status-${record.messAttendance}">${record.messAttendance}</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        </div>
    `;
}

function showAttendanceView(viewType) {
    document.querySelectorAll('.toggle-btn').forEach(btn => btn.classList.remove('active'));
    event.target.classList.add('active');

    if (viewType === 'calendar') {
        document.getElementById('attendanceCalendar').style.display = 'block';
        document.getElementById('attendanceList').style.display = 'none';
    } else {
        document.getElementById('attendanceCalendar').style.display = 'none';
        document.getElementById('attendanceList').style.display = 'block';
    }
}

// Request functions
function loadRequests() {
    // Sample request data (will be loaded from Django backend)
    requests = [
        {
            id: 1,
            type: 'complaint',
            title: 'AC not working in room 201',
            description: 'The air conditioning unit in room 201 has been malfunctioning for 2 days.',
            status: 'pending',
            date: '2025-07-10',
            comments: ''
        },
        {
            id: 2,
            type: 'cleaning',
            title: 'Room cleaning request',
            description: 'Request for deep cleaning of room 201.',
            status: 'approved',
            date: '2025-07-08',
            comments: 'Scheduled for tomorrow morning'
        },
        {
            id: 3,
            type: 'leave',
            title: 'Home visit',
            description: 'Going home for family function',
            fromDate: '2025-07-15',
            toDate: '2025-07-17',
            status: 'approved',
            date: '2025-07-05',
            comments: 'Approved by warden'
        }
    ];

    displayRequests();
}

function displayRequests() {
    const requestsList = document.getElementById('requestsList');

    requestsList.innerHTML = requests.map(request => `
        <div class="request-item">
            <div class="request-header">
                <div class="request-type">
                    <i class="fas fa-${getRequestIcon(request.type)}"></i>
                    ${request.title}
                </div>
                <div class="request-status status-${request.status}">${request.status}</div>
            </div>
            <div class="request-content">
                <p>${request.description}</p>
                ${request.fromDate ? `<p><strong>From:</strong> ${formatDate(request.fromDate)} <strong>To:</strong> ${formatDate(request.toDate)}</p>` : ''}
                <p><strong>Submitted:</strong> ${formatDate(request.date)}</p>
                ${request.comments ? `<p><strong>Comments:</strong> ${request.comments}</p>` : ''}
            </div>
        </div>
    `).join('');
}

function getRequestIcon(type) {
    switch (type) {
        case 'complaint': return 'tools';
        case 'cleaning': return 'broom';
        case 'leave': return 'calendar-alt';
        default: return 'clipboard';
    }
}

function showRequestForm(requestType) {
    const modal = document.getElementById('requestFormModal');
    const title = document.getElementById('requestFormTitle');
    const formFields = document.getElementById('requestFormFields');

    document.getElementById('requestType').value = requestType;

    // Set title and generate form fields based on request type
    switch (requestType) {
        case 'complaint':
            title.innerHTML = '<i class="fas fa-tools"></i> New Complaint';
            formFields.innerHTML = `
                <div class="form-group">
                    <label for="complaintTitle">Complaint Title *</label>
                    <input type="text" id="complaintTitle" name="title" required>
                </div>
                <div class="form-group">
                    <label for="complaintDescription">Description *</label>
                    <textarea id="complaintDescription" name="description" required></textarea>
                </div>
                <div class="form-group">
                    <label for="urgency">Urgency Level</label>
                    <select id="urgency" name="urgency">
                        <option value="low">Low</option>
                        <option value="medium">Medium</option>
                        <option value="high">High</option>
                    </select>
                </div>
            `;
            break;
        case 'cleaning':
            title.innerHTML = '<i class="fas fa-broom"></i> Room Cleaning Request';
            formFields.innerHTML = `
                <div class="form-group">
                    <label for="cleaningType">Cleaning Type *</label>
                    <select id="cleaningType" name="cleaningType" required>
                        <option value="">Select cleaning type</option>
                        <option value="regular">Regular Cleaning</option>
                        <option value="deep">Deep Cleaning</option>
                        <option value="maintenance">Maintenance Cleaning</option>
                    </select>
                </div>
                <div class="form-group">
                    <label for="preferredDate">Preferred Date</label>
                    <input type="date" id="preferredDate" name="preferredDate">
                </div>
                <div class="form-group">
                    <label for="cleaningNotes">Additional Notes</label>
                    <textarea id="cleaningNotes" name="notes"></textarea>
                </div>
            `;
            break;
        case 'leave':
            title.innerHTML = '<i class="fas fa-calendar-alt"></i> Leave Request';
            formFields.innerHTML = `
                <div class="form-group">
                    <label for="leaveFrom">From Date *</label>
                    <input type="date" id="leaveFrom" name="fromDate" required>
                </div>
                <div class="form-group">
                    <label for="leaveTo">To Date *</label>
                    <input type="date" id="leaveTo" name="toDate" required>
                </div>
                <div class="form-group">
                    <label for="leaveReason">Reason for Leave *</label>
                    <textarea id="leaveReason" name="reason" required></textarea>
                </div>
                <div class="form-group">
                    <label for="emergencyContact">Emergency Contact</label>
                    <input type="text" id="emergencyContact" name="emergencyContact">
                </div>
            `;
            break;
    }

    modal.style.display = 'block';
}

// Request form submission
document.addEventListener('DOMContentLoaded', function() {
    const requestForm = document.getElementById('requestForm');
    if (requestForm) {
        requestForm.addEventListener('submit', function(e) {
            e.preventDefault();

            const formData = new FormData(requestForm);
            const requestData = {};

            for (let [key, value] of formData.entries()) {
                requestData[key] = value;
            }

            // Add request to list (temporary - will be sent to Django backend)
            const newRequest = {
                id: requests.length + 1,
                type: requestData.requestType,
                title: requestData.title || `${requestData.requestType} request`,
                description: requestData.description || requestData.reason || requestData.notes || '',
                status: 'pending',
                date: new Date().toISOString().split('T')[0],
                fromDate: requestData.fromDate || null,
                toDate: requestData.toDate || null,
                comments: ''
            };

            requests.unshift(newRequest);
            displayRequests();

            alert('Request submitted successfully!');
            closeModal('requestFormModal');
        });
    }
});

// Fee functions
function loadPaymentHistory() {
    // Sample payment history (will be loaded from Django backend)
    paymentHistory = [
        { date: '2025-06-15', month: 'June 2025', amount: 6500, status: 'paid', transactionId: 'TXN123456' },
        { date: '2025-05-15', month: 'May 2025', amount: 6500, status: 'paid', transactionId: 'TXN123455' },
        { date: '2025-04-15', month: 'April 2025', amount: 6200, status: 'paid', transactionId: 'TXN123454' }
    ];

    displayPaymentHistory();
}

function displayPaymentHistory() {
    const historyTable = document.getElementById('paymentHistoryTable');

    historyTable.innerHTML = paymentHistory.map(payment => `
        <tr>
            <td>${formatDate(payment.date)}</td>
            <td>${payment.month}</td>
            <td>₹${payment.amount}</td>
            <td class="status-${payment.status}">${payment.status}</td>
            <td>
                <button class="download-btn" onclick="downloadReceipt('${payment.transactionId}')">
                    <i class="fas fa-download"></i> Download
                </button>
            </td>
        </tr>
    `).join('');
}

function payFees() {
    document.getElementById('paymentModal').style.display = 'block';
}

function processPayment() {
    // This will integrate with payment gateway (Razorpay/Stripe)
    alert('Payment gateway integration will be implemented with Django backend.');
    closeModal('paymentModal');
}

function downloadReceipt(transactionId) {
    alert(`Downloading receipt for transaction: ${transactionId}`);
    // This will generate and download PDF receipt
}

// Hostel Info functions
function showHostelInfo() {
    document.getElementById('hostelInfoModal').style.display = 'block';
}

// Modal functions
function closeModal(modalId) {
    document.getElementById(modalId).style.display = 'none';
}

// Close modal when clicking outside
window.onclick = function(event) {
    const modals = document.querySelectorAll('.modal');
    modals.forEach(modal => {
        if (event.target === modal) {
            modal.style.display = 'none';
        }
    });

    // Close notification dropdown when clicking outside
    if (!event.target.closest('.notification-bell') && !event.target.closest('.notification-dropdown')) {
        document.getElementById('notificationDropdown').style.display = 'none';
    }
};

// Utility functions
function formatDate(dateString) {
    const options = { year: 'numeric', month: 'short', day: 'numeric' };
    return new Date(dateString).toLocaleDateString('en-US', options);
}

// Filter functions
function filterRequests() {
    const typeFilter = document.getElementById('requestTypeFilter').value;
    const statusFilter = document.getElementById('requestStatusFilter').value;

    let filteredRequests = requests;

    if (typeFilter !== 'all') {
        filteredRequests = filteredRequests.filter(r => r.type === typeFilter);
    }

    if (statusFilter !== 'all') {
        filteredRequests = filteredRequests.filter(r => r.status === statusFilter);
    }

    // Update display with filtered requests
    const requestsList = document.getElementById('requestsList');
    requestsList.innerHTML = filteredRequests.map(request => `
        <div class="request-item">
            <div class="request-header">
                <div class="request-type">
                    <i class="fas fa-${getRequestIcon(request.type)}"></i>
                    ${request.title}
                </div>
                <div class="request-status status-${request.status}">${request.status}</div>
            </div>
            <div class="request-content">
                <p>${request.description}</p>
                ${request.fromDate ? `<p><strong>From:</strong> ${formatDate(request.fromDate)} <strong>To:</strong> ${formatDate(request.toDate)}</p>` : ''}
                <p><strong>Submitted:</strong> ${formatDate(request.date)}</p>
                ${request.comments ? `<p><strong>Comments:</strong> ${request.comments}</p>` : ''}
            </div>
        </div>
    `).join('');
}

// Add event listeners for filters
document.addEventListener('DOMContentLoaded', function() {
    const requestTypeFilter = document.getElementById('requestTypeFilter');
    const requestStatusFilter = document.getElementById('requestStatusFilter');

    if (requestTypeFilter) {
        requestTypeFilter.addEventListener('change', filterRequests);
    }

    if (requestStatusFilter) {
        requestStatusFilter.addEventListener('change', filterRequests);
    }
});

// Update login script to redirect to dashboard
function updateLoginRedirect() {
    // This should be added to the existing script.js file
    // After successful login, redirect to student-dashboard.html instead
    // window.location.href = 'student-dashboard.html';
}