const playApp =
    document.getElementById("play-app");

if (playApp) {
    const config = JSON.parse(
        playApp.dataset.config
    );

    console.log(config);
}
