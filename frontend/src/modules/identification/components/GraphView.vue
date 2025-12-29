<template>
  <div class="graph-view" :style="{ height }">
    <div ref="containerRef" class="cy-container"></div>
    <div v-if="!hasData" class="empty">暂无可视化数据</div>

    <!-- 收缩按钮 -->
    <button v-if="collapsed" class="layout-toggle" @click.stop="openPanel">布局</button>

    <!-- 布局参数面板 -->
    <div v-else class="layout-controls" @mousedown.stop @wheel.stop @touchstart.stop>
      <div class="row header">
        <div class="title">布局参数</div>
        <button class="close-btn" @click.stop="closePanel">×</button>
      </div>
      <div class="row">
        <label>布局模式</label>
        <select v-model="layoutMode" class="ctl-input" @change="onControlChange">
          <option value="auto">自动</option>
          <option value="concentric">同心(小图)</option>
          <option value="fcose-components">分组件 fcose(大图)</option>
        </select>
      </div>

      <template v-if="layoutMode !== 'fcose-components'">
        <div class="row">
          <label>Padding: {{ concentricPadding }}</label>
          <input class="ctl-range" type="range" min="0" max="200" step="5" v-model.number="concentricPadding" @change="onControlChange" />
        </div>
        <div class="row">
          <label>节点最小间距: {{ minNodeSpacingCtl }}</label>
          <input class="ctl-range" type="range" min="0" max="200" step="5" v-model.number="minNodeSpacingCtl" @change="onControlChange" />
        </div>
        <div class="row">
          <label>Fit留白: {{ fitPadding }}</label>
          <input class="ctl-range" type="range" min="0" max="300" step="5" v-model.number="fitPadding" @change="onControlChange" />
        </div>
      </template>

      <template v-else>
        <div class="row">
          <label>组件间距: {{ componentsSpacing }}</label>
          <input class="ctl-range" type="range" min="100" max="1200" step="50" v-model.number="componentsSpacing" @change="onControlChange" />
        </div>
        <div class="row">
          <label>nodeSeparation: {{ fcoseNodeSeparation }}</label>
          <input class="ctl-range" type="range" min="0" max="300" step="5" v-model.number="fcoseNodeSeparation" @change="onControlChange" />
        </div>
        <div class="row">
          <label>componentSpacing: {{ fcoseComponentSpacing }}</label>
          <input class="ctl-range" type="range" min="0" max="600" step="10" v-model.number="fcoseComponentSpacing" @change="onControlChange" />
        </div>
        <div class="row">
          <label>nodeRepulsion: {{ fcoseNodeRepulsion }}</label>
          <input class="ctl-range" type="range" min="0" max="40000" step="500" v-model.number="fcoseNodeRepulsion" @change="onControlChange" />
        </div>
        <div class="row">
          <label>idealEdgeLength: {{ fcoseIdealEdgeLen }}</label>
          <input class="ctl-range" type="range" min="10" max="400" step="10" v-model.number="fcoseIdealEdgeLen" @change="onControlChange" />
        </div>
        <div class="row">
          <label>gravity: {{ fcoseGravity }}</label>
          <input class="ctl-range" type="range" min="0" max="2" step="0.05" v-model.number="fcoseGravity" />
        </div>
        <div class="row">
          <label>Fit留白: {{ fitPadding }}</label>
          <input class="ctl-range" type="range" min="0" max="300" step="5" v-model.number="fitPadding" @change="onControlChange" />
        </div>
      </template>
    </div>
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
    graph: {
      type: Object,
      required: true
    },
    layout: {
      type: String,
      default: 'cose'
    },
    height: {
      type: String,
      default: '420px'
    }
  },
  setup(props) {
    const containerRef = ref(null)
    let cy = null

    // 布局参数面板状态
    const collapsed = ref(true)
    let collapseTimer = null
    const layoutMode = ref('auto') // auto | concentric | fcose-components
    const concentricPadding = ref(60)
    const minNodeSpacingCtl = ref(40)
    const componentsSpacing = ref(800)
    const fcoseNodeSeparation = ref(80)
    const fcoseComponentSpacing = ref(200)
    const fcoseNodeRepulsion = ref(6000)
    const fcoseIdealEdgeLen = ref(150)
    const fcoseGravity = ref(0.25)
    const fitPadding = ref(120)

    const openPanel = () => { collapsed.value = false }
    const closePanel = () => { collapsed.value = true }
    const onControlChange = () => {
      if (collapseTimer) clearTimeout(collapseTimer)
      collapseTimer = setTimeout(() => { collapsed.value = true }, 800)
    }

    const hasData = computed(() => {
      const g = props.graph || {}
      return Array.isArray(g.nodes) && g.nodes.length > 0
    })

    const buildElements = (g) => {
      const nodes = (g.nodes || []).map(n => ({ data: { id: String(n.id), label: n.label ?? String(n.id) } }))
      const edges = (g.edges || []).map(e => ({ data: { source: String(e.source), target: String(e.target), label: e.weight != null ? String(e.weight) : '' } }))
      return [...nodes, ...edges]
    }

    const getLayoutOptions = (g) => {
      // 同心圆布局参数由面板控制
      return { name: 'concentric', animate: false, padding: concentricPadding.value, startAngle: 3/2 * Math.PI, sweep: 2 * Math.PI, equidistant: true, minNodeSpacing: minNodeSpacingCtl.value }
    }

    const applyFcoseWithComponents = () => {
      if (!cy) return
      const comps = cy.elements().components() // 连通分量集合
      const spacing = componentsSpacing.value // 组件间横向间距
      let offsetX = 0
      comps.forEach((comp) => {
        const layout = comp.layout({
          name: 'fcose',
          animate: false,
          randomize: true,
          fit: false,
          padding: 30,
          quality: 'default',
          nodeSeparation: fcoseNodeSeparation.value,
          componentSpacing: fcoseComponentSpacing.value,
          nodeRepulsion: () => fcoseNodeRepulsion.value,
          idealEdgeLength: () => fcoseIdealEdgeLen.value,
          edgeElasticity: () => 0.2,
          gravity: fcoseGravity.value
        })
        layout.run()
        const bb = comp.boundingBox()
        const dx = offsetX - bb.x1
        const dy = 0 - bb.y1
        cy.batch(() => {
          comp.nodes().forEach((ele) => {
            const p = ele.position()
            ele.position({ x: p.x + dx, y: p.y + dy })
          })
        })
        offsetX += bb.w + spacing
      })
      cy.fit(undefined, fitPadding.value)
    }

    const applyLayout = (g) => {
      if (!cy) return
      const n = (g.nodes || []).length
      const mode = layoutMode.value
      if (mode === 'fcose-components' || (mode === 'auto' && n > 60)) {
        applyFcoseWithComponents()
      } else { // concentric
        cy.layout(getLayoutOptions(g)).run()
        cy.fit(undefined, fitPadding.value)
      }
    }

    const mountCytoscape = async () => {
      await nextTick()
      if (!containerRef.value) return
      const g = props.graph || { nodes: [], edges: [] }
      cy = cytoscape({
        container: containerRef.value,
        elements: buildElements(g),
        style: [
          { selector: 'node', style: { 'background-color': '#1677ff', 'label': 'data(label)', 'font-size': 10, 'color': '#333', 'text-opacity': 0, 'min-zoomed-font-size': 10 } },
          { selector: 'edge', style: { 'line-color': '#9ca3af', 'width': 1.5, 'curve-style': 'bezier', 'target-arrow-shape': 'triangle', 'target-arrow-color': '#9ca3af', 'arrow-scale': 0.8, 'label': 'data(label)', 'font-size': 8, 'color': '#666', 'text-opacity': 0, 'min-zoomed-font-size': 8 } },
          { selector: '.hovered', style: { 'text-opacity': 1 } },
          { selector: 'node:selected', style: { 'background-color': '#0d5ccc', 'text-opacity': 1 } },
          { selector: 'edge:selected', style: { 'line-color': '#0d5ccc', 'target-arrow-color': '#0d5ccc', 'text-opacity': 1 } }
        ],
        wheelSensitivity: 0.2
      })
      applyLayout(g)

      // 交互增强：点击高亮相邻
      cy.on('select', 'node', (evt) => {
        const n = evt.target
        const neighborhood = n.closedNeighborhood()
        cy.elements().difference(neighborhood).addClass('faded')
      })
      cy.on('unselect', 'node', () => {
        cy.elements().removeClass('faded')
      })
      cy.style().selector('.faded').style({ 'opacity': 0.25 }).update()

      // 悬停时仅显示当前元素（以及相邻边）的标签
      cy.on('mouseover', 'node', (evt) => {
        const n = evt.target
        n.addClass('hovered')
        n.connectedEdges().addClass('hovered')
      })
      cy.on('mouseout', 'node', (evt) => {
        const n = evt.target
        n.removeClass('hovered')
        n.connectedEdges().removeClass('hovered')
      })
      cy.on('mouseover', 'edge', (evt) => {
        evt.target.addClass('hovered')
      })
      cy.on('mouseout', 'edge', (evt) => {
        evt.target.removeClass('hovered')
      })
    }

    const destroyCytoscape = () => {
      if (cy) {
        cy.destroy()
        cy = null
      }
    }

    const rerender = () => {
      if (!containerRef.value) return
      if (!cy) {
        mountCytoscape()
      } else {
        const g = props.graph || { nodes: [], edges: [] }
        cy.elements().remove()
        cy.add(buildElements(g))
        applyLayout(g)
      }
    }

    onMounted(mountCytoscape)
    onBeforeUnmount(destroyCytoscape)

    watch(() => props.graph, () => {
      rerender()
    }, { deep: true })

    // 参数变更时重跑布局
    watch([
      layoutMode,
      concentricPadding,
      minNodeSpacingCtl,
      componentsSpacing,
      fcoseNodeSeparation,
      fcoseComponentSpacing,
      fcoseNodeRepulsion,
      fcoseIdealEdgeLen,
      fcoseGravity,
      fitPadding
    ], () => {
      if (!cy) return
      applyLayout(props.graph || { nodes: [], edges: [] })
    })

    return {
      containerRef,
      hasData,
      // 折叠控制
      collapsed,
      openPanel,
      closePanel,
      onControlChange,
      // 控件绑定
      layoutMode,
      concentricPadding,
      minNodeSpacingCtl,
      componentsSpacing,
      fcoseNodeSeparation,
      fcoseComponentSpacing,
      fcoseNodeRepulsion,
      fcoseIdealEdgeLen,
      fcoseGravity,
      fitPadding
    }
  }
}
</script>

