// HOSTELLO - Hostel Management System JavaScript

// Registration Form Handler
document.addEventListener('DOMContentLoaded', function() {
    const registrationForm = document.getElementById('registrationForm');
    const loginForm = document.getElementById('loginForm');

    // Registration form submission
    if (registrationForm) {
        registrationForm.addEventListener('submit', function(e) {
            e.preventDefault();

            // Get form data
            const formData = new FormData(registrationForm);
            const studentData = {};

            for (let [key, value] of formData.entries()) {
                studentData[key] = value;
            }

            // Validate required fields
            if (validateRegistrationForm(studentData)) {
                // Store in localStorage (temporary - will be replaced with Django backend)
                localStorage.setItem('studentData_' + studentData.admissionNo, JSON.stringify(studentData));

                alert('Registration successful! Your application has been submitted.');
                console.log('Student registered:', studentData);

                // Redirect to login page
                window.location.href = 'login.html';
            }
        });
    }

    // Login form submission
    if (loginForm) {
        loginForm.addEventListener('submit', function(e) {
            e.preventDefault();

            const email = document.getElementById('loginEmail').value;
            const password = document.getElementById('loginPassword').value;

            // Validate login (temporary - will be replaced with Django backend)
            if (validateLogin(email, password)) {
                alert('Login successful! Welcome to HOSTELLO.');
                console.log('User logged in:', email);

                // Redirect to dashboard (to be created)
                // window.location.href = 'dashboard.html';
            } else {
                alert('Invalid email or password. Please try again.');
            }
        });
    }
});

// Validation Functions
function validateRegistrationForm(data) {
    // Check if all required fields are filled
    const requiredFields = ['admissionNo', 'fullName', 'email', 'password', 'guardianName', 
                           'guardianEmail', 'address', 'mobile', 'dob', 'city', 'program', 'discipline'];

    for (let field of requiredFields) {
        if (!data[field] || data[field].trim() === '') {
            alert(`Please fill in the ${field.replace(/([A-Z])/g, ' $1').toLowerCase()} field.`);
            return false;
        }
    }

    // Check if terms are accepted
    if (!data.terms) {
        alert('Please accept the terms and conditions.');
        return false;
    }

    // Validate email format
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(data.email)) {
        alert('Please enter a valid email address.');
        return false;
    }

    if (!emailRegex.test(data.guardianEmail)) {
        alert('Please enter a valid guardian email address.');
        return false;
    }

    // Validate mobile number (basic check)
    const mobileRegex = /^[0-9]{10}$/;
    if (!mobileRegex.test(data.mobile.replace(/[^0-9]/g, ''))) {
        alert('Please enter a valid 10-digit mobile number.');
        return false;
    }

    // Validate password strength
    if (data.password.length < 6) {
        alert('Password must be at least 6 characters long.');
        return false;
    }

    return true;
}

function validateLogin(email, password) {
    // This is temporary validation - will be replaced with Django backend
    // For now, check if user exists in localStorage
    const students = Object.keys(localStorage)
        .filter(key => key.startsWith('studentData_'))
        .map(key => JSON.parse(localStorage.getItem(key)));

    const user = students.find(student => student.email === email && student.password === password);

    if (user) {
        // Store logged in user data
        sessionStorage.setItem('loggedInUser', JSON.stringify(user));
        return true;
    }

    return false;
}

// Forgot Password Function
function forgotPassword() {
    const email = prompt('Please enter your registered email address:');
    if (email) {
        // This will be implemented with Django backend
        alert('Password reset link has been sent to your email address.');
        console.log('Password reset requested for:', email);
    }
}

// Form validation helpers
function validateEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

function validateMobile(mobile) {
    const re = /^[0-9]{10}$/;
    return re.test(mobile.replace(/[^0-9]/g, ''));
}

// Real-time validation
document.addEventListener('DOMContentLoaded', function() {
    // Email validation
    const emailInputs = document.querySelectorAll('input[type="email"]');
    emailInputs.forEach(input => {
        input.addEventListener('blur', function() {
            if (this.value && !validateEmail(this.value)) {
                this.style.borderColor = '#e74c3c';
                this.setAttribute('title', 'Please enter a valid email address');
            } else {
                this.style.borderColor = '#e1e5e9';
                this.removeAttribute('title');
            }
        });
    });

    // Mobile validation
    const mobileInput = document.getElementById('mobile');
    if (mobileInput) {
        mobileInput.addEventListener('blur', function() {
            if (this.value && !validateMobile(this.value)) {
                this.style.borderColor = '#e74c3c';
                this.setAttribute('title', 'Please enter a valid 10-digit mobile number');
            } else {
                this.style.borderColor = '#e1e5e9';
                this.removeAttribute('title');
            }
        });
    }
});