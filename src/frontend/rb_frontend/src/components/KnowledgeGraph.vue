<template>
  <div class="knowledge-graph">
    <div ref="chartContainer" style="width: 100%; height: 600px;"></div>
    <div v-if="loading" class="loading-overlay">
      <a-spin size="large" tip="加载中..."></a-spin>
    </div>
    <div v-if="error" style="color: red;">{{ error }}</div>
  </div>
</template>

<script>
import * as echarts from 'echarts';
import { Spin } from 'ant-design-vue';
// 引入 queryMemory 函数，请根据你的实际路径调整
import { queryMemory } from '@/api/memory';

export default {
  name: 'KnowledgeGraph',
  components: {
    ASpin: Spin,
  },
  props: {
    userId: {
      type: String,
      required: true
    }
  },
  data() {
    return {
      chartInstance: null,
      nodes: [],
      links: [],
      loading: false,
      error: null,
      rootNodeId: null,
      categoryColors: {
        'Person': '#c23531',
        'Movie': '#2f4554',
        'Concept': '#61a0a8',
        'Root': '#d48265',
        'default': '#409EFF'
      }
    };
  },
  mounted() {
    this.initChart();
    this.fetchGraphData();
  },
  beforeDestroy() {
    this.destroyChart();
  },
  watch: {
    userId(newUserId, oldUserId) {
      if (newUserId && newUserId !== oldUserId) {
        this.fetchGraphData();
      }
    }
  },
  methods: {
    initChart() {
      this.chartInstance = echarts.init(this.$refs.chartContainer);
      this.chartInstance.setOption(this.getChartOptions());
    },
    destroyChart() {
      if (this.chartInstance) {
        this.chartInstance.dispose();
        this.chartInstance = null;
      }
    },
    getChartOptions() {
      return {
        tooltip: {
          trigger: 'item',
          formatter: (params) => {
            params = params.data
            if (params.dataType === 'node') {
              let tooltipContent = `<b>${params.name}</b><br>`;

              if (params.properties) {
                for (const key in params.properties) {
                  if (key === 'created') {
                    const timestamp = params.properties[key];
                    const date = new Date(timestamp);
                    const timeString = date.toLocaleString('en-US', {
                      year: 'numeric',
                      month: '2-digit',
                      day: '2-digit',
                      hour: '2-digit',
                      minute: '2-digit',
                      second: '2-digit',
                      hour12: false
                    });
                    tooltipContent += `${key}: ${timeString}<br>`;

                  } else if (key === 'embedding') {
                    continue
                  } else {
                    tooltipContent += `${key}: ${params.properties[key]}<br>`;
                  }
                }
              }
              return tooltipContent;
            } else if (params.dataType === 'edge') {
              return `<b>[${params.sourceName}] 👉<${params.label.formatter}>👉 [${params.targetName}]<br></b>`;
            }
            return params.name || 'Unknown';
          }
        },
        legend: {
          data: ['节点', '关系']
        },
        series: [
          {
            name: 'Knowledge Graph',
            type: 'graph',
            layout: 'force',
            force: {
              repulsion: 300,
              edgeLength: [80, 180]
            },
            data: this.nodes,
            links: this.links,
            categories: [
              { name: '节点' },
              { name: '关系' }
            ],
            roam: true,
            label: {
              show: true,
              position: 'inside',
              color: '#fff',
              fontSize: 12,
              formatter: (params) => {
                params = params.data;
                if (params.dataType === 'node') {
                  let labelText = '';
                  if (params.properties && params.properties.name) {
                    labelText = params.properties.name;
                  } else if (params.properties && params.properties.title) {
                    labelText = params.properties.title;
                  } else {
                    labelText = params.name || params.labels || 'Node';
                  }

                  const maxLength = 10;
                  if (labelText.length > maxLength) {
                    return labelText.substring(0, maxLength) + '...';
                  }

                  if (params.id === this.rootNodeId) {
                    return '用户';
                  }

                  return labelText;

                } else if (params.dataType === 'edge') {
                  return params.name || params.label.formatter;
                }
                return params.name || 'Unknown';
              }
            },
            lineStyle: {
              color: 'rgba(200, 200, 200, 0.8)',
              curveness: 0.1
            },
            itemStyle: {
              borderColor: '#fff',
              borderWidth: 1,
            },
            emphasis: {
              focus: 'adjacency',
              label: {
                show: true
              },
              lineStyle: {
                width: 2
              }
            }
          }
        ]
      };
    },
    async fetchGraphData() {
      if (!this.userId) {
        return;
      }
      this.loading = true;
      this.error = null;
      this.rootNodeId = null;

      try {
        const params = {  // 构造 queryMemory 函数需要的参数
          condition: 'WHERE n.user_id = $userId', //  后端接口可能不需要condition，这里假设需要，如果不需要可以删除
          condition_parameters: {
            userId: this.userId
          } // 将 userId 传递给后端
        };
        const response = await queryMemory(params); // 调用 queryMemory 函数

        if (response.data.status_code !== 200) {
          throw new Error(response.status_message || '获取图谱数据失败');
        }

        this.processNeo4jData(response.data.data); // 处理后端返回的数据

      } catch (err) {
        console.error('Error fetching graph data:', err);
        this.error = err.message || '获取图谱数据失败，请检查控制台错误信息。';
      } finally {
        this.loading = false;
        this.updateChart();
      }
    },
    processNeo4jData(records) {
      const nodesMap = new Map();
      this.nodes = [];
      this.links = [];
      const existingLinks = new Set();

      if (records.length > 0) {
        this.rootNodeId = records[0].source;
      }

      records.forEach(record => {
        const sourceName = record.source;
        const targetName = record.target;
        const relationshipType = record.relationship;

        if (!nodesMap.has(sourceName)) {
          nodesMap.set(sourceName, true);
          this.nodes.push(this.createEchartsNode(sourceName, record.source_created));
        }

        if (!nodesMap.has(targetName)) {
          nodesMap.set(targetName, true);
          this.nodes.push(this.createEchartsNode(targetName, record.target_created));
        }

        const sourceId = sourceName;
        const targetId = targetName;
        const linkKey = [sourceId, targetId].sort().join('-');

        if (!existingLinks.has(linkKey)) {
          existingLinks.add(linkKey);
          this.links.push(this.createEchartsLink(relationshipType, sourceId, targetId, sourceName, targetName));
        }
      });
    },
    createEchartsNode(nodeName, createdTimestamp) {
      let category = 'default';
      let symbolSize = 45;
      let nodeColor = this.categoryColors[category] || this.categoryColors['default'];

      if (nodeName === this.rootNodeId) {
        category = 'Root';
        nodeColor = this.categoryColors['Root'];
        symbolSize = 50;
      }

      const properties = {
        name: nodeName,
        created: createdTimestamp
      };

      return {
        dataType: 'node',
        id: nodeName,
        name: nodeName,
        properties: properties,
        category: 0,
        categoryName: category,
        symbol: 'circle',
        symbolSize: symbolSize,
        itemStyle: {
          color: nodeColor,
          borderColor: '#fff',
          borderWidth: 1,
        },
        label: {
          show: true,
        }
      };
    },
    createEchartsLink(relationshipType, sourceId, targetId, sourceName, targetName) {
      return {
        dataType: 'edge',
        source: sourceId,
        target: targetId,
        label: {
          show: true,
          formatter: relationshipType
        },
        sourceName: sourceName === this.rootNodeId ? '用户' : sourceName,
        targetName: targetName
      };
    },
    updateChart() {
      if (this.chartInstance) {
        this.chartInstance.setOption({
          series: [{
            data: this.nodes,
            links: this.links
          }]
        });
      }
    }
  }
};
</script>

<style scoped>
.knowledge-graph {
  font-family: sans-serif;
  position: relative;
}

.loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 600px;
  display: flex;
  justify-content: center;
  align-items: center;
  background-color: rgba(255, 255, 255, 0.7);
  z-index: 10;
}
</style>