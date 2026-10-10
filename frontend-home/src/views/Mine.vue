<template>
  <div>
    <van-nav-bar title="我的" />

    <!-- 用户卡片 -->
    <div class="user-card">
      <van-icon name="user-circle-o" size="56" color="#1989fa" />
      <div class="info">
        <div class="name">{{ userInfo?.real_name || userInfo?.username || '未登录' }}</div>
        <div class="sub">{{ userInfo?.phone || '' }}</div>
      </div>
    </div>

    <van-cell-group inset>
      <van-cell title="修改密码" is-link @click="showPwd = true" />
      <van-cell title="牧场信息" is-link @click="loadFarm" />
      <van-cell title="版本" value="v0.1.0" />
    </van-cell-group>

    <div class="logout">
      <van-button round block plain type="danger" @click="handleLogout">退出登录</van-button>
    </div>

    <!-- 修改密码 -->
    <van-dialog v-model:show="showPwd" title="修改密码" show-cancel-button
                @confirm="submitPwd">
      <div style="padding: 16px">
        <van-field v-model="pwd.old_password" type="password" label="旧密码" />
        <van-field v-model="pwd.new_password" type="password" label="新密码"
                   placeholder="至少6位" />
      </div>
    </van-dialog>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { showToast } from 'vant'
import { getUserInfo, changePassword, logout } from '../api/auth'
import { getFarmInfo } from '../api/farm'

const router = useRouter()
const userInfo = ref(null)
const showPwd = ref(false)
const pwd = reactive({ old_password: '', new_password: '' })

async function loadUser() {
  try {
    userInfo.value = await getUserInfo()
  } catch (e) { /* token 失效时跳登录 */ }
}

async function loadFarm() {
  try {
    const farm = await getFarmInfo({ farm_id: localStorage.getItem('farmId') || 1 })
    showToast(`${farm.name}：牛 ${farm.cattle_count} 头，羊 ${farm.sheep_count} 只`)
  } catch (e) { /* 后端未开放时静默 */ }
}

async function submitPwd() {
  if (!pwd.old_password || pwd.new_password.length < 6) {
    showToast('请填写完整，新密码至少6位')
    return
  }
  await changePassword(pwd)
  showToast('密码已修改，请重新登录')
  handleLogout()
}

async function handleLogout() {
  try {
    await logout()
  } finally {
    localStorage.removeItem('token')
    localStorage.removeItem('username')
    router.push('/login')
  }
}

onMounted(loadUser)
</script>

<style scoped>
.user-card { display: flex; align-items: center; gap: 14px;
             background: #fff; padding: 20px 16px; margin-bottom: 12px; }
.name { font-size: 18px; font-weight: bold; }
.sub { color: #969799; font-size: 13px; margin-top: 2px; }
.logout { margin: 32px 16px; }
</style>
