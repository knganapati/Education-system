import './style.css'
import { auth, batches, sessions, attendance, summary, monitoring } from './api.js'

const state = {
  user: JSON.parse(localStorage.getItem('sb_user')) || null,
  view: 'dashboard',
  loading: false,
}

const appEl = document.querySelector('#app')

// --- Router ---
function navigate(view) {
  state.view = view
  render()
}

// --- Utils ---
function showToast(msg, error = false) {
  const toast = document.createElement('div')
  toast.className = `toast ${error ? 'error' : 'success'}`
  toast.style.cssText = `
    position: fixed; bottom: 2rem; right: 2rem;
    padding: 1rem 2rem; border-radius: 0.5rem;
    background: ${error ? '#ef4444' : '#10b981'};
    color: white; z-index: 1000; box-shadow: 0 10px 20px rgba(0,0,0,0.2);
    animation: slideIn 0.3s ease-out;
  `
  toast.innerText = msg
  document.body.appendChild(toast)
  setTimeout(() => toast.remove(), 3000)
}

// --- Views ---

function renderLogin() {
  appEl.innerHTML = `
    <div class="auth-wrapper">
      <div class="auth-card">
        <h1 class="auth-title">SkillBridge <span>+</span></h1>
        <p class="auth-subtitle">Secure access to state skilling portal</p>
        <form id="login-form">
          <div class="form-group">
            <label class="label">Email Address</label>
            <input type="email" name="email" class="input" placeholder="name@email.com" required>
          </div>
          <div class="form-group">
            <label class="label">Password</label>
            <input type="password" name="password" class="input" placeholder="••••••••" required>
          </div>
          <button type="submit" class="btn btn-primary">Sign In</button>
        </form>
        <div style="text-align: center; margin-top: 1.5rem">
           <button class="btn btn-link" style="margin:0" onclick="window.navigate('signup')">Create Account</button>
        </div>
      </div>
    </div>
  `
  document.querySelector('#login-form').addEventListener('submit', async (e) => {
    e.preventDefault()
    try {
      const res = await auth.login(e.target.email.value, e.target.password.value)
      localStorage.setItem('sb_token', res.access_token)
      localStorage.setItem('sb_user', JSON.stringify(res.user))
      state.user = res.user
      navigate('dashboard')
    } catch (err) {
      showToast(err.detail || 'Login failed', true)
    }
  })
}

function renderSignup() {
  appEl.innerHTML = `
    <div class="auth-wrapper">
      <div class="auth-card">
        <h1 class="auth-title">SkillBridge <span>+</span></h1>
        <p class="auth-subtitle">Create your skilling account</p>
        <form id="signup-form">
          <div class="form-group">
            <label class="label">Full Name</label>
            <input type="text" name="name" class="input" placeholder="Type your full name..." required>
          </div>
          <div class="form-group"><label class="label">Email</label><input type="email" name="email" class="input" required></div>
          <div class="form-group"><label class="label">Password</label><input type="password" name="password" class="input" required></div>
          <div class="form-group">
            <label class="label">Role</label>
            <select name="role" class="input">
              <option value="student">Student</option>
              <option value="trainer">Trainer</option>
              <option value="institution">Institution Admin</option>
              <option value="programme_manager">Programme Manager</option>
              <option value="monitoring_officer">Monitoring Officer</option>
            </select>
          </div>
          <button type="submit" class="btn btn-primary">Create Account</button>
        </form>
        <button class="btn btn-link" onclick="window.navigate('login')">Already have an account? Login</button>
      </div>
    </div>
  `
  document.querySelector('#signup-form').addEventListener('submit', async (e) => {
    e.preventDefault()
    const data = Object.fromEntries(new FormData(e.target))
    try {
      const res = await auth.signup(data)
      localStorage.setItem('sb_token', res.access_token)
      localStorage.setItem('sb_user', JSON.stringify(res.user))
      state.user = res.user
      navigate('dashboard')
    } catch (err) {
       showToast(Array.isArray(err.detail) ? err.detail.join(', ') : (err.detail || 'Signup failed'), true)
    }
  })
}

