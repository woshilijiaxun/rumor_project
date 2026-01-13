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

export default {
  name: 'PropagationGraphView',
  props: {
    graph: { type: Object, required: true },
    highlightMap: { type: Object, default: () => ({}) },
    roots: { type: Array, default: () => [] },
    height: { type: String, default: '420px' }
  },
  setup(props, { expose }) {
    const containerRef = ref(null)
    let cy = null

    const FIT_PADDING = 60
    let initialViewport = null

    const hasData = computed(() => Array.isArray(props.graph?.nodes) && props.graph.nodes.length > 0)

    const buildElements = (g) => {
      const highlight = props.highlightMap || {}
      const nodes = (g.nodes || []).map(n => {
        const id = String(n.id)
        const color = highlight[id]
        return {
          data: { id, label: n.label ?? id, highlightColor: color || '' },
          classes: color ? 'topk' : 'normal'
        }
      })

      const edges = (g.edges || []).map(e => ({
        data: {
          source: String(e.source),
          target: String(e.target),
          weight: e.weight != null ? Number(e.weight) : 0,
          label: e.weight != null ? String(e.weight) : ''
        }
      }))

      return [...nodes, ...edges]
    }

    const runLayoutAndFit = () => {
      if (!cy) return
      const roots = Array.isArray(props.roots) ? props.roots.map(r => String(r)) : []
      const layout = cy.layout({
        name: 'breadthfirst',
        animate: false,
        fit: true,
        padding: FIT_PADDING,
        directed: true,
        spacingFactor: 1.25,
        circle: false,
        grid: false,
        roots: roots.length ? roots : undefined,
        orientation: 'horizontal'
      })
      layout.run()
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
        elements: buildElements(props.graph || {}),
        style: [
          { selector: 'node', style: { 'background-color': '#1677ff', 'label': 'data(label)', 'font-size': 10, 'color': '#333', 'text-opacity': 0, 'min-zoomed-font-size': 10 } },
          { selector: 'edge', style: { 'line-color': '#9ca3af', 'width': 'mapData(weight, 0, 1, 1, 6)', 'curve-style': 'bezier', 'target-arrow-shape': 'triangle', 'target-arrow-color': '#9ca3af', 'arrow-scale': 0.8, 'label': 'data(label)', 'font-size': 8, 'color': '#666', 'text-opacity': 0, 'min-zoomed-font-size': 8 } },
          { selector: '.hovered', style: { 'text-opacity': 1 } },
          { selector: 'node:selected', style: { 'background-color': '#0d5ccc', 'text-opacity': 1 } },
          { selector: 'edge:selected', style: { 'line-color': '#0d5ccc', 'target-arrow-color': '#0d5ccc', 'text-opacity': 1 } },
          { selector: 'node.topk', style: { 'background-color': 'data(highlightColor)', 'border-width': 2, 'border-color': 'data(highlightColor)', 'opacity': 1, 'text-opacity': 1 } },
          { selector: 'node.normal', style: { 'opacity': 1 } }
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
      if (cy) {
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
      runLayoutAndFit()
      saveInitialViewport()
    }, { deep: true })

    watch([() => props.highlightMap, () => props.roots], () => {
      if (!cy) return
      const highlight = props.highlightMap || {}
      props.graph?.nodes?.forEach(n => {
        const id = String(n.id)
        const ele = cy.getElementById(id)
        if (ele && ele.nonempty) {
          const color = highlight[id]
          ele.data('highlightColor', color || '')
          ele.removeClass('topk normal')
          ele.addClass(color ? 'topk' : 'normal')
        }
      })
      cy.style().update()
      runLayoutAndFit()
      saveInitialViewport()
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

