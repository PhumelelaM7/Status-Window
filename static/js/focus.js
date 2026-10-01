// Countdown timer for the Fire-ring focus mode page. Supports
// pause/resume, and shows a "time's up" prompt when it reaches
// zero instead of auto-completing the quest.

document.addEventListener("DOMContentLoaded", function () {
    // Elements we need to read from or update on the page
    const timerDisplay = document.getElementById("focus-timer");
    const pauseBtn = document.getElementById("focus-pause-btn");
    const completeBtn = document.getElementById("focus-complete-btn");
    const timeUpBox = document.getElementById("focus-time-up");
    const addTimeBtn = document.getElementById("focus-add-time-btn");
    const completeFromTimeUpBtn = document.getElementById(
        "focus-complete-from-timeup-btn"
    );
    const completeForm = document.getElementById("complete-form");

    // FOCUS_DURATION_MINUTES comes from a small inline <script> in
    // focus.html, set directly from the quest's duration in Django
    let secondsRemaining = FOCUS_DURATION_MINUTES * 60;

    // Tracks whether the countdown is currently paused
    let isPaused = false;

    // Holds the reference returned by setInterval, so we can stop
    // it later with clearInterval
    let intervalId = null;

    function formatTime(totalSeconds) {
        // Convert a raw second count into "MM:SS" display text
        const minutes = Math.floor(totalSeconds / 60);
        const seconds = totalSeconds % 60;

        // padStart ensures single digits show as "05" not "5"
        const minutesText = String(minutes).padStart(2, "0");
        const secondsText = String(seconds).padStart(2, "0");

        return minutesText + ":" + secondsText;
    }

    function tick() {
        if (secondsRemaining <= 0) {
            // Countdown reached zero — stop ticking and show the
            // time's-up prompt instead of auto-completing
            clearInterval(intervalId);
            timeUpBox.classList.remove("hidden");
            return;
        }

        secondsRemaining -= 1;
        timerDisplay.textContent = formatTime(secondsRemaining);
    }

    function startTicking() {
        // setInterval runs tick() once every 1000 milliseconds
        // (one second) until we clearInterval it
        intervalId = setInterval(tick, 1000);
    }

    // Show the initial time immediately, then start counting down
    timerDisplay.textContent = formatTime(secondsRemaining);
    startTicking();

    pauseBtn.addEventListener("click", function () {
        if (isPaused) {
            // Currently paused — resume
            startTicking();
            pauseBtn.textContent = "Pause";
        } else {
            // Currently running — pause
            clearInterval(intervalId);
            pauseBtn.textContent = "Resume";
        }
        isPaused = !isPaused;
    });

    addTimeBtn.addEventListener("click", function () {
        // Add 10 minutes (600 seconds), hide the time's-up prompt,
        // and start counting down again
        secondsRemaining += 600;
        timeUpBox.classList.add("hidden");
        timerDisplay.textContent = formatTime(secondsRemaining);
        startTicking();
        isPaused = false;
        pauseBtn.textContent = "Pause";
    });

    function submitComplete() {
        // Submitting the hidden form sends a real POST request to
        // toggle_quest_complete, exactly like clicking "Mark
        // complete" on the normal schedule page would
        completeForm.submit();
    }

    completeBtn.addEventListener("click", submitComplete);
    completeFromTimeUpBtn.addEventListener("click", submitComplete);
});