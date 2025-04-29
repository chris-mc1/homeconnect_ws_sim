<script setup lang="ts">
import type { pptMetadata } from '@/const';
import { type Entity } from '@/types'
import ws from "@/ws"
const props = defineProps<{ entity: Entity; ppt: pptMetadata }>()

async function update(value: any) {
  let key = String(props.ppt.key)
  if (key == "value") {
    key = "value_raw"
  }
  let data = {action : "set", uid: props.entity.uid, key: key, value: value}
  ws.send(data)
}

</script>

<template>
  <div class="d-flex flex-column">
    <div class="text-caption text-grey">
      {{ ppt.key }}
    </div>
    <div>
      <v-switch v-model="entity[ppt.key]" color="primary" density="compact" @update:model-value="update"></v-switch>
    </div>
  </div>
</template>
