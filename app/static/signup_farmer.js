function showError(message) {
    const errorContainer = document.getElementById('errorContainer');
    const errorMessage = document.getElementById('errorMessage');
    errorContainer.classList.remove('hidden');
    errorMessage.textContent = message;
}

// Hide error message
function hideError() {
    const errorContainer = document.getElementById('errorContainer');
    errorContainer.classList.add('hidden');
}

// Validation functions
function validateField(fieldId, errorMessage) {
    const field = document.getElementById(fieldId);
    const errorElement = document.getElementById(`${fieldId}_error`);
    
    if (!field.checkValidity()) {
        errorElement.textContent = errorMessage;
        errorElement.classList.remove('hidden');
        return false;
    } else {
        errorElement.classList.add('hidden');
        return true;
    }
}

function validatePhone(input) {
    const errorElement = document.getElementById('phone_number_error');
    const phoneRegex = /^[0-9]{10}$/;
    
    if (!phoneRegex.test(input.value)) {
        errorElement.textContent = 'Phone number must be exactly 10 digits';
        errorElement.classList.remove('hidden');
        return false;
    } else {
        errorElement.classList.add('hidden');
        return true;
    }
}

function validateEmail(input) {
    const errorElement = document.getElementById('email_error');
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    
    if (!emailRegex.test(input.value)) {
        errorElement.textContent = 'Please enter a valid email address';
        errorElement.classList.remove('hidden');
        return true;
    } else {
        errorElement.classList.add('hidden');
        return true;
    }
}

// Password strength checker
function checkPasswordStrength(input) {
    const password = input.value;
    const checks = {
        length: password.length >= 8,
        uppercase: /[A-Z]/.test(password),
        lowercase: /[a-z]/.test(password),
        number: /[0-9]/.test(password),
        special: /[!@#$%^&*(),.?":{}|<>]/.test(password)
    };
    
    // Update requirement checks
    Object.keys(checks).forEach(check => {
        const element = document.getElementById(`${check}_check`);
        element.className = checks[check] ? 'text-green-600' : 'text-gray-500';
        element.textContent = `${checks[check] ? '✓' : '✗'} ${element.textContent.slice(2)}`;
    });
    
    // Calculate strength
    const strength = Object.values(checks).filter(Boolean).length;
    const indicator = document.getElementById('strength_indicator');
    const strengthText = document.getElementById('strength_text');
    
    // Update strength indicator
    const colors = ['bg-red-500', 'bg-orange-500', 'bg-yellow-500', 'bg-blue-500', 'bg-green-500'];
    const texts = ['Very Weak', 'Weak', 'Medium', 'Strong', 'Very Strong'];
    
    indicator.className = `h-2 rounded-full transition-all duration-300 ${colors[strength-1] || ''}`;
    indicator.style.width = `${(strength/5) * 100}%`;
    strengthText.textContent = `Password strength: ${texts[strength-1] || 'None'}`;
    
    return strength >= 4;
}

async function handleSubmit(event) {
    event.preventDefault();
    hideError();
    
    const formData = {
        first_name: document.getElementById('first_name').value,
        last_name: document.getElementById('last_name').value,
        phone_number: document.getElementById('phone_number').value,
        email: document.getElementById('email').value,
        password: document.getElementById('password').value
    };
    
    // Password strength validation
    if (!checkPasswordStrength(document.getElementById('password'))) {
        showError('Please ensure your password is strong enough.');
        return;
    }
    
    const submitButton = document.getElementById('submitButton');
    const spinner = document.getElementById('spinner');
    spinner.classList.remove('hidden');
    
    try {
        const response = await fetch('/signup/farmer', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(formData)
        });
        
        if (!response.ok) {
            const data = await response.json();
            showError(data.message || 'Registration failed. Please try again.');
        } else {
            window.location.href = '/farmer/home';
        }
    } catch (error) {
        showError('Network error. Please try again later.');
    } finally {
        spinner.classList.add('hidden');
    }
}