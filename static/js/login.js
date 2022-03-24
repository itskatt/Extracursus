"use strict"

const SEMESTER_SELECT = "semester-select"
const loader = document.getElementById("loader")

// prevent the forms from reloading the page...
document.querySelectorAll("form").forEach((frm) => {
    frm.addEventListener("submit", (e) => {
        e.preventDefault()
    })
})

async function login() {
    // we get the data
    const form = document.getElementById("login-form")
    let formData = new FormData(form)
    let username = formData.get("username")
    let password = formData.get("password")

    // we make the form unaccesible while we send the request
    form.elements[0].disabled = true

    // We start the loader
    loader.style.display = "flex"
    
    // we send it to the server
    // TODO: rewrite to use callbacks to catch net::ERR_CONNECTION_RESET
    console.log(`${username} is logging in...`)
    let resp = await fetch("/login", {
        method: "POST",
        headers: {
            "Accept": "application/json",
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            "username": username,
            "password": password
        })
    })

    // has everything happened correctly ?
    if (!resp.ok) {
        console.log(`Error in request (status ${resp.status})`)
        return
    }

    // process the data...
    let json =  await resp.json()

    // login was successfull
    if (json.sucess) { 
        console.log("Login sucessful")
        console.log(json.semesters)

        createSemSelection(json.semesters)
        document.getElementById("semester-select").classList.remove("invisible")
    }

    // login failed
    else { 
        form.elements[0].disabled = false
        console.log("Login failed")
    }

    // disable the loader
    loader.style.display = "none";
}

function createSemSelection(semesters) {
    let fieldset = document.getElementById("semester-form").elements[0]

    let ul = document.createElement("ul")
    for (let sem of semesters) {
        // create the list
        let li = document.createElement("li")

        // create the inputs
        let input = document.createElement("input")
        input.setAttribute("type", "radio")
        input.setAttribute("required", "true")
        input.setAttribute("name", SEMESTER_SELECT)
        input.id = sem

        // create the label
        let label = document.createElement("label")
        label.setAttribute("for", sem)
        label.appendChild(document.createTextNode(sem))

        // add everything to the list
        li.appendChild(input)
        li.appendChild(label)
        ul.appendChild(li)
    }

    fieldset.appendChild(ul)
}

async function getSemester() {
    // start the loader
    loader.style.display = "flex"

    // get the value from the selected radio button
    let buttons = document.getElementsByName(SEMESTER_SELECT)
    let semester
    for (let b of buttons) {
        if (b.checked) {
            semester = b.id
        }
    }

    console.log("Selected semester:", semester)

    // load the pdf serverside
    console.log("Preloading pdf...")
    await fetch(`/load_pdf?sem=${semester}`)
    console.log("done")

    // when we are ready, redirect and disable loader
    window.location.href = `${window.location.origin}/pretty_grades?sem=${semester}`
    loader.style.display = "none"
}
