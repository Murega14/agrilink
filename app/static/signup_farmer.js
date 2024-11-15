function validateEmailInput() {
    const emailInput = document.getElementById('emailInput').value;
    const feedbackElement = document.getElementById('emailFeedback');
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

    if (emailRegex.test(emailInput)) {
        feedbackElement.textContent = "";
    } else {
        feedbackElement.textContent = "Please enter a valid email"
    }
}

function matchPassword() {
    var firstPassword = document.getElementById('firstPassword').value;
    var secondPassword = document.getElementById('secondPassword').value;
    var messageElement = document.getElementById('passwordMatchMessage');

    if (firstPassword === secondPassword) {
        messageElement.classList.add('hidden');
        messageElement.classList.remove('text-red-500');
        messageElement.classList.add('text-green-500');
        messageElement.textContent = "Passwords match.";
    } else {
        messageElement.classList.remove('hidden');
        messageElement.classList.remove('text-green-500');
        messageElement.classList.add('text-red-500');
        messageElement.textContent = "Passwords do not match.";
    }
}
