/* 
CRUD
Create - POST
Read - GET
Update - PUT
Delete - DELETE

js file: client(browser) makes the HTTP request, decides how/when to call server
 */

const url = "http://127.0.0.1:5500/Lab%207/templates/prof_course.html";


//load all students
function loadAllStudents() {

    fetch(url, {method: "GET"}) //sends HTTP request to the url
        //returns a promise that contains the server's response

    .then(response => response.json())
        //server response converted into JSON (turns into an object)

    .then(data => {
        //data is JS object containing students/grades

        //find table from html
        const table = document.querySelector(".Gradebook tbody");

        //clear prev table (refreshes table)
        table.innerHTML="";

        //loops through each studentname & gets grade
        for (const name in data){
            const grade = data[name];
            const row = document.createElement("tr");

            row.innerHTML = `
                <td>${name}</td>

                <td>
                   <input class = "gradeInput" type="number" value="${grade}" id="grade-${name}">
                </td>

            `;
            table.appendChild(row);
        }

    })

    .catch(error => console.error(error));
}

//auto loads all students
loadAllStudents();
