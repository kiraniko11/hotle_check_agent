// 媒体地址解析工具：把后端返回的相对路径补全为可访问地址。

export function resolveMediaUrl(value) {
  if (!value) return ''
  if (/^(https?:)?\/\//i.test(value)) return value
  if (value.startsWith('data:') || value.startsWith('blob:')) return value
  if (value.startsWith('/media/') || value.startsWith('/static/')) return value
  return `/media/${String(value).replace(/^\/+/, '')}`
}

export default resolveMediaUrl
