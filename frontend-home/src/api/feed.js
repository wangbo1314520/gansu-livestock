import request from './request'

// 饲料
export const getLatestFeed = (params) => request.get('/price/feed/latest', { params })
export const getFeedTrend = (params) => request.get('/price/feed/trend', { params })
export const addFeedPrice = (data) => request.post('/price/feed/add', data)
