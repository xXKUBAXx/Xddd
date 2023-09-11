$(document).ready(function() {
    $("button#categories").on('click', (event) => {
        var cardId = $('#main').data('card-id');
        $.ajax({
            type: 'GET',
            url: '/api/structure/'+ cardId +'/',
            success: (response) => {
                $("#cat_table").parent().show();
                response.sort((a,b) => a.parent - b.parent);
                parents = {};
                $("#cat_table>tbody").empty();
                response.forEach(e => {
                    e.parent == 0 ? parents[e.id] = e.name : null;
                    const fragment = document.createDocumentFragment()
                        .appendChild(document.createElement("tr"));
                    const check = document.createElement("input");
                    check.type = "checkbox";
                    check.id = e.id;
                    check.name = e.name;
                    check.checked = false;
                    fragment
                        .appendChild(document.createElement("td"))
                        .appendChild(check);
                    fragment
                        .appendChild(document.createElement("td"))
                        .textContent = e.parent==0 ? e.name : parents[e.parent]+' -> '+e.name;
                    $("#cat_table>tbody").append(fragment);
                });
                $("button#categories").remove();
                $("#articles").show();
                $.ajax({
                    type: 'PUT',
                    url: '/api/' + cardId + '/',
                    headers: {
                        'X-CSRFToken': getCookie('csrftoken')
                    },
                    data: {"wp_post_count": response.length}
                });
            },
            error: (e) => {
                console.error(e)
            }
        });
    });
    $("#articles").on('click', function(event) {
        const ul = document.createElement("ul");
        const rows = document.getElementById("cat_table").getElementsByTagName("tr");
        for (let i = 0; i < rows.length; i++) {
            const checkbox = rows[i].getElementsByTagName("input")[0];
            if (checkbox && checkbox.type === "checkbox" && checkbox.checked) {
                const rowData = rows[i].textContent.trim();
                li = document.createElement("li");
                li.textContent = rowData;
                ul.append(li);
            }
        }
        $(this).parent().append(ul);
        $("#cat_table").parent().remove();
        $(this).remove();
        $("#writeForm").show();
    });
});