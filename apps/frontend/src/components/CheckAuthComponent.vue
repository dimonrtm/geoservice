<template>
  <div>
    <button type="button" @click="loginViewer">Login(Viewer)</button>
    <button type="button" @click="loginEditor">Login(Editor)</button>
    <button type="button" @click="secureGet">Secure GET</button>
    <button type="button" @click="securePost">Secure POST</button>
    <div style="white-space: pre-wrap">{{ labelText }}</div>
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
