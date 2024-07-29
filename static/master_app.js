document.addEventListener('DOMContentLoaded', () => {
    fetch('/fetch_session_data')
        .then(response => response.json())
        .then(data => {
            console.log("Fetched data:", data); 
            let dataDisplay = document.getElementById('data_display');
            dataDisplay.innerHTML = '';

            let table = document.createElement('table');
            table.classList.add('data_table');  // Add a class for styling

            table.innerHTML = `
                <tr>
                    <th>Name</th>
                </tr>
            `;
            data.forEach(user => {
                let row = document.createElement('tr');
                row.innerHTML = `
                    <td><a href="/student_data/${user[1]}/${user[0]}">${user[0]}</a></td>
                `;
                table.appendChild(row);
            });
            dataDisplay.appendChild(table);

            // Display the number of students who took the test
            let studentCount = document.getElementById('student_count');
            studentCount.innerHTML = `<p>Students who completed the test: <strong>${data.length}</strong></p>`;
        })
        .catch(error => {
            console.error('Error fetching data:', error);
            document.getElementById('data_display').innerHTML = `<p>Error: ${error}</p>`;
        });
});
