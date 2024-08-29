document.addEventListener('DOMContentLoaded', () => {
    fetch('/fetch_session_data')
        .then(response => response.json())
        .then(data => {
            console.log("Fetched data:", data); 
            let dataDisplay = document.getElementById('data_display');
            let numStudentsTakenTest = 0;
            dataDisplay.innerHTML = '';

            let table = document.createElement('table');
            table.classList.add('data_table');  // Add a class for styling

            table.innerHTML = `
                <tr>
                    <th>Name</th>
                    <th>Most Recent Attempt</th>
                    <th># of Attempts</th>

                </tr>
            `;
            data.forEach(user => {
                let row = document.createElement('tr');
                if (user[2] != null) { // Only display students who have finished the test
                row.innerHTML = `
                    <td><a href="/student_data/${user[1]}/${user[0]}">${user[0]}</a></td>
                    <td>${user[2]}</td>
                    <td>${user[3]}</td>
                `;
                table.appendChild(row);
                numStudentsTakenTest += 1;
                }
            });
            dataDisplay.appendChild(table);

            // Display the number of students who took the test
            let studentCount = document.getElementById('student_count');
            studentCount.innerHTML = `<p>Students who completed the test: <strong>${numStudentsTakenTest}</strong></p>`;
        })
        .catch(error => {
            console.error('Error fetching data:', error);
            document.getElementById('data_display').innerHTML = `<p>Error: ${error}</p>`;
        });
});
