document.addEventListener('DOMContentLoaded', function() {
    const isResetPasswordPage = window.location.pathname.includes('reset-password');
    const isConfirmEmailPage = window.location.pathname.includes('confirm-email');
    
    if (window.history.replaceState) {
        window.history.replaceState(null, null, window.location.href);
    }

    if (isResetPasswordPage || isConfirmEmailPage) {
        const infoMessage = document.querySelector('.info-message');
        
        if (infoMessage) {
            if (isResetPasswordPage)
                startCountdown(infoMessage, "reset token", "Token");
            else if (isConfirmEmailPage)
                startCountdown(infoMessage, "confirmation code", "Code");
        }
    }
    
    hideMessages();

    const forms = document.querySelectorAll('form');

    forms.forEach(form => {
        form.addEventListener('submit', handleFormSubmit);
    });

    window.addEventListener('pageshow', function(event) {
        if (event.persisted) {
            formSubmitting = false;
            const submitButtons = document.querySelectorAll('button[type="submit"]');
            
            submitButtons.forEach(button => {
                button.disabled = false;
            });
        }
    });
});

function hideMessages() {
    setTimeout(function() {
        const messages = document.querySelectorAll('.error-message, .success-message, .info-message');

        messages.forEach(message => {
            message.style.transition = 'opacity 0.5s ease-out';
            message.style.opacity = '0';
            
            setTimeout(function() {
                message.remove();
            }, 500);
        });
    }, 5000);
}

function startCountdown(infoMessage, long_prefix, short_prefix) {
    const timeRegex = /(\d+) minutes and (\d+) seconds/;
    const match = infoMessage.textContent.match(timeRegex);

    if (!match)
        return;

    let minutes = parseInt(match[1]);
    let seconds = parseInt(match[2]);
    let totalSeconds = minutes * 60 + seconds;

    const countdownInterval = setInterval(() => {
        totalSeconds--;

        if (totalSeconds <= 0) {
            clearInterval(countdownInterval);
            const successMessage = document.querySelector('.success-message');
            
            if (!successMessage) {
                const errorMessage = document.createElement('div');

                errorMessage.className = 'error-message';
                errorMessage.textContent = `Your ${long_prefix} has expired. Please return to the registration page.`;

                document.querySelector('.form-value').appendChild(errorMessage);
            }
            
            hideMessages();
            return;
        }

        minutes = Math.floor(totalSeconds / 60);
        seconds = totalSeconds % 60;

        infoMessage.className = 'info-message';
        infoMessage.textContent = `${short_prefix} expires in ${minutes} minutes and ${seconds} seconds`;
    }, 1000);
}

function togglePasswordVisibility(inputId) {
    const input = document.getElementById(inputId);
    const icon = input.parentElement.querySelector('.toggle-password');

    if (input.value) {
        if (input.type === 'password') {
            input.type = 'text';
            icon.setAttribute('name', 'eye-off-outline');
        } else {
            input.type = 'password';
            icon.setAttribute('name', 'eye-outline');
        }
    }
}

let formSubmitting = false;

function handleFormSubmit(event) {
    if (formSubmitting) {
        event.preventDefault();
        return;
    }

    const submitButton = event.target.querySelector('button[type="submit"]');

    if (submitButton) {
        submitButton.disabled = true;
        formSubmitting = true;
    }
}
