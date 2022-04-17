importScripts("https://storage.googleapis.com/workbox-cdn/releases/6.4.1/workbox-sw.js")

// cache scripts and stylesheets
workbox.routing.registerRoute(
    ({ request }) =>
        request.destination == "style" ||
        request.destination == "script",

    new workbox.strategies.NetworkFirst({
        cacheName: "script-style"
    })
)

// cache fonts and images
workbox.routing.registerRoute(
    ({ request }) =>
        request.destination == "font" ||
        request.destination == "image",

    new workbox.strategies.StaleWhileRevalidate({
        cacheName: "font-image"
    })
)
