<template>
  <div>
    <div class="page-header">
      <h2 class="page-title">Posts</h2>
      <el-button type="primary" @click="$router.push('/posts/new')">
        <el-icon><Plus /></el-icon> New Post
      </el-button>
    </div>

    <el-card shadow="never">
      <div class="toolbar">
        <el-input
          v-model="searchQuery"
          placeholder="Search posts..."
          prefix-icon="Search"
          style="width:260px"
          clearable
          @keyup.enter="fetchPosts"
          @clear="fetchPosts"
        />
        <el-select v-model="filterStatus" placeholder="Status" clearable style="width:140px" @change="fetchPosts">
          <el-option label="All" value="" />
          <el-option label="Published" value="published" />
          <el-option label="Draft" value="draft" />
        </el-select>
        <el-button @click="fetchPosts" :loading="loading">Search</el-button>
      </div>

      <el-table :data="posts" v-loading="loading" style="width:100%;margin-top:16px">
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column label="Title">
          <template #default="{ row }">
            <el-link @click="editPost(row.id)">{{ row.title }}</el-link>
          </template>
        </el-table-column>
        <el-table-column prop="author_name" label="Author" width="120" />
        <el-table-column prop="category" label="Category" width="120" />
        <el-table-column prop="status" label="Status" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === 'published' ? 'success' : 'info'" size="small">
              {{ row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="Created" width="160" />
        <el-table-column label="Actions" width="140">
          <template #default="{ row }">
            <el-button size="small" type="primary" link @click="editPost(row.id)">Edit</el-button>
            <el-button size="small" type="danger" link @click="confirmDelete(row)">Delete</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div style="margin-top:16px;text-align:right">
        <el-pagination
          v-model:current-page="page"
          :page-size="perPage"
          :total="total"
          layout="total, prev, pager, next"
          @current-change="fetchPosts"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessageBox, ElMessage } from 'element-plus'
import { getPosts, deletePost } from '@/api'

const router = useRouter()
const posts = ref([])
const loading = ref(false)
const searchQuery = ref('')
const filterStatus = ref('')
const page = ref(1)
const perPage = ref(10)
const total = ref(0)

async function fetchPosts() {
  loading.value = true
  try {
    const res = await getPosts({
      search: searchQuery.value,
      status: filterStatus.value,
      page: page.value,
      per_page: perPage.value,
    })
    posts.value = res.data.posts
    total.value = res.data.total
  } finally {
    loading.value = false
  }
}

function editPost(id) {
  router.push(`/posts/${id}/edit`)
}

async function confirmDelete(row) {
  await ElMessageBox.confirm(`Delete "${row.title}"?`, 'Confirm', { type: 'warning' })
  await deletePost(row.id)
  ElMessage.success('Post deleted')
  fetchPosts()
}

onMounted(fetchPosts)
</script>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.page-title { font-size: 20px; font-weight: 600; color: #1a237e; }
.toolbar { display: flex; gap: 12px; }
</style>
