import { defineStore } from 'pinia'
import { getMcpDetailInfo, createMcpServer } from '@/api/mcp'
import { ref } from 'vue'

export const useMcpStore = defineStore('mcp', () => {
  const mcpConfig = ref<string>(`{
    "mcpServers": {
      \n
      \n
      \n
      \n
      \n
      \n
    }
  }`)
  
  const toolsDetail = ref<Record<string, any> | null>(null)
  
  // 获取解析后的MCP服务配置
  const parsedMcpServers = computed(() => {
    try {
      const config = JSON.parse(mcpConfig.value)
      return config.mcpServers || {}
    } catch (error) {
      console.error('解析MCP配置失败:', error)
      return {}
    }
  })
  
  const fetchData = async () => {
    try {
      const res = await getMcpDetailInfo()
      if (res.data.status_code === 200) {
        if (res.data.data.mcp_servers) {
          mcpConfig.value = JSON.stringify(res.data.data.mcp_servers, null, 2)
        }
        toolsDetail.value = res.data.data.tools_detail || {}
      }
    } catch (error) {
      console.error('获取工具详情失败:', error)
    }
  }
  
  const saveMcpConfig = async () => {
    if (!mcpConfig.value) {
      return { success: false, message: '请填写配置内容' }
    }

    try {
      const configObj = JSON.parse(mcpConfig.value)
      await createMcpServer(configObj)
      await fetchData()
      return { success: true, message: '保存成功' }
    } catch (error) {
      console.error('保存配置失败:', error)
      return { success: false, message: '保存失败，请检查 JSON 格式是否正确' }
    }
  }
  
  return { 
    mcpConfig, 
    toolsDetail, 
    parsedMcpServers,
    fetchData, 
    saveMcpConfig 
  }
})