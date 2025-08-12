<template>
  <div>
    <!-- Quick Stats -->
    <div class="row mb-3">
      <div class="col-12">
        <div class="section-card p-3">
          <div class="row g-3">
            <div class="col-sm-3">
              <div class="stat-card">
                <div class="stat-label">Running</div>
                <div class="stat-value">{{ runningTask ? 1 : 0 }}</div>
              </div>
            </div>
            <div class="col-sm-3">
              <div class="stat-card">
                <div class="stat-label">Waiting</div>
                <div class="stat-value">{{ waitingTaskList.length }}</div>
              </div>
            </div>
            <div class="col-sm-3">
              <div class="stat-card">
                <div class="stat-label">Completed</div>
                <div class="stat-value">{{ historyTaskList.length }}</div>
              </div>
            </div>
            <div class="col-sm-3">
              <div class="stat-card">
                <div class="stat-label">Success rate</div>
                <div class="stat-value">{{ successRate }}</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Running Task Spotlight -->
    <div v-if="runningTask" class="row mb-3">
      <div class="col-12">
        <div class="section-card p-3 d-flex align-items-center justify-content-between">
          <div class="d-flex align-items-center gap-3">
            <div class="status-pill"><span class="dot running"></span><span>Running</span></div>
            <div class="spot-text">
              <div class="spot-title">{{ runningTask.task_desc || 'Active Task' }}</div>
              <div class="spot-meta">Task ID: {{ runningTask.task_id || '-' }} • Scenario: {{ runningTask.attachment_data?.scenario || '-' }}</div>
            </div>
          </div>
          <div class="spot-actions">
            <button class="btn btn-sm btn--outline" @click="scrollToLogs">View Logs</button>
          </div>
        </div>
      </div>
    </div>

    <div class="row">
    <div class="col-4">
      <div class="part">
        <scheduler-panel v-bind:waiting-task-list="waitingTaskList"
                         v-bind:running-task="runningTask"
                         v-bind:history-task-list="historyTaskList"
                         v-bind:cron-job-list="cronJobList"
        ></scheduler-panel>
      </div>
    </div>
    <div class="col-8">
      <log-panel v-bind:log-content="logContent"
                 v-bind:auto-log="autoLog"
                 v-bind:toggle-auto-log="toggleAutoLog"
      ></log-panel>
      <!-- Recent Activity under logs -->
      <!-- intentionally left blank for future content -->
    </div>
  </div>
</div>
</template>

<script>
import SchedulerPanel from "../components/SchedulerPanel.vue";
import LogPanel from "../components/base/LogPanel.vue"
export default {
  name: "AutoController",
  components: { LogPanel, SchedulerPanel},
  data() {
    return {
      taskId:'0',
      runningTask: undefined,
      waitingTaskList:[],
      historyTaskList:[],
      cronJobList:[],
      taskList:[],
      logContent:"",
      autoLog: true,
      taskLogTimer: undefined
    }
  },
  computed: {
    successRate(){
      const total = this.historyTaskList.length
      if (!total) return '—'
      const success = this.historyTaskList.filter(t => t && (t.task_status === 5 || t.status === 5 || t.task_result === 'success')).length
      return Math.round((success/total)*100) + '%'
    }
  },
  mounted:function() {
    let vue = this;
    setInterval(function () {
      vue.getTaskList();
    },1000)

    this.taskLogTimer = setInterval(function () {
      vue.getTaskLog()
    },1000)
  },
  methods:{
    scrollToLogs(){
      // focus the log textarea if present
      const el = document.getElementById('scroll_text');
      if (el) el.focus();
    },
    getTaskList:function (){
      this.axios.get("/task").then(
          res=>{
            this.taskList = res.data;
            let waitingTaskList = []
            let historyTaskList = []
            let cronJobList = []
            let runningTask = undefined

            this.taskList.forEach(
              t=>{
                if(t['task_execute_mode'] === 1){
                  if(t['task_status'] === 2){
                    runningTask = t
                  }else if (t['task_status'] === 1){
                    waitingTaskList.push(t)
                  }else if (t['task_status'] === 5 || t['task_status'] === 4 || t['task_status'] === 3){
                    historyTaskList.push(t)
                  }
                }else if(t['task_execute_mode'] === 2){
                  if(t['task_status'] === 6||t['task_status'] === 7){
                    cronJobList.push(t)
                  }
                }
              }
            )
            this.waitingTaskList = waitingTaskList
            this.historyTaskList = historyTaskList
            this.runningTask = runningTask
            this.cronJobList = cronJobList
            if(this.runningTask === undefined){
              this.taskId = '0'
            }else{
              this.taskId = runningTask['task_id']
            }
          }
      );
    },
    getTaskLog:function () {
      if (this.taskId !== '0') {
        this.axios.get("/log/" + this.taskId).then(
            res => {
              this.logContent = res.data.join('\n')
            }
        );
      }
    },
    toggleAutoLog:function () {
      this.autoLog = !this.autoLog;
      if (this.autoLog) {
        if (this.taskLogTimer === undefined) {
          this.taskLogTimer = setInterval(this.getTaskLog,1000)
        }
      } else {
        if (this.taskLogTimer) {
          clearInterval(this.taskLogTimer)
          this.taskLogTimer = undefined
        }
      }
    }
  }
}
</script>

<style scoped>
.stat-card{padding:8px 12px;border:1px solid #e5e7eb;border-radius:10px;background:#fff;box-shadow:0 1px 2px rgba(0,0,0,.03)}
.stat-label{font-size:12px;color:#6b7280}
.stat-value{font-size:20px;font-weight:700;color:#111827}
.spot-title{font-weight:600}
.spot-meta{font-size:12px;color:#6b7280}

</style>