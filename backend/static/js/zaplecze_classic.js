var currentUrl = window.location.href;

document.addEventListener('DOMContentLoaded', (event) => {
	const dateInput = document.getElementById('dateInput');
	const today = new Date();
	const day = String(today.getDate()).padStart(2, '0');
	const month = String(today.getMonth() + 1).padStart(2, '0');
	const year = today.getFullYear();
	dateInput.value = `${year}-${month}-${day}`;
});

function updateRGB(value) {
	var r = parseInt(value.substring(1, 3), 16);
	var g = parseInt(value.substring(3, 5), 16);
	var b = parseInt(value.substring(5, 7), 16);
	var rgbValue = r + ',' + g + ',' + b;
	$('#rgbValue').val(rgbValue);
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
	localStorage.setItem(currentUrl + '-overlayColor', color);
}

$(document).ready(function () {
	// change of date input
	const today = new Date();
	const day = String(today.getDate()).padStart(2, '0');
	const month = String(today.getMonth() + 1).padStart(2, '0');
	const year = today.getFullYear();
	$('#dateInput').val(`${year}-${month}-${day}`);
	// end of snippet

	var cardId = $('#classic_main').data('card-id');

	var defaultColor = '204,255,102';
	var savedColor = localStorage.getItem(currentUrl + '-overlayColor');

	if (savedColor) {
		var savedColorArray = savedColor.split(',').map(Number);
		var hexColor = rgbToHex(
			savedColorArray[0],
			savedColorArray[1],
			savedColorArray[2]
		);
		$('#colorPicker').val(hexColor);
		$('#rgbValue').val(savedColor);
	} else {
		var defaultColorArray = defaultColor.split(',').map(Number);
		var hexDefaultColor = rgbToHex(
			defaultColorArray[0],
			defaultColorArray[1],
			defaultColorArray[2]
		);
		$('#colorPicker').val(hexDefaultColor);
		updateColorInLocalStorage(defaultColor);
	}

	$('button[type="submit_tsv"]').on('click', function (event) {
		event.preventDefault();
		console.log('Zaliczyło!');

		var chosenColor = $('#rgbValue').val() || defaultColor;

		if (chosenColor !== savedColor) {
			updateColorInLocalStorage(chosenColor);
		}

		const data = {
			tsvInput: $('#tsvInput').val(),
			graphicSource: $('input[name="graphicSource"]:checked').val(),
			overlayOption: $('input[name="overlayOption"]:checked').val(),
			dateInput: $('#dateInput').val(),
			publishInterval: $('#publishInterval').val(),
			openai_api_key: $('#openai_api_key_classic').val(),
			faqOption: $('input[name="faqOption"]:checked').val(),
			overlayColor: chosenColor,
		};

		// console.log(data.overlayColor);

		$('#classic_main').hide();
		$('#resetButton').hide();

		$('table.table thead tr').append('<th>Status</th>');

		$('table.table tbody tr').each(function () {
			$(this).append(
				'<td class="status-cell"><div class="loading-icon"></div></td>'
			);
		});

		$.ajax({
			url: '/api/create/' + cardId + '/zaplecze_classic/',
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

	function getWordpressPostsTitles() {
		const password = document.getElementById('wp_api_key').innerText;
		const domain = document.getElementById('domain').innerText;
		const login = document.getElementById('wp_user').innerText;

		const token = btoa(`${login}:${password}`);
		const authHeader = { Authorization: `Basic ${token}` };

		const apiUrl = `https://${domain}/wp-json/wp/v2/posts?per_page=100`;

		const tsvTitles = parseTSV($('#tsvInput').val()).map(decodeHTMLEntities);

		fetch(apiUrl, { headers: authHeader })
			.then((response) => {
				if (!response.ok) {
					throw new Error(`HTTP error! status: ${response.status}`);
				}
				return response.json();
			})
			.then((posts) => {
				const wordpressTitles = posts.map((post) =>
					decodeHTMLEntities(post.title.rendered)
				);
				console.log('Tytuły, które pokrywają się z plikiem TSV:');
				tsvTitles.forEach((tsvTitle) => {
					if (wordpressTitles.includes(tsvTitle)) {
						console.log(`${tsvTitle} - opublikowano`);
						updateStatusCells(posts);
					}
				});
			})
			.catch((error) => {
				console.error('Wystąpił błąd podczas pobierania wpisów:', error);
			});
	}

	function parseTSV(tsv) {
		const lines = tsv.trim().split('\n');
		const headers = lines.shift().split('\t');
		const titleIndex = headers.indexOf('title');

		if (titleIndex === -1) {
			console.error("Nie znaleziono kolumny 'title'");
			return [];
		}

		return lines.map((line) => {
			const columns = line.split('\t');
			return columns[titleIndex];
		});
	}

	function decodeHTMLEntities(text) {
		var textArea = document.createElement('textarea');
		textArea.innerHTML = text;
		return textArea.value;
	}

	setInterval(getWordpressPostsTitles, 90000);

	function updateStatusCells(posts) {
		const wordpressTitles = posts.map((post) =>
			decodeHTMLEntities(post.title.rendered)
		);
		$('table.table tbody tr').each(function () {
			var titleCell = $(this).find('td:first');
			var statusCell = $(this).find('.status-cell');
			if (wordpressTitles.includes(titleCell.text())) {
				statusCell.html('<div class="checkmark">✓</div>');
			}
		});
	}

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
