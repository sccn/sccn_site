var shiftWindow = function() { scrollBy(0, -150) };
if (location.hash) shiftWindow();
window.addEventListener("hashchange", shiftWindow);