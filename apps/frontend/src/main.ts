import "maplibre-gl/dist/maplibre-gl.css";
//import maplibregl from "maplibre-gl"
import { createApp } from "vue";
import "./style.css";
import App from "./App.vue";
import { pinia } from "./pinia";
import { installEditorRuntime } from "./editor/editorRuntime";

const app = createApp(App).use(pinia);
const editorRuntime = installEditorRuntime(pinia);
app.onUnmount(() => editorRuntime.dispose());
app.mount("#app");
