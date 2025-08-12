<template>
  <div>
    <div class="card">
      <div class="card-body">
        <div class="d-flex bd-highlight align-items-center">
          <h5 class="card-title mb-0">UAT</h5>
          <div class="ms-3 status-pill">
            <span :class="['dot', botStatus]"></span>
            <span class="text-capitalize">{{ botStatus }}</span>
          </div>
          <button @click="autoStart"  class="ml-auto btn btn-sm btn--primary">Start</button>
          <button @click="autoStop" class="btn btn-sm btn--outline">Stop</button>
          <button class="btn btn-sm btn--primary" data-target="#create-task-list-modal" data-toggle="modal">Create Task</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: "AutoStatusPanel",
  data(){
    return { botStatus: 'idle', pollTimer: undefined }
  },
  methods:{
    autoStart:function (){
      this.axios.post("/action/bot/start").then(
          ()=>{ this.botStatus = 'starting' }
      )
    },
    autoStop:function (){
      this.axios.post("/action/bot/stop").then(
          ()=>{ this.botStatus = 'stopping' }
      )
    },
    pollStatus(){
      this.axios.get('/action/bot/status').then(res=>{
        if (res && res.data && res.data.status){ this.botStatus = res.data.status }
      }).catch(()=>{})
    }
  },
  mounted(){ this.pollTimer = setInterval(this.pollStatus, 1500); this.pollStatus() },
  beforeUnmount(){ if (this.pollTimer) clearInterval(this.pollTimer) }
}
</script>

<style scoped>
  .btn+.btn{
    margin-left: 5px;
  }
</style>