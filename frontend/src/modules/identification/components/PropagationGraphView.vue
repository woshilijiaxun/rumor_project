<template>
  <div class="graph-view" :style="{ height }">
    <div ref="containerRef" class="cy-container"></div>

    <button v-if="hasData" class="reset-btn" type="button" @click="onResetClick">复原</button>
    <div v-if="!hasData" class="empty">暂无可视化数据</div>
  </div>
</template>

<script>
import { ref, onMounted, onBeforeUnmount, watch, computed, nextTick } from 'vue'
import cytoscape from 'cytoscape'
import fcose from 'cytoscape-fcose'
cytoscape.use(fcose)

export default {
  name: 'PropagationGraphView',
  props: {
    // 兼容旧用法：graph 仍然可传；若传 baseGraph，则以 baseGraph 为底图
    graph: { type: Object, required: false, default: () => ({ nodes: [], edges: [] }) },
    baseGraph: { type: Object, required: false, default: null },
    // 传播/高亮边（可选）：[{ source, target }]
    overlayEdges: { type: Array, required: false, default: () => [] },

    highlightMap: { type: Object, default: () => ({}) },
    roots: { type: Array, default: () => [] },
    height: { type: String, default: '420px' },
    freezeLayout: { type: Boolean, default: false },
    dimUnhighlighted: { type: Boolean, default: true }
  },
  setup(props, { expose }) {
    const containerRef = ref(null)
    let cy = null

    const FIT_PADDING = 60
    let initialViewport = null

    const activeGraph = computed(() => props.baseGraph || props.graph)

    const hasData = computed(() => Array.isArray(activeGraph.value?.nodes) && activeGraph.value.nodes.length > 0)

    const buildElements = () => {
      const g = activeGraph.value
      if (!g) return []

      const highlight = props.highlightMap || {}
      const nodes = (g.nodes || []).map(n => {
        const id = String(n.id)
        const color = highlight[id]
        const dim = props.dimUnhighlighted && !color
        return {
          data: { id, label: n.label ?? id, highlightColor: color || '' },
          classes: color ? 'topk' : (dim ? 'dim' : 'normal')
        }
      })

      const overlayEdgeSet = new Set(props.overlayEdges.map(e => `${e.source}|${e.target}`))

      const edges = (g.edges || []).map(e => {
        const key = `${e.source}|${e.target}`
        const isOverlay = overlayEdgeSet.has(key)
        return {
          data: {
            source: String(e.source),
            target: String(e.target),
            weight: e.weight != null ? Number(e.weight) : 0,
            label: e.weight != null ? String(e.weight) : ''
          },
          classes: isOverlay ? 'overlay-edge' : ''
        }
      })

      return [...nodes, ...edges]
    }

    let layoutRunId = 0
    const yieldToMain = () => new Promise(resolve => setTimeout(resolve, 0))

    const runLayoutAndFit = async () => {
      if (!cy) return

      const runId = ++layoutRunId

      // 先让出一个 tick，保证返回按钮/路由跳转等交互优先被处理
      await yieldToMain()
      if (runId !== layoutRunId || !cy) return

      const layout = cy.layout({
        name: 'fcose',
        animate: false,
        // 为了让“同一份图数据”在不同卡片/不同时间步渲染时拓扑位置保持一致，
        // freezeLayout=true 时关闭 randomize，并固定 randomSeed。
        randomize: !props.freezeLayout,
        randomSeed: 7,
        fit: true,
        padding: FIT_PADDING,
        quality: 'default',
        nodeSeparation: 80,
        nodeRepulsion: () => 6000,
        idealEdgeLength: () => 150,
        edgeElasticity: () => 0.2,
        gravity: 0.25
      })

      layout.run()
      if (runId !== layoutRunId || !cy) return

      cy.fit(undefined, FIT_PADDING)
    }

    const saveInitialViewport = () => {
      if (!cy) return
      initialViewport = { zoom: cy.zoom(), pan: { ...cy.pan() } }
    }

    const resetView = () => {
      if (!cy) return
      if (initialViewport) {
        cy.animate({ zoom: initialViewport.zoom, pan: initialViewport.pan, duration: 250 })
      } else {
        cy.fit(undefined, FIT_PADDING)
        saveInitialViewport()
      }
    }

    const onResetClick = () => resetView()

    expose({ resetView })

    const mountCytoscape = async () => {
      await nextTick()
      if (!containerRef.value) return

      cy = cytoscape({
        container: containerRef.value,
        elements: buildElements(),
        style: [
          // 基础样式（与 GraphView 保持一致）
          { selector: 'node', style: { 'background-color': '#1677ff', 'label': 'data(label)', 'font-size': 10, 'color': '#333', 'text-opacity': 0, 'min-zoomed-font-size': 10 } },
          { selector: 'edge', style: { 'line-color': '#9ca3af', 'width': 1.5, 'curve-style': 'bezier', 'target-arrow-shape': 'triangle', 'target-arrow-color': '#9ca3af', 'arrow-scale': 0.8, 'label': 'data(label)', 'font-size': 8, 'color': '#666', 'text-opacity': 0, 'min-zoomed-font-size': 8 } },
          { selector: '.hovered', style: { 'text-opacity': 1 } },
          { selector: 'node:selected', style: { 'background-color': '#0d5ccc', 'text-opacity': 1 } },
          { selector: 'edge:selected', style: { 'line-color': '#0d5ccc', 'target-arrow-color': '#0d5ccc', 'text-opacity': 1 } },
          
          // 传播可视化定制样式
          { selector: 'node.topk', style: { 'background-color': 'data(highlightColor)', 'border-width': 2, 'border-color': 'data(highlightColor)', 'opacity': 1, 'text-opacity': 1 } },
          { selector: 'node.dim', style: { 'background-color': '#9ca3af', 'opacity': 0.22, 'text-opacity': 0 } },
          { selector: 'node.normal', style: { 'opacity': 1 } },
          
          // 传播边高亮
          { selector: 'edge.overlay-edge', style: { 'line-color': '#ef4444', 'target-arrow-color': '#ef4444', 'opacity': 0.95, 'width': 2.5 } },
          { selector: 'edge.dim', style: { 'line-color': '#cbd5e1', 'target-arrow-color': '#cbd5e1', 'opacity': 0.18 } }
        ],
        wheelSensitivity: 0.2
      })

      // hover 显示 label
      cy.on('mouseover', 'node, edge', (evt) => {
        evt.target.addClass('hovered')
      })
      cy.on('mouseout', 'node, edge', (evt) => {
        evt.target.removeClass('hovered')
      })

      runLayoutAndFit()
      saveInitialViewport()
    }

    const destroy = () => {
      // 标记：中断后续布局/fit 等操作
      layoutRunId++

      if (cy) {
        try {
          cy.removeAllListeners()
        } catch (e) {
          // ignore
        }
        cy.destroy()
        cy = null
      }
    }

    onMounted(mountCytoscape)
    onBeforeUnmount(destroy)

    const applyOverlayEdges = () => {
      if (!cy) return
      const overlayEdgeSet = new Set((props.overlayEdges || []).map(e => `${e.source}|${e.target}`))
      cy.edges().forEach(edge => {
        const key = `${edge.data('source')}|${edge.data('target')}`
        edge.removeClass('overlay-edge')
        if (overlayEdgeSet.has(key)) {
          edge.addClass('overlay-edge')
        }
      })
    }

    watch([() => props.graph, () => props.baseGraph], () => {
      if (!cy) return
      cy.elements().remove()
      cy.add(buildElements())
      if (!props.freezeLayout) {
        runLayoutAndFit()
        saveInitialViewport()
      }
      applyOverlayEdges()
    }, { deep: true })

    watch(() => props.overlayEdges, () => {
      if (!cy) return
      applyOverlayEdges()
      cy.style().update()
    }, { deep: true })

    watch([() => props.highlightMap, () => props.roots], () => {
      if (!cy) return
      const highlight = props.highlightMap || {}
      const g = activeGraph.value

      g?.nodes?.forEach(n => {
        const id = String(n.id)
        const ele = cy.getElementById(id)
        if (ele && ele.nonempty) {
          const color = highlight[id]
          ele.data('highlightColor', color || '')
          ele.removeClass('topk normal dim')
          const dim = props.dimUnhighlighted && !color
          ele.addClass(color ? 'topk' : (dim ? 'dim' : 'normal'))
        }
      })

      if (props.dimUnhighlighted) {
        const hlIds = new Set(Object.keys(highlight || {}).map(x => String(x)))
        cy.edges().forEach(edge => {
          const s = String(edge.data('source'))
          const t = String(edge.data('target'))
          edge.removeClass('dim')
          if (!hlIds.has(s) || !hlIds.has(t)) {
            edge.addClass('dim')
          }
        })
      } else {
        cy.edges().removeClass('dim')
      }

      cy.style().update()
      if (!props.freezeLayout) {
        runLayoutAndFit()
        saveInitialViewport()
      }
    }, { deep: true })

    return { containerRef, hasData, onResetClick }
  }
}
</script>

<style scoped>
.graph-view { position: relative; width: 100%; }
.cy-container { position: absolute; inset: 0; }
.empty { position: absolute; inset: 0; display: flex; align-items: center; justify-content: center; color: #9ca3af; font-size: 13px; }

.reset-btn {
  position: absolute;
  top: 10px;
  right: 10px;
  z-index: 2;

  height: 28px;
  padding: 0 10px;
  border-radius: 6px;
  border: 1px solid rgba(0, 0, 0, 0.12);
  background: rgba(255, 255, 255, 0.92);
  color: #333;
  font-size: 12px;
  cursor: pointer;
}

.reset-btn:hover { background: rgba(255, 255, 255, 1); }
</style>

