const theme_switch = document.getElementById('theme-switch');
const body = document.getElementsByTagName('body');

// Trys to get and set prefered theme and set theme switch correctly
if (localStorage.getItem('theme') === ('auto' || null)) {
    if (window.matchMedia('(prefers-color-scheme: dark)').matches === true) {
        document.body.className = 'vh-100 dark-theme';
        theme_switch.checked = true;
        localStorage.setItem('theme', 'dark')
    }
    else {
        localStorage.setItem('theme', 'light');
    }
}
else if (localStorage.getItem('theme') === 'dark') {
    document.body.className = 'vh-100 dark-theme';
    theme_switch.checked = true;
}
else {
    localStorage.setItem('theme', 'light');
}
// Theme switch logic
document.addEventListener('DOMContentLoaded', function () {
    theme_switch.addEventListener('change', function () {
        if (theme_switch.checked) {
            document.body.className = 'vh-100 dark-theme';
            localStorage.setItem('theme', 'dark');
        } else {
            document.body.className = 'vh-100 ';
            localStorage.setItem('theme', 'light');
        }
    });
});

function updateUserBalance() {
    // Make an AJAX request to the Django view
    fetch('/get_user_balance')
        .then(response => response.json())
        .then(data => {
            // Update the user balance in the navbar
            const user_balance = document.getElementById('user-balance');
            if (user_balance) {
                user_balance.innerText = `${parseFloat(data.user_balance).toFixed(2)}$`;
            }
        })
        .catch(error => console.error('Error updating user balance:', error));
}
updateUserBalance();