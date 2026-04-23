const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export async function request(endpoint, options = {}) {
  const token = localStorage.getItem('sb_token');
  const monitoringToken = localStorage.getItem('sb_monitoring_token');
  
  // Use monitoring token for monitoring endpoints if available
  const activeToken = endpoint.includes('/monitoring') ? monitoringToken : token;

  const headers = {
    'Content-Type': 'application/json',
    ...options.headers,
  };

  if (activeToken) {
    headers['Authorization'] = `Bearer ${activeToken}`;
  }

  const response = await fetch(`${API_URL}${endpoint}`, {
    ...options,
    headers,
  });

  const data = await response.json();

  if (!response.ok) {
    throw { status: response.status, ...data };
  }

  return data;
}

export const auth = {
  login: (email, password) => request('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  }),
  signup: (userData) => request('/auth/signup', {
    method: 'POST',
    body: JSON.stringify(userData),
  }),
  getMonitoringToken: (key) => request('/auth/monitoring-token', {
    method: 'POST',
    body: JSON.stringify({ key }),
  }),
};

export const batches = {
  list: () => request('/batches'),
  create: (data) => request('/batches', {
    method: 'POST',
    body: JSON.stringify(data),
  }),
  getInvite: (id) => request(`/batches/${id}/invite`, { method: 'POST' }),
  join: (token) => request('/batches/join', {
    method: 'POST',
    body: JSON.stringify({ token }),
  }),
};

export const sessions = {
  create: (data) => request('/sessions', {
    method: 'POST',
    body: JSON.stringify(data),
  }),
  getAttendance: (id) => request(`/sessions/${id}/attendance`),
};

export const attendance = {
  mark: (session_id, status) => request('/attendance/mark', {
    method: 'POST',
    body: JSON.stringify({ session_id, status }),
  }),
};

export const summary = {
  getBatch: (id) => request(`/batches/${id}/summary`),
  getInstitution: (id) => request(`/institutions/${id}/summary`),
  getProgramme: () => request('/programme/summary'),
  getStudentStats: () => request('/students/me/stats'),
  getTrainerStats: () => request('/trainers/me/stats'),
};

export const monitoring = {
  getAttendance: () => request('/monitoring/attendance'),
};
