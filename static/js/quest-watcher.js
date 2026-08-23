// This script checks, once per minute, whether any incomplete
// quest's scheduled end time has passed. If one has, it shows a
// custom-styled modal asking the user to reschedule or mark it
// failed, instead of the browser's plain confirm() dialog.

document.addEventListener("DOMContentLoaded", function () {
    // Track which quest IDs we've already prompted about this page
    // load, so we don't nag the user repeatedly for the same quest
    const alreadyPrompted = new Set();

    // Grab references to the modal elements once, up front, so we
    // don't have to look them up every time we need them
    const modal = document.getElementById("overdue-modal");
    const modalMessage = document.getElementById("overdue-modal-message");
    const rescheduleBtn = document.getElementById("overdue-reschedule-btn");
    const failBtn = document.getElementById("overdue-fail-btn");

    // Holds the quest ID currently being shown in the modal, so
    // the button click handlers know which quest to act on
    let currentQuestId = null;

    function checkOverdueQuests() {
        const now = new Date();
        const nowHours = String(now.getHours()).padStart(2, "0");
        const nowMinutes = String(now.getMinutes()).padStart(2, "0");
        const nowLabel = nowHours + ":" + nowMinutes;

        const panels = document.querySelectorAll(".timeline-panel");

        panels.forEach(function (panel) {
            const questId = panel.dataset.questId;
            const endTime = panel.dataset.endTime;
            const isCompleted = panel.dataset.isCompleted === "true";
            const isFailed = panel.dataset.isFailed === "true";

            if (isCompleted || isFailed || alreadyPrompted.has(questId)) {
                return;
            }

            if (endTime < nowLabel) {
                alreadyPrompted.add(questId);
                showOverdueModal(panel, questId);
            }
        });
    }

    function showOverdueModal(panel, questId) {
        const title = panel.dataset.questTitle;

        // Remember which quest this modal is currently about
        currentQuestId = questId;

        modalMessage.textContent =
            '"' + title + '" was scheduled to end by now and ' +
            "isn't marked complete. Reschedule it, or mark it failed.";

        // Removing the "hidden" class makes the modal visible —
        // matches the CSS rule .modal-overlay.hidden { display: none; }
        modal.classList.remove("hidden");
    }

    function hideModal() {
        modal.classList.add("hidden");
        currentQuestId = null;
    }

    function markQuestFailed(questId) {
        const csrfToken = document.querySelector(
            "[name=csrfmiddlewaretoken]"
        ).value;

        fetch("/quest/" + questId + "/mark-failed/", {
            method: "POST",
            headers: {
                "X-CSRFToken": csrfToken,
            },
        }).then(function () {
            window.location.reload();
        });
    }

    // Wire up the two modal buttons once, up front, rather than
    // recreating them every time the modal shows
    rescheduleBtn.addEventListener("click", function () {
        if (currentQuestId) {
            window.location.href = "/quest/" + currentQuestId + "/reschedule/";
        }
    });

    failBtn.addEventListener("click", function () {
        if (currentQuestId) {
            markQuestFailed(currentQuestId);
        }
        hideModal();
    });

    checkOverdueQuests();
    setInterval(checkOverdueQuests, 60000);
});