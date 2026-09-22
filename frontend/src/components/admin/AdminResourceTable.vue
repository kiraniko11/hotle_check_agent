<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { CirclePlus, Refresh, Search } from '@element-plus/icons-vue'

import {
  createAdminResource,
  deleteAdminResource,
  fetchAdminResource,
  fetchAdminStats,
  updateAdminResource,
} from '../../api/adminPanel'
import { baseSelectOptions } from '../../admin/resourceConfigs'
import { resolveMediaUrl } from '../../utils/image'

const props = defineProps({
  config: {
    type: Object,
    required: true,
  },
})

const emit = defineEmits(['stats-loaded'])

const loading = ref(false)
const supportLoading = ref(false)
const dialogVisible = ref(false)
const dialogMode = ref('create')
const editingId = ref(null)
const keyword = ref('')
const rows = ref([])
const support = reactive({
  users: [],
  roomTypes: [],
  rooms: [],
})
const dialogForm = reactive({})
const fileInputRef = ref(null)
const coverPreviewUrl = ref('')

const selectOptions = computed(() => ({
  ...baseSelectOptions,
  users: support.users.map((item) => ({ label: `${item.username} / ${item.mobile}`, value: item.id })),
  roomTypes: support.roomTypes.map((item) => ({ label: item.name, value: item.id })),
  rooms: support.rooms.map((item) => ({ label: `${item.room_number} / ${item.room_type_name}`, value: item.id })),
}))

function formatDateTime(value) {
  if (!value) return ''
  return String(value).substring(0, 16).replace('T', ' ')
}

function formatCell(row, column) {
  const value = row[column.prop]
  if (column.type === 'boolean') {
    return value ? '是' : '否'
  }
  if (column.type === 'image') {
    return value ? '图片' : '无'
  }
  if (column.type === 'datetime') {
    return formatDateTime(value)
  }
  if (column.type === 'money') {
    return value === null || value === undefined || value === '' ? '' : `¥${value}`
  }
  if (column.type === 'role') {
    return baseSelectOptions.roles.find((item) => item.value === value)?.label || value
  }
  return value ?? ''
}

function getFieldOptions(field) {
  return selectOptions.value[field.optionsKey] || []
}

function resetForm(row = null) {
  Object.keys(dialogForm).forEach((key) => delete dialogForm[key])
  props.config.fields.forEach((field) => {
    let value = row?.[field.prop] ?? field.default ?? ''
    if (field.type === 'file') {
      value = ''
    }
    dialogForm[field.prop] = value
  })
  // 房型编辑时显示当前封面图，方便管理员判断是否需要替换。
  coverPreviewUrl.value = row?.cover_image ? resolveMediaUrl(row.cover_image) : ''
  if (dialogMode.value === 'edit') {
    dialogForm.password = ''
  }
}

function handleFileChange(event, field) {
  const target = event.target
  const file = target?.files?.[0]
  if (!file) {
    return
  }

  dialogForm[field.prop] = file
  coverPreviewUrl.value = URL.createObjectURL(file)
  target.value = ''
}

async function loadStats() {
  const response = await fetchAdminStats()
  if (response.data?.code === 200) {
    emit('stats-loaded', response.data.data || {})
  }
}

async function loadSupportData() {
  supportLoading.value = true
  try {
    const [userRes, roomTypeRes, roomRes] = await Promise.all([
      fetchAdminResource('users'),
      fetchAdminResource('room-types'),
      fetchAdminResource('rooms'),
    ])
    support.users = userRes.data?.data || []
    support.roomTypes = roomTypeRes.data?.data || []
    support.rooms = roomRes.data?.data || []
  } finally {
    supportLoading.value = false
  }
}

async function loadRows() {
  loading.value = true
  try {
    const response = await fetchAdminResource(props.config.resource, { keyword: keyword.value })
    if (response.data?.code === 200) {
      rows.value = response.data.data || []
    }
  } finally {
    loading.value = false
  }
}

async function refreshAll() {
  await Promise.all([loadStats(), loadSupportData()])
  await loadRows()
}

