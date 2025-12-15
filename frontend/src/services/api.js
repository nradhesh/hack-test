import axios from 'axios';

const API_BASE_URL = '/api/v1';

const api = axios.create({
    baseURL: API_BASE_URL,
    headers: { 'Content-Type': 'application/json' },
});

// Assets
export const getAssets = (params) => api.get('/assets', { params });
export const getAssetsForMap = (params) => api.get('/assets/map', { params });
export const getAsset = (id) => api.get(`/assets/${id}`);
export const createAsset = (data) => api.post('/assets', data);
export const updateAsset = (id, data) => api.put(`/assets/${id}`, data);
export const deleteAsset = (id) => api.delete(`/assets/${id}`);

// Issues
export const getIssues = (params) => api.get('/issues', { params });
export const getIssueSummary = (params) => api.get('/issues/summary', { params });
export const getIssue = (id) => api.get(`/issues/${id}`);
export const createIssue = (data) => api.post('/issues', data);
export const resolveIssue = (id, data) => api.patch(`/issues/${id}/resolve`, data);

// Debt
export const getAssetDebt = (id) => api.get(`/debt/asset/${id}`);
export const getAssetDebtHistory = (id, days = 30) => api.get(`/debt/asset/${id}/history`, { params: { days } });
export const simulateDebt = (data) => api.post('/debt/simulate', data);
export const getWardDebt = (id) => api.get(`/debt/ward/${id}`);
export const getCityDebt = () => api.get('/debt/city');

// Scores
export const getDashboard = () => api.get('/scores/dashboard');
export const getAssetScore = (id) => api.get(`/scores/asset/${id}`);
export const getAssetScoreHistory = (id, days = 30) => api.get(`/scores/asset/${id}/history`, { params: { days } });
export const getWardScore = (id) => api.get(`/scores/ward/${id}`);
export const getWardScoreHistory = (id, days = 30) => api.get(`/scores/ward/${id}/history`, { params: { days } });
export const getCityScore = () => api.get('/scores/city');
export const getAllWardScores = (params) => api.get('/scores/wards', { params });

// Explanations
export const explainAsset = (id) => api.get(`/explain/asset/${id}`);
export const explainWard = (id) => api.get(`/explain/ward/${id}`);
export const getCostComparison = (id) => api.get(`/explain/asset/${id}/cost-comparison`);

export default api;