<style scoped>
.graph-view {
  position: relative;
  width: 100%;
}
.cy-container {
  position: absolute;
  inset: 0;
}
.empty {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #9ca3af;
  font-size: 13px;
}

.layout-controls {
  position: absolute;
  top: 8px;
  right: 8px;
  z-index: 2;
  background: rgba(255, 255, 255, 0.92);
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 10px 12px;
  width: 280px;
  box-shadow: 0 6px 18px rgba(0,0,0,0.08);
  backdrop-filter: saturate(120%) blur(4px);
}
.layout-controls .row { margin-bottom: 8px; display: grid; grid-template-columns: 1fr; gap: 6px; }
.layout-controls .row:last-child { margin-bottom: 0; }
.layout-controls label { font-size: 12px; color: #374151; }
.layout-controls .ctl-input { width: 100%; padding: 6px 8px; border: 1px solid #d1d5db; border-radius: 6px; font-size: 12px; }
.layout-controls .ctl-range { width: 100%; }

/* 折叠按钮样式 */
.layout-toggle {
  position: absolute;
  top: 8px;
  right: 8px;
  z-index: 2;
  padding: 6px 10px;
  background-color: #1677ff;
  color: #fff;
  border: none;
  border-radius: 6px;
  font-size: 12px;
  cursor: pointer;
  box-shadow: 0 4px 12px rgba(0,0,0,0.12);
}
.layout-toggle:hover { background-color: #0d5ccc; }

/* 面板头部 */
.layout-controls .row.header { display: flex; align-items: center; justify-content: space-between; }
.layout-controls .row.header .title { font-weight: 600; color: #1f2937; }
.layout-controls .row.header .close-btn {
  background: none;
  border: none;
  font-size: 18px;
  line-height: 1;
  width: 28px;
  height: 28px;
  border-radius: 6px;
  color: #6b7280;
  cursor: pointer;
}
.layout-controls .row.header .close-btn:hover { background-color: #f3f4f6; color: #111827; }
</style>

