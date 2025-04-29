<script setup lang="ts">
import { computed, onBeforeMount, ref } from 'vue'
import ws from "@/ws"
import {useStore} from "@/store"
import Entity from '@/components/Entity.vue'

const files_ref = ref<File[]>()
const store = useStore()
const search = ref('')

async function submit(): Promise<void> {
  let files = files_ref.value
  if (files) {
    let formData = new FormData()
    for (let i in files) {
      let file = files[i]
      formData.append(file.name, file)
    }
    fetch('/api/file_upload', { method: 'POST', body: formData })
  }
}

const entities = computed(() => {
  return Object.values(store.entities)
})

onBeforeMount(async () => {
  await ws.ws_init()
})
</script>

<template>
  <v-app>
    <v-app-bar color="primary">
      <v-app-bar-title>Home Connect Websocket Simulator</v-app-bar-title>
      <v-dialog max-width="500">
        <template v-slot:activator="{ props: activatorProps }">
          <v-btn v-bind="activatorProps" text="Add new Appliance" variant="flat"></v-btn>
        </template>
        <template v-slot:default="{ isActive }">
          <v-card title="Upload new Profile File">
            <v-card-text>
              <v-file-input multiple v-model="files_ref" label="Profile File"></v-file-input>
            </v-card-text>
            <v-card-actions>
              <v-btn @click.stop="submit().then(() => {isActive.value = false})">Submit</v-btn>
            </v-card-actions>
          </v-card>
        </template>
      </v-dialog>
    </v-app-bar>
    <v-main>
      <v-container class="ma-0">
        <v-text-field v-model="search" label="Search" prepend-inner-icon="mdi-magnify" hide-details
          single-line></v-text-field>
        <v-data-table :items="entities" :search="search" :filter-keys="['name', 'uid']" hide-default-header
          class="pa-0">
          <template v-slot:item="{ item }">
            <Entity :model-value="item"></Entity>
          </template>
        </v-data-table>
      </v-container>
    </v-main>
  </v-app>
</template>
