<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  languages: { type: Object, required: true },
  disabled: { type: Boolean, default: false },
})
const emit = defineEmits(['generate'])

const MAX = 500
const text = ref('')
const language = ref(Object.keys(props.languages)[0])

const remaining = computed(() => MAX - text.value.length)
const canSubmit = computed(() => text.value.trim().length > 0 && !props.disabled)

function submit() {
  if (!canSubmit.value) return
  emit('generate', { text: text.value.trim(), language: language.value })
}
</script>

<template>
  <form class="space-y-4" @submit.prevent="submit">
    <div>
      <label class="mb-1 block font-semibold text-slate-700">언어</label>
      <select
        v-model="language"
        :disabled="disabled"
        class="w-full rounded-lg border-2 border-slate-200 p-3 focus:border-indigo-500 focus:outline-none"
      >
        <option v-for="(label, model) in languages" :key="model" :value="model">
          {{ label }}
        </option>
      </select>
    </div>

    <div>
      <label class="mb-1 block font-semibold text-slate-700">변환할 텍스트</label>
      <textarea
        v-model="text"
        :maxlength="MAX"
        :disabled="disabled"
        rows="5"
        placeholder="여기에 텍스트를 입력하세요..."
        class="w-full resize-y rounded-lg border-2 border-slate-200 p-3 focus:border-indigo-500 focus:outline-none"
      ></textarea>
      <p class="mt-1 text-right text-sm text-slate-400">{{ remaining }}자 남음</p>
    </div>

    <button
      type="submit"
      :disabled="!canSubmit"
      class="w-full rounded-lg bg-indigo-600 py-3 font-semibold text-white transition hover:bg-indigo-700 disabled:cursor-not-allowed disabled:bg-slate-300"
    >
      {{ disabled ? '음성 생성 중...' : '🎵 음성 생성' }}
    </button>
  </form>
</template>
