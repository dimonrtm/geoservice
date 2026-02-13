<template>
  <div class="authCard">
    <div class="header">
      <div class="title">Auth Dev Panel</div>
      <div class="subtitle">Быстрые проверки JWT/ Ролей</div>
    </div>

    <div class="controls">
      <button type="button" class="btn btnSecondary" @click="loginViewer">
        Login(Viewer)
      </button>
      <button type="button" class="btn btnPrimary" @click="loginEditor">
        Login(Editor)
      </button>
      <button type="button" class="btn btnGhost" @click="secureGet">
        Secure GET
      </button>
      <button type="button" class="btn btnGhost" @click="securePost">
        Secure POST
      </button>
    </div>

    <div class="output" aria-live="polite">
      <div class="outputLabel">Вывод</div>
      <pre class="outputText">{{ labelText || "—" }}</pre>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { devLogin, secureGetRequest, securePostRequest } from "@/api/auth";
import axios, { AxiosError, type AxiosResponse } from "axios";

type ApiErrorBody = { detail?: string };
type SecureGetOkBody = { user_id: string; role: string };
type SecurePostOkBody = { write: boolean; user_id: string; role: string };
const labelText = ref("");

async function loginViewer() {
  const response = await devLogin("g@gmail.com", "viewer");
  labelText.value = `Access Token: ${response.data.access_token}`;
}

async function loginEditor() {
  const response = await devLogin("d@gmail.com", "editor");
  labelText.value = `Access Token: ${response.data.access_token}`;
}

async function secureGet() {
  try {
    const response: AxiosResponse<SecureGetOkBody> = await secureGetRequest();
    if (response.status >= 200 && response.status <= 300) {
      labelText.value = `UserId: ${response.data.user_id}; Role: ${response.data.role}`;
      return;
    }
    labelText.value = `Неожиданный статус ${response.status}`;
  } catch (e: unknown) {
    onFailedAuth(e);
  }
}

async function securePost() {
  try {
    const response: AxiosResponse<SecurePostOkBody> = await securePostRequest();
    if (response.status >= 200 && response.status <= 300) {
      labelText.value = `Write ${response.data.write}; UserId: ${response.data.user_id}; Role: ${response.data.role}`;
      return;
    }
    labelText.value = `Неожиданный статус ${response.status}`;
  } catch (e: unknown) {
    onFailedAuth(e);
  }
}

function onFailedAuth(e: unknown) {
  if (axios.isAxiosError(e)) {
    const error = e as AxiosError<ApiErrorBody>;
    const status = error.response?.status;
    const detail = error.response?.data?.detail;
    if (status === 401 || status == 403) {
      labelText.value = `Ошибка: ${status} ${detail}`;
      return;
    }
    if (!status) {
      labelText.value = `Сетевая ошибка ${error.message}`;
      return;
    }

    labelText.value = `Ошибка ${status} ${detail}`;
  }
}
</script>
<style scoped>
.authCard {
  max-width: 720px;
  padding: 16px;
  border: 1px solid rgba(0, 0, 0, 0.12);
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.92);
  box-shadow: 0 6px 18px rgba(0, 0, 0, 0.08);
}
.header {
  display: grid;
  gap: 4px;
  margin-bottom: 12px;
}
.title {
  font-size: 18px;
  font-weight: 700;
  line-height: 1.2;
}
.subtitle {
  font-size: 13px;
  opacity: 0.75;
}
.controls {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-bottom: 14px;
}
.btn {
  border: 1px solid transparent;
  border-radius: 10px;
  padding: 10px 12px;
  font-size: 14px;
  line-height: 1;
  cursor: pointer;
  user-select: none;
  transition:
    transform 0.05s ease,
    box-shadow 0.15s ease,
    background 0.15s ease,
    border-color 0.15s ease,
    opacity 0.15s ease;
}
.btn:active {
  transform: translateY(1px);
}
.btn:focus-visible {
  outline: 3px solid rgba(0, 0, 0, 0.25);
  outline-offset: 2px;
}
.btnPrimary {
  background: #111827;
  color: #ffffff;
  border-color: rgba(0, 0, 0, 0.25);
  box-shadow: 0 6px 14px rgba(17, 24, 39, 0.18);
}
.btnPrimary:hover {
  opacity: 0.92;
}
.btnSecondary {
  background: #ffffff;
  color: #111827;
  border-color: rgba(17, 24, 39, 0.25);
}
.btnSecondary:hover {
  background: rgba(17, 24, 39, 0.06);
}
.btnGhost {
  background: rgba(17, 24, 39, 0.06);
  color: #111827;
  border-color: rgba(17, 24, 39, 0.12);
}
.btnGhost:hover {
  background: rgba(17, 24, 39, 0.1);
}
.output {
  border: 1px solid rgba(0, 0, 0, 0.12);
  border-radius: 12px;
  overflow: hidden;
  background: rgba(0, 0, 0, 0.04);
}
.outputLabel {
  padding: 10px 12px;
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.02em;
  opacity: 0.75;
  border-bottom: 1px solid rgba(0, 0, 0, 0.1);
  background: rgba(255, 255, 255, 0.65);
}
.outputText {
  margin: 0;
  padding: 12px;
  font-size: 13px;
  line-height: 1.35;
  white-space: pre-wrap;
  word-break: break-word;
  font-family:
    ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono",
    "Courier New", monospace;
  min-height: 84px;
  max-height: 120 px;
  overflow: auto;
}
</style>
