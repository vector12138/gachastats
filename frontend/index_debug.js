// 调试：捕获ElementPlus加载问题
debugconsole.log('ElementPlus加载状态:', typeof ElementPlus !== 'undefined');
debugconsole.log('Vue版本:', Vue.version);
debugconsole.log('当前编译:', '---start---');
// 添加Element Plus组件加载检测
document.addEventListener('DOMContentLoaded', () => {
    debugconsole.log('DOM加载完成');
    debugconsole.log('容器存在:', document.getElementById('app'));
    setTimeout(() => {
        debugconsole.log('延时后ElementPlus:', typeof ElementPlus !== 'undefined');
    }, 500);
});

const { createApp } = Vue;
const app = createApp({
  data() {
    return {
      accounts: [],
      allStats: [],
      analysisData: null,
      showAddAccount: false,
      addAccountMethod: '', // '' 表示显示选择界面, 'manual' 表示手动, 'browser' 表示浏览器登录
      browserLoginForm: {
        game_type: ''
      },
      browserLoginLoading: false,
      showImport: false,
      importing: false,
      importTab: 'official',
      importUrl: '',
      currentAccountId: null,
      accountForm: {
        game_type: '',
        account_name: '',
        server: '',
        uid: '',
        auth_key: ''
      }
    }
  },
  mounted() {
    debugconsole.log('Vue应用mounted')
    this.loadAccounts()
    this.loadAllStats()
  },
  methods: {
    // 打开添加账号对话框
    openAddAccount() {
      debugconsole.log('调用openAddAccount，显示添加账号对话框')
      this.showAddAccount = true
      this.addAccountMethod = '' // 显示选择界面
    },
    // 开始浏览器登录
    async startBrowserLogin() {
      if (!this.browserLoginForm.game_type) {
        ElMessage.warning('请选择游戏')
        return
      }
      this.browserLoginLoading = true
      try {
        const res = await axios.post('/api/auth/sessions', {
          game_type: this.browserLoginForm.game_type,
          save_account: true
        })
        ElMessage.success('已启动浏览器登录，请在浏览器中完成登录')
        // 关闭对话框并刷新账号列表
        this.showAddAccount = false
        this.addAccountMethod = ''
        // 延迟刷新账号列表
        setTimeout(() => {
          this.loadAccounts()
          this.loadAllStats()
        }, 2000)
      } catch (e) {
        ElMessage.error('启动浏览器登录失败：' + (e.response?.data?.detail || '未知错误'))
      } finally {
        this.browserLoginLoading = false
      }
    },
    // 取消浏览器登录
    cancelBrowserLogin() {
      this.addAccountMethod = '' // 返回选择界面
    },
    async loadAccounts() {
      try {
        const res = await axios.get('/api/accounts')
        debugconsole.log('账号API返回:', res)
        this.accounts = res.data
        debugconsole.log('账号数组:', this.accounts, '长度:', this.accounts?.length)
      } catch (e) {
        debugconsole.log('加载账号失败:', e)
        ElMessage.error('加载账号失败')
      }
    },
    async loadAllStats() {
      try {
        const res = await axios.get('/api/statistics/all')
        debugconsole.log('统计API返回:', res)
        this.allStats = res.data.data
        debugconsole.log('统计数组:', this.allStats, '长度:', this.allStats?.length)
      } catch (e) {
        debugconsole.log('加载统计失败:', e)
      }
    },
    async createAccount() {
      try {
        await axios.post('/api/accounts', this.accountForm)
        ElMessage.success('账号添加成功')
        this.showAddAccount = false
        this.addAccountMethod = ''
        this.accountForm = { game_type: '', account_name: '', server: '', uid: '', auth_key: '' }
        await this.loadAccounts()
        await this.loadAllStats()
      } catch (e) {
        ElMessage.error(e.response?.data?.detail || '添加失败')
      }
    },
    importData(accountId) {
      debugconsole.log('选择导入账号:', accountId)
      this.currentAccountId = accountId
      this.showImport = true
      this.importUrl = ''
    },
    async importOfficial() {
      if (!this.importUrl) {
        ElMessage.warning('请输入抽卡链接')
        return
      }
      this.importing = true
      try {
        const res = await axios.post(`/api/import/official?account_id=${this.currentAccountId}&gacha_url=${encodeURIComponent(this.importUrl)}`)
        ElMessage.success(`导入成功，共导入 ${res.data.imported} 条记录`)
        this.showImport = false
        await this.loadAllStats()
        this.viewAnalysis(this.currentAccountId)
      } catch (e) {
        ElMessage.error(e.response?.data?.detail || '导入失败')
      } finally {
        this.importing = false
      }
    },
    async viewAnalysis(accountId) {
      debugconsole.log('查看分析:', accountId)
      try {
        const res = await axios.get(`/api/analysis/${accountId}`)
        this.analysisData = res.data.data
        debugconsole.log('分析数据:', this.analysisData)
        window.scrollTo({ top: 0, behavior: 'smooth' })
      } catch (e) {
        debugconsole.log('获取分析失败:', e)
        ElMessage.error('获取分析失败')
      }
    },
    deleteAccount(accountId) {
      debugconsole.log('删除账号', accountId)
      ElMessage.warning('删除功能待实现')
    },
    getPoolName(poolType, gameType) {
      const names = {
        'genshin': {
          '100': '新手祈愿',
          '200': '常驻祈愿',
          '301': '角色活动祈愿',
          '302': '武器活动祈愿'
        },
        'zzz': {
          '1': '音擎祈愿',
          '2': '角色祈愿',
          '3': '常驻祈愿',
          '4': '新手祈愿'
        },
        'starrail': {
          '1': '新手跃迁',
          '2': '常驻跃迁',
          '11': '角色活动跃迁',
          '12': '光锥活动跃迁'
        }
      }
      return names[gameType]?.[poolType] || `卡池${poolType}`
    }
  }
})

// 添加错误检查
debugapp.use(ElementPlus)
debugconsole.log('Vue应用创建完成，准备挂载')
debugapp.mount('#app')
debugconsole.log('Vue应用已挂载')

debugconsole.log('调试信息:', typeof ElementPlus === 'undefined' ? 'ElementPlus加载失败!' : 'ElementPlus加载成功')