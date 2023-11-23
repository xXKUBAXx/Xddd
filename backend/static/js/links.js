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
    const z_slider = $("#zapleczaSlider");
    const z_value = $("#zapleczaSliderValue");
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

    z_slider.on('input', function() {
        z_value.val(z_slider.val());
        document.getElementById("zapleczaCount").innerHTML = document.querySelectorAll('#zaplacza-table tbody input[type="checkbox"]:checked').length+parseInt(z_value.val());
    });


    const checkboxes = document.querySelectorAll('#zaplacza-table tbody input[type="checkbox"]');

    checkboxes.forEach(box => {
        box.addEventListener("click", (event) => {
            document.getElementById("zapleczaCount").innerHTML = document.querySelectorAll('#zaplacza-table tbody input[type="checkbox"]:checked').length+parseInt(z_value.val());
        });
    });

    const linki_values = document.querySelectorAll('#frazy-table tbody input[type="number"]');
    function updateLinksSum() {
        let sum = 0;
        linki_values.forEach(l => {
            sum += parseInt(l.value);
        });
        document.getElementById("linksCount").innerHTML = sum + parseInt(document.querySelectorAll("#linki-form-group div").length);
    };
    linki_values.forEach(box => {
        box.addEventListener("change", updateLinksSum);
    })
    

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
            btn.addEventListener('click', updateLinksSum);  

            div.appendChild(btn);

            document.querySelector("button#addlinks").insertAdjacentElement("beforebegin", div);
            updateLinksSum();
            $(this).remove()
        }
    });

    $("#writeLinks").on('submit', function(event) {
        event.preventDefault();
        
        //check if api key provided
        if ($(this).find("input#openai_api_key").val() === "") {
            alert('Please fill in all fields.');
            return;
        }


        let formData = $(this).serialize();

        //get zapleczas data
        const checkboxes_checked = document.querySelectorAll('#zaplacza-table tbody input[type="checkbox"]:checked');
        const checkedRows = [];
        checkboxes_checked.forEach(box => {
            row = box.closest('tr');
            checkedRows.push({
                domain: row.cells[2].textContent,
                wp_user: box.getAttribute("data-user"),
                wp_api_key: box.getAttribute("data-key")
            });
        })
        let collection = document.getElementById("topics").selectedOptions;
        const zaplecza = document.querySelectorAll("#zaplacza-table tbody tr");
        let topic_list = [];
        zaplecza.forEach(z => {
            if (z.children[1].innerText == collection[0].value) {
                topic_list.push(z);
            }
        })
        topic_list.sort((a, b) => 0.5 - Math.random()).slice(0,parseInt(z_value.val())).forEach(e => {
            checkedRows.push({
                domain: e.children[2].innerText,
                wp_user: e.children[0].children[0].getAttribute("data-user"),
                wp_api_key: e.children[0].children[0].getAttribute("data-key"),
            })
        })

        //check if any zaplecza selected
        if(checkedRows.length == 0) {
            alert("Please select zaplecza!");
            return;
        }
        formData += "&zapleczas="+JSON.stringify(checkedRows);

        

        //get links data
        let link_data = [];
        if ($("#linki-form-group").length) {
            const links = document.getElementById("linki-form-group").getElementsByTagName("div");  
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
        }

        linki_values.forEach(box => {
            if(box.value > 0) {
                row = box.closest('tr');
                for (let i = 0; i < box.value; i++) {
                    link_data.push({
                        url: row.cells[0].textContent,
                        keyword: row.cells[1].textContent
                    });
                }
            };
        })

        if(link_data.length == 0) {
            alert("Please select any links");
            return;
        }
        if(link_data.length < checkedRows.length) {
            alert("There should be more links than zapleczas");
            return;
        }

        
        formData += "&links="+JSON.stringify(link_data);
        //add spinner to make waiting more bearable
        const spin = document.createElement("div");
        spin.classList.add("spinner");
        spin.setAttribute("id", "articles_spinner")
        $(this).parent().append("<ul id=\"link-results\">Preparing texts for:</ul>");
        $(this).parent().append(spin);
        $(this).remove();
        
        console.log(formData);
        $.ajax({
            type: 'POST',
            url: '/api/links/',
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            },
            data: formData,
            success: function(response) {
                let count = 0;
                for (let i in response.data){
                    // $("#write-details").append("<h6>"+ i +"</h6>");
                    // $("#write-details").append("<ul id=\""+ ++count +"\"></ul>");
                    // for (let j in response.data[i]){
                    //     for (let k in response.data[i][j]){
                    //         $("#write-details > ul#"+count).append("<li><a href=\""+response.data[i][j][k]+"\" target=\"_blank\">"+response.data[i][j][k]+"</a></li>");
                    //     };
                    // };
                };
                $("#write-details").parent().append("<p>Tokens used: "+response.tokens+"</p>");
                $("div#articles_spinner").remove()
            },
            error: function(response) {
                console.error(response);
            }
        })
    });
});