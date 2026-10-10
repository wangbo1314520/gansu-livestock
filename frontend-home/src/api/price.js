import request from './request'

// 价格看板
export const getLatestPrices = (params) => request.get('/price/latest', { params })
export const getPriceTrend = (params) => request.get('/price/trend', { params })
export const getYoy = (params) => request.get('/price/yoy', { params })
