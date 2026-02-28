import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_URL || '/api';

const api = axios.create({
  baseURL: API_BASE,
  headers: { 'Content-Type': 'application/json' },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});


api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // Don't try to refresh tokens on auth endpoints - a 401 here just
    // means the credentials were wrong, not that a token expired
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
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          window.location.href = '/login';
        }
      }
    }
    return Promise.reject(error);
  }
);


// Auth
export const login = (email, password) =>
  api.post('/accounts/login/', { email, password });

export const register = (data) =>
  api.post('/accounts/register/', data);

export const getMe = () => api.get('/accounts/me/');

export const getUsers = (role) =>
  api.get('/accounts/users/', { params: role ? { role } : {} });

// Cases
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

// Surgery hours
export const getSurgeryStatus = () =>
  api.get('/accounts/surgery-status/');

export const getSurgeryHours = () =>
  api.get('/accounts/surgery-hours/');

export const updateSurgeryHours = (data) =>
  api.put('/accounts/surgery-hours/', data);

export default api;
