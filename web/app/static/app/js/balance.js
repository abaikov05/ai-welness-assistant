async function runDelayedFunction() {
    // Adding a delay
    await new Promise(resolve => setTimeout(resolve, 1000));
    // Calling the delayed function
    await updateUserBalance();
}

$(document).ready(function () {
    // Intercept form submission
    $('form').submit(function (event) {
        // Prevent the default form submission
        event.preventDefault();

        // Get form data
        var formData = $(this).serialize();

        // Send AJAX request to Django server
        $.ajax({
            type: 'POST',
            url: '/balance/top-up',  // Update with your Django endpoint
            data: formData,
        });
        // Updating balance with delay   
        runDelayedFunction();
    });

});