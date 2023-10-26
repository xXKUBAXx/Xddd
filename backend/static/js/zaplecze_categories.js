$(document).ready(function() {
    // Select sliders and value elements 
    const art_slider = $("#ArtSlider");
    const art_value = $("#ArtSliderValue");
    const p_slider = $("#ParagraphsSlider");
    const p_value = $("#ParagraphsSliderValue");
    const d_slider = $("#DaysSlider");
    const d_value = $("#DaysSliderValue");

    // Add an input event listener 
    art_slider.on('input', function() {
        art_value.val(art_slider.val());
    });

    p_slider.on('input', function() {
        p_value.val(p_slider.val());
    });

    d_slider.on('input', function() {
        d_value.val(d_slider.val());
    });

    const today = new Date();
    let dd = today.getDate();
    let mm = today.getMonth() + 1;
    let yyyy = today.getFullYear();
    dd < 10 ? dd = '0' + dd : null;
    mm < 10 ? mm = '0' + mm : null; 
    document.getElementById("start_date").setAttribute("value", yyyy + '-' + mm + '-' + dd);

    $("button#categories").on('click', (event) => {
        const cardId = $('#main').data('card-id');
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
                if (response.length != $("#wp_post_count").innerHTML){
                    $.ajax({
                        type: 'PUT',
                        url: '/api/' + cardId + '/',
                        headers: {
                            'X-CSRFToken': getCookie('csrftoken')
                        },
                        data: {"wp_post_count": response.length}
                    });
                }
            },
            error: (e) => {
                console.error(e)
            }
        });
    });
    $("#articles").on('click', function(event) {
        const ul = document.createElement("ul");
        ul.setAttribute("id", "selected_cats")
        const rows = document.getElementById("cat_table").getElementsByTagName("tr");
        for (let i = 0; i < rows.length; i++) {
            const checkbox = rows[i].getElementsByTagName("input")[0];
            if (checkbox && checkbox.type === "checkbox" && checkbox.checked) {
                const rowData = rows[i].textContent.trim();
                li = document.createElement("li");
                li.textContent = rowData;
                li.setAttribute("data-id", checkbox.id);
                li.setAttribute("data-name", checkbox.name);
                li.append(document.createElement("ul"))
                ul.append(li);
            }
        }
        $(this).parent().append(ul);
        $("#cat_table").parent().remove();
        $(this).remove();
        $("#writeForm").show();
    });
    $("#addlinks").on('click', function(event) {
        event.preventDefault();
        if (!$("div#linki-form-group").length) {
            console.log('0');
            const div = document.createElement('div');
            div.style.display = 'flex';
            div.style.flexWrap = 'wrap';
            div.style.paddingTop = '20px';
            div.setAttribute('id', 'linki-form-group');
            div.classList.add('form-group');

            const inputs = document.createElement('div');
            inputs.style.display = 'flex';

            const input_url = document.createElement('input');
            input_url.classList.add('form-control');
            input_url.setAttribute('type', 'text');
            input_url.setAttribute('placeholder', 'url');
            input_url.setAttribute('name', 'url');
            input_url.style.width = "50%";
            inputs.appendChild(input_url);

            const input_keyword = document.createElement('input');
            input_keyword.classList.add('form-control');
            input_keyword.setAttribute('type', 'text');
            input_keyword.setAttribute('placeholder', 'keyword');
            input_keyword.setAttribute('name', 'keyword');
            input_keyword.style.width = "50%";
            inputs.appendChild(input_keyword);

            div.appendChild(inputs);
            
            const btn = document.createElement('button');
            btn.classList.add('btn');
            btn.classList.add('btn-outline-primary');
            btn.classList.add('btn-floating');
            btn.setAttribute('type','button');
            btn.setAttribute('id','addlinksrow');
            const icon = document.createElement('i');
            icon.classList.add('fas');
            icon.classList.add('fa-plus');
            btn.appendChild(icon);
            btn.style.height = "38px";

            btn.addEventListener('click', function(event) {
                event.preventDefault();
                if ($("div#linki-form-group").length) {
                    const inputs = document.createElement('div');
                    inputs.style.display = 'flex';

                    const input_url = document.createElement('input');
                    input_url.classList.add('form-control');
                    input_url.setAttribute('type', 'text');
                    input_url.setAttribute('placeholder', 'url');
                    input_url.setAttribute('name', 'url');
                    input_url.style.width = "50%";
                    inputs.appendChild(input_url);

                    const input_keyword = document.createElement('input');
                    input_keyword.classList.add('form-control');
                    input_keyword.setAttribute('type', 'text');
                    input_keyword.setAttribute('placeholder', 'keyword');
                    input_keyword.setAttribute('name', 'keyword');
                    input_keyword.style.width = "50%";
                    inputs.appendChild(input_keyword);
                    document.querySelector("#addlinksrow").insertAdjacentElement("beforebegin", inputs);
                }
            })

            div.appendChild(btn);

            document.querySelector("button#addlinks").insertAdjacentElement("beforebegin", div);
            $(this).remove()
        }
    });

    $("#writeForm").on('submit', function(event) {
        event.preventDefault();
        
        //check if api key provided
        if ($(this).find("input#openai_api_key").val() === "") {
            alert('Please fill in all fields.');
            return;
        }

        $('[name="url"], this').prop('disabled', true);
        $('[name="keyword"], this').prop('disabled', true);

        let formData = $(this).serialize();
        const cardId = $('#main').data('card-id');
        const cats = document.getElementById("selected_cats").getElementsByTagName("li");
        if ($(this).find("#linki-form-group").length) {
            const links = document.getElementById("linki-form-group").getElementsByTagName("div");  
            let link_data = [];
            for (div of links){
                let tmp = {};
                for (link of div.getElementsByTagName("input")){
                    if (link.value != ""){
                        tmp[link.getAttribute('name')] = link.value;
                    }
                }
                if (link.value != ""){
                    link_data.push(tmp);
                }
            }
            formData += "&links="+JSON.stringify(link_data);
        }

        const spin = document.createElement("div");
        spin.classList.add("spinner");
        spin.setAttribute("id", "articles_spinner")
        $(this).parent().append(spin);
        $(this).remove();

        const cats_num = $("ul#selected_cats li").length;
        const arts_num = $("#ArtSliderValue").val();
        const pars_num = $("#ParagraphsSliderValue").val();

        let deadline = new Date();
        console.log(5*cats_num*arts_num*pars_num);
        deadline.setSeconds(deadline.getSeconds() + 5*cats_num*arts_num*pars_num);
        let x = setInterval(() => {
            let now = new Date();
            let dist = deadline - now;
            $("div#articles_spinner").innerHTML = dist;
            console.log(dist);
            if (dist < 0) $("div#articles_spinner").innerHTML = "";
        }, 1000)

        let data = [];
        for (i of cats) {
            let cat_data = {};
            cat_data['id'] = i.getAttribute("data-id");
            cat_data['name'] = i.getAttribute("data-name");
            data.push(cat_data);
            last_id = cat_data['id'];
        }
        formData += "&categories="+JSON.stringify(data);

        
        console.log(formData);
        $.ajax({
            type: 'POST',
            url: '/api/write/'+ cardId +'/',
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            },
            data: formData,
            success: function(response) {
                for (const [id, urls] of Object.entries(response.data)) {
                    urls.forEach(function(e){
                        $("#selected_cats > [data-id=\'"+id+"\'] > ul")
                        .append("<li><a href=\""+e+"\">"+e+"</a></li>");
                        id == last_id ? $("div#articles_spinner").remove() : null;
                    })
                }
                $("#selected_cats").parent().append("<p>Tokens used: "+response.tokens+"</p>");
            },
            error: function(response) {
                console.error(response);
            }
        })
    });
});