function openCreateDialog() {
  dialogMode.value = 'create'
  editingId.value = null
  resetForm()
  dialogVisible.value = true
}

function openEditDialog(row) {
  dialogMode.value = 'edit'
  editingId.value = row.id
  resetForm(row)
  dialogVisible.value = true
}

function buildPayload() {
  const payload = new FormData()
  props.config.fields.forEach((field) => {
    const value = dialogForm[field.prop]
    if (field.prop === 'password' && dialogMode.value === 'edit' && !value) {
      return
    }
    if (field.type === 'file') {
      if (value instanceof File) {
        payload.append(field.prop, value)
      }
      return
    }
    if (field.type === 'number') {
      payload.append(field.prop, value === '' || value === null || value === undefined ? '0' : String(Number(value)))
      return
    }
    if (value !== undefined && value !== null && value !== '') {
      payload.append(field.prop, value)
    }
  })
  return payload
}

async function submitForm() {
  const payload = buildPayload()
  try {
    if (dialogMode.value === 'create') {
      await createAdminResource(props.config.resource, payload)
      ElMessage.success('创建成功')
    } else {
      await updateAdminResource(props.config.resource, editingId.value, payload)
      ElMessage.success('更新成功')
    }
    dialogVisible.value = false
    await refreshAll()
  } catch (err) {
    const message = err.response?.data?.msg || err.response?.data?.detail || '保存失败'
    ElMessage.error(message)
  }
}

async function handleDelete(row) {
  try {
    await ElMessageBox.confirm(`确认删除「${row.username || row.name || row.title || row.id}」吗？`, '删除确认', {
      type: 'warning',
      confirmButtonText: '删除',
      cancelButtonText: '取消',
    })
    await deleteAdminResource(props.config.resource, row.id)
    ElMessage.success('删除成功')
    await refreshAll()
  } catch (err) {
    if (err !== 'cancel') {
      ElMessage.error(err.response?.data?.msg || '删除失败')
    }
  }
}

onMounted(async () => {
  await refreshAll()
})
</script>

