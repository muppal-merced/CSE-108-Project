import React, { useState, useEffect } from "react";
import "./App.css";

const API_URL = "/grades";

function App() {
  const [grades, setGrades] = useState({});
  const [name, setName] = useState("");
  const [grade, setGrade] = useState("");
  const [searchName, setSearchName] = useState("");
  const [searchResult, setSearchResult] = useState("");

  // ===============================
  // 2 Show All Students and Grades
  // ===============================
  const loadGrades = () => {
    fetch(API_URL)
      .then((res) => res.json())
      .then((data) => setGrades(data))
      .catch(() => alert("Error loading grades"));
  };

  useEffect(() => {
    loadGrades();
  }, []);

  // ===============================
  // 3 Create New Student (POST)
  // ===============================
  const addGrade = () => {
    if (!name || !grade) {
      alert("Enter name and grade.");
      return;
    }

    fetch(API_URL, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        name: name.trim(),
        grade: Number(grade),
      }),
    })
      .then((res) => res.json())
      .then(() => {
        loadGrades();
        setName("");
        setGrade("");
      })
      .catch(() => alert("Error adding student"));
  };

  // ===============================
  // 4 Edit Grade (PUT)
  // ===============================
  const editGrade = () => {
    if (!name || !grade) {
      alert("Enter name and new grade.");
      return;
    }

    const encodedName = encodeURIComponent(name.trim());

    fetch(`${API_URL}/${encodedName}`, {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        grade: Number(grade),
      }),
    })
      .then((res) => res.json())
      .then(() => {
        loadGrades();
        setName("");
        setGrade("");
      })
      .catch(() => alert("Error editing grade"));
  };

  // ===============================
  // 1 Get One Grade (GET /grades/<name>)
  // ===============================
  const getGrade = () => {
    if (!searchName) {
      alert("Enter student name.");
      return;
    }

    const trimmed = searchName.trim();
    const encodedName = encodeURIComponent(trimmed);

    fetch(`${API_URL}/${encodedName}`)
      .then((res) => res.json())
      .then((data) => {
        if (data[trimmed] !== undefined) {
          setSearchResult(`${trimmed}'s grade is ${data[trimmed]}`);
        } else {
          setSearchResult("Student not found.");
        }
      })
      .catch(() => setSearchResult("Error retrieving grade."));
  };

  // ===============================
  // 5 Delete Grade (DELETE)
  // ===============================
  const deleteGrade = (studentName) => {
    const encodedName = encodeURIComponent(studentName);

    fetch(`${API_URL}/${encodedName}`, {
      method: "DELETE",
    })
      .then((res) => res.json())
      .then(() => loadGrades())
      .catch(() => alert("Error deleting student"));
  };

  return (
    <div className="App">
      <h1>Grades Management System</h1>

      {/* Add / Edit Section */}
      <div className="section">
        <h2>Add or Edit Grade</h2>

        <input
          type="text"
          placeholder="Student Name (case sensitive)"
          value={name}
          onChange={(e) => setName(e.target.value)}
        />

        <input
          type="number"
          placeholder="Grade"
          value={grade}
          onChange={(e) => setGrade(e.target.value)}
        />

        <button onClick={addGrade}>Add</button>
        <button onClick={editGrade}>Edit</button>
      </div>

      {/* Get Grade Section */}
      <div className="section">
        <h2>Get Grade</h2>

        <input
          type="text"
          placeholder="Student Name"
          value={searchName}
          onChange={(e) => setSearchName(e.target.value)}
        />

        <button onClick={getGrade}>Get Grade</button>

        <p>{searchResult}</p>
      </div>

      {/* All Grades Table */}
      <div className="section">
        <h2>All Students and Grades</h2>

        <button onClick={loadGrades}>Refresh</button>

        <table>
          <thead>
            <tr>
              <th>Student</th>
              <th>Grade</th>
              <th>Delete</th>
            </tr>
          </thead>
          <tbody>
            {Object.keys(grades).map((student) => (
              <tr key={student}>
                <td>{student}</td>
                <td>{grades[student]}</td>
                <td>
                  <button onClick={() => deleteGrade(student)}>
                    Delete
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default App;