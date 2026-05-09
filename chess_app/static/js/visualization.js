const visualizationApp =
    document.getElementById(
        "visualization-app"
    );

if (visualizationApp) {
    const tasks = JSON.parse(
        visualizationApp.dataset.tasks
    );

    console.log(tasks);
}
