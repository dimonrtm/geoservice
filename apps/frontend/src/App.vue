<script setup lang="ts">
import { computed, onMounted } from "vue";

import LoginScreen from "./components/LoginScreen.vue";
import MapPageView from "./components/MapPageView.vue";
import { useAuthStore } from "@/stores/auth";
import "./assets/main.css";

const auth = useAuthStore();

const userLabel = computed(() => {
  if (!auth.user) {
    return "";
  }

  const roleLabel = auth.user.role === "editor" ? "Редактор" : "Наблюдатель";

  return `${auth.user.email} (${roleLabel})`;
});

onMounted(() => {
  if (!auth.isReady && !auth.isRestoring) {
    void auth.restoreSession();
  }
});
</script>

<template>
  <div class="page">
    <div v-if="!auth.isReady" class="statusScreen">
      <div class="statusCard">
        <div class="statusTitle">Восстановление сессии</div>
        <div class="statusText">
          Проверяем текущий вход перед загрузкой карты.
        </div>
      </div>
    </div>

    <div v-else-if="auth.sessionError" class="statusScreen">
      <div class="statusCard">
        <div class="statusTitle">Не удалось восстановить сессию</div>
        <div class="statusText">{{ auth.sessionError }}</div>
        <div class="statusActions">
          <button
            class="btn btnPrimary"
            type="button"
            @click="auth.restoreSession"
          >
            Повторить
          </button>
          <button class="btn btnSecondary" type="button" @click="auth.logout">
            Выйти
          </button>
        </div>
      </div>
    </div>

    <div v-else-if="auth.isAuthenticated" class="authedPage">
      <div class="topBar">
        <div class="identityBlock">
          <div class="identityLabel">Выполнен вход</div>
          <div class="identityValue">{{ userLabel }}</div>
        </div>
        <button class="btn btnSecondary" type="button" @click="auth.logout">
          Выйти
        </button>
      </div>

      <div class="content">
        <MapPageView class="mapSlot" />
      </div>
    </div>

    <div v-else class="content authContent">
      <LoginScreen />
    </div>
  </div>
</template>

<style scoped>
.page {
  height: 100%;
  width: 100%;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.authedPage {
  flex: 1 1 auto;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.topBar {
  flex: 0 0 auto;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 12px 16px;
  border-bottom: 1px solid rgba(15, 23, 42, 0.08);
  background: rgba(255, 255, 255, 0.96);
}

.identityBlock {
  display: grid;
  gap: 2px;
  min-width: 0;
}

.identityLabel {
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: #64748b;
}

.identityValue {
  font-size: 14px;
  font-weight: 600;
  color: #0f172a;
  word-break: break-word;
}

.content {
  flex: 1 1 auto;
  min-height: 0;
  position: relative;
  overflow: hidden;
}

.authContent {
  background: #f6f8fb;
}

.mapSlot {
  height: 100%;
  width: 100%;
  min-height: 0;
}

.statusScreen {
  flex: 1 1 auto;
  display: grid;
  place-items: center;
  padding: 24px;
  background: linear-gradient(180deg, #f8fafc 0%, #eef2f7 100%);
}

.statusCard {
  width: min(100%, 420px);
  display: grid;
  gap: 12px;
  padding: 24px;
  border: 1px solid rgba(15, 23, 42, 0.08);
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.96);
  box-shadow: 0 20px 40px rgba(15, 23, 42, 0.1);
}

.statusTitle {
  font-size: 24px;
  font-weight: 700;
  color: #0f172a;
}

.statusText {
  font-size: 14px;
  line-height: 1.5;
  color: #475569;
}

.statusActions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.btn {
  border: 1px solid transparent;
  border-radius: 12px;
  padding: 10px 14px;
  font: inherit;
  font-weight: 600;
  cursor: pointer;
}

.btnPrimary {
  color: #fff;
  background: #166534;
  border-color: #166534;
}

.btnSecondary {
  color: #0f172a;
  background: #fff;
  border-color: rgba(15, 23, 42, 0.14);
}
</style>
