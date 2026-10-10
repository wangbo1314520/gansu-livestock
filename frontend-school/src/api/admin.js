import request from './request'

// 后台管理
export const getUsers = (params) => request.get('/admin/users', { params })
export const addUser = (data) => request.post('/admin/user/add', data)
export const runSpider = (spider) => request.post('/admin/spider/run', { spider })
export const getSpiderLog = (params) => request.get('/admin/spider/log', { params })
export const getSystemInfo = () => request.get('/admin/system/info')
