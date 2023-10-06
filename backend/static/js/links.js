$(document).ready(function() {
    // Select sliders and value elements 
    const art_slider = $("#ArtSlider");
    const art_value = $("#ArtSliderValue");
    const p_slider = $("#ParagraphsSlider");
    const p_value = $("#ParagraphsSliderValue");
    const d_slider = $("#DaysSlider");
    const d_value = $("#DaysSliderValue");
    const f_slider = $("#NoFollowSlider");
    const f_value = $("#NoFollowSliderValue");

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

    f_slider.on('input', function() {
        f_value.val(f_slider.val());
    });

    const today = new Date();
    let dd = today.getDate();
    let mm = today.getMonth() + 1;
    let yyyy = today.getFullYear();
    dd < 10 ? dd = '0' + dd : null;
    mm < 10 ? mm = '0' + mm : null; 
    document.getElementById("start_date").setAttribute("value", yyyy + '-' + mm + '-' + dd);

    $("#addlinks").on('click', function(event) {
        event.preventDefault();
        if (!$("div#linki-form-group").length) {
            console.log('0');
            const div = document.createElement('div');
            div.style.display = 'flex';
            div.style.flexWrap = 'wrap';
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

            document.querySelector("#writeForm > button").insertAdjacentElement("beforebegin", div);
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
        spin.setAttribute("id", "spinner")
        $(this).parent().append(spin);
        $(this).remove();

        const cats_num = 1;
        const arts_num = $("#ArtSliderValue").val();
        const pars_num = $("#ParagraphsSliderValue").val();

        let deadline = new Date();
        console.log(5*cats_num*arts_num*pars_num);
        deadline.setSeconds(deadline.getSeconds() + 5*cats_num*arts_num*pars_num);
        let x = setInterval(() => {
            let now = new Date();
            let dist = deadline - now;
            $("div#spinner").innerHTML = dist;
            console.log(dist);
            if (dist < 0) $("div#spinner").innerHTML = "";
        }, 1000)
        
        formData += "&categories=1";

        
        console.log(formData);
        $.ajax({
            type: 'POST',
            url: '/api/write/',
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            },
            data: formData,
            success: function(response) {
                for (const [id, urls] of Object.entries(JSON.parse(response))) {
                    urls.forEach(function(e){
                        $("#selected_cats > [data-id=\'"+id+"\'] > ul")
                        .append("<li><a href=\""+e+"\">"+e+"</a></li>");
                        id == last_id ? $("div.spinner").remove() : null;
                    })
                }
            },
            error: function(response) {
                console.error(response);
            }
        })
    });
});