"use strict"

const rootStyle = document.documentElement.style

function toggleEmpty() {
    if (document.getElementById("hide").checked) {
        rootStyle.setProperty("--emptyDisplay", "none")
    } else {
        rootStyle.setProperty("--emptyDisplay", "block")
    }
}
