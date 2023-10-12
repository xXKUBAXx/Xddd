$(document).ready(function() {
    var cardId = $('#classic_comp').data('card-id');

    $('button[type="submit_comp"]').on('click', function(event) {
        event.preventDefault();
        console.log('Zaliczyło!');

        const data = {
            compSelect: $('#comparisonSelect').val(),
            compQuant: $('#compQuant').val(),
            graphicSource: $('input[name="graphicSource_comp"]:checked').val(),
            overlayOption: $('input[name="overlayOption_comp"]:checked').val(),
            dateInput: $('#dateInput_comp').val(),
            publishInterval: $('#publishInterval_comp').val(),
            openai_api_key: $('#openai_api_key_comp').val(),
            faqOption: $('input[name="faqOption_comp"]:checked').val()
        };

        $.ajax({
            url: '/api/create/' + cardId + '/zaplecze_comp/',
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            data: JSON.stringify(data),
            success: function(response) {
                console.log(response);
                
            },
            error: function(error) {
                console.error('Error:', error);
            }
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
