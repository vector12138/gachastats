// settings.js - 系统设置模块
(function() {
    'use strict';

    // 设置组件
    const settings = {
        data() {
            return {
                // 应用设置
                config: {
                    theme: 'light',
                    language: 'zh-CN',
                    fontSize: 'medium',
                    autoUpdate: true,
                    showPityBar: true,
                    dataRetentionDays: 365,
                    backupEnabled: true
                },

                // 系统信息
                systemInfo: {
                    version: '2.0.0',
                    buildDate: new Date().toISODateString(),
                    platform: navigator.platform,
                    userAgent: navigator.userAgent,
                    backendStatus: 'unknown'
                },

                // 通知设置
                notification: {
                    enabled: true,
                    sounds: true,
                    desktop: false,
                    email: false,
                    pushNotification: false
                },

                // 隐私设置
                privacy: {
                    telemetry: false,
                    analytics: false,
                    crashReports: false,
                    dataSharing: false
                },

                // 加载状态
                loading: {
                    config: false,
                    backup: false,
                    reset: false
                },

                // 备份操作
                backupStatus: 'idle', // idle, creating, restoring, done

                // 模态框状态
                modals: {
                    about: false,
                    backup: false,
                    reset: false
                }
            };
        },

        computed: {
            isDarkMode() {
                return this.config.theme === 'dark';
            },

            themeIcon() {
                return this.isDarkMode ? 'el-icon-moon' : 'el-icon-sunny';
            },

            themeLabel() {
                return this.isDarkMode ? '深色' : '浅色';
            },

            backendStatusLabel() {
                return {
                    'online': '在线',
                    'offline': '离线',
                    'error': '错误',
                    'unknown': '未知'
                }[this.systemInfo.backendStatus];
            }
        },

        methods: {
            // 加载配置
            async loadConfig() {
                try {
                    this.loading.config = true;
                    const response = await axios.get('/api/config');
                    Object.assign(this.config, response.data.config || {});
                    Object.assign(this.notification, response.data.notification || {});
                    Object.assign(this.privacy, response.data.privacy || {});
                } catch (error) {
                    console.error('加载配置失败:', error);
                    this.$root.showMessage('加载配置失败，使用默认配置', 'warning');
                } finally {
                    this.loading.config = false;
                }
            },

            // 保存配置
            async saveConfig() {
                try {
                    this.loading.config = true;

                    const payload = {
                        config: this.config,
                        notification: this.notification,
                        privacy: this.privacy
                    };

                    await axios.post('/api/config', payload);
                    this.$root.showMessage('配置已保存', 'success');

                    // 应用配置更改
                    this.applyConfig();
                } catch (error) {
                    console.error('保存配置失败:', error);
                    this.$root.showMessage('保存配置失败', 'error');
                } finally {
                    this.loading.config = false;
                }
            },

            // 应用配置
            applyConfig() {
                // 应用主题
                if (this.isDarkMode) {
                    document.body.classList.add('dark-theme');
                    document.body.classList.remove('light-theme');
                } else {
                    document.body.classList.add('light-theme');
                    document.body.classList.remove('dark-theme');
                }

                // 应用字体大小
                document.documentElement.style.fontSize = this.config.fontSize === 'large' ? '16px' :
                                                        this.config.fontSize === 'small' ? '12px' : '14px';

                // 应用其他设置...
            },

            // 创建备份
            async createBackup() {
                try {
                    this.backupStatus = 'creating';

                    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
                    const fileName = `gachastats-backup-${timestamp}.json`;

                    const response = await axios.get('/api/backup/export');
                    const backupData = response.data;

                    // 创建下载
                    const blob = new Blob([JSON.stringify(backupData, null, 2)], { type: 'application/json' });
                    const url = URL.createObjectURL(blob);
                    const link = document.createElement('a');
                    link.href = url;
                    link.download = fileName;
                    link.click();

                    URL.revokeObjectURL(url);

                    this.$root.showMessage('备份已创建', 'success');
                    this.backupStatus = 'done';

                } catch (error) {
                    console.error('创建备份失败:', error);
                    this.$root.showMessage('创建备份失败', 'error');
                    this.backupStatus = 'idle';
                }
            },

            // 恢复备份
            async restoreBackup(file) {
                try {
                    this.backupStatus = 'restoring';

                    const formData = new FormData();
                    formData.append('file', file);

                    await axios.post('/api/backup/import', formData, {
                        headers: {
                            'Content-Type': 'multipart/form-data'
                        }
                    });

                    this.$root.showMessage('备份已恢复，请重新加载应用', 'success');

                    // 延迟后刷新页面
                    setTimeout(() => {
                        location.reload();
                    }, 2000);

                } catch (error) {
                    console.error('恢复备份失败:', error);
                    this.$root.showMessage('恢复备份失败', 'error');
                    this.backupStatus = 'idle';
                }
            },

            // 重置所有设置
            async resetAllSettings() {
                try {
                    this.loading.reset = true;

                    // 发送重置请求
                    await axios.post('/api/reset');

                    // 重新加载页面
                    await this.$root.nextTick();
                    location.reload();

                } catch (error) {
                    console.error('重置设置失败:', error);
                    this.$root.showMessage('重置设置失败', 'error');
                    this.loading.reset = false;
                }
            },

            // 检查更新
            async checkForUpdates() {
                try {
                    const response = await axios.get('/api/system/version');
                    const latestVersion = response.data.latest_version;

                    if (this.systemInfo.version !== latestVersion) {
                        this.$root.showMessage(`发现新版本：${latestVersion}`, 'info');

                        // 显示更新提示
                        if (confirm(`发现新版本 ${latestVersion}，是否现在更新？`)) {
                            await this.downloadUpdate();
                        }
                    } else {
                        this.$root.showMessage('已是最新版本', 'info');
                    }

                } catch (error) {
                    console.error('检查更新失败:', error);
                    this.$root.showMessage('检查更新失败', 'error');
                }
            },

            // 下载更新
            async downloadUpdate() {
                try {
                    await axios.post('/api/system/update');
                    this.$root.showMessage('更新下载完成，请重启应用', 'success');
                } catch (error) {
                    console.error('下载更新失败:', error);
                    this.$root.showMessage('下载更新失败', 'error');
                }
            },

            // 导出日志
            async exportLogs() {
                try {
                    const response = await axios.get('/api/logs/export');
                    const logs = response.data;

                    const blob = new Blob([JSON.stringify(logs, null, 2)], { type: 'text/plain' });
                    const url = URL.createObjectURL(blob);
                    const link = document.createElement('a');
                    link.href = url;
                    link.download = `gachastats-logs-${new Date().toISOString()}.txt`;
                    link.click();

                    URL.revokeObjectURL(url);

                } catch (error) {
                    console.error('导出日志失败:', error);
                    this.$root.showMessage('导出日志失败', 'error');
                }
            }
        },

        created() {
            this.loadConfig();
        },

        template: `
            <div class="tab-content fade-in">
                <div class="page-header">
                    <h3>⚙️ 系统设置</h3>
                    <p>配置您的 GachaStats 体验。</p>
                </div>

                <el-tabs tab-position="left" model-value="config">
                    <!-- 外观设置 -->
                    <el-tab-pane label="外观设置" name="appearance" disabled>
                        <div class="settings-section">
                            <h4>📱 界面设置</h4>

                            <div class="setting-form">
                                <el-form :model="config" label-width="120px">
                                    <el-form-item label="主题">
                                        <el-radio-group v-model="config.theme">
                                            <el-radio :label="'light'">
                                                <i class="el-icon-sunny"></i> 浅色
                                            </el-radio>
                                            <el-radio :label="'dark'">
                                                <i class="el-icon-moon"></i> 深色
                                            </el-radio>
                                        </el-radio-group>
                                    </el-form-item>

                                    <el-form-item label="语言">
                                        <el-select v-model="config.language" disabled>
                                            <el-option label="中文（简体）" value="zh-CN"></el-option>
                                            <el-option label="中文（繁体）" value="zh-TW" disabled></el-option>
                                            <el-option label="English" value="en-US" disabled></el-option>
                                        </el-select>
                                    </el-form-item>

                                    <el-form-item label="字体大小">
                                        <el-radio-group v-model="config.fontSize">
                                            <el-radio-button :label="'small'">小</el-radio-button>
                                            <el-radio-button :label="'medium'">中</el-radio-button>
                                            <el-radio-button :label="'large'">大</el-radio-button>
                                        </el-radio-group>
                                    </el-form-item>

                                    <el-form-item label="欧皇度显示">
                                        <el-switch v-model="config.showPityBar"></el-switch>
                                    </el-form-item>
                                </el-form>
                            </div>
                        </div>

                        <div class="settings-actions">
                            <el-button @click="saveConfig()" type="primary" :loading="loading.config">
                                <i class="el-icon-check"></i> 保存设置
                            </el-button>
                            <el-button @click="clearCache()">
                                <i class="el-icon-delete"></i> 清空缓存
                            </el-button>
                        </div>
                    </el-tab-pane>

                    <!-- 账户管理 -->
                    <el-tab-pane disabled header="data-settings">
                        <template #header>
                            <div class="custom-tab-header">账户管理</div>
                        </template>
                        <div class="settings-section">
                            <h4>💰 数据分析设置</h4>
                            <p>这些设置已整合到数据分析TAB中，请切换到数据分析TAB进行管理。</p>
                        </div>
                    </el-tab-pane>

                    <!-- 系统信息 -->
                    <el-tab-pane label="系统信息" name="system">
                        <div class="settings-section">
                            <h4>ℹ️ 关于 GachaStats</h4>
                            <div class="info-grid">
                                <div class="info-item">
                                    <span class="label">版本信息：</span>
                                    <span class="value">{{ systemInfo.version }}</span>
                                </div>
                                <div class="info-item">
                                    <span class="label">构建日期：</span>
                                    <span class="value">{{ new Date(systemInfo.buildDate).toLocaleDateString() }}</span>
                                </div>
                                <div class="info-item">
                                    <span class="label">运行平台：</span>
                                    <span class="value">{{ systemInfo.platform }}</span>
                                </div>
                                <div class="info-item">
                                    <span class="label">后端状态：</span>
                                    <span class="value">
                                        <el-tag :type="$root.connectionStatus === 'success' ? 'success' : 'danger'" size="small">
                                            {{ $root.connectionStatus === 'success' ? '在线' : '离线' }}
                                        </el-tag>
                                    </span>
                                </div>
                            </div>

                            <div class="system-actions">
                                <el-button @click="checkForUpdates()" size="mini">
                                    <i class="el-icon-refresh"></i> 检查更新
                                </el-button>
                                <el-button @click="exportLogs()" size="mini">
                                    <i class="el-icon-download"></i> 导出日志
                                </el-button>
                            </div>
                        </div>
                    </el-tab-pane>

                    <!-- 备份与恢复 -->
                    <el-tab-pane label="备份与恢复" name="backup">
                        <div class="settings-section">
                            <h4>💾 数据备份</h4>

                            <div class="backup-section">
                                <el-alert title="强烈建议定期备份您的数据" type="info" :closable="false" show-icon></el-alert>

                                <div class="backup-actions">
                                    <el-button @click="createBackup()" :loading="backupStatus === 'creating'" type="primary">
                                        <i class="el-icon-download"></i> 创建备份
                                    </el-button>

                                    <el-upload action="/api/backup/import" :limit="1" :before-upload="(file) => { restoreBackup(file); return false; }">
                                        <el-button :loading="backupStatus === 'restoring'">
                                            <i class="el-icon-upload"></i> 恢复备份
                                        </el-button>
                                    </el-upload>
                                </div>
                            </div>
                        </div>

                        <div class="settings-section">
                            <h4>⚠️ 危险操作</h4>

                            <el-card class="danger-section">
                                <div slot="header">
                                    <span>重置应用</span>
                                </div>
                                <p>此操作将删除所有数据并重置所有设置，操作不可恢复。</p>
                                <p>丢失的数据包括：账户、抽卡记录、配置等。</p>

                                <el-button @click="resetAllSettings()" type="danger" :loading="loading.reset">
                                    <i class="el-icon-warning-outline"></i>
                                    重置所有设置
                                </el-button>
                            </el-card>
                        </div>
                    </el-tab-pane>

                    <!-- 隐私设置 -->
                    <el-tab-pane label="高级设置" name="advanced" disabled>
                        <div class="settings-section">
                            <h4>🔒 隐私设置</h4>

                            <el-form :model="privacy" label-width="150px">
                                <el-form-item label="数据统计">
                                    <el-switch v-model="privacy.telemetry" disabled></el-switch>
                                    <small class="setting-text">帮助我们改进产品（即将推出）</small>
                                </el-form-item>

                                <el-form-item label="崩溃报告">
                                    <el-switch v-model="privacy.crashReports" disabled></el-switch>
                                    <small class="setting-text">自动发送崩溃报告（即将推出）</small>
                                </el-form-item>

                                <el-form-item label="数据保留">
                                    <el-slider v-model="config.dataRetentionDays" show-input :min="30" :max="1095" :step="30" show-stops></el-slider>
                                </el-form-item>
                            </el-form>
                        </div>
                    </el-tab-pane>
                </el-tabs>
            </div>
        `
    }
})();