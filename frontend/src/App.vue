<script setup>
import { ref, onMounted } from 'vue'
import TtsForm from './components/TtsForm.vue'
import HistoryList from './components/HistoryList.vue'
import { fetchStatus, generateSpeech } from './api.js'

const status = ref(null)
const statusError = ref('')
const generating = ref(false)
const errorMsg = ref('')
const history = ref([])
let counter = 0

onMounted(async () => {
  try {
    status.value = await fetchStatus()
  } catch {
    statusError.value = '백엔드에 연결할 수 없습니다. (uvicorn 실행을 확인하세요)'
  }
})

async function handleGenerate({ text, language }) {
  errorMsg.value = ''
  generating.value = true
  try {
    const { filename } = await generateSpeech(text, language)
    history.value.unshift({
      id: ++counter,
      text,
      languageLabel: status.value?.languages?.[language] ?? language,
      filename,
      createdAt: new Date(),
    })
    // 모델이 전환됐을 수 있으므로 상태 갱신
    fetchStatus().then((s) => (status.value = s)).catch(() => {})
  } catch (e) {
    errorMsg.value = e.message
  } finally {
    generating.value = false
  }
}
</script>

<template>
  <div class="min-h-screen bg-gradient-to-br from-indigo-500 to-purple-600 p-5">
    <div class="mx-auto max-w-xl rounded-2xl bg-white p-8 shadow-2xl">
      <h1 class="text-center text-3xl font-bold text-slate-800">🎤 Tiny TTS</h1>
      <p class="mb-6 text-center text-sm text-slate-400">Text-to-Speech</p>

      <div
        v-if="statusError"
        class="mb-4 rounded-lg bg-red-50 p-3 text-sm text-red-600"
      >
        {{ statusError }}
      </div>

      <div
        v-if="status"
        class="mb-5 rounded-lg border-l-4 border-indigo-500 bg-indigo-50 p-3 text-sm text-slate-600"
      >
        <p>
          <strong>디바이스:</strong> {{ status.device }}
          <span v-if="status.gpu_name">({{ status.gpu_name }})</span>
        </p>
        <p><strong>모델:</strong> {{ status.model_name }}</p>
      </div>

      <TtsForm
        v-if="status"
        :languages="status.languages"
        :disabled="generating"
        @generate="handleGenerate"
      />

      <div
        v-if="errorMsg"
        class="mt-4 rounded-lg bg-red-50 p-3 text-sm text-red-600"
      >
        ❌ {{ errorMsg }}
      </div>

      <div class="mt-6">
        <HistoryList :items="history" />
      </div>
    </div>
  </div>
</template>
