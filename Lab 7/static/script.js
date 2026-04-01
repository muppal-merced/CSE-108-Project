/* 
CRUD
Create - POST
Read - GET
Update - PUT
Delete - DELETE

js file: client(browser) makes the HTTP request, decides how/when to call server
 */

//const url = "https://amhep.pythonanywhere.com/grades"; from lab 5
const url = "http://127.0.0.1:5000/students";


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

                <td>
                    <button class = "tableButtons" onclick = "updateGrade('${name}')">Update</button>
                </td>

                <td>
                <button class = "tableButtons" onclick = "deleteStudent('${name}')">Delete</button>
                </td>

            `;
            table.appendChild(row);
        }

    })

    .catch(error => console.error(error));
}

//Search
function searchStudent() {

    const inputField = document.getElementById("searchName");
    const input = inputField.value;


    //use %20 instead for spaces, spaces not allowed in URI
    //const encoded = name.replace(/ /g, "%20");
        // / / finds spaces, g: global replaces all space,
    const encoded = encodeURIComponent(input);
        //converts name into safe form for urls

    const table = document.querySelector(".Gradebook tbody");
    table.innerHTML = "";

    fetch(`${url}/${encoded}`)
        //sends request to specific url (the student)
    .then(response => { 
        if (!response.ok) {
            //if reponse is not 200, throw error
            throw new Error ("Student not found");
        }
        return response.json();
    })
    .then(student => {

        //get name from response
        const name = Object.keys(student)[0];
        const grade = student[name];

        const row = document.createElement("tr");

        row.innerHTML = `
            <td>${name}</td>

            <td class ="grade">
                <input class = "gradeInput" type="number" value="${grade}" id="grade-${name}">
            </td>

            <td>
                <button class = "tableButtons" onclick = "updateGrade('${name}')">Update</button>
            </td>

            <td>
                <button class = "tableButtons" onclick = "deleteStudent('${name}')">Delete</button>
            </td>

            `;
        table.appendChild(row);

        //clear input box
        inputField.value = "";
        
    })

    .catch(error => {
        //if student not found display error
        const table = document.querySelector(".Gradebook tbody");
        table.innerHTML = "";

        const row = document.createElement("tr");
        row.innerHTML = `
            <td colspan = "2" style = "text-align: center" > Student not found </td>
        `;
        table.appendChild(row);
    });
}

//Add 
function addStudent() {
    //input elements
    const nameInput = document.getElementById("newName");
    const gradeInput = document.getElementById("newGrade");

    //values
    const name = nameInput.value;
    const grade = parseFloat(gradeInput.value);

    fetch(url, {method: "POST",

        //tells server that data is in JSON format
        headers: {"Content-Type": "application/json"},

        //converts JS object into JSON string for server
        body: JSON.stringify({
            name: name,
            grade: grade
        })

    })
    
    //server reponse with JSON, then convert reponse back into JS object
    .then(response => response.json())

    //refreshes table
    .then(() => {
        loadAllStudents();

        //refreshes input fields
        nameInput.value = "";
        gradeInput.value = "";
    })
    
    .catch(error => console.error("Error adding student:", error));
}

// Update
function updateGrade(name) {
    const grade = document.getElementById(`grade-${name}`).value;
    const encoded = encodeURIComponent(name);

    fetch(`${url}/${encoded}`, {method: "PUT",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            grade: parseFloat(grade)
        })
    })
    .then(response => response.json())
    .then(() => {
        loadAllStudents();
    })

    .catch(error => console.error("Error updating grade:", error));
}

// Delete Student
function deleteStudent(name) {
    const encoded = encodeURIComponent(name);

    fetch(`${url}/${encoded}`, {method: "DELETE"}
    )

    .then(response => response.json())
    .then(() => {
        loadAllStudents();
    })

    .catch(error => console.error("Error deleting student:", error));
}

//auto loads all students
loadAllStudents();