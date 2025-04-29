<script setup lang="ts">
import type { pptMetadata } from '@/const';
import { type Entity } from '@/types'

const props = defineProps<{ entity: Entity; ppt: pptMetadata}>()

</script>

<template>
  <div class="d-flex flex-column">
    <div class="text-caption text-grey">
      {{ ppt.key }}
    </div>
    <div>
      {{ entity[ppt.key] }}
    </div>
  </div>
</template>
