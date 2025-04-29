<script setup lang="ts">
import { computed } from 'vue'
import type { pptMetadata } from '@/const'
import { type Entity } from '@/types'
import ws from '@/ws'
const props = defineProps<{ entity: Entity; ppt: pptMetadata }>()

const items = computed(() => {
  let items_list = []
  let value
  for (value in props.entity.enum) {
    items_list.push({ title: props.entity.enum[value], value: Number(value) })
  }
  return items_list
})

async function update(value: any) {
  props.entity[props.ppt.key]
  let data = { action: 'set', uid: props.entity.uid, key: "value_raw", value: value }
  ws.send(data)
}
</script>

<template>
  <div class="d-flex flex-column">
    <div class="text-caption text-grey">
      {{ ppt.key }}
    </div>
    <div>
      <v-select :items="items" v-model="props.entity.value_raw" width="120" density="compact"
        @update:model-value="update" menu-icon=""></v-select>
    </div>
  </div>
</template>
