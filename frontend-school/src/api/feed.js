import request from './request'

// 饲料价格
export const getFeedList = (params) => request.get('/price/feed/list', { params })
export const getFeedTrend = (params) => request.get('/price/feed/trend', { params })
export const getLatestFeed = (params) => request.get('/price/feed/latest', { params })
export const addFeedPrice = (data) => request.post('/price/feed/add', data)
