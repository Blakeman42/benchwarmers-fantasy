document.addEventListener('DOMContentLoaded', () => {
    fetch('data.json')
        .then(response => response.json())
        .then(data => {
            const tbody = document.getElementById('table-body');
            
            data.forEach(team => {
                const row = document.createElement('tr');
                
                row.innerHTML = `
                    <td>#${team['BUSH RANK']}</td>
                    <td>${team['Team']}</td>
                    <td>${team['BUSH'].toFixed(2)}</td>
                    <td>${team['AVG'].toFixed(2)}</td>
                    <td>${team['WRank']}</td>
                    <td>${team['RealWins']}</td>
                    <td>${team['Expected Wins'].toFixed(2)}</td>
                    <td>${team['RecordvsAll Win%']}</td>
                `;
                tbody.appendChild(row);
            });
        })
        .catch(error => {
            console.error("Error loading data:", error);
            document.getElementById('table-body').innerHTML = `<tr><td colspan="8">Error loading ranking data. Make sure data.json exists.</td></tr>`;
        });
});