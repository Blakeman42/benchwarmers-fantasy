document.addEventListener('DOMContentLoaded', () => {
    fetch('data.json')
        .then(response => response.json())
        .then(data => {
            document.getElementById('week-subtitle').textContent = `Official Analytics for Week ${data.current_week}`;

            // 1. Populate Rankings
            const rBody = document.getElementById('rankings-body');
            rBody.innerHTML = '';
            data.rankings.forEach(t => {
                rBody.innerHTML += `<tr>
                    <td>#${t['BUSH RANK']}</td><td>${t.Team}</td><td>${t.BUSH}</td><td>${t.AVG}</td><td>${t.RealWins}</td>
                </tr>`;
            });

            // 2. Populate Playoff Odds
            const oBody = document.getElementById('odds-body');
            oBody.innerHTML = '';
            data.odds.forEach(t => {
                oBody.innerHTML += `<tr><td>${t.Team}</td><td style="color:#3b82f6; font-weight:bold;">${t.Odds}%</td></tr>`;
            });

            // 3. Populate History
            const hBody = document.getElementById('history-body');
            hBody.innerHTML = '';
            data.history.forEach(t => {
                hBody.innerHTML += `<tr><td>${t.Team}</td><td>${t.Wins}</td><td>${t.Losses}</td><td>${t.WinPct.toFixed(3)}</td></tr>`;
            });

            // 4. Populate Recap
            const rBox = document.getElementById('recap-content');
            if(data.recap.high_score) {
                rBox.innerHTML = `
                    <p><strong>🔥 High Scorer:</strong> ${data.recap.high_score.team} (${data.recap.high_score.points} pts)</p>
                    <p><strong>🧊 Low Scorer:</strong> ${data.recap.low_score.team} (${data.recap.low_score.points} pts)</p>
                    <p><strong>🤏 Closest Game:</strong> ${data.recap.closest.winner} beat ${data.recap.closest.loser} by ${data.recap.closest.diff.toFixed(2)} pts</p>
                    <p><strong>🥊 Biggest Blowout:</strong> ${data.recap.blowout.winner} crushed ${data.recap.blowout.loser} by ${data.recap.blowout.diff.toFixed(2)} pts</p>
                `;
            } else { rBox.innerHTML = "<p>No recap available yet (Week 1).</p>"; }

            // 5. Populate Matchups
            const mBox = document.getElementById('matchups-container');
            mBox.innerHTML = '';
            data.matchups.forEach(m => {
                mBox.innerHTML += `
                    <div class="matchup-box">
                        <div class="team-row"><span>${m.team1}</span> <span class="pts">${m.score1}</span></div>
                        <div class="vs">vs</div>
                        <div class="team-row"><span>${m.team2}</span> <span class="pts">${m.score2}</span></div>
                    </div>
                `;
            });
        });
});
