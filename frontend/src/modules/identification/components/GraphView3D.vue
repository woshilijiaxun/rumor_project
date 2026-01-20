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
  name: 'GraphView3D',
  props: {
    graph: { type: Object, required: true },
    highlightMap: { type: Object, default: () => ({}) },
    nonTopkGray: { type: Boolean, default: true },
    overlayEdges: { type: Array, default: () => [] },
    height: { type: String, default: '420px' },
    layerGap: { type: Number, default: 900 },
  },
  setup(props, { expose }) {
    const containerRef = ref(null)
    let cy = null

    const FIT_PADDING = 60

    let initialViewport = null

    const hasData = computed(() => Array.isArray(props.graph?.layers) && props.graph.layers.length > 0)

    const _sortedLayers = () => {
      const layers = Array.isArray(props.graph?.layers) ? props.graph.layers : []
      return layers
        .slice()
        .sort((a, b) => {
          const av = Number(a?.layer_id)
          const bv = Number(b?.layer_id)
          if (Number.isFinite(av) && Number.isFinite(bv)) return av - bv
          return String(a?.layer_id ?? '').localeCompare(String(b?.layer_id ?? ''))
        })
    }

    const TILT_SLOPE = 0.8
    const LAYER_X_OFFSET = 260
    const MAX_CROSS_LINKS_PER_PAIR = 80

    const buildElements = () => {
      const layers = _sortedLayers()
      const highlight = props.highlightMap || {}

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
          edges.push({
            data: {
              source: `${layerId}::${String(s)}`,
              target: `${layerId}::${String(t)}`,
              label: e?.weight != null ? String(e.weight) : '',
              layerId,
            }
          })
        })
      })

      // 跨层连线（少量）：相邻层相同 rawId 之间连线，用于表达层间“对应/演化”关系
      const layersByIdx = layers.map(l => String(l?.layer_id ?? ''))
      for (let i = 0; i < layersByIdx.length - 1; i += 1) {
        const a = layersByIdx[i]
        const b = layersByIdx[i + 1]

        const aNodes = nodes.filter(n => n?.data?.layerId === a)
        const bSet = new Set(nodes.filter(n => n?.data?.layerId === b).map(n => String(n?.data?.rawId ?? '')))

        let added = 0
        for (let j = 0; j < aNodes.length; j += 1) {
          if (added >= MAX_CROSS_LINKS_PER_PAIR) break
          const rawId = String(aNodes[j]?.data?.rawId ?? '')
          if (!rawId) continue
          if (!bSet.has(rawId)) continue

          edges.push({
            data: {
              source: `${a}::${rawId}`,
              target: `${b}::${rawId}`,
              layerId: `${a}__${b}`,
              isCrossLayer: 1,
            },
            classes: 'cross-layer'
          })
          added += 1
        }
      }

      return [...nodes, ...edges]
    }

    const _applyLayerBandsTopDown = () => {
      if (!cy) return
      const layers = _sortedLayers()
      if (!layers.length) return

      layers.forEach((layer, idx) => {
        const layerId = String(layer?.layer_id ?? '')
        const targetY = idx * Number(props.layerGap || 160)
        cy.nodes(`[layerId = "${layerId}"]`).forEach(n => {
          const p = n.position()
          n.position({ x: p.x, y: targetY })
        })
      })

      const bb = cy.elements().boundingBox()
      const shiftY = bb.y1 - FIT_PADDING
      if (Number.isFinite(shiftY) && shiftY !== 0) {
        cy.nodes().forEach(n => {
          const p = n.position()
          n.position({ x: p.x, y: p.y - shiftY })
        })
      }
    }

    const runLayoutAndFit = () => {
      if (!cy) return

      const layers = _sortedLayers()

      // 每层独立布局：避免把整层节点强行压到同一条 y 线上导致“几条横线”
      layers.forEach((layer, idx) => {
        const layerId = String(layer?.layer_id ?? '')
        const eles = cy.elements().filter(el => el.data('layerId') === layerId)

        const layout = eles.layout({
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

        // 将该层整体平移到目标 y 带上（保留层内 y 方向结构）
        const targetTopY = idx * Number(props.layerGap || 160)
        const bb = eles.boundingBox()
        const dy = targetTopY - bb.y1
        if (Number.isFinite(dy) && dy !== 0) {
          cy.nodes(`[layerId = "${layerId}"]`).forEach(n => {
            const p = n.position()
            n.position({ x: p.x, y: p.y + dy })
          })
        }
      })

      // 每层轻微倾斜（shear）：层内 y 越大，x 越往右偏一点
      layers.forEach((layer, idx) => {
        const layerId = String(layer?.layer_id ?? '')
        const targetTopY = idx * Number(props.layerGap || 160)
        cy.nodes(`[layerId = "${layerId}"]`).forEach(n => {
          const p = n.position()
          const yInLayer = p.y - targetTopY
          const layerX = idx * LAYER_X_OFFSET
          n.position({ x: p.x + (TILT_SLOPE * yInLayer) + layerX, y: p.y })
        })
      })

      // 整体上移，让第一层贴近顶部
      const bbAll = cy.elements().boundingBox()
      const shiftY = bbAll.y1 - FIT_PADDING
      if (Number.isFinite(shiftY) && shiftY !== 0) {
        cy.nodes().forEach(n => {
          const p = n.position()
          n.position({ x: p.x, y: p.y - shiftY })
        })
      }

      cy.fit(undefined, FIT_PADDING)
    }

    const saveInitialViewport = () => {
      if (!cy) return
      initialViewport = {
        zoom: cy.zoom(),
        pan: { ...cy.pan() }
      }
    }

    const resetView = () => {
      if (!cy) return
      if (initialViewport) {
        cy.animate({
          zoom: initialViewport.zoom,
          pan: initialViewport.pan,
          duration: 250
        })
      } else {
        cy.fit(undefined, FIT_PADDING)
        saveInitialViewport()
      }
    }

    const onResetClick = () => {
      resetView()
    }

    expose({ resetView })

    const applyOverlayEdges = () => {
      if (!cy) return

      const rawPairs = Array.isArray(props.overlayEdges) ? props.overlayEdges : []
      const rawSet = new Set(
        rawPairs
          .map(e => {
            const s = e?.source
            const t = e?.target
            if (s == null || t == null) return ''
            return `${String(s)}|${String(t)}`
          })
          .filter(Boolean)
      )

      cy.edges().forEach(edge => {
        const sRaw = String(edge.data('source') || '').split('::').pop()
        const tRaw = String(edge.data('target') || '').split('::').pop()
        const key = `${sRaw}|${tRaw}`

        edge.removeClass('overlay-edge')
        if (rawSet.has(key)) {
          edge.addClass('overlay-edge')
        }
      })
    }

    const mountCytoscape = async () => {
      await nextTick()
      if (!containerRef.value) return

      cy = cytoscape({
        container: containerRef.value,
        elements: buildElements(),
        style: [
          { selector: 'node', style: { 'background-color': '#1677ff', 'label': 'data(label)', 'font-size': 10, 'color': '#333', 'text-opacity': 0, 'min-zoomed-font-size': 10 } },
          { selector: 'edge', style: { 'line-color': '#9ca3af', 'width': 1.2, 'curve-style': 'bezier', 'target-arrow-shape': 'triangle', 'target-arrow-color': '#9ca3af', 'arrow-scale': 0.7, 'label': 'data(label)', 'font-size': 8, 'color': '#666', 'text-opacity': 0, 'min-zoomed-font-size': 8 } },
          { selector: '.hovered', style: { 'text-opacity': 1 } },
          { selector: 'node:selected', style: { 'background-color': '#0d5ccc', 'text-opacity': 1 } },
          { selector: 'edge:selected', style: { 'line-color': '#0d5ccc', 'target-arrow-color': '#0d5ccc', 'text-opacity': 1 } },
          { selector: 'node.topk', style: { 'background-color': 'data(highlightColor)', 'border-width': 2, 'border-color': 'data(highlightColor)', 'opacity': 1 } },
          { selector: 'node.not-topk', style: { 'background-color': '#9ca3af', 'opacity': 0.22 } },
          { selector: 'node.not-topk-blue', style: { 'background-color': '#1677ff', 'opacity': 1 } },
          { selector: 'edge.overlay-edge', style: { 'line-color': '#ef4444', 'target-arrow-color': '#ef4444', 'opacity': 0.95, 'width': 2.5 } },
          { selector: 'edge.cross-layer', style: { 'line-color': '#94a3b8', 'line-style': 'dashed', 'width': 0.8, 'opacity': 0.35, 'target-arrow-shape': 'none', 'curve-style': 'bezier' } },
        ],
        wheelSensitivity: 0.2
      })

      runLayoutAndFit()
      applyOverlayEdges()
      saveInitialViewport()
    }

    const destroy = () => {
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
      cy.add(buildElements())
      runLayoutAndFit()
      applyOverlayEdges()
      saveInitialViewport()
    }, { deep: true })

    watch([() => props.highlightMap, () => props.nonTopkGray], () => {
      if (!cy) return
      const highlight = props.highlightMap || {}
      const nonGray = !!props.nonTopkGray

      cy.nodes().forEach(n => {
        const rawId = n.data('rawId')
        const color = highlight[String(rawId)]
        n.data('highlightColor', color || '')
        n.removeClass('topk not-topk not-topk-blue')
        n.addClass(color ? 'topk' : (nonGray ? 'not-topk' : 'not-topk-blue'))
      })

      cy.style().update()
    }, { deep: true })

    watch(() => props.overlayEdges, () => {
      if (!cy) return
      applyOverlayEdges()
      cy.style().update()
    }, { deep: false })

    watch(() => props.layerGap, () => {
      if (!cy) return
      _applyLayerBandsTopDown()
      cy.fit(undefined, FIT_PADDING)
      saveInitialViewport()
    })

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
