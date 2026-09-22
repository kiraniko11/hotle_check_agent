<script setup>
import AdminResourceTable from '../../components/admin/AdminResourceTable.vue'
import { resourceConfigs } from '../../admin/resourceConfigs'
</script>

<template>
  <AdminResourceTable :config="resourceConfigs.users" />
</template>
