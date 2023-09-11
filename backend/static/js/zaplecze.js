$(document).ready(function() {
    const catSlider = document.getElementById('CatSlider');
    const catSliderValue = document.getElementById('CatSliderValue');

    catSlider.addEventListener('input', function () {
        catSliderValue.value = catSlider.value;
    });
    const subCatSlider = document.getElementById('SubCatSlider');
    const subCatSliderValue = document.getElementById('SubCatSliderValue');

    subCatSlider.addEventListener('input', function () {
        subCatSliderValue.value = subCatSlider.value;
    });


    $('#catForm').on('submit', function(event) {
        event.preventDefault(); // Prevent form from submitting normally
        
        // Serialize form data
        var formData = $(this).serialize();
        var cardId = $('#main').data('card-id');

        // Check if any field is empty
        var emptyFields = false;
        $(this).find('input').each(function() {
            if ($(this).val() === '') {
                emptyFields = true;
                return false; // Exit the loop early
            }
        });
        
        if (emptyFields) {
            alert('Please fill in all fields.');
            return; // Do not proceed with submission
        }

        if ($("#topic").val()){
            //PUT request to update DB
            $.ajax({
                type: 'PUT',
                url: '/api/' + cardId + '/',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken')
                },
                data: {"topic": $("#topic").val()},
                success: function(response) {
                    console.log(response);
                },
                error: function(response) {
                    console.error(response);
                }
            })
        }

        const spin = document.createElement("div");
        spin.classList.add("spinner");
        $(this).parent().append(spin);
        $(this).remove();

        // Send POST request to the /api/all/ endpoint
        $.ajax({
            type: 'POST',
            url: '/api/structure/'+ cardId +'/',
            data: formData,
            success: function(response) {
                const fragment = document.createDocumentFragment();
                fragment
                    .appendChild(document.createElement("h3"))
                    .textContent = "Utworzono kategorie";
                const ul = document.createElement("ul");
                Object.keys(response).forEach((e) => {
                    const li = document.createElement("li");
                    li.textContent = e;
                    const inner_ul = document.createElement("ul");
                    response[e].forEach((i) => {
                        const inner_li = document.createElement("li");
                        inner_li.textContent = i;
                        inner_ul.appendChild(inner_li);
                    });
                    li.appendChild(inner_ul);
                    ul.appendChild(li);
                })
                fragment.appendChild(ul);
                $("div.spinner").parent().append(fragment);
                $("div.spinner").remove();
            },
            error: function(error) {
                // Handle error response here
                console.error(error);
            }
        });
    });

    $("button#categories").on('click', (event) => {
        var cardId = $('#main').data('card-id');
        $.ajax({
            type: 'GET',
            url: '/api/structure/'+ cardId +'/',
            success: (response) => {
                $("#cat_table").show();
                response.sort((a,b) => a.parent - b.parent);
                parents = {};
                response.forEach(e => {
                    e.parent == 0 ? parents[e.id] = e.name : null;
                    const fragment = document.createDocumentFragment()
                        .appendChild(document.createElement("tr"));
                    const check = document.createElement("input");
                    check.type = "checkbox";
                    check.id = e.id;
                    check.value = e.id;
                    check.name = e.name;
                    fragment
                        .appendChild(document.createElement("td"))
                        .appendChild(check);
                    fragment
                        .appendChild(document.createElement("td"))
                        .textContent = e.parent==0 ? e.name : parents[e.parent]+' -> '+e.name;
                    $("#cat_table>table>tbody").append(fragment);
                });
                $("button#categories").text("Wypierdalaj");
                $("button#categories").attr('id', "write");
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
        $(this).innerHTML = "Wypierdalaj";
        $(this).attr('id', "write");
    });

});