import {
  ChatLineRound,
  CollectionTag,
  House,
  OfficeBuilding,
  Star,
  Tickets,
  UserFilled,
} from '@element-plus/icons-vue'

export const adminRoles = [
  { label: '普通用户', value: 'user' },
  { label: '管理员', value: 'admin' },
]

export const roomStatuses = [
  { label: '空闲', value: 'vacant' },
  { label: '已入住', value: 'occupied' },
  { label: '清洁中', value: 'cleaning' },
  { label: '维修中', value: 'maintenance' },
]

export const bookingStatuses = [
  { label: '已预订', value: 'booked' },
  { label: '已入住', value: 'checked_in' },
  { label: '已完成', value: 'completed' },
  { label: '已取消', value: 'cancelled' },
]

export const feedbackStatuses = [
  { label: '待回复', value: 'pending' },
  { label: '已回复', value: 'replied' },
  { label: '已关闭', value: 'closed' },
]

export const adminNavItems = [
  { key: 'users', label: '用户管理', route: '/admin/users', icon: UserFilled },
  { key: 'room-types', label: '房型管理', route: '/admin/room-types', icon: OfficeBuilding },
  { key: 'rooms', label: '房间管理', route: '/admin/rooms', icon: House },
  { key: 'bookings', label: '订单管理', route: '/admin/bookings', icon: Tickets },
  { key: 'feedbacks', label: '留言管理', route: '/admin/feedbacks', icon: ChatLineRound },
  { key: 'reviews', label: '评论管理', route: '/admin/reviews', icon: Star },
  { key: 'favorites', label: '收藏管理', route: '/admin/favorites', icon: CollectionTag },
]
