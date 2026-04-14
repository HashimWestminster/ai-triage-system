// api.js - axios client for talking to the django backend
// handles JWT tokens automatically and refreshes them when they expire
// all the API calls are exported as named functions

import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_URL || '/api';

const api = axios.create({
  baseURL: API_BASE,
  headers: { 'Content-Type': 'application/json' },
});

// attach the JWT token to every request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// handle 401 errors - try to refresh the token automatically
// IMPORTANT: skip this for login/register endpoints, otherwise
// a wrong password triggers a token refresh which makes no sense
// and causes a redirect loop (this was a bug i had to fix)
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    const isAuthEndpoint = originalRequest.url?.includes('/accounts/login/')
      || originalRequest.url?.includes('/accounts/register/');

    if (error.response?.status === 401 && !originalRequest._retry && !isAuthEndpoint) {
      originalRequest._retry = true;
      const refreshToken = localStorage.getItem('refresh_token');
      if (refreshToken) {
        try {
          const { data } = await axios.post(`${API_BASE}/accounts/token/refresh/`, {
            refresh: refreshToken,
          });
          localStorage.setItem('access_token', data.access);
          originalRequest.headers.Authorization = `Bearer ${data.access}`;
          return api(originalRequest);
        } catch {
          // refresh failed too, send them back to login
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          window.location.href = '/login';
        }
      }
    }
    return Promise.reject(error);
  }
);


// --- auth ---
export const login = (email, password) =>
  api.post('/accounts/login/', { email, password });

export const register = (data) =>
  api.post('/accounts/register/', data);

export const getMe = () => api.get('/accounts/me/');

export const getUsers = (role) =>
  api.get('/accounts/users/', { params: role ? { role } : {} });

// --- cases ---
export const submitCase = (data) => api.post('/cases/submit/', data);

export const getMyCases = () => api.get('/cases/my-cases/');

export const getCases = (params) =>
  api.get('/cases/list/', { params });

export const getCaseDetail = (id) => api.get(`/cases/${id}/`);

export const clinicianDecide = (caseId, data) =>
  api.post(`/cases/${caseId}/decide/`, data);

export const navigatorCloseCase = (caseId, data) =>
  api.post(`/cases/${caseId}/close/`, data);

export const getDashboardStats = () =>
  api.get('/cases/dashboard/stats/');

// --- surgery hours ---
export const getSurgeryStatus = () =>
  api.get('/accounts/surgery-status/');

export const getSurgeryHours = () =>
  api.get('/accounts/surgery-hours/');

export const updateSurgeryHours = (data) =>
  api.put('/accounts/surgery-hours/', data);

export default api;
