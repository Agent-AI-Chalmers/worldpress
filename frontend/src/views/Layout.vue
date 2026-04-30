<template>
  <el-container style="min-height:100vh">
    <el-aside :width="collapsed ? '64px' : '220px'" class="sidebar">
      <div class="sidebar-brand" @click="collapsed = !collapsed">
        <span class="brand-icon">W</span>
        <span v-if="!collapsed" class="brand-text">WorldPress</span>
      </div>
      <el-menu
        :default-active="$route.path"
        router
        :collapse="collapsed"
        background-color="#1a237e"
        text-color="#c5cae9"
        active-text-color="#fff"
      >
        <el-menu-item index="/dashboard">
          <el-icon><Odometer /></el-icon>
          <template #title>Dashboard</template>
        </el-menu-item>
        <el-menu-item index="/posts">
          <el-icon><Document /></el-icon>
          <template #title>Posts</template>
        </el-menu-item>
        <el-menu-item index="/media">
          <el-icon><PictureFilled /></el-icon>
          <template #title>Media</template>
        </el-menu-item>
        <el-menu-item v-if="auth.isAdmin" index="/users">
          <el-icon><UserFilled /></el-icon>
          <template #title>Users</template>
        </el-menu-item>
        <el-menu-item v-if="auth.isAdmin" index="/settings">
          <el-icon><Setting /></el-icon>
          <template #title>Settings</template>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <el-container>
      <el-header class="topbar">
        <div class="topbar-left">
          <el-breadcrumb separator="/">
            <el-breadcrumb-item :to="{ path: '/dashboard' }">Home</el-breadcrumb-item>
            <el-breadcrumb-item>{{ currentPageName }}</el-breadcrumb-item>
          </el-breadcrumb>
        </div>
        <div class="topbar-right">
          <el-dropdown @command="handleCommand">
            <span class="user-trigger">
              <el-avatar size="small" :style="{ background: '#1a237e' }">
                {{ (auth.currentUser?.username || 'U')[0].toUpperCase() }}
              </el-avatar>
              <span class="username">{{ auth.currentUser?.username }}</span>
              <el-icon><ArrowDown /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="profile">Profile</el-dropdown-item>
                <el-dropdown-item divided command="logout">Sign Out</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>

      <el-main>
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/store/auth'

const auth = useAuthStore()
const route = useRoute()
const router = useRouter()
const collapsed = ref(false)

const currentPageName = computed(() => {
  const map = { dashboard: 'Dashboard', posts: 'Posts', users: 'Users', media: 'Media', settings: 'Settings' }
  const seg = route.path.split('/')[1]
  return map[seg] || seg
})

async function handleCommand(cmd) {
  if (cmd === 'logout') {
    await auth.logout()
    router.push('/login')
  }
}
</script>

<style scoped>
.sidebar { background: #1a237e; transition: width .2s; overflow: hidden; }
.sidebar-brand {
  height: 60px; display: flex; align-items: center; gap: 10px;
  padding: 0 16px; cursor: pointer; border-bottom: 1px solid rgba(255,255,255,.1);
}
.brand-icon {
  width: 32px; height: 32px; background: #fff; color: #1a237e;
  border-radius: 6px; display: flex; align-items: center; justify-content: center;
  font-weight: 700; font-size: 16px; flex-shrink: 0;
}
.brand-text { color: #fff; font-weight: 600; font-size: 15px; white-space: nowrap; }
.topbar {
  background: #fff; display: flex; align-items: center;
  justify-content: space-between; box-shadow: 0 1px 4px rgba(0,0,0,.1);
}
.topbar-right { display: flex; align-items: center; gap: 16px; }
.user-trigger { display: flex; align-items: center; gap: 6px; cursor: pointer; }
.username { font-size: 14px; color: #333; }
</style>
