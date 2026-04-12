// 账户管理模块 使用 Vue3 Composition API 风格 (兼容 Element Plus)
(function() {
  'use strict';

  // 账户管理主组件
  const accounts = {
    name: 'accounts-tab',
    data() {
      return {
        // 加载状态
        loading: false,

        // 账户列表
        accounts: [],

        // 编辑模式
        editMode: null, // null: 列表模式, 'new': 新建模式, object: 编辑模式

        // 表单数据 (using Element Plus format for Vue3)
        accountForm: {
          id: null,
          game_type: 'genshin',
          account_name: '',
          uid: '',
          server: 'cn_gf01',
          auth_key: ''
        },

        // 分页数据
        pagination: {
          current: 1,
          pageSize: 10,
          total: 0
        },

        // 筛选
        filter: {
          game_type: '',
          search_text: ''
        }
      };
    },

    computed: {
      // 处理分页
      paginatedAccounts() {
        if (!this.pagination.total) return this.accounts;
        const start = (this.pagination.current - 1) * this.pagination.pageSize;
        const end = start + this.pagination.pageSize;
        return this.accounts.slice(start, end);
      },

      // 过滤文本高亮
      highlighted() {
        return function(text) {
          if (!this.filter.search_text || !text) return text;
          return text.replace(new RegExp(this.filter.search_text, 'gi'), match =>
            `<mark>${match}</mark>`
          );
        }
      }
    },

    methods: {
      // 获取状态类名
      getStatusClass() {
        return {
          success: this.$root.connectionStatus === 'success',
          error: this.$root.connectionStatus === 'error'
        };
      },

      // 获取游戏名称
      getGameName(type) {
        const games = {
          genshin: '原神',
          honkai: '崩坏3',
          starrail: '星穹铁道'
        };
        return games[type] || type;
      },

      // 获取服务器标签
      getServerLabel(server) {
        const servers = {
          cn_gf01: '国服正式服',
          cn_gf02: '国服iOS',
          cn_qd01: '国服安卓渠道'
        };
        return servers[server] || server;
      },

      // 格式化时间
      formatTime(date) {
        return this.$dayjs(date).format('YYYY-MM-DD HH:mm:ss');
      },

      // 计算相对时间
      fromNow(date) {
        const diff = Date.now() - new Date(date).getTime();
        const minutes = diff / 60000;
        const hours = diff / 3600000;
        const days = diff / 86400000;

        if (diff < 3600000) return `${Math.floor(minutes)}分钟前`;
        if (diff < 86400000) return `${Math.floor(hours)}小时前`;
        if (diff < 604800000) return `${Math.floor(days)}天前`;
        return this.formatTime(date);
      },

      // 校验表单
      validateAccount(account) {
        const gameTypes = ['genshin', 'honkai', 'starrail'];
        const servers = ['cn_gf01', 'cn_gf02', 'cn_qd01', 'os_usa'];

        if (!account) return '账户对象不能为空';
        if (!account.account_name?.trim()) return '账号名称不能为空';
        if (!account.uid?.trim()) return '游戏UID不能为空';
        if (!gameTypes.includes(account.game_type)) return '游戏类型无效';
        if (!servers.includes(account.server)) return '服务器无效';

        return null;
      },

      // 重置表单
      resetForm() {
        this.accountForm = {
          id: null,
          game_type: 'genshin',
          account_name: '',
          uid: '',
          server: 'cn_gf01',
          auth_key: ''
        };
        this.editMode = null;
      },

      // 开始编辑
      startEdit(account) {
        this.accountForm = {
          id: account.id,
          game_type: account.game_type,
          account_name: account.account_name,
          uid: account.uid,
          server: account.server,
          auth_key: account.auth_key
        };
        this.editMode = account;
      },

      // 删除账户
      async deleteAccount(id) {
        try {
          await this.$confirm('确定要删除该账号吗？所有相关数据将被清除。', '确认删除', {
            confirmButtonText: '删除',
            cancelButtonText: '取消',
            type: 'warning'
          });

          await this.$root.$api.delete(`/api/accounts/${id}`);
          this.$root.showMessage('账号已删除');
          await this.loadAccounts();

        } catch (error) {
          if (error !== 'cancel') {
            console.error('删除账号失败:', error);
            this.$root.showMessage('操作失败', 'error');
          }
        }
      },

      // 保存账户
      async saveAccount() {
        const error = this.validateAccount(this.accountForm);
        if (error) {
          this.$root.showMessage(error, 'warning');
          return;
        }

        this.loading = true;
        try {
          if (this.editMode === null) {
            // 新增
            await this.$root.$api.post('/api/accounts', this.accountForm);
            this.$root.showMessage('账号添加成功');
          } else {
            // 编辑
            await this.$root.$api.put(`/api/accounts/${this.accountForm.id}`, this.accountForm);
            this.$root.showMessage('账号更新成功');
          }

          await this.loadAccounts();
          this.resetForm();

        } catch (error) {
          console.error('保存账号失败:', error);
          this.$root.showMessage('保存失败', 'error');
        } finally {
          this.loading = false;
        }
      },

      // 加载账户列表
      async loadAccounts() {
        this.loading = true;
        try {
          const response = await this.$root.$api.get('/api/accounts', {
            params: {
              page: this.pagination.current,
              page_size: this.pagination.pageSize,
              game_type: this.filter.game_type,
              search: this.filter.search_text
            }
          });

          this.accounts = response.data.items || [];
          this.pagination.total = response.data.total || this.accounts.length;

        } catch (error) {
          console.error('加载账户失败:', error);
          this.$root.showMessage('加载失败');
          this.accounts = [
            {
              id: 1,
              game_type: 'genshin',
              account_name: '示例账号',
              uid: '700000000',
              server: 'cn_gf01',
              auth_key: 'sample-auth-key',
              created_at: new Date().toISOString()
            }
          ];

        } finally {
          this.loading = false;
        }
      },

      // 分页变更
      handlePageChange(page) {
        this.pagination.current = page;
      },

      // 搜索输入
      handleSearch() {
        this.pagination.current = 1;
        this.loadAccounts();
      }
    },

    mounted() {
      console.log('👤 账户管理模块已加载');
      if (this.accounts.length === 0) {
        this.loadAccounts();
      }
    }
  };

  // 注册组件给 gachaApp 使用
  if (typeof gachaApp !== 'undefined') {
    try {
      gachaApp.component('accounts-tab', accounts);
      console.log('✅ 账户组件已注册到 gachaApp');
    } catch (e) {
      console.error('❌ 无法注册账户组件:', e);
    }
  } else {
    console.error('❌ gachaApp 未定义 - 无法注册账户组件');
  }
})();