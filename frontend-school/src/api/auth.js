import request from './request'

// 认证
export const login = (data) => request.post('/auth/login', data)
export const logout = () => request.post('/auth/logout')
export const getUserInfo = () => request.get('/auth/info')
export const changePassword = (data) => request.post('/auth/change-password', data)

// 基础数据
export const getRegions = () => request.get('/base/regions')
export const getBreeds = () => request.get('/base/breeds')
export const getCategories = () => request.get('/base/categories')
