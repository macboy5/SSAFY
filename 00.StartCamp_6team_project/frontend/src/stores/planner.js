import { defineStore } from 'pinia'
import { plannerApi } from '../api/client'

const service = plannerApi()

export const usePlannerStore = defineStore('planner', {
  state: () => ({ items: [], loading: false, error: '', ready: false }),
  getters: {
    byDate: (state) => (date) => state.items.filter((item) => item.plan_date === date),
  },
  actions: {
    async load() {
      this.loading = true; this.error = ''
      try { this.items = await service.get(); this.ready = true }
      catch (e) { this.error = e.message }
      finally { this.loading = false }
    },
    async addItem(date, content) {
      const item = await service.add({ content_id: content.contentid, plan_date: date })
      this.items.push(item)
      return item
    },
    async updateItem(item, changes) {
      const updated = await service.update(item.id, changes)
      const index = this.items.findIndex((x) => x.id === item.id)
      if (index >= 0) this.items[index] = updated
    },
    async removeItem(item) {
      await service.remove(item.id)
      this.items = this.items.filter((x) => x.id !== item.id)
    },
  },
})
