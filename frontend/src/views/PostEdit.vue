<template>
  <div>
    <div class="page-header">
      <h2 class="page-title">{{ isNew ? 'New Post' : 'Edit Post' }}</h2>
      <div class="header-actions">
        <el-button @click="$router.push('/posts')">Cancel</el-button>
        <el-button type="primary" :loading="saving" @click="savePost">
          {{ form.status === 'published' ? 'Update' : 'Save Draft' }}
        </el-button>
        <el-button v-if="form.status !== 'published'" type="success" :loading="saving" @click="publishPost">
          Publish
        </el-button>
      </div>
    </div>

    <el-row :gutter="20">
      <el-col :span="17">
        <el-card shadow="never" style="margin-bottom:16px">
          <el-input
            v-model="form.title"
            placeholder="Post title"
            size="large"
            style="font-size:18px;margin-bottom:16px"
          />
          <div class="editor-label">Content (HTML supported)</div>
          <el-input
            v-model="form.content"
            type="textarea"
            :rows="16"
            placeholder="Write your content here... HTML is supported."
          />
        </el-card>

        <el-card shadow="never">
          <template #header>Excerpt</template>
          <el-input v-model="form.excerpt" type="textarea" :rows="3" placeholder="Short description" />
        </el-card>
      </el-col>

      <el-col :span="7">
        <el-card shadow="never" style="margin-bottom:16px">
          <template #header>Publish</template>
          <el-form label-width="80px" size="small">
            <el-form-item label="Status">
              <el-select v-model="form.status" style="width:100%">
                <el-option label="Draft" value="draft" />
                <el-option label="Published" value="published" />
              </el-select>
            </el-form-item>
          </el-form>
        </el-card>

        <el-card shadow="never" style="margin-bottom:16px">
          <template #header>Category & Tags</template>
          <el-form label-width="80px" size="small">
            <el-form-item label="Category">
              <el-input v-model="form.category" />
            </el-form-item>
            <el-form-item label="Tags">
              <el-input v-model="form.tags" placeholder="comma separated" />
            </el-form-item>
          </el-form>
        </el-card>

        <el-card v-if="!isNew" shadow="never">
          <template #header>Comments</template>
          <el-empty v-if="!comments.length" description="No comments yet" :image-size="60" />
          <div v-for="c in comments" :key="c.id" class="comment-item">
            <div class="comment-author">{{ c.author }}</div>
            <div class="comment-body">{{ c.content }}</div>
            <div class="comment-date">{{ c.created_at }}</div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getPost, createPost, updatePost, getComments } from '@/api'

const route = useRoute()
const router = useRouter()
const saving = ref(false)
const comments = ref([])

const isNew = computed(() => !route.params.id)

const form = reactive({
  title: '',
  content: '',
  excerpt: '',
  status: 'draft',
  category: 'General',
  tags: '',
})

onMounted(async () => {
  if (!isNew.value) {
    const res = await getPost(route.params.id)
    Object.assign(form, res.data)
    const cr = await getComments(route.params.id)
    comments.value = cr.data
  }
})

async function savePost() {
  saving.value = true
  try {
    if (isNew.value) {
      const res = await createPost(form)
      ElMessage.success('Post saved')
      router.push(`/posts/${res.data.id}/edit`)
    } else {
      await updatePost(route.params.id, form)
      ElMessage.success('Post updated')
    }
  } catch (e) {
    ElMessage.error(e.response?.data?.error || 'Failed to save')
  } finally {
    saving.value = false
  }
}

async function publishPost() {
  form.status = 'published'
  await savePost()
}
</script>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.header-actions { display: flex; gap: 8px; }
.page-title { font-size: 20px; font-weight: 600; color: #1a237e; }
.editor-label { font-size: 13px; color: #888; margin-bottom: 6px; }
.comment-item { padding: 10px 0; border-bottom: 1px solid #f0f2f5; }
.comment-author { font-weight: 600; font-size: 13px; }
.comment-body { font-size: 13px; color: #555; margin: 4px 0; }
.comment-date { font-size: 11px; color: #aaa; }
</style>
