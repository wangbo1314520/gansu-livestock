import request from './request'

// 预警
export const getRecords = (params) => request.get('/alert/records', { params })
export const markRead = (id) => request.post('/alert/read', { id })
export const getRules = (params) => request.get('/alert/rules', { params })
