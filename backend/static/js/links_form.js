const linki_values = document.querySelectorAll('#frazy-table tbody input[type="number"]');
function updateLinksSum() {
    let sum = 0;
    linki_values.forEach(l => {
        sum += parseInt(l.value);
    });
    try{
        document.getElementById("linksCount").innerHTML = sum + parseInt(document.querySelectorAll("#linki-form-group div").length);
    }
    catch(error){
        console.log("No place to store links count!");
    }
    
};
linki_values.forEach(box => {
    box.addEventListener("change", updateLinksSum);
})

function createTexts(url_text, keyword_text) {
    const inputs = document.createElement('div');
    inputs.style.display = 'flex';

    const input_url = document.createElement('input');
    input_url.classList.add('form-control');
    input_url.classList.add('paste-url');
    input_url.setAttribute('type', 'text');
    input_url.setAttribute('placeholder', 'url');
    input_url.setAttribute('name', 'url');
    input_url.style.width = "50%";
    input_url.value = url_text;
    input_url.addEventListener('paste', (e) => {
        e.stopPropagation();
        e.preventDefault();

        // get the data the user wants to paste, in our case text
        const pastedData = e.clipboardData || this.window.clipboardData;
        const pastedText = pastedData.getData("Text");
        const pastedArray = pastedText.split(/\r?\n/);
        input_url.value = pastedArray[0].split(/[\t]+/)[0];
        // Find the closest input with class 'paste-keyword' and update its value
        input_url.parentNode.lastChild.value = pastedArray[0].split(/[\t]+/)[1];
        if (pastedArray.length > 1) {
            pastedArray.slice(1).forEach(e => {
                const inputs = createTexts(e.split(/[\t]+/)[0], e.split(/[\t]+/)[1]);
                document.querySelector("#addlinksrow").insertAdjacentElement("beforebegin", inputs);
                updateLinksSum();
            })
        } 
    });

    inputs.appendChild(input_url);

    const input_keyword = document.createElement('input');
    input_keyword.classList.add('form-control');
    input_keyword.classList.add('paste-keyword');
    input_keyword.setAttribute('type', 'text');
    input_keyword.setAttribute('placeholder', 'keyword');
    input_keyword.setAttribute('name', 'keyword');
    input_keyword.style.width = "50%";
    input_keyword.value = keyword_text;
    inputs.appendChild(input_keyword);

    return inputs;
}


function createButton() {
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
            inputs = createTexts('', '');
            document.querySelector("#addlinksrow").insertAdjacentElement("beforebegin", inputs);
        }
    })
    btn.addEventListener('click', updateLinksSum);  

    return btn;
}

$("#addlinks").on('click', function(event) {
    event.preventDefault();
    if (!$("div#linki-form-group").length) {
        const div = document.createElement('div');
        div.style.display = 'flex';
        div.style.flexWrap = 'wrap';
        div.style.paddingTop = '20px';
        div.setAttribute('id', 'linki-form-group');
        div.classList.add('form-group');

        inputs = createTexts('', '');

        div.appendChild(inputs);
        
        btn = createButton();

        div.appendChild(btn);

        document.querySelector("button#addlinks").insertAdjacentElement("beforebegin", div);
        updateLinksSum();
        $(this).remove()
    }
});