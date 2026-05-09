function showToast(message, type = "success") {
    const toast = document.getElementById("toast");

    toast.textContent = message;
    toast.className = "toast show " + type;

    setTimeout(() => {
        toast.classList.remove("show");
    }, 2000);
}

async function copyCollectionLink(link) {
    try {
        await navigator.clipboard.writeText(link);
        showToast("Link kopiert ✔");
    } catch (err) {
        showToast("Kopieren fehlgeschlagen", "error");
        prompt("Kopiere den Link:", link);
    }
}