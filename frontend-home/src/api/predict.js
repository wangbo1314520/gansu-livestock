import request from './request'

// 预测（家用版只读）
export const predictArimax = (params) => request.get('/predict/arimax', { params })
export const getAccuracy = (params) => request.get('/predict/accuracy', { params })
