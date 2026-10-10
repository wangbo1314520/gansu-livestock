import request from './request'

// 牧场（存栏 + 饲料库存）
export const getFarmInfo = (params) => request.get('/farm/info', { params })
export const getLivestock = (params) => request.get('/farm/livestock/list', { params })
export const addLivestock = (data) => request.post('/farm/livestock/add', data)
export const updateLivestock = (data) => request.put('/farm/livestock/update', data)
export const deleteLivestock = (id, farmId) =>
  request.delete('/farm/livestock/delete', { params: { id, farm_id: farmId } })
export const getFeedStock = (params) => request.get('/farm/feed/list', { params })
export const feedIn = (data) => request.post('/farm/feed/in', data)
export const feedOut = (data) => request.post('/farm/feed/out', data)