function renderNavbar() {
  return `
    <nav class="nav">
      <div class="nav-container">
        <div class="logo">SkillBridge<span>+</span></div>
        <div class="user-badge">
          <span class="badge">${state.user.role}</span>
          <span style="font-weight: 500">${state.user.name}</span>
          <button class="btn btn-primary" style="padding: 0.5rem 1rem; font-size: 0.8rem" onclick="window.handleLogout()">Logout</button>
        </div>
      </div>
    </nav>
  `
}

async function renderDashboard() {
  appEl.innerHTML = renderNavbar() + `
    <main class="container">
      <header style="margin-bottom: 2.5rem">
        <h2 style="font-size: 1.5rem">Welcome back, ${state.user.name.split(' ')[0]}</h2>
        <p style="color: var(--text-dim)">Overview of your attendance and sessions</p>
      </header>
      <div id="role-dashboard-content"><div class="loader"></div></div>
    </main>
  `

  const container = document.querySelector('#role-dashboard-content')
  
  if (state.user.role === 'student') renderStudentDashboard(container)
  else if (state.user.role === 'trainer') renderTrainerDashboard(container)
  else if (state.user.role === 'programme_manager') renderPMDashboard(container)
  else if (state.user.role === 'monitoring_officer') renderMonitoringDashboard(container)
  else container.innerHTML = `<p>Dashboard for ${state.user.role} is coming soon.</p>`
}

