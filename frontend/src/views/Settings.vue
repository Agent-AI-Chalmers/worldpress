<template>
  <div>
    <h2 class="page-title">Settings</h2>

    <el-tabs v-model="activeTab">
      <el-tab-pane label="General" name="general">
        <el-card shadow="never" v-loading="loading">
          <el-form :model="generalForm" label-width="180px" style="max-width:600px">
            <el-form-item label="Site Name">
              <el-input v-model="generalForm.site_name" />
            </el-form-item>
            <el-form-item label="Site Description">
              <el-input v-model="generalForm.site_description" type="textarea" :rows="2" />
            </el-form-item>
            <el-form-item label="Allow Registration">
              <el-switch v-model="generalForm.allow_registration" active-value="true" inactive-value="false" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" :loading="saving" @click="saveGeneral">Save Changes</el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-tab-pane>

      <el-tab-pane label="Remote Fetch" name="fetch">
        <el-card shadow="never">
          <template #header>Fetch Remote Resource</template>
          <el-form label-width="60px" style="max-width:600px">
            <el-form-item label="URL">
              <el-input v-model="fetchUrl" placeholder="https://example.com/data.json" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" :loading="fetchLoading" @click="fetchRemote">Fetch</el-button>
            </el-form-item>
          </el-form>
          <el-card v-if="fetchResult" shadow="never" style="margin-top:16px;background:#f8f9fa">
            <div style="font-size:12px;margin-bottom:8px">
              Status: <strong>{{ fetchResult.status_code }}</strong>
              &nbsp; Type: <strong>{{ fetchResult.content_type }}</strong>
            </div>
            <pre style="max-height:300px;overflow:auto;font-size:12px">{{ fetchResult.body }}</pre>
          </el-card>
        </el-card>
      </el-tab-pane>

      <el-tab-pane label="Import" name="import">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-card shadow="never">
              <template #header>Import Settings (Base64)</template>
              <el-input
                v-model="importData"
                type="textarea"
                :rows="6"
                placeholder="Paste base64-encoded settings blob here"
              />
              <el-button
                type="primary"
                style="margin-top:12px"
                :loading="importLoading"
                @click="doImport"
              >
                Import
              </el-button>
            </el-card>
          </el-col>
          <el-col :span="12">
            <el-card shadow="never">
              <template #header>Import Settings (XML)</template>
              <el-input
                v-model="xmlData"
                type="textarea"
                :rows="6"
                placeholder="Paste XML settings here"
              />
              <el-button
                type="primary"
                style="margin-top:12px"
                :loading="xmlLoading"
                @click="doXmlImport"
              >
                Import XML
              </el-button>
            </el-card>
          </el-col>
        </el-row>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getSettings, updateSettings, fetchRemoteUrl, importSettings, importXmlSettings } from '@/api'

const activeTab = ref('general')
const loading = ref(false)
const saving = ref(false)
const fetchLoading = ref(false)
const importLoading = ref(false)
const xmlLoading = ref(false)
const fetchUrl = ref('')
const fetchResult = ref(null)
const importData = ref('')
const xmlData = ref('')

const generalForm = reactive({
  site_name: '',
  site_description: '',
  allow_registration: 'false',
})

onMounted(async () => {
  loading.value = true
  try {
    const res = await getSettings()
    Object.assign(generalForm, {
      site_name: res.data.site_name || '',
      site_description: res.data.site_description || '',
      allow_registration: res.data.allow_registration || 'false',
    })
  } finally {
    loading.value = false
  }
})

async function saveGeneral() {
  saving.value = true
  try {
    await updateSettings(generalForm)
    ElMessage.success('Settings saved')
  } catch (e) {
    ElMessage.error(e.response?.data?.error || 'Failed')
  } finally {
    saving.value = false
  }
}

async function fetchRemote() {
  if (!fetchUrl.value) return
  fetchLoading.value = true
  fetchResult.value = null
  try {
    const res = await fetchRemoteUrl(fetchUrl.value)
    fetchResult.value = res.data
  } catch (e) {
    ElMessage.error(e.response?.data?.error || 'Fetch failed')
  } finally {
    fetchLoading.value = false
  }
}

async function doImport() {
  if (!importData.value) return
  importLoading.value = true
  try {
    const res = await importSettings(importData.value)
    ElMessage.success(`Imported ${res.data.count} settings`)
  } catch (e) {
    ElMessage.error(e.response?.data?.error || 'Import failed')
  } finally {
    importLoading.value = false
  }
}

async function doXmlImport() {
  if (!xmlData.value) return
  xmlLoading.value = true
  try {
    const res = await importXmlSettings(xmlData.value)
    ElMessage.success(`Imported ${res.data.count} XML settings`)
  } catch (e) {
    ElMessage.error(e.response?.data?.error || 'XML import failed')
  } finally {
    xmlLoading.value = false
  }
}
</script>

<style scoped>
.page-title { font-size: 20px; font-weight: 600; color: #1a237e; margin-bottom: 20px; }
</style>
