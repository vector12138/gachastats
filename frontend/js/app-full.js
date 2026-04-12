(function() {
  'use strict';

  const { createApp, ref, reactive, computed, onMounted } = Vue;

  const app = createApp({
    setup() {
      const loading = ref(true);
      const connectionStatus = ref('pending');
      const currentTab = ref('accounts');
      const accounts = ref([]);
      const editingAccount = ref(false);

      const importTab = ref('official');
      const importing = ref(false);
      const importForm = reactive({
        account_id: null,
        gacha_url: ''
      });
      const manualForm = reactive({
        account_id: null,
        item_name: '',
        item_type: '角色',
        rarity: 5,
        gacha_type: '301',
        time: null
      });

      const selectedAnalysisAccount = ref(null);
      const analysisData = ref(null);
      const analysisLoading = ref(false);

      const browserLoginForm = reactive({
        game_type: ''
      });
      const browserLoginLoading = ref(false);
    const browserStatus = ref({has_display: false, browser_available: false, can_auto_login: false});
      const extractForm = reactive({
        url: ''
      });

      const availableTabs = [
        { key: 'accounts', label: '账号管理' },
        { key: 'import', label: '导入抽卡数据' },
        { key: 'analysis', label: '数据分析' },
        { key: 'browser', label: '浏览器登录' },
        { key: 'settings', label: '系统设置' }
      ];

      const games = {
        genshin: '原神',
        honkai: '崩坏3',
        starrail: '星穹铁道',
        zenless: '绝区零'
      };

      const servers = {
        cn_gf01: '国服官方服',
        cn_gf02: '国服iOS',
        cn_qd01: '国服渠道服',
        os_usa: '国际服'
      };

      const accountForm = reactive({
        id: null,
        game_type: 'genshin',
        account_name: '',
        uid: '',
        server: 'cn_gf01',
        auth_key: ''
      });

      const currentYear = computed(() => new Date().getFullYear());

      async function testConnection() {
        try {
          const res = await axios.get('/api/accounts');
          const data = Array.isArray(res.data) ? res.data : (res.data?.data || []);
          if (Array.isArray(data)) {
            connectionStatus.value = 'success';
          } else {
            connectionStatus.value = 'error';
          }
        } catch (err) {
          console.error('连接测试失败:', err);
          connectionStatus.value = 'error';
        }
      }

      function getGameName(type) {
        return games[type] || type;
      }

      function getServerLabel(server) {
        return servers[server] || server;
      }

      function resetAccountForm() {
        accountForm.id = null;
        accountForm.game_type = 'genshin';
        accountForm.account_name = '';
        accountForm.uid = '';
        accountForm.server = 'cn_gf01';
        accountForm.auth_key = '';
        editingAccount.value = false;
      }

      function editAccount(account) {
        accountForm.id = account.id;
        accountForm.game_type = account.game_type;
        accountForm.account_name = account.account_name;
        accountForm.uid = account.uid;
        accountForm.server = account.server;
        accountForm.auth_key = account.auth_key || '';
        editingAccount.value = true;
      }

      async function deleteAccount(id) {
        try {
          await ElementPlus.ElMessageBox.confirm('确定要删除这个账号吗？', '确认删除', {
            confirmButtonText: '删除',
            cancelButtonText: '取消',
            type: 'warning'
          });

          await axios.delete(`/api/accounts/${id}`);
          ElementPlus.ElMessage.success('账号已删除');
          await loadAccounts();
        } catch (error) {
          if (error !== 'cancel') {
            console.error('删除账号失败:', error);
            ElementPlus.ElMessage.error('删除账号失败');
          }
        }
      }

      async function addAccount() {
        if (!accountForm.account_name || !accountForm.uid) {
          ElementPlus.ElMessage.warning('请填写完整的账号信息');
          return;
        }

        try {
          if (editingAccount.value && accountForm.id) {
            await axios.put(`/api/accounts/${accountForm.id}`, accountForm);
            ElementPlus.ElMessage.success('账号已更新');
          } else {
            await axios.post('/api/accounts', accountForm);
            ElementPlus.ElMessage.success('账号添加成功');
          }

          await loadAccounts();
          resetAccountForm();
        } catch (error) {
          console.error('保存账号失败:', error);
          ElementPlus.ElMessage.error('保存账号失败');
        }
      }

      async function loadAccounts() {
        try {
          const response = await axios.get('/api/accounts');
          const data = Array.isArray(response.data) ? response.data : (response.data?.data || []);
          accounts.value = data;
        } catch (error) {
          console.error('加载账户失败:', error);
          ElementPlus.ElMessage.error('加载账户失败');
        }
      }

      function resetImportForm() {
        importForm.account_id = null;
        importForm.gacha_url = '';
      }

      function resetManualForm() {
        manualForm.account_id = null;
        manualForm.item_name = '';
        manualForm.item_type = '角色';
        manualForm.rarity = 5;
        manualForm.gacha_type = '301';
        manualForm.time = null;
      }

      async function importFromOfficial() {
        if (!importForm.account_id) {
          ElementPlus.ElMessage.warning('请选择账号');
          return;
        }
        if (!importForm.gacha_url) {
          ElementPlus.ElMessage.warning('请输入抽卡链接');
          return;
        }
        importing.value = true;
        try {
          const response = await axios.post('/api/import/official', {
            account_id: importForm.account_id,
            gacha_url: importForm.gacha_url
          });
          ElementPlus.ElMessage.success(response.data.message || '导入成功');
          resetImportForm();
        } catch (error) {
          console.error('导入失败:', error);
          ElementPlus.ElMessage.error(error.response?.data?.message || '导入失败');
        } finally {
          importing.value = false;
        }
      }

      async function addManualRecord() {
        if (!manualForm.account_id) {
          ElementPlus.ElMessage.warning('请选择账号');
          return;
        }
        if (!manualForm.item_name) {
          ElementPlus.ElMessage.warning('请输入物品名称');
          return;
        }
        try {
          const timeStr = manualForm.time ? new Date(manualForm.time).toISOString().slice(0, 19).replace('T', ' ') : '';
          await axios.post('/api/import/manual', {
            account_id: manualForm.account_id,
            records: [{
              item_name: manualForm.item_name,
              item_type: manualForm.item_type,
              rarity: manualForm.rarity,
              gacha_type: manualForm.gacha_type,
              time: timeStr
            }]
          });
          ElementPlus.ElMessage.success('记录添加成功');
          resetManualForm();
        } catch (error) {
          console.error('添加记录失败:', error);
          ElementPlus.ElMessage.error('添加记录失败');
        }
      }

      async function loadAnalysisData() {
        if (!selectedAnalysisAccount.value) return;
        analysisLoading.value = true;
        try {
          const response = await axios.get(`/api/analysis/${selectedAnalysisAccount.value}`);
          analysisData.value = response.data;
        } catch (error) {
          console.error('加载分析数据失败:', error);
          ElementPlus.ElMessage.error('加载分析数据失败');
          analysisData.value = null;
        } finally {
          analysisLoading.value = false;
        }
      }

      async function startBrowserLogin() {
        if (!browserLoginForm.game_type) {
          ElementPlus.ElMessage.warning('请选择游戏');
          return;
        }
        browserLoginLoading.value = true;
        try {
          await axios.post('/api/auth/browser-login', {
            game_type: browserLoginForm.game_type,
            save_account: true
          });
          ElementPlus.ElMessage.success('浏览器登录已启动');
        } catch (error) {
          console.error('浏览器登录启动失败:', error);
          ElementPlus.ElMessage.error(error.response?.data?.message || '浏览器登录启动失败');
        } finally {
          browserLoginLoading.value = false;
        }
      }

      async function extractAuthkey() {
        if (!extractForm.url) {
          ElementPlus.ElMessage.warning('请输入链接');
          return;
        }
        try {
          const response = await axios.post('/api/auth/extract-url', { url: extractForm.url });
          ElementPlus.ElMessage.success(response.data.message || '提取成功');
          extractForm.url = '';
        } catch (error) {
          console.error('提取失败:', error);
          ElementPlus.ElMessage.error(error.response?.data?.message || '提取失败');
        }
      }

      async function confirmClearData() {
        try {
          await ElementPlus.ElMessageBox.confirm('确定要清空所有数据吗？', '警告', {
            confirmButtonText: '确定清空',
            cancelButtonText: '取消',
            type: 'warning'
          });
          ElementPlus.ElMessage.success('数据已清空');
          await loadAccounts();
        } catch (error) {
          if (error !== 'cancel') {
            console.error('清空数据失败:', error);
          }
        }
      }

      async function exportAllData() {
      const url = '/api/export/all/xlsx';
      window.open(url, '_blank');
    }
    
    function exportAccount(accountId, format) {
        const url = `/api/export/${accountId}/${format}`;
        window.open(url, '_blank');
      }

      onMounted(async () => {
        console.log('GachaStats mounted');
        await testConnection();
        if (connectionStatus.value === 'success') {
          await loadAccounts();
        }
        loading.value = false;
      });

      return {
        loading,
        connectionStatus,
        currentTab,
        availableTabs,
        accounts,
        accountForm,
        editingAccount,
        currentYear,
        importTab,
        importing,
        importForm,
        manualForm,
        selectedAnalysisAccount,
        analysisData,
        analysisLoading,
        browserLoginForm,
        browserLoginLoading,
      browserStatus,
        extractForm,
        getGameName,
        getServerLabel,
        resetAccountForm,
        editAccount,
        deleteAccount,
        addAccount,
        loadAccounts,
        resetImportForm,
        resetManualForm,
        importFromOfficial,
        addManualRecord,
        loadAnalysisData,
        startBrowserLogin,
        extractAuthkey,
        confirmClearData,
        exportAccount
      };
    }
  });

  app.use(ElementPlus);
  app.mount('#app');
})();
