<template>
  <div>
    <h2 class="page-title">Dashboard</h2>

    <el-row :gutter="20" style="margin-bottom:24px">
      <el-col :span="6" v-for="stat in stats" :key="stat.label">
        <el-card class="stat-card" shadow="never">
          <div class="stat-inner">
            <div class="stat-icon" :style="{ background: stat.color }">
              <el-icon :size="24"><component :is="stat.icon" /></el-icon>
            </div>
            <div>
              <div class="stat-value">{{ stat.value }}</div>
              <div class="stat-label">{{ stat.label }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20">
      <el-col :span="16">
        <el-card shadow="never">
          <template #header>
            <span>Recent Posts</span>
            <el-button type="primary" size="small" link @click="$router.push('/posts/new')" style="float:right">
              New Post
            </el-button>
          </template>
          <el-table :data="recentPosts" size="small" style="width:100%">
            <el-table-column prop="title" label="Title" />
            <el-table-column prop="author_name" label="Author" width="120" />
            <el-table-column prop="status" label="Status" width="100">
              <template #default="{ row }">
                <el-tag :type="row.status === 'published' ? 'success' : 'info'" size="small">
                  {{ row.status }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="created_at" label="Date" width="160" />
          </el-table>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="never">
          <template #header>Quick Info</template>
          <div class="info-item">
            <span>Logged in as</span>
            <strong>{{ auth.currentUser?.username }}</strong>
          </div>
          <div class="info-item">
            <span>Role</span>
            <el-tag size="small">{{ auth.currentUser?.role }}</el-tag>
          </div>
          <div class="info-item">
            <span>Last login</span>
            <span>{{ auth.currentUser?.last_login || 'N/A' }}</span>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useAuthStore } from '@/store/auth'
import { getPosts, getUsers, getMedia } from '@/api'

const auth = useAuthStore()
const recentPosts = ref([])
const stats = ref([
  { label: 'Posts', value: 0, icon: 'Document', color: '#1a237e' },
  { label: 'Users', value: 0, icon: 'UserFilled', color: '#00897b' },
  { label: 'Media Files', value: 0, icon: 'PictureFilled', color: '#e65100' },
  { label: 'Published', value: 0, icon: 'Check', color: '#2e7d32' },
])

onMounted(async () => {
  try {
    const [postsRes, usersRes, mediaRes, publishedRes] = await Promise.allSettled([
      getPosts({ per_page: 5 }),
      getUsers(),
      getMedia(),
      getPosts({ status: 'published', per_page: 1 }),
    ])
    if (postsRes.status === 'fulfilled') {
      recentPosts.value = postsRes.value.data.posts
      stats.value[0].value = postsRes.value.data.total
    }
    if (usersRes.status === 'fulfilled') stats.value[1].value = usersRes.value.data.length
    if (mediaRes.status === 'fulfilled') stats.value[2].value = mediaRes.value.data.length
    if (publishedRes.status === 'fulfilled') stats.value[3].value = publishedRes.value.data.total
  } catch {}
})
</script>

<style scoped>
.page-title { font-size: 20px; font-weight: 600; margin-bottom: 20px; color: #1a237e; }
.stat-card { border-radius: 10px; }
.stat-inner { display: flex; align-items: center; gap: 16px; }
.stat-icon {
  width: 52px; height: 52px; border-radius: 10px; display: flex;
  align-items: center; justify-content: center; color: #fff;
}
.stat-value { font-size: 26px; font-weight: 700; color: #1a237e; }
.stat-label { font-size: 13px; color: #888; }
.info-item { display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #f0f2f5; font-size: 14px; }
</style>
