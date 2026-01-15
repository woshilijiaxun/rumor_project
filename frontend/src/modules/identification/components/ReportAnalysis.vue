<template>
  <div class="report-analysis-container">
    <div v-if="loading" class="loading-state">
      <p>智能分析报告生成中...</p>
    </div>

    <div v-else-if="error" class="error-state">
      <p>{{ error }}</p>
    </div>

    <div v-else-if="report" class="report-content">
      <!-- 兼容：若后端已输出 sections，则按模板章节渲染；否则回退到旧 summary -->
      <div v-if="Array.isArray(report.sections) && report.sections.length > 0" class="sections">
        <div v-for="sec in report.sections" :key="sec.id" class="section">
          <div class="section-header">
            <h4 class="section-title">{{ sec.title }}</h4>
          </div>

          <div v-if="sec.narrative" class="section-narrative">
            {{ sec.narrative }}
          </div>

          <!-- 网络概览（图 + 指标） -->
          <div v-if="sec.id === 'network_overview'" class="section-block">
            <div class="kv-grid">
              <div class="kv"><div class="k">文件名</div><div class="v">{{ sec.data?.file?.original_name || '-' }}</div></div>
              <div class="kv"><div class="k">节点数</div><div class="v">{{ sec.data?.metrics?.nodes ?? '-' }}</div></div>
              <div class="kv"><div class="k">边数</div><div class="v">{{ sec.data?.metrics?.edges ?? '-' }}</div></div>
              <div class="kv"><div class="k">平均度</div><div class="v">{{ formatNumber(sec.data?.metrics?.avg_degree, 4) }}</div></div>
              <div class="kv"><div class="k">密度</div><div class="v">{{ formatNumber(sec.data?.metrics?.density, 6) }}</div></div>
              <div class="kv"><div class="k">连通分量</div><div class="v">{{ sec.data?.metrics?.components ?? '-' }}</div></div>
              <div class="kv"><div class="k">最大分量占比</div><div class="v">{{ formatPercent(sec.data?.metrics?.largest_component_ratio) }}</div></div>
              <div class="kv"><div class="k">平均路径长度（最大连通分量）</div><div class="v">{{ formatNumber(sec.data?.metrics?.largest_component_metrics?.avg_path_length, 4) }}</div></div>
              <div class="kv"><div class="k">平均聚类系数（最大连通分量）</div><div class="v">{{ formatNumber(sec.data?.metrics?.largest_component_metrics?.avg_clustering, 4) }}</div></div>
            </div>

            <div class="graph-block" v-if="sec.data?.graph">
              <div class="graph-title-row">
                <div class="graph-title">网络拓扑图</div>
                <button
                  class="non-topk-toggle"
                  type="button"
                  :aria-pressed="nonTopkGray"
                  @click="$emit('toggle-non-topk-gray')"
                  :title="nonTopkGray ? '当前：非Top-K置灰（点击恢复蓝色）' : '当前：非Top-K蓝色（点击置灰）'"
                >
                  <span class="toggle-dot" :class="{ on: nonTopkGray }"></span>
                  <span class="toggle-text">非Top-K{{ nonTopkGray ? '置灰' : '蓝色' }}</span>
                </button>
              </div>
              <GraphView :graph="sec.data.graph" :highlight-map="highlightMap" :non-topk-gray="nonTopkGray" height="420px" />
            </div>
          </div>

          <!-- 关键节点与传播路径 -->
          <div v-if="sec.id === 'key_nodes_and_propagation'" class="section-block">
            <div class="table-wrapper" v-if="Array.isArray(sec.data?.top_nodes) && sec.data.top_nodes.length">
              <table class="table">
                <thead>
                  <tr>
                    <th>序号</th>
                    <th>节点</th>
                    <th>分数</th>
                    <th>度</th>
                    <th>邻居采样</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="row in sec.data.top_nodes" :key="row.node_id">
                    <td>{{ row.rank }}</td>
                    <td class="mono">{{ row.node_id }}</td>
                    <td>{{ formatNumber(row.score, 4) }}</td>
                    <td>{{ row.degree ?? '-' }}</td>
                    <td class="neighbors">{{ formatNeighbors(row.neighbors_sample) }}</td>
                  </tr>
                </tbody>
              </table>
            </div>

            <div class="graph-block" v-if="sec.data?.propagation?.multi?.probability_graph || sec.data?.propagation?.multi?.graph?.graph || sec.data?.propagation?.multi?.graph">
              <div class="graph-title">潜在传播路径预测（multi：Top-10 联合种子）</div>

              <div v-if="propStepCards.length" class="prop-graph-scroll">
                <div
                  v-for="card in propStepCards"
                  :key="card.t"
                  class="prop-step-card"
                >
                  <div class="prop-step-title">t={{ card.t }}</div>
                  <div class="prop-step-graph">
                    <PropagationGraphView
                      :base-graph="card.baseGraph"
                      :overlay-edges="card.overlayEdges"
                      :highlight-map="card.highlightMap"
                      :roots="card.roots"
                      :freeze-layout="true"
                      height="360px"
                    />
                  </div>
                </div>
              </div>

              <PropagationGraphView
                v-else-if="propGraphForView"
                :graph="propGraphForView"
                :overlay-edges="propOverlayEdges"
                :highlight-map="propHighlightMap"
                :roots="propRoots"
                :freeze-layout="true"
                height="420px"
              />

              <div v-else class="empty-inline">暂无传播可视化数据</div>
            </div>
          </div>

          <!-- Top 节点表（旧 id 兼容） -->
          <div v-if="sec.id === 'top_influencers'" class="section-block">
            <div class="table-wrapper" v-if="Array.isArray(sec.data?.top_nodes) && sec.data.top_nodes.length">
              <table class="table">
                <thead>
                  <tr>
                    <th>序号</th>
                    <th>节点</th>
                    <th>分数</th>
                    <th>度</th>
                    <th>邻居采样</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="row in sec.data.top_nodes" :key="row.node_id">
                    <td>{{ row.rank }}</td>
                    <td class="mono">{{ row.node_id }}</td>
                    <td>{{ formatNumber(row.score, 4) }}</td>
                    <td>{{ row.degree ?? '-' }}</td>
                    <td class="neighbors">{{ formatNeighbors(row.neighbors_sample) }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <!-- 治理建议 actions -->
          <div v-if="sec.id === 'governance_actions'" class="section-block">
            <div v-if="Array.isArray(sec.data?.actions) && sec.data.actions.length" class="actions">
              <div v-for="(a, idx) in sortedGovernanceActions(sec.data.actions)" :key="idx" class="action">
                <div class="action-title-row">
                  <span class="badge" :class="`p-${String(a.priority || '').toLowerCase()}`">{{ formatPriority(a.priority) }}</span>
                  <span class="action-title">{{ a.title || '处置建议' }}</span>
                </div>

                <div v-if="a.reason" class="action-reason">原因：{{ a.reason }}</div>

                <div v-if="a.targets" class="action-targets">
                  <div v-if="Array.isArray(a.targets.nodes) && a.targets.nodes.length">
                    <span class="label">目标节点：</span>
                    <span class="mono">{{ a.targets.nodes.join(', ') }}</span>
                  </div>
                  <div v-if="a.targets.scope">
                    <span class="label">作用范围：</span>
                    <span>{{ a.targets.scope }}</span>
                  </div>
                  <div v-if="a.targets.component">
                    <span class="label">目标组件：</span>
                    <span>{{ a.targets.component }}</span>
                  </div>
                </div>

                <div v-if="Array.isArray(a.operations) && a.operations.length" class="action-ops">
                  <div class="label">建议动作：</div>
                  <ul class="ops">
                    <li v-for="(op, j) in a.operations" :key="j">
                      <span class="op-type">{{ op.type || 'action' }}</span>
                      <span class="op-desc">{{ op.desc || '' }}</span>
                    </li>
                  </ul>
                </div>
              </div>
            </div>
            <div v-else class="empty-inline">暂无治理建议</div>
          </div>

          <!-- 其他章节：展示关键字段（可选） -->
          <div v-if="sec.id === 'executive_summary'" class="section-block">
            <div class="kv-grid">
              <div class="kv">
                <div class="k">风险等级</div>
                <div class="v">{{ formatRiskLevel(sec.data?.risk?.level) }}</div>
              </div>
              <div class="kv">
                <div class="k">处置优先级</div>
                <div class="v">{{ sec.data?.priority || '-' }}</div>
              </div>
            </div>
          </div>

          <div v-if="sec.id === 'structure_judgement'" class="section-block">
            <div class="kv-grid">
              <div class="kv"><div class="k">节点数</div><div class="v">{{ sec.data?.nodes ?? '-' }}</div></div>
              <div class="kv"><div class="k">边数</div><div class="v">{{ sec.data?.edges ?? '-' }}</div></div>
              <div class="kv"><div class="k">密度</div><div class="v">{{ formatNumber(sec.data?.density, 6) }}</div></div>
              <div class="kv"><div class="k">连通分量</div><div class="v">{{ sec.data?.components ?? '-' }}</div></div>
              <div class="kv"><div class="k">最大分量占比</div><div class="v">{{ formatPercent(sec.data?.largest_component_ratio) }}</div></div>
            </div>
          </div>

        </div>
      </div>

      <!-- 旧结构回退 -->
      <div v-else class="legacy">
        <div class="report-grid">
          <div class="summary-section">
            <div class="summary-item risk-level" :class="`risk-${report.summary?.risk?.level}`">
              <span class="label">综合风险</span>
              <span class="value">{{ formatRiskLevel(report.summary?.risk?.level) }}</span>
            </div>
            <div class="summary-item">
              <span class="label">风险评估</span>
              <span class="value reason">{{ report.summary?.risk?.reason || '-' }}</span>
            </div>
            <div class="summary-item">
              <span class="label">算法解释</span>
              <span class="value">{{ report.summary?.algo_explain || '-' }}</span>
            </div>
          </div>

          <div class="metrics-section">
            <div class="metric-item"><span class="label">节点数</span><span class="value">{{ report.summary?.nodes ?? '-' }}</span></div>
            <div class="metric-item"><span class="label">边数</span><span class="value">{{ report.summary?.edges ?? '-' }}</span></div>
            <div class="metric-item"><span class="label">网络密度</span><span class="value">{{ formatNumber(report.summary?.density, 6) }}</span></div>
            <div class="metric-item"><span class="label">连通分量</span><span class="value">{{ report.summary?.components ?? '-' }}</span></div>
            <div class="metric-item"><span class="label">最大分量占比</span><span class="value">{{ formatPercent(report.summary?.largest_component_ratio) }}</span></div>
            <div class="metric-item"><span class="label">分数均值</span><span class="value">{{ formatNumber(report.summary?.score_distribution?.mean, 4) }}</span></div>
          </div>
        </div>
      </div>
    </div>

    <div v-else class="empty-state">
      <p>暂无分析报告</p>
    </div>
  </div>
</template>

<script>
import { computed, ref, watch } from 'vue'
import GraphView from './GraphView.vue'
import PropagationGraphView from './PropagationGraphView.vue'

export default {
  name: 'ReportAnalysis',
  components: { GraphView, PropagationGraphView },
  props: {
    report: { type: Object, default: null },
    loading: { type: Boolean, default: false },
    error: { type: String, default: '' },
    highlightMap: { type: Object, default: () => ({}) },
    nonTopkGray: { type: Boolean, default: true },
  },
  emits: ['toggle-non-topk-gray'],
  setup(props) {
    /* ---------------- 传播可视化（报告页专用简化版） ---------------- */
    const _getPropagationMulti = computed(() => {
      const secs = Array.isArray(props.report?.sections) ? props.report.sections : []
      const sec = secs.find(s => s?.id === 'key_nodes_and_propagation')
      return sec?.data?.propagation?.multi || null
    })

    const propSteps = computed(() => {
      const m = _getPropagationMulti.value
      // 对齐后端 report（已按 /identification/propagation 补齐）：multi.steps
      const steps = m?.steps ?? m?.graph?.steps ?? m?.graph?.graph?.steps
      return Array.isArray(steps) ? steps : []
    })

    const propStepMaxT = computed(() => Math.max(0, propSteps.value.length - 1))
    const propCurrentStep = ref(0)

    watch(propSteps, () => { propCurrentStep.value = 0 })

    // 辅助：构造 overlayEdges / highlightMap / roots，沿用识别页逻辑
    const propOverlayEdges = computed(() => {
      const steps = propSteps.value
      if (!steps.length) return []
      const edges = new Set()
      // 累积展示：0..t
      for (let i = 0; i <= propCurrentStep.value; i++) {
        const es = Array.isArray(steps[i]?.edges) ? steps[i].edges : []
        es.forEach(e => {
          if (e?.source != null && e?.target != null) {
            edges.add(`${e.source}|${e.target}`)
          }
        })
      }
      return Array.from(edges).map(k => {
        const [s, t] = k.split('|')
        return { source: s, target: t }
      })
    })

    const propRoots = computed(() => {
      const roots = Array.isArray(propSteps.value[0]?.nodes) ? propSteps.value[0].nodes : []
      return roots.map(x => String(x))
    })

    const propHighlightMap = computed(() => {
      const steps = propSteps.value
      if (!steps.length) return {}
      const t = Math.max(0, Math.min(propCurrentStep.value, propStepMaxT.value))

      const seeds = new Set((steps[0]?.nodes || []).map(n => String(n)))
      const currentNodes = new Set((steps[t]?.nodes || []).map(n => String(n)))
      const prevNodes = new Set(t > 0 ? (steps[t-1]?.nodes || []).map(n => String(n)) : [])

      const map = {}
      seeds.forEach(n => { map[n] = '#ef4444' })
      if (t > 0) {
        currentNodes.forEach(n => {
          if (!prevNodes.has(n) && !seeds.has(n)) map[n] = '#1677ff'
        })
      }
      return map
    })

    const propStepCards = computed(() => {
      const steps = propSteps.value
      if (!steps.length) return []

      const baseGraph = propGraphForView.value
      if (!baseGraph) return []

      const roots = Array.isArray(steps[0]?.nodes) ? steps[0].nodes.map(x => String(x)) : []

      // 把每个时间步的 edges 转成 overlayEdges，并按时间步累积（0..t）
      const stepEdges = steps.map((st) => {
        const es = Array.isArray(st?.edges) ? st.edges : []
        return es
          .map(e => ({ source: String(e?.source), target: String(e?.target) }))
          .filter(e => e.source && e.target)
      })

      const cards = []
      for (let t = 0; t <= steps.length - 1; t++) {
        // 激活节点：0..t 的 nodes 都高亮为红色（识别页卡片模式逻辑）
        const activated = new Set()
        for (let i = 0; i <= t; i++) {
          const ns = Array.isArray(steps[i]?.nodes) ? steps[i].nodes : []
          ns.forEach(n => activated.add(String(n)))
        }

        const highlightMap = {}
        activated.forEach(id => { highlightMap[id] = '#ef4444' })

        const overlayEdgeSet = new Set()
        for (let i = 0; i <= t; i++) {
          ;(stepEdges[i] || []).forEach(e => overlayEdgeSet.add(`${e.source}|${e.target}`))
        }
        const overlayEdges = Array.from(overlayEdgeSet).map(k => {
          const [source, target] = k.split('|')
          return { source, target }
        })

        cards.push({
          t,
          roots,
          baseGraph,
          overlayEdges,
          highlightMap,
        })
      }

      return cards
    })

    const propGraphForView = computed(() => {
      // 报告页 propagation.multi 可能是：
      // 1) { graph: {nodes,edges} }
      // 2) { graph: { graph: {nodes,edges}, ... } }
      // 3) { probability_graph: {"u|v": p, ...} } 或 { edges: [...] }
      const m = _getPropagationMulti.value
      if (!m) return null

      const g = m.graph
      const gg = (g && (g.graph || g)) || null
      if (gg && Array.isArray(gg.nodes) && gg.nodes.length) return gg

      // 兜底：用概率图（map/edges）构建一个最小可视化图
      const pg = m.probability_graph || m.probabilityGraph || null
      const rawEdges = Array.isArray(pg?.edges) ? pg.edges : (Array.isArray(pg?.links) ? pg.links : [])
      const mapEdges = (pg && typeof pg === 'object' && !Array.isArray(pg) && !Array.isArray(pg?.edges) && !Array.isArray(pg?.links) && !Array.isArray(pg?.nodes))
        ? Object.entries(pg)
        : null

      const edges = (mapEdges ? mapEdges.map(([k, v]) => {
        const parts = String(k).split('|')
        if (parts.length < 2) return null
        const p = Number(v)
        return { source: String(parts[0]), target: String(parts[1]), weight: Number.isFinite(p) ? p : 0 }
      }) : rawEdges.map(e => {
        const source = e?.source ?? e?.from ?? e?.u
        const target = e?.target ?? e?.to ?? e?.v
        const prob = e?.prob ?? e?.p ?? e?.probability ?? e?.value ?? e?.weight ?? e?.score
        if (source == null || target == null) return null
        const p = Number(prob)
        return { source: String(source), target: String(target), weight: Number.isFinite(p) ? p : 0 }
      })).filter(Boolean)

      if (!edges.length) return null

      const nodeSet = new Set()
      edges.forEach(e => { nodeSet.add(e.source); nodeSet.add(e.target) })
      const nodes = Array.from(nodeSet).map(id => ({ id, label: id }))

      return { nodes, edges, meta: { nodes: nodes.length, edges: edges.length } }
    })

    const formatRiskLevel = (level) => {
      if (level === 'high') return '高'
      if (level === 'medium') return '中'
      if (level === 'low') return '低'
      return '未知'
    }

    const _priorityRank = (p) => {
      const pp = String(p || '').trim().toUpperCase()
      if (pp === 'P0') return 0
      if (pp === 'P1') return 1
      if (pp === 'P2') return 2
      return 9
    }

    const sortedGovernanceActions = (actions) => {
      const arr = Array.isArray(actions) ? actions.slice() : []
      // 稳定排序：同优先级保持原顺序
      return arr
        .map((a, idx) => ({ a, idx }))
        .sort((x, y) => {
          const d = _priorityRank(x.a?.priority) - _priorityRank(y.a?.priority)
          return d !== 0 ? d : (x.idx - y.idx)
        })
        .map(x => x.a)
    }

    const formatPriority = (priority) => {
      const p = String(priority || 'P2').trim().toUpperCase()
      if (p === 'P0') return '紧急（P0）'
      if (p === 'P1') return '高优先级（P1）'
      if (p === 'P2') return '中优先级（P2）'
      return `优先级（${p}）`
    }

    const formatNumber = (val, precision = 4) => {
      const n = Number(val)
      if (!Number.isFinite(n)) return '-'
      return n.toFixed(precision)
    }

    const formatPercent = (val) => {
      const n = Number(val)
      if (!Number.isFinite(n)) return '-'
      return `${(n * 100).toFixed(2)}%`
    }

    const formatNeighbors = (arr) => {
      if (!Array.isArray(arr) || arr.length === 0) return '-'
      return arr.join(', ')
    }

    return {
      formatRiskLevel,
      formatPriority,
      sortedGovernanceActions,
      formatNumber,
      formatPercent,
      formatNeighbors,
      propCurrentStep,
      propStepMaxT,
      propOverlayEdges,
      propHighlightMap,
      propRoots,
      propGraphForView,
      propStepCards,
    }
  }
}
</script>

<style scoped>
.graph-block {
  margin-top: 12px;
  border: 1px solid #eef2f7;
  border-radius: 10px;
  background: #fff;
  padding: 10px;
}

.graph-title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin: 0 0 10px 0;
}

