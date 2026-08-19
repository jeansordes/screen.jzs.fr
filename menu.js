const images = document.querySelectorAll('.visuel');

images.forEach(function (image) {
    image.addEventListener('click', function () {
        window.location.href = 'static/index.html';
    });
});