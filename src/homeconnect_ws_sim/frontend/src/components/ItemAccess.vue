<script setup lang="ts">
import type { pptMetadata } from '@/const';
import { type Entity } from '@/types'
import ws from "@/ws"
const props = defineProps<{ entity: Entity; ppt: pptMetadata }>()


const items = [
  {
    title: 'None',
    value: "NONE"
  },
  {
    title: 'Read',
    value: "READ"
  },
  {
    title: 'Read Write',
    value: "READWRITE"
  },
  {
    title: 'Write Only',
    value: "WRITEONLY"
  },
  {
    title: 'Read static',
    value: "READSTATIC"
  },

]

async function update(value: any) {
  let key = String(props.ppt.key)
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
      <v-select :items="items" v-model="props.entity[props.ppt.key]" width="120" density="compact"
        @update:model-value="update" menu-icon=""></v-select>
    </div>
  </div>
</template>