.graph-title {
  font-size: 12px;
  font-weight: 700;
  color: #374151;
  margin: 0;
}

.step-controls {
  margin: 8px 0 10px;
}

.step-slider {
  width: 100%;
}

.edges-meta {
  font-size: 12px;
  color: #6b7280;
  margin-bottom: 8px;
}

.prop-graph-scroll {
  width: 100%;
  display: flex;
  gap: 12px;
  overflow-x: auto;
  padding-bottom: 6px;
  align-items: stretch;
  scroll-snap-type: x mandatory;
}

.prop-graph-scroll::-webkit-scrollbar {
  height: 8px;
}

.prop-graph-scroll::-webkit-scrollbar-thumb {
  background: #e5e7eb;
  border-radius: 999px;
}

.prop-graph-scroll::-webkit-scrollbar-track {
  background: transparent;
}

.prop-step-card {
  flex: 0 0 320px;
  max-width: 320px;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  overflow: hidden;
  background: #fff;
  scroll-snap-align: start;
}

.prop-step-title {
  padding: 8px 10px;
  font-size: 12px;
  font-weight: 800;
  color: #111827;
  background: #f9fafb;
  border-bottom: 1px solid #e5e7eb;
}

.prop-step-graph {
  position: relative;
}

.non-topk-toggle {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 6px 10px;
  border-radius: 999px;
  border: 1px solid #e5e7eb;
  background: #fff;
  color: #374151;
  font-size: 12px;
  line-height: 1;
  cursor: pointer;
  user-select: none;
}

