const buttons = document.querySelectorAll('.info-button');
const description = document.getElementById('description');

buttons.forEach(function (button) {
	button.addEventListener('click', function () {
		description.textContent = button.dataset.description;
		description.hidden = false;
	});
});

