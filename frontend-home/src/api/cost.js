import request from './request'

// 成本计算
export const calcProfit = (data) => request.post('/cost/calculate', data)
export const calcDelay = (data) => request.post('/cost/delay', data)
export const getBreakeven = (params) => request.get('/cost/breakeven', { params })
export const getCostConfig = (params) => request.get('/cost/config', { params })
export const saveCostConfig = (data) => request.post('/cost/config/save', data)
