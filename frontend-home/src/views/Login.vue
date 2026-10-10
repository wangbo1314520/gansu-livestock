<template>
  <div class="login">
    <div class="logo">🐂🐑</div>
    <h2 class="title">牛羊行情</h2>
    <p class="sub">家里人的价格参谋</p>

    <van-form @submit="handleLogin">
      <van-cell-group inset>
        <van-field v-model="form.username" label="用户名" placeholder="家庭账号"
                   :rules="[{ required: true, message: '请输入用户名' }]" />
        <van-field v-model="form.password" type="password" label="密码" placeholder="密码"
                   :rules="[{ required: true, message: '请输入密码' }]" />
      </van-cell-group>
      <div class="btn-wrap">
        <van-button round block type="primary" native-type="submit" :loading="loading">
          登录
        </van-button>
      </div>
    </van-form>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { showToast } from 'vant'
import { login } from '../api/auth'

const router = useRouter()
const loading = ref(false)
const form = reactive({ username: '', password: '' })

async function handleLogin() {
  loading.value = true
  try {
    const data = await login(form)
    localStorage.setItem('token', data.token)
    localStorage.setItem('username', data.user.username)
    showToast('欢迎回来')
    router.push('/')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login { padding-top: 18vh; }
.logo { text-align: center; font-size: 56px; }
.title { text-align: center; margin: 8px 0 0; }
.sub { text-align: center; color: #969799; margin: 4px 0 32px; }
.btn-wrap { margin: 24px 16px; }
</style>
