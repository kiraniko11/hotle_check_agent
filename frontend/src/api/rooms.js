import http from './http'

export function fetchRoomTypes(params) {
  return http.get('/rooms/types/', { params })
}

export function fetchRoomTypeDetail(id) {
  return http.get(`/rooms/types/${id}/`)
}

export function fetchRoomStats() {
  return http.get('/rooms/stats/')
}

// 切换特定房型的收藏状态。
export function toggleFavorite(id) {
  return http.post(`/rooms/types/${id}/favorite/`)
}

// 获取当前登录用户对该房型的收藏状态。
export function getFavoriteStatus(id) {
  return http.get(`/rooms/types/${id}/favorite/status/`)
}

// 发起房间预订请求。
export function createBooking(id, data) {
  return http.post(`/rooms/types/${id}/book/`, data)
}

// 获取当前用户的所有历史订单列表。
export function getUserBookings() {
  return http.get('/rooms/bookings/')
}

// 获取房型的历史评论。
export function fetchRoomReviews(id) {
  return http.get(`/rooms/types/${id}/reviews/`)
}

// 发表客房打星与文字评语。
export function createReview(id, data) {
  return http.post(`/rooms/types/${id}/reviews/`, data)
}

// 取消特定订单预订行程。
export function cancelBooking(bookingId) {
  return http.post(`/rooms/bookings/${bookingId}/cancel/`)
}

// 获取当前登录用户收藏的所有房间类型列表。
export function getUserFavorites() {
  return http.get('/rooms/favorites/')
}

// 获取酒店评论看板：评分汇总、全部评价与可选房型。
export function fetchReviewBoard() {
  return http.get('/rooms/reviews/')
}

// 在酒店评论区发表评价（选房型 + 打星 + 文字）。
export function createBoardReview(data) {
  return http.post('/rooms/reviews/', data)
}
