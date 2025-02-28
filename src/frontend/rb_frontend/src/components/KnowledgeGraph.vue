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
  import neo4j from 'neo4j-driver';
  import { Spin } from 'ant-design-vue';
  
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
        neo4jDriver: null,
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
      this.closeNeo4jDriver();
    },
    watch: { // 添加 watch 选项
      userId(newUserId, oldUserId) { // 监听 userId prop 的变化
        if (newUserId && newUserId !== oldUserId) { // 确保 newUserId 存在且与旧值不同时才重新获取数据
          this.fetchGraphData(); // 重新获取图谱数据
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
                // console.log(params)
  
                let tooltipContent = `<b>${params.name}</b><br>`;
  
                if (params.properties) {
                  for (const key in params.properties) {
                    if (key === 'created') {
                    //   console.log("params.properties.created:", params.properties[key]);
                      const { high, low } = params.properties[key];
                      const timestamp = (high * 2**32) + low;
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
  
                    }else if (key === 'embedding') {
                      continue
                    }else{
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
                      labelText = params.name || params.labels.join(', ') || 'Node';
                    }
  
                    const maxLength = 10;
                    if (labelText.length > maxLength) {
                      return labelText.substring(0, maxLength) + '...';
                    }
  
                    // console.log('当前节点 ID:', params.id);
                    // console.log('rootNodeId:', this.rootNodeId);
                    // console.log('params.id === this.rootNodeId:', params.id === this.rootNodeId);
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
        if (!this.userId) { // 检查 userId 是否存在，避免在没有 userId 的情况下发起请求
          return;
        }
        this.loading = true;
        this.error = null;
        this.rootNodeId = null;
  
        try {
          this.neo4jDriver = neo4j.driver(
            'bolt://localhost:7687',
            neo4j.auth.basic('neo4j', '12345678')
          );
  
          const session = this.neo4jDriver.session();
  
          const query = `
            MATCH (n)-[r]-(m)
            WHERE n.user_id = "${this.userId}" OR m.user_id = "${this.userId}"
            RETURN n, r, m
          `;
  
          const result = await session.run(query);
  
          this.processNeo4jData(result.records);
  
          session.close();
  
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
  
        if (records.length > 0 && records[0].get('n')) {
          this.rootNodeId = records[0].get('n').identity.toString();
        }
  
        records.forEach(record => {
          const node1 = record.get('n');
          const relationship = record.get('r');
          const node2 = record.get('m');
  
          if (!nodesMap.has(node1.identity.toString())) {
            nodesMap.set(node1.identity.toString(), true);
            this.nodes.push(this.neo4jNodeToEchartsNode(node1));
          }
  
          if (!nodesMap.has(node2.identity.toString())) {
            nodesMap.set(node2.identity.toString(), true);
            this.nodes.push(this.neo4jNodeToEchartsNode(node2));
          }
  
          const sourceId = node1.identity.toString();
          const targetId = node2.identity.toString();
          const linkKey = [sourceId, targetId].sort().join('-');
  
          if (!existingLinks.has(linkKey)) {
            existingLinks.add(linkKey);
            this.links.push(this.neo4jRelationshipToEchartsLink(relationship, sourceId, targetId, node1, node2));
          }
        });
      },
      neo4jNodeToEchartsNode(neo4jNode) {
        const labels = neo4jNode.labels;
        let category = labels[0] || 'default';
        let symbolSize = 45;
        let nodeColor = this.categoryColors[category] || this.categoryColors['default'];
  
        if (neo4jNode.identity.toString() === this.rootNodeId) {
          category = 'Root';
          nodeColor = this.categoryColors['Root'];
          symbolSize = 50;
        }
  
        return {
          dataType: 'node',
          id: neo4jNode.identity.toString(),
          name: neo4jNode.properties.name || neo4jNode.properties.title || neo4jNode.labels.join(', '),
          properties: neo4jNode.properties,
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
      neo4jRelationshipToEchartsLink(neo4jRelationship, sourceId, targetId, node1, node2) {
        return {
          dataType: 'edge',
          source: sourceId,
          target: targetId,
          label: {
            show: true,
            formatter: neo4jRelationship.type
          },
          sourceName: sourceId === this.rootNodeId ? '用户' : (node1.properties.name || node1.properties.title || node1.labels.join(', ') || 'Node'),
          targetName: node2.properties.name || node2.properties.title || node2.labels.join(', ') || 'Node'
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
      },
      closeNeo4jDriver() {
        if (this.neo4jDriver) {
          this.neo4jDriver.close();
          this.neo4jDriver = null;
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