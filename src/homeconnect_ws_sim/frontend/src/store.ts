import { defineStore } from 'pinia'
import { type Entity, type WsMessage } from '@/types'

export const useStore = defineStore('store', {
  state: () => ({
    entities: {} as { [key: string]: Entity },
  }),
  actions: {
    update_entity(message: WsMessage) {
      this.entities[message.entity.uid] = message.entity
    },
    init_entities(message: WsMessage) {
      this.$reset()
      let idx
      for (idx in message.entities) {
        let entity = message.entities[idx]
        this.entities[entity.uid] = entity
      }
    },
  },
})
