const eyeball = document.querySelector('.eyeball');

document.addEventListener('mousemove', (e) => {
    const { clientX: mouseX, clientY: mouseY } = e;

        const pupil = eyeball.querySelector('.pupil');
        const { left, top, width, height } = eyeball.getBoundingClientRect();
        const eyeX = left + width / 2;
        const eyeY = top + height / 2;
        const deltaX = mouseX - eyeX;
        const deltaY = mouseY - eyeY;
        const angle = Math.atan2(deltaY, deltaX);
        const distance = Math.min(width, height) / 4;
        const eyePositionX = eyeX + distance * Math.cos(angle) - 3;
        const eyePositionY = eyeY + distance * Math.sin(angle) - 6;

        pupil.style.transform = `translate(${eyePositionX - eyeX}px, ${eyePositionY - eyeY}px)`;
        const pupil2 = document.querySelector('#pupil2');
        pupil2.style.transform = `translate(${eyePositionX - eyeX}px, ${eyePositionY - eyeY}px)`;
});