import axios from 'axios';

// Base URL for the API
// In production, this might be handled by Nginx proxy, so '/api' is relative
const API_URL = '/api';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for adding the auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for handling common errors (like 401 Unauthorized)
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      // Auto logout if 401 occurs
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export const authService = {
  login: async (email, password) => {
    const response = await api.post('/auth/token', new URLSearchParams({
      username: email,
      password: password,
    }), {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
    });
    return response.data;
  },
  
  register: async (userData) => {
    const response = await api.post('/auth/register', userData);
    return response.data;
  },
  
  me: async () => {
    const response = await api.get('/auth/me');
    return response.data;
  }
};

export const forensicService = {
  uploadEvidence: async (file, onUploadProgress) => {
    const formData = new FormData();
    formData.append('backup_file', file);

    const response = await api.post('/forensics/analyze', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress,
      timeout: 3600000 // 1 hour timeout for large files
    });
    return response.data;
  },

  getMyCases: async () => {
    const response = await api.get('/forensics/my-cases');
    return response.data;
  },

  getCaseStatus: async (caseId) => {
    const response = await api.get(`/forensics/status/${caseId}`);
    return response.data;
  },

  downloadReport: async (caseId, format = 'pdf') => {
    const response = await api.get(`/forensics/report/${caseId}?format=${format}`, {
      responseType: 'blob', // Important for file downloads
    });
    return response;
  }
};

export const paymentService = {
  // Mock Payment Implementation
  processPayment: async (caseId, paymentDetails) => {
    // In a real scenario, this would talk to Stripe/PayPal endpoint
    // Here we use the mock endpoint we will create
    const response = await api.post('/payment/process-mock', {
      case_id: caseId,
      ...paymentDetails
    });
    return response.data;
  },
  
  getPaymentHistory: async () => {
    const response = await api.get('/payment/history');
    return response.data;
  }
};

export const adminService = {
  getAllCases: async () => {
    // Admin endpoint to get ALL forensic cases
    const response = await api.get('/admin/forensics'); 
    return response.data;
  },

  getAllClients: async () => {
    const response = await api.get('/admin/clients');
    return response.data;
  },

  createMagicLink: async (data) => {
    // data: { client_number, request_type, expiry_days, notes, scenario_type }
    const response = await api.post('/requests/create', data);
    return response.data;
  },
  
  createCollectionLink: async (data) => {
    // data: { clientNumber, deviceType, sendSms, scenarioType }
    const response = await api.post('/collection/create-link', data);
    return response.data;
  }
};

export default api;
