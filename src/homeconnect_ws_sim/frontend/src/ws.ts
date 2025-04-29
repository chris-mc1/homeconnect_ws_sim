import { type UpdateMessage, type WsMessage } from '@/types'
import { useStore } from '@/store'

class Ws {
  websocket: WebSocket | undefined
  async ws_init() {
    const url = new URL('/api/ws', window.location.origin)
    url.protocol = 'ws:'
    console.log('Starting connection to WebSocket')
    this.websocket = new WebSocket(url)
    this.websocket.onmessage = this.ws_onmessage
    this.websocket.onopen = function (event) {
      console.log('Connected to WebSocket')
    }
    this.websocket.onclose = function (event) {
      console.log('Closed WebSocket')
    }
    this.websocket.onerror = function (event) {
      console.log('WebSocket Error')
    }
  }

  async ws_onmessage(event: MessageEvent) {
    const message: WsMessage = JSON.parse(event.data)
    if (message.action == 'init') {
      useStore().init_entities(message)
    }
    if (message.action == 'update') {
      useStore().update_entity(message)
    }
  }
  async send(data: object) {
    this.websocket?.send(JSON.stringify(data))
  }
}

const ws = new Ws()

export default ws