<template>
  <section class="resource-page">
    <div class="resource-header">
      <div>
        <span class="resource-eyebrow">管理中心</span>
        <h1>{{ config.title }}</h1>
        <p>{{ config.subtitle }}</p>
      </div>
      <div class="resource-actions">
        <el-button :icon="Refresh" plain :loading="loading || supportLoading" @click="refreshAll">刷新</el-button>
        <el-button :icon="CirclePlus" type="primary" class="admin-primary-btn" @click="openCreateDialog">
          {{ config.createText || '新增' }}
        </el-button>
      </div>
    </div>

    <section class="admin-work-card">
      <div class="table-toolbar">
        <el-input
          v-model="keyword"
          clearable
          class="search-input"
          placeholder="输入关键词搜索当前数据"
          @keyup.enter="loadRows"
          @clear="loadRows"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        <el-button plain @click="loadRows">搜索</el-button>
      </div>

      <el-table v-loading="loading" :data="rows" border stripe class="admin-table">
        <el-table-column
          v-for="column in config.columns"
          :key="column.prop"
          :prop="column.prop"
          :label="column.label"
          :width="column.width"
          :min-width="column.minWidth"
          show-overflow-tooltip
        >
          <template #default="{ row }">
            <img
              v-if="column.type === 'image' && row[column.prop]"
              class="image-thumb"
              :src="row[column.prop]"
              :alt="row.name || '封面图片'"
            />
            <span v-else>{{ formatCell(row, column) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="168" fixed="right">
          <template #default="{ row }">
            <el-button size="small" plain @click="openEditDialog(row)">编辑</el-button>
            <el-button size="small" type="danger" plain @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </section>

    <el-dialog
      v-model="dialogVisible"
      :title="dialogMode === 'create' ? config.createText : `编辑${config.title}`"
      width="760px"
      class="admin-dialog"
      :close-on-click-modal="false"
    >
      <div class="form-grid">
        <label
          v-for="field in config.fields"
          :key="field.prop"
          class="form-item"
          :class="{ wide: field.type === 'textarea' }"
        >
          <span>{{ field.label }}</span>
          <template v-if="field.type === 'file'">
            <input
              ref="fileInputRef"
              class="file-input"
              type="file"
              :accept="field.accept || 'image/*'"
              @change="handleFileChange($event, field)"
            />
            <div class="file-preview" v-if="coverPreviewUrl">
              <img :src="coverPreviewUrl" alt="图片预览" />
            </div>
          </template>
          <el-input
            v-if="field.type === 'input'"
            v-model="dialogForm[field.prop]"
            :placeholder="`请输入${field.label}`"
          />
          <el-input
            v-else-if="field.type === 'password'"
            v-model="dialogForm[field.prop]"
            type="password"
            show-password
            :placeholder="dialogMode === 'edit' ? '留空则不修改密码' : `请输入${field.label}`"
          />
          <el-input
            v-else-if="field.type === 'textarea'"
            v-model="dialogForm[field.prop]"
            type="textarea"
            :rows="4"
            :placeholder="`请输入${field.label}`"
          />
          <el-input-number
            v-else-if="field.type === 'number'"
            v-model="dialogForm[field.prop]"
            :min="0"
            controls-position="right"
            class="full-control"
          />
          <el-switch v-else-if="field.type === 'switch'" v-model="dialogForm[field.prop]" />
          <el-date-picker
            v-else-if="field.type === 'date'"
            v-model="dialogForm[field.prop]"
            type="date"
            value-format="YYYY-MM-DD"
            class="full-control"
          />
          <el-select
            v-else-if="field.type === 'select'"
            v-model="dialogForm[field.prop]"
            filterable
            clearable
            class="full-control"
            :placeholder="`请选择${field.label}`"
          >
            <el-option
              v-for="option in getFieldOptions(field)"
              :key="option.value"
              :label="option.label"
              :value="option.value"
            />
          </el-select>
        </label>
      </div>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" class="admin-primary-btn" @click="submitForm">保存</el-button>
      </template>
    </el-dialog>
  </section>
</template>

<style scoped>
.resource-page {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.resource-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 18px;
}

.resource-eyebrow {
  color: #6c63ff;
  font-size: 12px;
  font-weight: 900;
  letter-spacing: 1.6px;
  text-transform: uppercase;
}

.resource-header h1 {
  margin: 6px 0 0;
  color: #172033;
  font-size: 28px;
  font-weight: 900;
  line-height: 1.18;
}

.resource-header p {
  margin: 8px 0 0;
  color: #697386;
  font-size: 14px;
}

.resource-actions,
.table-toolbar {
  display: flex;
  align-items: center;
  gap: 10px;
}

.admin-primary-btn {
  background: #1f2937 !important;
  border-color: #1f2937 !important;
  font-weight: 800;
}

.admin-work-card {
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 14px;
  padding: 18px;
  box-shadow: 0 18px 45px rgba(15, 23, 42, 0.06);
}

.table-toolbar {
  margin-bottom: 16px;
}

.search-input {
  width: 360px;
}

.admin-table {
  width: 100%;
}

.image-thumb {
  width: 72px;
  height: 46px;
  object-fit: cover;
  border-radius: 10px;
  border: 1px solid #e5e7eb;
  display: block;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px 18px;
}

.form-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
  color: #374151;
  font-size: 13px;
  font-weight: 800;
}

.form-item.wide {
  grid-column: 1 / -1;
}

.full-control {
  width: 100%;
}

.file-input {
  width: 100%;
  color: #4b5563;
}

.file-preview {
  width: 100%;
  max-width: 220px;
  padding: 8px;
  border: 1px dashed #d1d5db;
  border-radius: 12px;
  background: #fafafa;
}

.file-preview img {
  width: 100%;
  height: 120px;
  object-fit: cover;
  border-radius: 10px;
  display: block;
}

@media (max-width: 760px) {
  .resource-header {
    flex-direction: column;
  }

  .resource-actions,
  .table-toolbar {
    width: 100%;
    flex-wrap: wrap;
  }

  .search-input {
    width: 100%;
  }

  .form-grid {
    grid-template-columns: 1fr;
  }
}
</style>
