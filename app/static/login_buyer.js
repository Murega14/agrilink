document.getElementById('loginForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const identifier = document.getElementById('identifier').value;
    const password = document.getElementById('password').value;
    const errorAlert = document.getElementById('errorAlert');
    const errorMessage = document.getElementById('errorMessage');

    try {
        const response = await fetch('/login/buyer', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                identifier,
                password
            })
        });

        const data = await response.json();

        if (response.ok) {
            window.location.href = '/dashboard'; // Redirect to dashboard on success
        } else {
            errorMessage.textContent = data.error || 'Login failed. Please try again.';
            errorAlert.classList.remove('hidden');
        }
    } catch (error) {
        errorMessage.textContent = 'An error occurred. Please try again later.';
        errorAlert.classList.remove('hidden');
    }
});