document.addEventListener("DOMContentLoaded", function () {
    const editButton = document.querySelector(".admin-only");

    if (editButton) {
        editButton.addEventListener("click", function () {
            window.location.href = "/modifier-profil/"; // Redirige vers la page de modification
        });
    }
});
