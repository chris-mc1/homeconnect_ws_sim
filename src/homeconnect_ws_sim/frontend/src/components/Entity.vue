<script setup lang="ts">
import { EntityProtocolType, type Entity } from '@/types'
import ItemSwitch from './ItemSwitch.vue'
import ItemAccess from './ItemAccess.vue'
import ItemText from './ItemText.vue'
import ItemEnum from './ItemEnum.vue'
import ItemTextValue from './ItemTextValue.vue'
import ItemInt from './ItemInt.vue'
import ItemIntValue from './ItemIntValue.vue'
import {entity_ppt,EntityPropertyType } from "@/const"

const entity = defineModel<Entity>({ required: true })

const getComponent = (type: EntityPropertyType, entity:Entity) => {
  switch (type) {
    case EntityPropertyType.SWITCH:
      return ItemSwitch
    case EntityPropertyType.ACCESS:
      return ItemAccess
    case EntityPropertyType.VALUE:
      switch (entity.protocolType) {
        case EntityProtocolType.BOOLEAN:
          return ItemSwitch
        case EntityProtocolType.FLOAT:
          return ItemText
        case EntityProtocolType.INTEGER:
          if (entity.enum != null) {
            return ItemEnum
          }
          return ItemIntValue
        case EntityProtocolType.OBJECT:
          return ItemTextValue

        case EntityProtocolType.STRING:
          return ItemTextValue
      }
    case EntityPropertyType.INTEGER:
      return ItemInt
    default:
      return ItemText
  }
}
</script>

<template>
  <v-card>
    <v-card-title class="text-wrap pt-1 pb-0 px-2 text-truncate" style="font-size: 0.97em">
      {{ entity.name }}
    </v-card-title>
    <v-card-text class="pa-2 pt-0 d-flex flex-gap flex-wrap ga-2">
      <template v-for="ppt in entity_ppt">
        <component :is="getComponent(ppt.type, entity)" :entity="entity" :ppt="ppt">
        </component>
      </template>
    </v-card-text>
  </v-card>
</template>
<!-- v-if="entity[ppt.key] != null" -->
