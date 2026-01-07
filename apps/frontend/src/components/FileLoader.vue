<template>
  <div>
    <input
      type="file"
      accept=".geojson,.json,application/geo+json"
      @change="onFileChange"
    />
    <div style="white-space: pre-wrap">{{ labelText }}</div>
    <button
      type="button"
      @click="uploadTo"
      :disabled="!selectedFile || isUploading"
    >
      Отправить
    </button>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
const selectedFile = ref<File | null>(null);
const labelText = ref("Файл не выбран");
const fileInput = ref<HTMLInputElement | null>(null);
const isUploading = ref(false);

async function onFileChange(e: Event) {
  const input = e.currentTarget as HTMLInputElement;
  const file = input.files?.[0] ?? null;
  if (!file) {
    resetSelection("Файл не выбран");
    return;
  }
  const maxFileSize = 20 * 1024 * 1024;
  if (file.size > maxFileSize) {
    resetSelection("Файл слишком большой");
    return;
  }
  selectedFile.value = file;
  const sizeKb = Math.ceil(file.size / 1024);

  const name = file.name.toLowerCase();
  if (!name.endsWith(".geojson") && !name.endsWith(".json")) {
    resetSelection("Файл должен быть либо GeoJson либо Json");
    return;
  }

  labelText.value = "Проверяю GeoJson...";
  const chunk = (await file.text()).slice(0, 2000).toLowerCase();

  if (
    !chunk.includes("type") ||
    (!chunk.includes("feature") && !chunk.includes("featurecollection"))
  ) {
    resetSelection("Файл не похож на GeoJson");
    return;
  }

  labelText.value = `OK: ${file.name} - ${sizeKb} KB`;
}

async function uploadTo() {
  console.log("upload", selectedFile.value?.name);
  if (!selectedFile.value) {
    resetSelection("Файл не найден");
    return;
  }
  isUploading.value = true;
  let timeoutId: ReturnType<typeof setTimeout> | null = null;
  try {
    const fd = new FormData();
    fd.append("file", selectedFile.value);
    fd.append("srid", "4326");
    const controller = new AbortController();
    timeoutId = setTimeout(() => controller.abort(), 15000);
    const res = await fetch("http://localhost:8000/api/geojson/import", {
      method: "POST",
      body: fd,
      signal: controller.signal,
    });
    if (!res.ok) {
      try {
        const jsonError = await res.json();
        const detail =
          typeof jsonError?.detail === "string"
            ? jsonError.detail
            : JSON.stringify(jsonError);
        labelText.value = `Ошибка: ${detail}`;
      } catch {
        const errorText = await res.text();
        labelText.value = `Ошибка: ${errorText}`;
      }
      return;
    }
    const data = await res.json();
    const idsText = Array.isArray(data.ids)
      ? data.ids.join(", ")
      : String(data.ids);
    labelText.value =
      "Файл успешно загружен\n" +
      "Название файла\t Количество отправленных объектов\t Количество сохраненных объектов\t Id объектов\n" +
      `${data.filename}\t${data.inputCount}\t${data.savedCount}\t${idsText}`;
  } catch (err) {
    if (err instanceof DOMException && err.name === "AbortError") {
      labelText.value = "Таймаут запроса";
    } else {
      labelText.value = "Ошибка сети";
    }
    console.log(err);
  } finally {
    isUploading.value = false;
    if (timeoutId !== null) {
      clearTimeout(timeoutId);
      timeoutId = null;
    }
  }
}

function resetSelection(reason: string) {
  selectedFile.value = null;
  labelText.value = reason;
  if (fileInput.value) {
    fileInput.value.value = "";
  }
}
</script>
