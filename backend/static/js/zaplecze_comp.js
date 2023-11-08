var currentUrl = window.location.href;

document.addEventListener('DOMContentLoaded', (event) => {
	const dateInput = document.getElementById('dateInput_comp');
	const today = new Date();
	const day = String(today.getDate()).padStart(2, '0');
	const month = String(today.getMonth() + 1).padStart(2, '0');
	const year = today.getFullYear();
	dateInput.value = `${year}-${month}-${day}`;
});

function updateCompRGB(value) {
	var r = parseInt(value.substring(1, 3), 16);
	var g = parseInt(value.substring(3, 5), 16);
	var b = parseInt(value.substring(5, 7), 16);
	var rgbValue = r + ',' + g + ',' + b;
	$('#rgbValue_comp').val(rgbValue);
	console.log(rgbValue);
}

function rgbToHex(r, g, b) {
	return '#' + ((1 << 24) + (r << 16) + (g << 8) + b).toString(16).slice(1);
}

function hexToRgb(hex) {
	var r = parseInt(hex.slice(1, 3), 16);
	var g = parseInt(hex.slice(3, 5), 16);
	var b = parseInt(hex.slice(5, 7), 16);
	return r + ',' + g + ',' + b;
}

function updateColorInLocalStorage(color) {
	localStorage.setItem(currentUrl + '-overlayColorComp', color);
}

$(document).ready(function () {
	// change of date input
	const today = new Date();
	const day = String(today.getDate()).padStart(2, '0');
	const month = String(today.getMonth() + 1).padStart(2, '0');
	const year = today.getFullYear();
	$('#dateInput_comp').val(`${year}-${month}-${day}`);
	// end of snippet

	var defaultColor = '204,255,102';
	var savedColor = localStorage.getItem(currentUrl + '-overlayColorComp');

	var cardId = $('#classic_comp').data('card-id');

	if (savedColor) {
		var savedColorArray = savedColor.split(',').map(Number);
		var hexColor = rgbToHex(
			savedColorArray[0],
			savedColorArray[1],
			savedColorArray[2]
		);
		$('#colorPicker_comp').val(hexColor);
		$('#rgbValue_comp').val(savedColor);
	} else {
		var defaultColorArray = defaultColor.split(',').map(Number);
		var hexDefaultColor = rgbToHex(
			defaultColorArray[0],
			defaultColorArray[1],
			defaultColorArray[2]
		);
		$('#colorPicker_comp').val(hexDefaultColor);
		updateColorInLocalStorage(defaultColor);
	}

	$('button[type="submit_comp"]').on('click', function (event) {
		event.preventDefault();
		console.log('Zaliczyło!');

		var chosenColor = $('#rgbValue_comp').val() || defaultColor;

		if (chosenColor !== savedColor) {
			updateColorInLocalStorage(chosenColor);
		}

		const data = {
			compSelect: $('#comparisonSelect').val(),
			compQuant: $('#compQuant').val(),
			graphicSource: $('input[name="graphicSource_comp"]:checked').val(),
			overlayOption: $('input[name="overlayOption_comp"]:checked').val(),
			dateInput: $('#dateInput_comp').val(),
			publishInterval: $('#publishInterval_comp').val(),
			openai_api_key: $('#openai_api_key_comp').val(),
			faqOption: $('input[name="faqOption_comp"]:checked').val(),
            overlayColor: chosenColor
		};

		$.ajax({
			url: '/api/create/' + cardId + '/zaplecze_comp/',
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
				if (cookie.substring(0, name.length + 1) === name + '=') {
					cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
					break;
				}
			}
		}
		return cookieValue;
	}
});
