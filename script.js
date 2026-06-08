const API = '';

async function api(path, opts = {}) {
  const res = await fetch(API + path, {
    headers: { 'Content-Type': 'application/json' },
    ...opts
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'خطأ');
  return data;
}

function renderStars(count, interactive = false) {
  let html = '<div class="stars-display">';
  for (let i = 1; i <= 5; i++) {
    html += `<span class="star ${i <= count ? 'active' : ''}">★</span>`;
  }
  html += '</div>';
  return html;
}

function renderAdminSelects(admins) {
  const selects = ['adminSelect', 'filterAdmin'];
  selects.forEach(id => {
    const el = document.getElementById(id);
    if (!el) return;
    const current = el.value;
    el.innerHTML = id === 'adminSelect'
      ? '<option value="">-- اختر --</option>'
      : '<option value="all">جميع الإداريين</option>';
    admins.forEach(a => {
      const opt = document.createElement('option');
      opt.value = a;
      opt.textContent = a;
      el.appendChild(opt);
    });
    if (current && admins.includes(current)) el.value = current;
  });
}

function getAdminStats(ratings, admins) {
  return admins.map(admin => {
    const adminRatings = ratings.filter(r => r.admin === admin);
    const count = adminRatings.length;
    const avg = count ? (adminRatings.reduce((s, r) => s + r.rating, 0) / count).toFixed(1) : 0;
    return { admin, avg, count };
  });
}

function sortByRank(stats) {
  return [...stats].sort((a, b) => b.avg - a.avg || b.count - a.count);
}

function renderAdminStats(stats) {
  const container = document.querySelector('.admin-stats') || createStatsContainer();
  const ranked = sortByRank(stats);
  container.innerHTML = ranked.map((s, i) => `
    <div class="admin-stat-card">
      ${i === 0 && s.count > 0 ? '<span class="crown-badge">👑</span>' : ''}
      <div class="stat-name">${s.admin}</div>
      <div class="stat-stars">${renderStars(Math.round(s.avg))}</div>
      <div class="stat-details">${s.avg} / 5 (${s.count} تقييم)</div>
    </div>
  `).join('');
}

function createStatsContainer() {
  const section = document.createElement('section');
  section.className = 'admin-stats';
  const addRating = document.querySelector('.add-rating');
  document.querySelector('.container').insertBefore(section, addRating);
  return section;
}

function isFriday3PM() {
  const now = new Date();
  const sa = new Date(now.toLocaleString('en-US', { timeZone: 'Asia/Riyadh' }));
  return sa.getDay() === 5 && sa.getHours() >= 15;
}

function renderLeaderboard(stats) {
  const container = document.getElementById('leaderboardContainer');
  if (!container) return;
  const ranked = sortByRank(stats);
  if (!ranked.length || ranked.every(s => s.count === 0)) {
    container.innerHTML = '<div class="no-ratings" style="padding:20px 0">لا توجد تقييمات بعد</div>';
    return;
  }
  const crowns = ['👑', '🥈', '🥉'];
  const labels = ['الأول', 'الثاني', 'الثالث'];
  container.innerHTML = ranked.map((s, i) => `
    <div class="lb-row ${i < 3 && s.count > 0 ? 'rank-' + (i+1) : ''}">
      <span class="lb-rank">${i < 3 && s.count > 0 ? crowns[i] : '#' + (i+1)}</span>
      <span class="lb-name">${s.admin}</span>
      <span class="lb-score">${s.avg} ⭐ (${s.count})</span>
    </div>
  `).join('');
}

function renderWinnerSection(stats) {
  const container = document.getElementById('winnerContainer');
  if (!container) return;
  const ranked = sortByRank(stats);
  const top = ranked[0];
  if (!top || top.count === 0) {
    container.innerHTML = '';
    return;
  }
  const isFriday = isFriday3PM();
  if (isFriday) {
    container.innerHTML = `
      <div class="winner-announce">
        <span class="big-crown">👑</span>
        <div class="winner-title">🏆 بطل هذا الأسبوع</div>
        <div class="winner-name">${top.admin}</div>
        <div class="winner-score">${top.avg} / 5 ⭐ (${top.count} تقييم)</div>
      </div>
      <div class="podium">
        ${[0,1,2].map(i => {
          const s = ranked[i];
          if (!s || s.count === 0) return '';
          const medals = ['🥇', '🥈', '🥉'];
          const labels = ['الأول', 'الثاني', 'الثالث'];
          const cls = ['podium-1', 'podium-2', 'podium-3'];
          return `
            <div class="podium-card ${cls[i]}">
              <span class="crown">${medals[i]}</span>
              <span class="podium-name">${s.admin}</span>
              <span class="podium-score">${s.avg} ⭐</span>
              <span class="podium-rank-label">${labels[i]}</span>
            </div>
          `;
        }).join('')}
      </div>
    `;
  } else {
    container.innerHTML = `
      <div class="winner-announce" style="border-color:rgba(0,229,255,0.15)">
        <div style="font-size:0.9em;color:#8896a8;margin-bottom:4px">📊 المتصدر حالياً</div>
        <div style="font-size:1.6em;font-weight:900;color:#00E5FF">${top.admin}</div>
        <div style="color:#00E5FF;font-size:0.95em;margin-top:4px">${top.avg} / 5 ⭐</div>
        <div style="font-size:0.8em;color:#546370;margin-top:8px">🗓 الجمعة 3:00 م — موعد إعلان البطل</div>
      </div>
    `;
  }
}

function renderRatings(ratings) {
  const container = document.getElementById('ratingsContainer');
  if (!ratings.length) {
    container.innerHTML = '<div class="no-ratings">لا توجد تقييمات بعد</div>';
    return;
  }
  container.innerHTML = ratings.map(r => `
    <div class="rating-card">
      <div class="rating-card-header">
        <span class="admin-name">${r.admin}</span>
        <span class="rating-date">${r.date}</span>
      </div>
      ${renderStars(r.rating)}
      ${r.comment ? `<p class="comment-text">"${r.comment}"</p>` : ''}
      <div style="text-align:left;margin-top:8px">
        <button class="btn-small" onclick="deleteRating(${r.id})" style="background:rgba(239,68,68,0.15);color:#ef4444;border:1px solid rgba(239,68,68,0.3);padding:4px 12px;font-size:0.8em">حذف</button>
      </div>
    </div>
  `).join('');
}

async function deleteRating(id) {
  if (!confirm('هل أنت متأكد من حذف التقييم؟')) return;
  await api(`/api/ratings/${id}`, { method: 'DELETE' });
  await safeRefreshUI();
}

async function refreshUI() {
  const [admins, ratings] = await Promise.all([
    api('/api/admins'),
    api('/api/ratings')
  ]);
  renderAdminSelects(admins);
  const filter = document.getElementById('filterAdmin').value;
  const filtered = filter === 'all' ? ratings : ratings.filter(r => r.admin === filter);
  renderRatings(filtered);
  const stats = getAdminStats(ratings, admins);
  renderAdminStats(stats);
  renderLeaderboard(stats);
  renderWinnerSection(stats);
}

async function safeRefreshUI() {
  try {
    await refreshUI();
  } catch (err) {
    document.getElementById('ratingsContainer').innerHTML =
      '<div class="no-ratings">⚠️ تعذر الاتصال بالخادم</div>';
  }
}

// --- Form ---
document.getElementById('ratingForm').addEventListener('submit', async function(e) {
  e.preventDefault();
  const admin = document.getElementById('adminSelect').value;
  const rating = parseInt(document.getElementById('ratingValue').value);
  const comment = document.getElementById('comment').value.trim();
  if (!admin) { alert('اختر الإداري أولاً'); return; }
  if (!rating) { alert('اختر التقييم بالنجوم'); return; }
  try {
    await api('/api/ratings', {
      method: 'POST',
      body: JSON.stringify({ admin, rating, comment })
    });
    this.reset();
    document.querySelectorAll('.star').forEach(s => s.classList.remove('active'));
    await safeRefreshUI();
  } catch (err) {
    alert(err.message);
  }
});

// --- Stars ---
document.querySelectorAll('.star').forEach(s => {
  s.addEventListener('click', function() {
    const val = parseInt(this.dataset.value);
    document.getElementById('ratingValue').value = val;
    document.querySelectorAll('.star').forEach(st => {
      st.classList.toggle('active', parseInt(st.dataset.value) <= val);
    });
  });
  s.addEventListener('mouseenter', function() {
    const val = parseInt(this.dataset.value);
    document.querySelectorAll('.star').forEach(st => {
      st.classList.toggle('hover', parseInt(st.dataset.value) <= val);
    });
  });
  s.addEventListener('mouseleave', function() {
    document.querySelectorAll('.star').forEach(st => st.classList.remove('hover'));
  });
});

// --- Filter ---
document.getElementById('filterAdmin').addEventListener('change', async function() {
  const ratings = await api('/api/ratings');
  const filter = this.value;
  const filtered = filter === 'all' ? ratings : ratings.filter(r => r.admin === filter);
  renderRatings(filtered);
});

// --- Modal ---
document.getElementById('manageAdminsBtn').addEventListener('click', function() {
  document.getElementById('adminModal').classList.add('show');
  renderAdminList();
});

document.getElementById('closeModal').addEventListener('click', function() {
  document.getElementById('adminModal').classList.remove('show');
});

document.getElementById('adminModal').addEventListener('click', function(e) {
  if (e.target === this) this.classList.remove('show');
});

async function renderAdminList() {
  const admins = await api('/api/admins');
  const list = document.getElementById('adminList');
  list.innerHTML = admins.map((a, i) => `
    <li>
      <span>${a}</span>
      <span class="delete-admin" onclick="deleteAdmin('${a}')">✕ حذف</span>
    </li>
  `).join('');
}

async function deleteAdmin(name) {
  const ratings = await api('/api/ratings');
  if (ratings.some(r => r.admin === name)) {
    if (!confirm(`هذا الإداري لديه تقييمات. هل أنت متأكد من حذفه؟`)) return;
  }
  await api(`/api/admins/${encodeURIComponent(name)}`, { method: 'DELETE' });
  await renderAdminList();
  await safeRefreshUI();
}

document.getElementById('addAdminBtn').addEventListener('click', async function() {
  const input = document.getElementById('newAdmin');
  const name = input.value.trim();
  if (!name) return;
  try {
    await api('/api/admins', {
      method: 'POST',
      body: JSON.stringify({ name })
    });
    input.value = '';
    await renderAdminList();
    await safeRefreshUI();
  } catch (err) {
    alert(err.message);
  }
});

document.getElementById('newAdmin').addEventListener('keypress', function(e) {
  if (e.key === 'Enter') document.getElementById('addAdminBtn').click();
});

// --- Init ---
safeRefreshUI();
