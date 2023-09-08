async function make_request(url, text1, text2) {
    var csrftoken = getCookie('csrftoken');
    // request to create zaplecze domain
    $(".spinner-text").text(text1);
    
    try {
        const response = await $.ajax({
            type: 'POST',
            url: url,
            headers: {
                'X-CSRFToken': csrftoken
            }
        });

        document.querySelector(".spinner-container").insertAdjacentHTML("beforebegin", "<li>&#10003;" + text1 + "</li>");
        
        if (text2 !== "") {
            $(".spinner-text").text(text2);
        } else {
            $(".spinner-container").remove();
        }

        return response;
    } catch (error) {
        document.querySelector(".spinner-container").insertAdjacentHTML("beforebegin", "<li>&#10007;" + text1 + "</li>");
        $(".spinner-container").remove();
        console.error(error);
        throw error; // Rethrow the error to handle it outside the function if needed.
    }
}

$(document).ready(function() {

    $('#start').on('click', async function(){
        var cardId = $('#start').data('card-id');
        $(this).remove();
        $("#progress").show();
        console.log(cardId);

        try {
            await make_request('/api/create/' + cardId + '/domain/', "Domain + IP + SSL", "DataBase");
            await make_request('/api/create/' + cardId + '/db/', "DataBase", "FTP");
            await make_request('/api/create/' + cardId + '/ftp/', "FTP", "WordPress Setup");
            await make_request('/api/create/' + cardId + '/setup/', "WordPress Setup", "Tweaking WordPress");
            await make_request('/api/create/' + cardId + '/tweak/', "Tweaking WordPress", "WordPress API Key");
            const res = await make_request('/api/create/' + cardId + '/wp_api/', "WordPress API Key", "");
            console.log(res);
            res.code == 201 ? location.reload() : null;
        } catch (error) {
            // Handle any errors that occurred during the requests here.
        }
    })
});
