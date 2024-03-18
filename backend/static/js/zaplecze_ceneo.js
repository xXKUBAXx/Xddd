document.addEventListener('DOMContentLoaded', (event) => {
    const dateInputCeneo = document.getElementById('dateInput_ceneo');
    const today = new Date();
    const day = String(today.getDate()).padStart(2, '0');
    const month = String(today.getMonth() + 1).padStart(2, '0');
    const year = today.getFullYear();
    dateInputCeneo.value = `${year}-${month}-${day}`;
});

$(document).ready(function () {
    const today = new Date();
    const day = String(today.getDate()).padStart(2, '0');
    const month = String(today.getMonth() + 1).padStart(2, '0');
    const year = today.getFullYear();
    $('#dateInput_ceneo').val(`${year}-${month}-${day}`);

    var cardId = $('#submit_ceneo').data('card-id');

    $('#submit_ceneo').on('click', function (event) {
        event.preventDefault();

        $(this).hide();

        $(this).after('<p>Zlecenie przyjęte.<br>Możesz wyłączyć kartę.</p>');

        const data = {
            ceneoFile: $('#ceneoDataDropdown').val(),
            ceneoQuant: $('#ceneoQuant').val(),
            dateInput: $('#dateInput_ceneo').val(),
            publishInterval: $('#publishInterval_ceneo').val(),
            openai_api_key: $('#openai_api_key_ceneo').val(),
        };

        $.ajax({
            url: '/api/create/' + cardId + '/zaplecze_ceneo/',
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
    });

    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = $.trim(cookies[i]);
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
});
