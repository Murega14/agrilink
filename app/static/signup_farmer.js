// Show and hide error messages
function showError(message) {
    const errorContainer = document.getElementById('errorContainer');
    const errorMessage = document.getElementById('errorMessage');
    errorContainer.classList.remove('hidden');
    errorMessage.textContent = message;
}

function hideError() {
    const errorContainer = document.getElementById('errorContainer');
    errorContainer.classList.add('hidden');
}

// Field validation function
function validateField(fieldId, errorMsg) {
    const field = document.getElementById(fieldId);
    const errorElement = document.getElementById(`${fieldId}_error`);
    const pattern = new RegExp(field.getAttribute('pattern'));

    if (pattern && !pattern.test(field.value)) {
        errorElement.textContent = errorMsg;
        errorElement.classList.remove('hidden');
    } else {
        errorElement.classList.add('hidden');
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

    Object.keys(checks).forEach(check => {
        const element = document.getElementById(`${check}_check`);
        element.className = checks[check] ? 'text-green-600' : 'text-gray-500';
        element.textContent = `${checks[check] ? '✓' : '✗'} ${element.textContent.slice(2)}`;
    });

    const strength = Object.values(checks).filter(Boolean).length;
    const indicator = document.getElementById('strength_indicator');
    const strengthText = document.getElementById('strength_text');

    const colors = ['bg-red-500', 'bg-orange-500', 'bg-yellow-500', 'bg-blue-500', 'bg-green-500'];
    const texts = ['Very Weak', 'Weak', 'Medium', 'Strong', 'Very Strong'];

    indicator.className = `h-2 rounded-full transition-all duration-300 ${colors[strength-1] || ''}`;
    indicator.style.width = `${(strength / 5) * 100}%`;
    strengthText.textContent = `Password strength: ${texts[strength - 1] || 'None'}`;

    return strength >= 4;
}

// Form submission handling
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

    // Spinner animation
    const spinner = document.getElementById('spinner');
    spinner.classList.remove('hidden');

    // Password strength check
    if (!checkPasswordStrength(document.getElementById('password'))) {
        showError("Password is not strong enough.");
        spinner.classList.add('hidden');
        return;
    }

    try {
        // API request (mocked)
        const response = await fetch("/signup_farmer", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(formData)
        });

        if (!response.ok) {
            throw new Error("Failed to submit the form.");
        }

        alert("Account created successfully!");
    } catch (error) {
        showError("There was an error submitting the form. Please try again.");
    } finally {
        spinner.classList.add('hidden');
    }
}
