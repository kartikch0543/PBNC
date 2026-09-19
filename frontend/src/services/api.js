import axios from 'axios';

const api = axios.create({
  baseURL: '/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Automatic JWT Token Injection
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('docuq_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor for session expiry handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      localStorage.removeItem('docuq_token');
      window.dispatchEvent(new Event('docuq:auth_expired'));
    }
    return Promise.reject(error);
  }
);

export const authAPI = {
  login: async (email, password) => {
    const res = await api.post('/auth/login', { email, password });
    return res.data;
  },
  register: async (email, password) => {
    const res = await api.post('/auth/register', { email, password });
    return res.data;
  },
  getMe: async () => {
    const res = await api.get('/auth/me');
    return res.data;
  },
};

export const dashboardAPI = {
  getStats: async () => {
    const res = await api.get('/dashboard/stats');
    return res.data;
  },
};

export const documentAPI = {
  upload: async (file, documentType = 'QUESTION_PAPER') => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('document_type', documentType);
    const res = await api.post('/documents/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return res.data;
  },
  list: async () => {
    const res = await api.get('/documents');
    return res.data;
  },
  get: async (id) => {
    const res = await api.get(`/documents/${id}`);
    return res.data;
  },
  getStatus: async (id) => {
    const res = await api.get(`/documents/${id}/status`);
    return res.data;
  },
  getSourcePageUrl: (docId, pageNumber) => {
    return `/api/v1/documents/${docId}/source/${pageNumber}`;
  },
  exportJSON: async (id) => {
    const res = await api.get(`/documents/${id}/export`);
    return res.data;
  },
  getSampleBlob: async (filename) => {
    const res = await api.get(`/documents/samples/${filename}`, {
      responseType: 'blob',
    });
    return res.data;
  },
  createRelationship: async (sourceId, targetId, relType = 'ANSWER_KEY_FOR') => {
    const res = await api.post(`/documents/${sourceId}/relationships`, {
      target_document_id: targetId,
      relationship_type: relType,
    });
    return res.data;
  },
};

export const questionAPI = {
  listByDocument: async (docId, params = {}) => {
    const res = await api.get(`/documents/${docId}/questions`, { params });
    return res.data;
  },
  getDetail: async (id) => {
    const res = await api.get(`/questions/${id}`);
    return res.data;
  },
  getWarnings: async (docId) => {
    const res = await api.get(`/documents/${docId}/warnings`);
    return res.data;
  },
  getAnswers: async (docId) => {
    const res = await api.get(`/documents/${docId}/answers`);
    return res.data;
  },
  review: async (id, reviewData) => {
    const res = await api.patch(`/questions/${id}/review`, reviewData);
    return res.data;
  },
};

export const setAuthToken = (token) => {
  localStorage.setItem('docuq_token', token);
};

export const getAuthToken = () => {
  return localStorage.getItem('docuq_token');
};

export const clearAuthToken = () => {
  localStorage.removeItem('docuq_token');
};

export default api;
