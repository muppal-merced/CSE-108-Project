async function loadMyCourses() {
    const res = await fetch('/my_courses');
    const data = await res.json();

    const table = document.getElementById('myCourses');
    table.innerHTML = "";

    data.forEach(c => {
        table.innerHTML += `
            <tr>
                <td>${c.name}</td>
                <td>${c.teacher}</td>
                <td>${c.time}</td>
                <td>${c.enrolled}/${c.capacity}</td>
                <td><button onclick="dropCourse(${c.id})">Remove</button></td>
            </tr>
        `;
    });
}

async function loadAllCourses() {
    const res = await fetch('/courses');
    const data = await res.json();

    const table = document.getElementById('allCourses');
    table.innerHTML = "";

    data.forEach(c => {
        const full = c.enrolled >= c.capacity;

        table.innerHTML += `
            <tr>
                <td>${c.name}</td>
                <td>${c.teacher}</td>
                <td>${c.time}</td>
                <td>${c.enrolled}/${c.capacity}</td>
                <td>
                    <button onclick="addCourse(${c.id})" ${full ? "disabled" : ""}>
                        ${full ? "Full" : "Add"}
                    </button>
                </td>
            </tr>
        `;
    });
}

async function addCourse(id) {
    await fetch(`/enroll/${id}`, { method: 'POST' });
    loadMyCourses();
    loadAllCourses();
}

async function dropCourse(id) {
    await fetch(`/drop/${id}`, { method: 'DELETE' });
    loadMyCourses();
    loadAllCourses();
}

function logout() {
    window.location.href = "/logout";
}

loadMyCourses();
loadAllCourses();