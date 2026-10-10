import request from './request'

// 预测
export const predictArima = (params) => request.get('/predict/arima', { params })
export const predictArimax = (params) => request.get('/predict/arimax', { params })
export const getAccuracy = (params) => request.get('/predict/accuracy', { params })
export const retrain = () => request.post('/predict/retrain')
