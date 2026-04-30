import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 15000,
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      window.location.href = '/login'
    }
    return Promise.reject(err)
  }
)

// Auth
export const login = (data, redirect) =>
  api.post(`/auth/login${redirect ? '?redirect=' + redirect : ''}`, data)
export const logout = () => api.post('/auth/logout')
export const getMe = () => api.get('/auth/me')
export const register = (data) => api.post('/auth/register', data)

// Users
export const getUsers = () => api.get('/users')
export const getUser = (id) => api.get(`/users/${id}`)
export const updateUser = (id, data) => api.put(`/users/${id}`, data)
export const deleteUser = (id) => api.delete(`/users/${id}`)
export const exportUsers = () => api.get('/users/export', { responseType: 'blob' })

// Posts
export const getPosts = (params) => api.get('/posts', { params })
export const getPost = (id) => api.get(`/posts/${id}`)
export const createPost = (data) => api.post('/posts', data)
export const updatePost = (id, data) => api.put(`/posts/${id}`, data)
export const deletePost = (id) => api.delete(`/posts/${id}`)
export const getComments = (postId) => api.get(`/posts/${postId}/comments`)
export const addComment = (postId, data) => api.post(`/posts/${postId}/comments`, data)

// Media
export const getMedia = () => api.get('/media')
export const uploadFile = (formData) =>
  api.post('/media/upload', formData, { headers: { 'Content-Type': 'multipart/form-data' } })
export const downloadFile = (filename) =>
  api.get('/media/download', { params: { file: filename }, responseType: 'blob' })
export const generateThumbnail = (filename, size) =>
  api.post('/media/thumbnail', { filename, size })
export const deleteMedia = (id) => api.delete(`/media/${id}`)

// Settings
export const getSettings = () => api.get('/settings')
export const updateSettings = (data) => api.put('/settings', data)
export const fetchRemoteUrl = (url) => api.post('/settings/fetch-url', { url })
export const importSettings = (data) => api.post('/settings/import', { data })
export const importXmlSettings = (xml) =>
  api.post('/settings/import-xml', xml, { headers: { 'Content-Type': 'application/xml' } })

export default api
