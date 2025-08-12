<template>
  <div ref="editorContainer" class="editor-container"></div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, defineProps, defineEmits } from 'vue'
import * as monaco from 'monaco-editor'

const props = defineProps<{
  modelValue: string
  language?: string
  editorOptions?: monaco.editor.IStandaloneEditorConstructionOptions
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: string): void
}>()

const editorContainer = ref<HTMLElement | null>(null)
let editor: monaco.editor.IStandaloneCodeEditor | null = null

// 默认配置
const defaultOptions: monaco.editor.IStandaloneEditorConstructionOptions = {
  automaticLayout: true,
  scrollBeyondLastLine: false,
  fontSize: 14,
  minimap: { enabled: false },  // 默认关闭小地图
  lineNumbers: 'off',          // 默认关闭行号
  formatOnPaste: true,
  formatOnType: true,
  glyphMargin: false,
  folding: false,
  lineDecorationsWidth: 0,
  lineNumbersMinChars: 0,
  renderLineHighlight: 'none',
  overviewRulerBorder: false,
  hideCursorInOverviewRuler: true
}

const initEditor = () => {
  if (!editorContainer.value) return

  // 合并配置 - 用户传入的 editorOptions 会覆盖默认配置
  const options: monaco.editor.IStandaloneEditorConstructionOptions = {
    ...defaultOptions,
    language: props.language || 'plaintext',
    ...props.editorOptions,  // 用户自定义配置
    value: props.modelValue   // 确保 value 不会被覆盖
  }

  editor = monaco.editor.create(editorContainer.value, options)

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

watch(
  () => props.language,
  () => {
    if (editor) {
      const model = editor.getModel()
      if (model) {
        monaco.editor.setModelLanguage(model, props.language || 'plaintext')
      }
    }
  }
)
</script>

<style scoped>
.editor-container {
  width: 100%;
  min-width: 100px;
  max-width: 1500px;
  height: 500px;
  border: 1px solid #ddd;
  border-radius: 8px;
  margin: 0 auto;
}
</style>

<style>
.monaco-editor .monaco-editor-background,
.monaco-editor .monaco-editor .lines-content {
  border-radius: 8px !important;
  padding-left: 8px !important;
}
</style>