<script setup>
import { audioUrl } from '../api.js'

defineProps({
  items: { type: Array, required: true },
})

function formatTime(d) {
  return new Date(d).toLocaleTimeString('ko-KR')
}
</script>

<template>
  <div v-if="items.length" class="space-y-3">
    <h2 class="font-semibold text-slate-700">생성 이력</h2>
    <div
      v-for="item in items"
      :key="item.id"
      class="rounded-lg border border-slate-200 bg-slate-50 p-3"
    >
      <div class="mb-2 flex items-center justify-between text-sm">
        <span class="rounded bg-indigo-100 px-2 py-0.5 text-indigo-700">
          {{ item.languageLabel }}
        </span>
        <span class="text-slate-400">{{ formatTime(item.createdAt) }}</span>
      </div>
      <p class="mb-2 break-words text-slate-700">{{ item.text }}</p>
      <audio :src="audioUrl(item.filename)" controls class="w-full"></audio>
      <a
        :href="audioUrl(item.filename)"
        :download="item.filename"
        class="mt-1 inline-block text-sm text-indigo-600 hover:underline"
      >
        ⬇ 다운로드
      </a>
    </div>
  </div>
</template>
