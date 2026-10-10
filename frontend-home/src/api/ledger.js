import request from './request'

// 家庭账本
export const getLedgerList = (params) => request.get('/ledger/list', { params })
export const addLedger = (data) => request.post('/ledger/add', data)
export const updateLedger = (data) => request.put('/ledger/update', data)
export const deleteLedger = (id, farmId) =>
  request.delete('/ledger/delete', { params: { id, farm_id: farmId } })
export const getLedgerSummary = (params) => request.get('/ledger/summary', { params })
export const getLedgerProfit = (params) => request.get('/ledger/profit', { params })