async function renderStudentDashboard(container) {
  try {
    const stats = await summary.getStudentStats()
    container.innerHTML = `
      <div class="stats-grid">
        <div class="stat-card"><p class="stat-label">Enrolled Batches</p><p class="stat-value">${stats.total_batches}</p></div>
        <div class="stat-card"><p class="stat-label">Total Sessions</p><p class="stat-value">${stats.total_sessions}</p></div>
        <div class="stat-card"><p class="stat-label">Attendance Rate</p><p class="stat-value">${stats.attendance_rate}%</p></div>
      </div>
      <div class="card">
        <h3 class="card-title">Join a Batch</h3>
        <div style="display: flex; gap: 0.5rem;">
          <input type="text" id="join-token" class="input" placeholder="Invite token...">
          <button class="btn btn-primary" style="width: auto" onclick="window.joinBatch()">Join</button>
        </div>
      </div>
      <div class="card">
        <h3 class="card-title">My Enrollment</h3>
        <div class="table-wrapper">
          <table>
            <thead><tr><th>Batch ID</th><th>Name</th></tr></thead>
            <tbody>
              ${stats.enrolled_batches.map(b => `<tr><td>#${b.id}</td><td>${b.name}</td></tr>`).join('')}
            </tbody>
          </table>
        </div>
      </div>
    `
  } catch (err) {
    container.innerHTML = `<p class="error">Failed to sync stats.</p>`
  }
}

async function renderTrainerDashboard(container) {
  try {
    const stats = await summary.getTrainerStats()
    container.innerHTML = `
      <div class="stats-grid">
        <div class="stat-card"><p class="stat-label">Batches</p><p class="stat-value">${stats.total_batches}</p></div>
        <div class="stat-card"><p class="stat-label">Students</p><p class="stat-value">${stats.total_students}</p></div>
        <div class="stat-card"><p class="stat-label">Sessions conducted</p><p class="stat-value">${stats.total_sessions_conducted}</p></div>
      </div>
      <div class="card">
        <h3 class="card-title">My Projects</h3>
        <div class="table-wrapper">
          <table>
            <thead><tr><th>ID</th><th>Name</th><th>Actions</th></tr></thead>
            <tbody>
              ${stats.assigned_batches.map(b => `
                <tr>
                  <td>#${b.id}</td>
                  <td>${b.name}</td>
                  <td>
                    <button class="btn btn-link" style="padding:0" onclick="window.genInvite(${b.id})">Get Invite Token</button>
                  </td>
                </tr>
              `).join('')}
            </tbody>
          </table>
        </div>
      </div>
    `
  } catch (err) {
    container.innerHTML = `<p class="error">Data fetch failed.</p>`
  }
}

async function renderPMDashboard(container) {
  try {
    const data = await summary.getProgramme()
    container.innerHTML = `
      <div class="stats-grid">
        <div class="stat-card"><p class="stat-label">Institutions</p><p class="stat-value">${data.total_institutions}</p></div>
        <div class="stat-card"><p class="stat-label">Programme Attendance</p><p class="stat-value">${data.overall_attendance_rate}%</p></div>
      </div>
      <div class="card">
        <h3 class="card-title">Performance Index</h3>
        <div class="table-wrapper">
          <table>
            <thead><tr><th>Institution</th><th>Batches</th><th>Rate</th></tr></thead>
            <tbody>
              ${data.institutions.map(inst => `
                <tr><td>${inst.institution_name}</td><td>${inst.total_batches}</td><td>${inst.overall_attendance_rate}%</td></tr>
              `).join('')}
            </tbody>
          </table>
        </div>
      </div>
    `
  } catch (err) {
    container.innerHTML = `<p class="error">Unauthorized or service offline.</p>`
  }
}

async function renderMonitoringDashboard(container) {
  const mToken = localStorage.getItem('sb_monitoring_token')
  if (!mToken) {
    container.innerHTML = `
      <div class="card" style="max-width: 500px; margin: 0 auto">
        <h3 class="card-title">Security Gateway</h3>
        <p class="stat-label" style="margin-bottom: 1.5rem">Enter Security API Key to view live logs.</p>
        <input type="password" id="m-key" class="input" placeholder="••••••••">
        <button class="btn btn-primary" style="margin-top: 1rem" onclick="window.getMToken()">Unlock Logs</button>
      </div>
    `
  } else {
    try {
      const logs = await monitoring.getAttendance()
      container.innerHTML = `
        <div class="card">
          <h3 class="card-title">Live Attendance Registry (${logs.total_records} records)</h3>
          <div class="table-wrapper">
            <table>
              <thead><tr><th>Student</th><th>Batch</th><th>Status</th><th>Timestamp</th></tr></thead>
              <tbody>
                ${logs.records.map(r => `
                  <tr><td>${r.student_name}</td><td>${r.batch_name}</td><td><span class="status status-${r.status}">${r.status}</span></td><td>${new Date(r.marked_at).toLocaleString()}</td></tr>
                `).join('')}
              </tbody>
            </table>
          </div>
          <button class="btn btn-link" onclick="localStorage.removeItem('sb_monitoring_token'); window.render();">Lock Session</button>
        </div>
      `
    } catch (err) {
      localStorage.removeItem('sb_monitoring_token')
      render()
    }
  }
}

// --- Global Actions ---
window.navigate = navigate
window.handleLogout = () => {
  localStorage.clear()
  state.user = null
  navigate('login')
}
window.joinBatch = async () => {
  const token = document.querySelector('#join-token').value
  try {
    await batches.join(token)
    showToast('Successfully joined batch!')
    render()
  } catch (err) {
    showToast(err.detail || 'Invalid token', true)
  }
}
window.genInvite = async (bid) => {
  try {
    const res = await batches.getInvite(bid)
    alert(`Invite Token: ${res.token}\nExpires: ${res.expires_at}`)
  } catch (err) {
    showToast(err.detail || 'Failed to gen token', true)
  }
}
window.getMToken = async () => {
  const key = document.querySelector('#m-key').value
  try {
    const res = await auth.getMonitoringToken(key)
    localStorage.setItem('sb_monitoring_token', res.access_token)
    showToast('Logs unlocked')
    render()
  } catch (err) {
    showToast('Invalid Access Key', true)
  }
}

function render() {
  if (state.view === 'signup') renderSignup()
  else if (!state.user) renderLogin()
  else renderDashboard()
}

render()
