<template>
  <div class="loginScreen">
    <div class="loginCard">
      <div class="eyebrow">Геосервис</div>
      <h1 class="title">Вход</h1>
      <p class="subtitle">
        Введите электронную почту и пароль, чтобы открыть карту.
      </p>

      <form class="form" @submit.prevent="onSubmit">
        <label class="field">
          <span class="label">Электронная почта</span>
          <input
            v-model.trim="email"
            class="input"
            type="email"
            autocomplete="username"
            required
          />
        </label>

        <label class="field">
          <span class="label">Пароль</span>
          <input
            v-model="password"
            class="input"
            type="password"
            autocomplete="current-password"
            required
          />
        </label>

        <p v-if="errorMessage" class="errorMessage">{{ errorMessage }}</p>

        <button class="submitButton" type="submit" :disabled="isSubmitting">
          {{ isSubmitting ? "Выполняем вход..." : "Войти" }}
        </button>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import axios from "axios";
import { ref } from "vue";

import { useAuthStore } from "@/stores/auth";

const auth = useAuthStore();
const email = ref("");
const password = ref("");
const isSubmitting = ref(false);
const errorMessage = ref("");

async function onSubmit() {
  errorMessage.value = "";
  isSubmitting.value = true;

  try {
    await auth.loginWithPassword(email.value, password.value);
  } catch (error: unknown) {
    if (axios.isAxiosError(error)) {
      const status = error.response?.status;
      const detail =
        typeof error.response?.data?.detail === "string"
          ? error.response.data.detail
          : "";

      if (status === 401 && detail) {
        errorMessage.value = detail;
      } else {
        errorMessage.value =
          "Сейчас не удалось выполнить вход. Попробуйте ещё раз.";
      }
    } else {
      errorMessage.value =
        "Сейчас не удалось выполнить вход. Попробуйте ещё раз.";
    }
  } finally {
    isSubmitting.value = false;
  }
}
</script>

<style scoped>
.loginScreen {
  min-height: 100%;
  display: grid;
  place-items: center;
  padding: 24px;
  background:
    radial-gradient(circle at top, rgba(34, 197, 94, 0.14), transparent 32%),
    linear-gradient(180deg, #f6f8fb 0%, #e9eef5 100%);
}

.loginCard {
  width: min(100%, 380px);
  display: grid;
  gap: 16px;
  padding: 28px;
  border: 1px solid rgba(15, 23, 42, 0.08);
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.96);
  box-shadow: 0 20px 50px rgba(15, 23, 42, 0.12);
}

.eyebrow {
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: #166534;
}

.title {
  margin: 0;
  font-size: 30px;
  line-height: 1;
  color: #0f172a;
}

.subtitle {
  margin: 0;
  font-size: 14px;
  line-height: 1.5;
  color: #475569;
}

.form {
  display: grid;
  gap: 14px;
}

.field {
  display: grid;
  gap: 6px;
}

.label {
  font-size: 13px;
  font-weight: 600;
  color: #0f172a;
}

.input {
  width: 100%;
  padding: 11px 12px;
  border: 1px solid rgba(15, 23, 42, 0.16);
  border-radius: 12px;
  font: inherit;
  color: #0f172a;
  background: #fff;
}

.input:focus-visible {
  outline: 2px solid rgba(34, 197, 94, 0.35);
  outline-offset: 1px;
  border-color: rgba(22, 101, 52, 0.35);
}

.errorMessage {
  margin: 0;
  padding: 10px 12px;
  border-radius: 12px;
  font-size: 13px;
  line-height: 1.4;
  color: #991b1b;
  background: rgba(254, 226, 226, 0.92);
}

.submitButton {
  border: 0;
  border-radius: 12px;
  padding: 12px 14px;
  font: inherit;
  font-weight: 700;
  color: #fff;
  background: linear-gradient(135deg, #166534 0%, #15803d 100%);
  cursor: pointer;
}

.submitButton:disabled {
  cursor: wait;
  opacity: 0.7;
}
</style>
