<script setup lang="ts">
import type { pptMetadata } from '@/const';
import { type Entity } from '@/types'
import ws from "@/ws"
const props = defineProps<{ entity: Entity; ppt: pptMetadata }>()

async function update(value: any) {
  let data = {action : "set", uid: props.entity.uid, key: props.ppt.key, value: value}
  ws.send(data)
}

</script>

<template>
  <div class="d-flex flex-column">
    <div class="text-caption text-grey">
      {{ ppt.key }}
    </div>
    <div class="d-flex">
      <v-number-input v-model="entity[ppt.key]" controlVariant="stacked" @update:model-value="update"
        min-width="150"></v-number-input>
    </div>
  </div>
</template>
