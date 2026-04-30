<template>
  <div>
    <div class="page-header">
      <h2 class="page-title">User Management</h2>
      <el-button type="primary" @click="openCreateDialog">
        <el-icon><Plus /></el-icon> Add User
      </el-button>
    </div>

    <el-card shadow="never">
      <el-table :data="users" v-loading="loading" style="width:100%">
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column label="User">
          <template #default="{ row }">
            <div style="display:flex;align-items:center;gap:8px">
              <el-avatar size="small" :style="{ background: '#1a237e' }">
                {{ row.username[0].toUpperCase() }}
              </el-avatar>
              <div>
                <div style="font-weight:500">{{ row.username }}</div>
                <div style="font-size:12px;color:#888">{{ row.email }}</div>
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="role" label="Role" width="100">
          <template #default="{ row }">
            <el-tag :type="row.role === 'admin' ? 'danger' : 'primary'" size="small">
              {{ row.role }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="last_login" label="Last Login" width="160" />
        <el-table-column prop="created_at" label="Joined" width="160" />
        <el-table-column label="Actions" width="160">
          <template #default="{ row }">
            <el-button size="small" link type="primary" @click="openEdit(row)">Edit</el-button>
            <el-button size="small" link type="danger" @click="confirmDelete(row)">Delete</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- Edit / Create dialog -->
    <el-dialog v-model="dialogVisible" :title="editing ? 'Edit User' : 'New User'" width="440px">
      <el-form :model="form" label-width="80px" size="default">
        <el-form-item label="Username">
          <el-input v-model="form.username" :disabled="editing" />
        </el-form-item>
        <el-form-item label="Email">
          <el-input v-model="form.email" />
        </el-form-item>
        <el-form-item label="Password">
          <el-input v-model="form.password" type="password" :placeholder="editing ? 'Leave blank to keep' : ''" show-password />
        </el-form-item>
        <el-form-item label="Role">
          <el-select v-model="form.role" style="width:100%">
            <el-option label="Subscriber" value="subscriber" />
            <el-option label="Editor" value="editor" />
            <el-option label="Admin" value="admin" />
          </el-select>
        </el-form-item>
        <el-form-item label="Bio">
          <el-input v-model="form.bio" type="textarea" :rows="3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">Cancel</el-button>
        <el-button type="primary" :loading="saving" @click="submitForm">Save</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getUsers, updateUser, deleteUser } from '@/api'
import api from '@/api'

const users = ref([])
const loading = ref(false)
const saving = ref(false)
const dialogVisible = ref(false)
const editing = ref(false)
const editingId = ref(null)

const form = reactive({ username: '', email: '', password: '', role: 'editor', bio: '' })

async function fetchUsers() {
  loading.value = true
  try {
    const res = await getUsers()
    users.value = res.data
  } finally {
    loading.value = false
  }
}

function openEdit(row) {
  editing.value = true
  editingId.value = row.id
  Object.assign(form, { username: row.username, email: row.email, password: '', role: row.role, bio: row.bio || '' })
  dialogVisible.value = true
}

function openCreateDialog() {
  editing.value = false
  editingId.value = null
  Object.assign(form, { username: '', email: '', password: '', role: 'editor', bio: '' })
  dialogVisible.value = true
}

async function submitForm() {
  saving.value = true
  try {
    const payload = { ...form }
    if (!payload.password) delete payload.password
    if (editing.value) {
      await updateUser(editingId.value, payload)
      ElMessage.success('User updated')
    } else {
      await api.post('/auth/register', payload)
      ElMessage.success('User created')
    }
    dialogVisible.value = false
    fetchUsers()
  } catch (e) {
    ElMessage.error(e.response?.data?.error || 'Operation failed')
  } finally {
    saving.value = false
  }
}

async function confirmDelete(row) {
  await ElMessageBox.confirm(`Delete user "${row.username}"?`, 'Confirm', { type: 'warning' })
  await deleteUser(row.id)
  ElMessage.success('User deleted')
  fetchUsers()
}

onMounted(fetchUsers)
</script>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.page-title { font-size: 20px; font-weight: 600; color: #1a237e; }
</style>
