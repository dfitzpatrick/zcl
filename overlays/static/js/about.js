async function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

alerter = document.getElementById('about-streamer');



async function displayAlert() {
    alerter.classList.add('animated', 'flipInX');
    alerter.style.display = "block";

    async function handleAnimationEnd() {
        await sleep(5000);
        alerter.style.display = "none";
        alerter.classList.remove('animated', 'flixInX');
        alerter.removeEventListener('animationend', handleAnimationEnd);
        alerter.style.display = "none";
    }
    alerter.addEventListener('animationend', handleAnimationEnd)
}

displayAlert();