import request from './request'

// 牛羊价格
export const getPriceList = (params) => request.get('/price/list', { params })
export const getPriceTrend = (params) => request.get('/price/trend', { params })
export const getPriceCompare = (params) => request.get('/price/compare', { params })
export const getLatestPrices = (params) => request.get('/price/latest', { params })
export const getYoy = (params) => request.get('/price/yoy', { params })
export const addPrice = (data) => request.post('/price/add', data)
export const updatePrice = (data) => request.put('/price/update', data)
export const deletePrice = (id) => request.delete('/price/delete', { params: { id } })
export const importPrices = (rows) => request.post('/price/import', rows)
export const exportPriceUrl = '/api/price/export'   // 直接 window.open 下载
