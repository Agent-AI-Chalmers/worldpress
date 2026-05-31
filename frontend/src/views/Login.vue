<template>
  <div class="login-page">
    <div class="login-box">
      <div class="brand">
        <span class="logo">W</span>
        <h1>WorldPress</h1>
        <p>Content Management System</p>
      </div>

      <el-form :model="form" @submit.prevent="handleLogin" size="large">
        <el-form-item>
          <el-input
            v-model="form.username"
            placeholder="Username"
            prefix-icon="User"
            autocomplete="username"
          />
        </el-form-item>
        <el-form-item>
          <el-input
            v-model="form.password"
            type="password"
            placeholder="Password"
            prefix-icon="Lock"
            show-password
            autocomplete="current-password"
            @keyup.enter="handleLogin"
          />
        </el-form-item>
        <el-form-item>
          <el-button
            type="primary"
            native-type="submit"
            :loading="auth.loading"
            style="width: 100%"
          >
            Sign In
          </el-button>
        </el-form-item>
      </el-form>

      <el-alert v-if="error" :title="error" type="error" :closable="false" style="margin-top:8px" />
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/store/auth'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()

const form = reactive({ username: '', password: '' })
const error = ref('')

async function handleLogin() {
  error.value = ''
  const redirect = route.query.redirect || ''
  try {
    const data = await auth.login(form, redirect)
    // Use the redirect value returned by the server (now validated to be a safe relative path)
    router.push(data.redirect || '/dashboard')
  } catch (e) {
    error.value = e.response?.data?.error || 'Login failed'
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #1a237e 0%, #283593 100%);
}
.login-box {
  background: #fff;
  padding: 40px;
  border-radius: 12px;
  width: 380px;
  box-shadow: 0 20px 60px rgba(0,0,0,.3);
}
.brand { text-align: center; margin-bottom: 32px; }
.logo {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 56px;
  height: 56px;
  background: #1a237e;
  color: #fff;
  font-size: 28px;
  font-weight: 700;
  border-radius: 12px;
  margin-bottom: 12px;
}
.brand h1 { font-size: 22px; color: #1a237e; margin-bottom: 4px; }
.brand p { color: #888; font-size: 13px; }
</style>
