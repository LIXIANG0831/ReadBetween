<template>
  <div ref="editorContainer" class="editor-container"></div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, defineProps, defineEmits } from 'vue'
import * as monaco from 'monaco-editor'

const props = defineProps<{
  modelValue: string
  language?: string
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: string): void
}>()

const editorContainer = ref<HTMLElement | null>(null)
let editor: monaco.editor.IStandaloneCodeEditor | null = null

const initEditor = () => {
  if (!editorContainer.value) return

  editor = monaco.editor.create(editorContainer.value, {
    value: props.modelValue,
    language: props.language || 'json',
    theme: 'vs-dark',
    automaticLayout: true,
    scrollBeyondLastLine: false,
    fontSize: 14,
    minimap: { enabled: false },
    formatOnPaste: true,
    formatOnType: true,
  })

  editor.onDidChangeModelContent(() => {
    const value = editor?.getValue()
    emit('update:modelValue', value || '')
  })
}

onMounted(() => {
  initEditor()
})

watch(
  () => props.modelValue,
  (newVal) => {
    if (editor && editor.getValue() !== newVal) {
      editor.setValue(newVal)
    }
  }
)
</script>

<style scoped>
.editor-container {
  width: 100%;
  height: 500px; /* 设置你需要的高度 */
  border: 1px solid #ddd;
  border-radius: 8px; /* 设置圆角 */
}
</style>

<!-- 全局样式或额外的样式标签 -->
<style>
.monaco-editor .monaco-editor-background,
.monaco-editor .monaco-editor .lines-content {
  border-radius: 8px !important; /* 确保使用足够的优先级 */
}
</style>