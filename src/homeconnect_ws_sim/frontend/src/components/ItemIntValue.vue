<script setup lang="ts">
import type { pptMetadata } from '@/const';
import { type Entity } from '@/types'
import ws from "@/ws"
const props = defineProps<{ entity: Entity; ppt: pptMetadata }>()

async function update(value: any) {
  let data = {action : "set", uid: props.entity.uid, key: "value_raw", value: value}
  ws.send(data)
}

</script>

<template>
  <div class="d-flex flex-column">
    <div class="text-caption text-grey">
      {{ ppt.key }}
    </div>
    <div>
      <v-number-input v-if="entity.step != null" v-model="entity[ppt.key]" controlVariant="stacked"
        @update:model-value="update" :min="entity.min" :max="entity.max" :step="entity.step"></v-number-input>
      <v-number-input v-else-if="entity.min != null" v-model="entity[ppt.key]" controlVariant="stacked"
        @update:model-value="update" :min="entity.min" :max="entity.max"></v-number-input>
      <v-number-input v-else v-model="entity[ppt.key]" controlVariant="stacked"
        @update:model-value="update"></v-number-input>
    </div>
  </div>
</template>
