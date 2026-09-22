<script setup>
import AdminResourceTable from '../../components/admin/AdminResourceTable.vue'
import { resourceConfigs } from '../../admin/resourceConfigs'
</script>

<template>
  <!-- 收藏管理：配置驱动渲染，新增页面只需声明式配置。 -->
  <AdminResourceTable :config="resourceConfigs.favorites" />
</template>