.non-topk-toggle:hover {
  border-color: #cbd5e1;
  background: #f9fafb;
}

.toggle-dot {
  width: 10px;
  height: 10px;
  border-radius: 999px;
  background: #1677ff;
  box-shadow: inset 0 0 0 1px rgba(0,0,0,0.08);
}

.toggle-dot.on {
  background: #9ca3af;
}

.toggle-text {
  font-weight: 600;
}
</style>

<style scoped>
.report-analysis-container {
  width: 100%;
}

.loading-state, .error-state, .empty-state {
  padding: 40px 20px;
  text-align: center;
  color: #6b7280;
  background: #f9fafb;
  border-radius: 8px;
}

.error-state {
  color: #ef4444;
}

.report-content {
  background: #f9fafb;
  border-radius: 8px;
  padding: 14px;
}

.sections {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.section {
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  padding: 14px;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 8px;
}

.section-title {
  margin: 0;
  font-size: 14px;
  font-weight: 700;
  color: #111827;
}

.section-narrative {
  font-size: 13px;
  color: #374151;
  line-height: 1.6;
  margin: 6px 0 10px;
}

.section-block {
  margin-top: 10px;
}

.kv-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px;
}

.kv {
  background: #f9fafb;
  border: 1px solid #eef2f7;
  border-radius: 8px;
  padding: 10px;
}

