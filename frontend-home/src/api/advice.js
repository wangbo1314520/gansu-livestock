import request from './request'

// 出栏建议
export const getSellAdvice = (params) => request.get('/advice/sell', { params })
export const getAdviceReason = (params) => request.get('/advice/reason', { params })
