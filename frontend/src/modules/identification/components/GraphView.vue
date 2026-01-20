<template>
  <div class="graph-view" :style="{ height }">
    <div ref="containerRef" class="cy-container"></div>

    <!-- 复原：回到初始视角（初始 pan/zoom），不重新布局、不改变节点位置 -->
    <button v-if="hasData" class="reset-btn" type="button" @click="onResetClick">
      复原
    </button>

    <div v-if="!hasData" class="empty">暂无可视化数据</div>
  </div>
</template>

<script>
import { ref, onMounted, onBeforeUnmount, watch, computed, nextTick } from 'vue'
import cytoscape from 'cytoscape'
import fcose from 'cytoscape-fcose'
cytoscape.use(fcose)

export default {
  name: 'GraphView',
  props: {
    graph: { type: Object, required: true },
    highlightMap: { type: Object, default: () => ({}) },
    nonTopkGray: { type: Boolean, default: true },
    height: { type: String, default: '420px' }
  },
  setup(props, { expose }) {
    const containerRef = ref(null)
    let cy = null

    const FIT_PADDING = 60
    const LAYER_GAP = 160

    // 记录“初始展示”的视角（pan/zoom）。
    // 这里的“初始”指：首次布局完成并 fit 之后的视角。
    let initialViewport = null

    const hasData = computed(() => {
      if (props.graph?.type === 'multilayer') {
        return Array.isArray(props.graph?.layers) && props.graph.layers.length > 0
      }
      return Array.isArray(props.graph?.nodes) && props.graph.nodes.length > 0
    })

    const buildElements = (g) => {
      const highlight = props.highlightMap || {}

      // 多层：把每一层当作一个“分区”(layer band)，用 y 固定到不同带上来形成“自上而下”的分层效果。
      // 规则：layer_id 越小越靠上（y 越小），层间距由 LAYER_GAP 控制。
      if (g?.type === 'multilayer' && Array.isArray(g.layers)) {
        const layers = g.layers
          .slice()
          .sort((a, b) => {
            const av = Number(a?.layer_id)
            const bv = Number(b?.layer_id)
            if (Number.isFinite(av) && Number.isFinite(bv)) return av - bv
            return String(a?.layer_id ?? '').localeCompare(String(b?.layer_id ?? ''))
          })

        const nodeKeySet = new Set()
        const nodes = []
        const edges = []

        layers.forEach((layer, idx) => {
          const layerId = String(layer?.layer_id ?? '')
          const rawNodes = Array.isArray(layer?.nodes) ? layer.nodes : []
          rawNodes.forEach(n => {
            const rawId = String(n?.id)
            if (!rawId) return
            const id = `${layerId}::${rawId}`
            if (nodeKeySet.has(id)) return
            nodeKeySet.add(id)

            const color = highlight[rawId]
            nodes.push({
              data: {
                id,
                label: String(n?.label ?? rawId),
                highlightColor: color || '',
                rawId,
                layerId,
                layerIndex: idx,
              },
              classes: color ? 'topk' : (props.nonTopkGray ? 'not-topk' : 'not-topk-blue')
            })
          })

          const rawEdges = Array.isArray(layer?.edges) ? layer.edges : []
          rawEdges.forEach(e => {
            const s = e?.source
            const t = e?.target
            if (s == null || t == null) return
            const source = `${layerId}::${String(s)}`
            const target = `${layerId}::${String(t)}`
            edges.push({
              data: {
                source,
                target,
                label: e?.weight != null ? String(e.weight) : '',
                layerId,
              }
            })
          })
        })

        return [...nodes, ...edges]
      }

      // 单层（原逻辑）
      const nodes = (g.nodes || []).map(n => {
        const id = String(n.id)
        const color = highlight[id]
        return {
          data: { id, label: n.label ?? id, highlightColor: color || '' },
          classes: color ? 'topk' : (props.nonTopkGray ? 'not-topk' : 'not-topk-blue')
        }
      })
      const edges = (g.edges || []).map(e => ({ data: { source: String(e.source), target: String(e.target), label: e.weight != null ? String(e.weight) : '' } }))
      return [...nodes, ...edges]
    }

    const _sortedLayerIds = () => {
      const layers = Array.isArray(props.graph?.layers) ? props.graph.layers : []
      return layers
        .slice()
        .sort((a, b) => {
          const av = Number(a?.layer_id)
          const bv = Number(b?.layer_id)
          if (Number.isFinite(av) && Number.isFinite(bv)) return av - bv
          return String(a?.layer_id ?? '').localeCompare(String(b?.layer_id ?? ''))
        })
        .map(l => String(l?.layer_id ?? ''))
    }

    const _applyLayerBandsTopDown = () => {
      if (!cy) return
      const ids = _sortedLayerIds()
      if (!ids.length) return

      // y 越小越靠上：第一层(最小 layer_id)放最上
      ids.forEach((layerId, idx) => {
        const targetY = idx * LAYER_GAP
        cy.nodes(`[layerId = "${layerId}"]`).forEach(n => {
          const p = n.position()
          n.position({ x: p.x, y: targetY })
        })
      })

      // 整体上移，让第一层贴近顶部（居中看起来更“上到下”）
      const bb = cy.elements().boundingBox()
      const shiftY = bb.y1 - FIT_PADDING
      if (Number.isFinite(shiftY) && shiftY !== 0) {
        cy.nodes().forEach(n => {
          const p = n.position()
          n.position({ x: p.x, y: p.y - shiftY })
        })
      }
    }

    let layoutRunId = 0
    const yieldToMain = () => new Promise(resolve => setTimeout(resolve, 0))

    const runLayoutAndFit = async () => {
      if (!cy) return

      const runId = ++layoutRunId

      // 先让出一个 tick，保证返回按钮/路由跳转能先被处理
      await yieldToMain()
      if (runId !== layoutRunId || !cy) return

      // 多层：先在全图上跑一次 fcose（保证层内形状合理），然后强制压到层带（自上而下）
      if (props.graph?.type === 'multilayer' && Array.isArray(props.graph.layers)) {
        const layout = cy.layout({
          name: 'fcose',
          animate: false,
          randomize: true,
          fit: false,
          padding: FIT_PADDING,
          quality: 'default',
          nodeSeparation: 80,
          nodeRepulsion: 6000,
          idealEdgeLength: 150,
          edgeElasticity: 0.2,
          gravity: 0.25,
        })

        layout.run()
        if (runId !== layoutRunId || !cy) return

        _applyLayerBandsTopDown()
        if (runId !== layoutRunId || !cy) return

        cy.fit(undefined, FIT_PADDING)
        return
      }

      // 单层（原逻辑）
      const layout = cy.layout({
        name: 'fcose',
        animate: false,
        randomize: true,
        fit: true,
        padding: FIT_PADDING,
        quality: 'default',
        nodeSeparation: 80,
        nodeRepulsion: 6000,
        idealEdgeLength: 150,
        edgeElasticity: 0.2,
        gravity: 0.25
      })
      layout.run()
      if (runId !== layoutRunId || !cy) return

      cy.fit(undefined, FIT_PADDING)
    }

    const saveInitialViewport = () => {
      if (!cy) return
      initialViewport = {
        zoom: cy.zoom(),
        pan: { ...cy.pan() }
      }
    }

    // 复原视图：只恢复到初始 pan/zoom（不重新布局）
    const resetView = () => {
      if (!cy) return
      if (initialViewport) {
        // 用动画更自然一点；如果你想瞬间复位，可以把 duration 改为 0
        cy.animate({
          zoom: initialViewport.zoom,
          pan: initialViewport.pan,
          duration: 250
        })
      } else {
        // 兜底：如果初始视角还没记录到，就至少 fit 回去
        cy.fit(undefined, FIT_PADDING)
        saveInitialViewport()
      }
    }

    const onResetClick = () => {
      resetView()
    }

    // expose reset method for parent
    expose({ resetView })

    const mountCytoscape = async () => {
      await nextTick()
      if (!containerRef.value) return
      cy = cytoscape({
        container: containerRef.value,
        elements: buildElements(props.graph || {}),
        style: [
          { selector: 'node', style: { 'background-color': '#1677ff', 'label': 'data(label)', 'font-size': 10, 'color': '#333', 'text-opacity': 0, 'min-zoomed-font-size': 10 } },
          { selector: 'edge', style: { 'line-color': '#9ca3af', 'width': 1.5, 'curve-style': 'bezier', 'target-arrow-shape': 'triangle', 'target-arrow-color': '#9ca3af', 'arrow-scale': 0.8, 'label': 'data(label)', 'font-size': 8, 'color': '#666', 'text-opacity': 0, 'min-zoomed-font-size': 8 } },
          { selector: '.hovered', style: { 'text-opacity': 1 } },
          { selector: 'node:selected', style: { 'background-color': '#0d5ccc', 'text-opacity': 1 } },
          { selector: 'edge:selected', style: { 'line-color': '#0d5ccc', 'target-arrow-color': '#0d5ccc', 'text-opacity': 1 } },
          { selector: 'node.topk', style: { 'background-color': 'data(highlightColor)', 'border-width': 2, 'border-color': 'data(highlightColor)', 'opacity': 1 } },
          { selector: 'node.not-topk', style: { 'background-color': '#9ca3af', 'opacity': 0.22 } },
          { selector: 'node.not-topk-blue', style: { 'background-color': '#1677ff', 'opacity': 1 } }
        ],
        wheelSensitivity: 0.2
      })

      // 初次渲染：布局 + fit，并记录“初始视角”
      runLayoutAndFit()
      saveInitialViewport()

      // interactions kept (omitted here for brevity)
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

    watch(() => props.graph, () => {
      if (!cy) return
      cy.elements().remove()
      cy.add(buildElements(props.graph || {}))

      // 数据变化时还是需要重新布局；并更新“初始视角”
      runLayoutAndFit()
      saveInitialViewport()
    }, { deep: true })

    watch([() => props.highlightMap, () => props.nonTopkGray], () => {
      if (!cy) return
      const highlight = props.highlightMap || {}
      const nonGray = !!props.nonTopkGray
      props.graph?.nodes?.forEach(n => {
        const id = String(n.id)
        const ele = cy.getElementById(id)
        if (ele && ele.nonempty) {
          const color = highlight[id]
          ele.data('highlightColor', color || '')
          ele.removeClass('topk not-topk not-topk-blue')
          ele.addClass(color ? 'topk' : (nonGray ? 'not-topk' : 'not-topk-blue'))
        }
      })
      cy.style().update()
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