.k {
  font-size: 12px;
  color: #6b7280;
  margin-bottom: 4px;
}

.v {
  font-size: 14px;
  font-weight: 700;
  color: #111827;
  overflow-wrap: anywhere;
}

.table-wrapper {
  overflow-x: auto;
}

.table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.table th {
  text-align: left;
  padding: 10px;
  background: #f3f4f6;
  border-bottom: 1px solid #e5e7eb;
}

.table td {
  padding: 10px;
  border-bottom: 1px solid #e5e7eb;
  color: #374151;
}

.mono {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
}

.neighbors {
  max-width: 320px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.actions {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.action {
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  padding: 12px;
  background: #f9fafb;
}

.action-title-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
}

.badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 4px 8px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 800;
}

.p-p0 { background: #fee2e2; color: #b91c1c; }
.p-p1 { background: #fffbeb; color: #b45309; }
.p-p2 { background: #e5e7eb; color: #374151; }

.action-title {
  font-size: 13px;
  font-weight: 700;
  color: #111827;
}

.action-reason {
  font-size: 12px;
  color: #4b5563;
  margin-bottom: 8px;
}

.action-targets {
  font-size: 12px;
  color: #374151;
  line-height: 1.6;
  margin-bottom: 8px;
}

.action-ops .label,
.action-targets .label {
  font-weight: 700;
  color: #111827;
}

.ops {
  margin: 6px 0 0;
  padding-left: 18px;
}

.ops li {
  margin: 6px 0;
  line-height: 1.5;
}

.op-type {
  display: inline-block;
  min-width: 120px;
  font-weight: 800;
  color: #111827;
}

.op-desc {
  color: #374151;
}

.empty-inline {
  padding: 10px;
  color: #6b7280;
}

/* legacy */
.report-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

.summary-section {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.summary-item {
  text-align: left;
}

.summary-item .label {
  display: block;
  font-size: 12px;
  color: #6b7280;
  margin-bottom: 4px;
}

.summary-item .value {
  font-size: 14px;
  color: #1f2937;
  line-height: 1.5;
}

.summary-item .value.reason {
  font-weight: 600;
}

.risk-level {
  padding: 12px;
  border-radius: 8px;
  text-align: center;
}

.risk-level .label {
  color: inherit;
  opacity: 0.8;
}

.risk-level .value {
  font-size: 24px;
  font-weight: 700;
  color: inherit;
}

.risk-high { background-color: #fef2f2; color: #dc2626; }
.risk-medium { background-color: #fffbeb; color: #d97706; }
.risk-low { background-color: #f0fdf4; color: #16a34a; }
.risk-unknown { background-color: #f3f4f6; color: #4b5563; }

.metrics-section {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
  align-content: start;
}

.metric-item {
  background: white;
  padding: 12px;
  border-radius: 6px;
  border: 1px solid #e5e7eb;
  text-align: center;
}

.metric-item .label {
  display: block;
  font-size: 12px;
  color: #6b7280;
  margin-bottom: 4px;
}

.metric-item .value {
  display: block;
  font-size: 18px;
  font-weight: 600;
  color: #1f2937;
}

@media (max-width: 768px) {
  .report-grid {
    grid-template-columns: 1fr;
  }
  .kv-grid {
    grid-template-columns: 1fr;
  }
  .op-type {
    min-width: auto;
    margin-right: 6px;
  }
}
</style>
