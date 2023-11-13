$(document).ready(function () {
    $('button[type="refresh_visibility"]').on('click', function (event) {
        event.preventDefault();
		console.log('Baza wirusów programu Avast została zaktualizowana.');

        $('#refresh_visibility').hide();
        
        const data = {
			semstorm_key: $('#semstorm_api_key').val()
		};

        $.ajax({
			url: '/api/visibility/',
			method: 'POST',
			headers: {
				'Content-Type': 'application/json',
				'X-CSRFToken': getCookie('csrftoken'),
			},
            data: JSON.stringify(data),
			success: function (response) {
				console.log(response);
			},
			error: function (error) {
				console.error('Error:', error);
			},
		});
    }
)});