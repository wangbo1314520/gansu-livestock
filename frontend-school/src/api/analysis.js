import request from './request'

// 关联分析
export const getCorrelation = (params) => request.get('/analysis/correlation', { params })
export const getLagCurve = (params) => request.get('/analysis/lag', { params })
export const getCostImpact = (params) => request.get('/analysis/cost-impact', { params })
