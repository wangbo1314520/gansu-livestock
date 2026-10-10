import request from './request'

// 预警
export const getRules = (params) => request.get('/alert/rules', { params })
export const addRule = (data) => request.post('/alert/rule/add', data)
export const updateRule = (data) => request.put('/alert/rule/update', data)
export const deleteRule = (id) => request.delete('/alert/rule/delete', { params: { id } })
export const getRecords = (params) => request.get('/alert/records', { params })
export const markRead = (id) => request.post('/alert/read', { id })
