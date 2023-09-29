//function to get session token
function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
//functions performed after document load
$(document).ready(function() {
    //Handle create icon click 
    $('i#create').on('click', function(event) {
        var cardId = $(this).closest('.card').data('card-id');
        window.location.href = '/'+cardId;
    });
    //Write icon onclick action
    $('i#write').on('click', function(event) {
        var cardId = $(this).closest('.card').data('card-id');
        window.location.href = '/'+cardId+'/update/';
    });
    // Handle delete icon click
    $('i#delete').on('click', function(event) {
        event.preventDefault();
        
        var cardId = $(this).closest('.card').data('card-id');
        var deleteUrl = '/api/' + cardId + '/';

        var csrftoken = getCookie('csrftoken');

        $.ajax({
            type: 'DELETE',
            url: deleteUrl,
            headers: {
                'X-CSRFToken': csrftoken
            },
            success: function(response) {
                alert(response.res);
                window.location.href = '/';
            },
            error: function(error) {
                alert('Error deleting: ' + JSON.stringify(error));
            }
        });
    });

    //zaplecze card onclick toggle
    $('.card-body').on('click', function() {
        var table = $(this).parent().find('.additional-attributes');
        table.toggle();
    });

    $(document).ready(function() {
        $('#tsvInput').on('paste', function() {
            setTimeout(() => {
                const tsvData = $(this).val();
                if (tsvData) {
                    createTableFromTSV(tsvData);
                    $(this).hide();
                    $('#resetButton').show();
    
                    $('.card').addClass('expanded-card');
                }
            }, 50);
        });
    
        $('#resetButton').on('click', function() {
            $('.table-container').empty();
            $('#tsvInput').val('').show();
            $(this).hide();
    
            $('.card').removeClass('expanded-card');
        });
    });
    
    function createTableFromTSV(tsvData) {
        const rows = tsvData.trim().split("\n");
        let tableHtml = '<table class="table table-bordered scrollable-table">';
    
        rows.forEach((row, index) => {
            const cells = row.split("\t");
            if (index === 0) {
                tableHtml += '<thead><tr>';
                cells.forEach(cell => {
                    tableHtml += `<th>${cell}</th>`;
                });
                tableHtml += '</tr></thead><tbody>';
            } else {
                tableHtml += '<tr>';
                cells.forEach(cell => {
                    tableHtml += `<td contenteditable="true">${cell}</td>`;
                });
                tableHtml += '</tr>';
            }
        });
    
        tableHtml += '</tbody></table>';
        $('.table-container').html(tableHtml).addClass('scrollable-table').show();
    }
});