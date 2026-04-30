<template>
  <div>
    <div class="page-header">
      <h2 class="page-title">Media Library</h2>
      <el-button type="primary" @click="triggerUpload">
        <el-icon><Upload /></el-icon> Upload File
      </el-button>
    </div>

    <input ref="fileInputRef" type="file" hidden @change="handleFileChange" />

    <el-card shadow="never" style="margin-bottom:16px">
      <template #header>Thumbnail Generator</template>
      <el-row :gutter="12" align="middle">
        <el-col :span="10">
          <el-input v-model="thumbForm.filename" placeholder="Filename in library" />
        </el-col>
        <el-col :span="6">
          <el-input v-model="thumbForm.size" placeholder="e.g. 150x150" />
        </el-col>
        <el-col :span="4">
          <el-button type="default" :loading="thumbLoading" @click="generateThumb">Generate</el-button>
        </el-col>
      </el-row>
    </el-card>

    <el-card shadow="never" style="margin-bottom:16px">
      <template #header>Download File</template>
      <el-row :gutter="12" align="middle">
        <el-col :span="14">
          <el-input v-model="downloadFilename" placeholder="Filename or relative path" />
        </el-col>
        <el-col :span="4">
          <el-button @click="handleDownload">Download</el-button>
        </el-col>
      </el-row>
    </el-card>

    <el-card shadow="never">
      <el-table :data="files" v-loading="loading" style="width:100%">
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="original_name" label="Filename" />
        <el-table-column prop="mime_type" label="Type" width="160" />
        <el-table-column label="Size" width="100">
          <template #default="{ row }">{{ formatSize(row.size) }}</template>
        </el-table-column>
        <el-table-column prop="uploader_name" label="Uploaded By" width="130" />
        <el-table-column prop="uploaded_at" label="Date" width="160" />
        <el-table-column label="Actions" width="120">
          <template #default="{ row }">
            <el-button size="small" link type="danger" @click="confirmDelete(row)">Delete</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getMedia, uploadFile, downloadFile, generateThumbnail, deleteMedia } from '@/api'

const files = ref([])
const loading = ref(false)
const thumbLoading = ref(false)
const fileInputRef = ref(null)
const downloadFilename = ref('')
const thumbForm = reactive({ filename: '', size: '150x150' })

async function fetchMedia() {
  loading.value = true
  try {
    const res = await getMedia()
    files.value = res.data
  } finally {
    loading.value = false
  }
}

function triggerUpload() {
  fileInputRef.value.click()
}

async function handleFileChange(e) {
  const file = e.target.files[0]
  if (!file) return
  const fd = new FormData()
  fd.append('file', file)
  try {
    await uploadFile(fd)
    ElMessage.success('File uploaded')
    fetchMedia()
  } catch (err) {
    ElMessage.error(err.response?.data?.error || 'Upload failed')
  }
  e.target.value = ''
}

async function handleDownload() {
  if (!downloadFilename.value) return
  try {
    const res = await downloadFile(downloadFilename.value)
    const url = URL.createObjectURL(res.data)
    const a = document.createElement('a')
    a.href = url
    a.download = downloadFilename.value
    a.click()
    URL.revokeObjectURL(url)
  } catch {
    ElMessage.error('Download failed')
  }
}

async function generateThumb() {
  if (!thumbForm.filename) return
  thumbLoading.value = true
  try {
    await generateThumbnail(thumbForm.filename, thumbForm.size)
    ElMessage.success('Thumbnail created')
    fetchMedia()
  } catch (e) {
    ElMessage.error(e.response?.data?.error || 'Failed')
  } finally {
    thumbLoading.value = false
  }
}

async function confirmDelete(row) {
  await ElMessageBox.confirm(`Delete "${row.original_name}"?`, 'Confirm', { type: 'warning' })
  await deleteMedia(row.id)
  ElMessage.success('Deleted')
  fetchMedia()
}

function formatSize(bytes) {
  if (!bytes) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return `${(bytes / Math.pow(k, i)).toFixed(1)} ${sizes[i]}`
}

onMounted(fetchMedia)
</script>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.page-title { font-size: 20px; font-weight: 600; color: #1a237e; }
</style>
