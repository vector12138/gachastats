(function() {
    'use strict';

    // 数据导入模块
    const importModule = {
        data() {
            return {
                // 导入选项卡
                activeTab: 'official',
                tabs: [
                    { key: 'official', label: '官方API导入' },
                    { key: 'file', label: '文件导入' },
                    { key: 'manual', label: '手动录入' }
                ],

                // 当前选中的账户
                selectedAccountId: null,

                // 导入状态
                importing: false,
                progress: 0,
                log: [],

                // 官方API导入
                officialForm: {
                    url: '',
                    start_time: '',
                    end_time: '',
                    page: 1,
                    size: 20
                },

                // 文件导入
                fileForm: {
                    files: []
                },

                // 手动录入
                manualForm: {
                    items: [{
                        name: '',
                        item_id: '',
                        item_type: '五星角色',
                        pull_time: '',
                        pity: 0
                    }]
                }
            };
        },

        computed: {
            selectedAccount() {
                const accounts = this.$root.accounts;
                return accounts.find(a => a.id === this.selectedAccountId);
            },

            isReadyToImport() {
                return Boolean(this.selectedAccountId);
            }
        },

        methods: {
            // 初始化
            loadDefaults() {
                if (this.$root.accounts.length > 0 && !this.selectedAccountId) {
                    this.selectedAccountId = this.$root.accounts[0].id;
                }
            },

            // 官方API导入
            async importFromOfficial() {
                if (!this.isReadyToImport) {
                    this.$root.showMessage('请先选择账户', 'warning');
                    return;
                }

                if (!this.officialForm.url) {
                    this.$root.showMessage('请输入抽卡链接', 'warning');
                    return;
                }

                try {
                    this.importing = true;
                    this.progress = 0;
                    this.log = [];

                    const params = {
                        account_id: this.selectedAccountId,
                        url: this.officialForm.url
                    };

                    this.log.push('开始从官方API导入数据...');

                    const response = await axios.post('/api/imports/official', params);

                    this.log.push(`成功导入 ${response.data.count} 条记录`);
                    this.$root.showMessage('数据导入成功', 'success');

                } catch (error) {
                    console.error('官方API导入失败:', error);
                    this.log.push(`导入失败：${error.message || '未知错误'}`);
                    this.$root.showMessage('数据导入失败', 'error');
                } finally {
                    this.importing = false;
                    this.progress = 100;
                }
            },

            // 文件导入
            async importFromFile() {
                if (!this.isReadyToImport) {
                    this.$root.showMessage('请先选择账户', 'warning');
                    return;
                }

                if (this.fileForm.files.length === 0) {
                    this.$root.showMessage('请选择要导入的文件', 'warning');
                    return;
                }

                try {
                    this.importing = true;
                    this.progress = 0;
                    this.log = [];

                    const formData = new FormData();
                    formData.append('account_id', this.selectedAccountId);

                    // 添加所有文件
                    Array.from(this.fileForm.files).forEach(file => {
                        formData.append('files', file);
                    });

                    this.log.push('开始处理文件...');

                    const response = await axios.post('/api/imports/file', formData, {
                        headers: {
                            'Content-Type': 'multipart/form-data'
                        },
                        onUploadProgress: (progressEvent) => {
                            this.progress = Math.round((progressEvent.loaded / progressEvent.total) * 100);
                        }
                    });

                    this.log.push(`成功导入 ${response.data.count} 条记录`);
                    this.$root.showMessage('文件导入成功', 'success');

                } catch (error) {
                    console.error('文件导入失败:', error);
                    this.log.push(`导入失败：${error.message || '未知错误'}`);
                    this.$root.showMessage('文件导入失败', 'error');
                } finally {
                    this.importing = false;
                }
            },

            // 手动录入
            async importFromManual() {
                if (!this.isReadyToImport) {
                    this.$root.showMessage('请先选择账户', 'warning');
                    return;
                }

                const validItems = this.manualForm.items.filter(item => item.name || item.item_id);

                if (validItems.length === 0) {
                    this.$root.showMessage('请至少录入一个抽卡记录', 'warning');
                    return;
                }

                try {
                    this.importing = true;
                    this.log = [];

                    const params = {
                        account_id: this.selectedAccountId,
                        items: validItems
                    };

                    this.log.push('开始手动录入数据...');

                    const response = await axios.post('/api/imports/manual', params);

                    this.$root.showMessage('数据录入成功', 'success');
                    this.log.push(`成功录入 ${response.data.count} 条记录`);

                    // 清空表单
                    this.resetManualForm();

                } catch (error) {
                    console.error('手动录入失败:', error);
                    this.log.push(`录入失败：${error.message || '未知错误'}`);
                    this.$root.showMessage('数据录入失败', 'error');
                } finally {
                    this.importing = false;
                }
            },

            // 重置手动录入表单
            resetManualForm() {
                this.manualForm.items = [{
                    name: '',
                    item_id: '',
                    item_type: '五星角色',
                    pull_time: new Date().toISOString(),
                    pity: 0
                }];
            },

            // 添加手动录入项
            addManualItem() {
                this.manualForm.items.push({
                    name: '',
                    item_id: '',
                    item_type: '五星角色',
                    pull_time: new Date().toISOString(),
                    pity: 0
                });
            },

            // 删除手动录入项
            removeManualItem(index) {
                if (this.manualForm.items.length > 1) {
                    this.manualForm.items.splice(index, 1);
                }
            },

            // 文件选择
            handleFileSelect(event) {
                const files = event.target.files;
                if (files && files.length > 0) {
                    this.fileForm.files = files;
                    const fileNames = Array.from(files).map(f => f.name).join(', ');
                    this.$root.showMessage(`已选择 ${files.length} 个文件：${fileNames}`, 'info');
                }
            },

            // 清空导入日志
            clearImportLog() {
                this.log = [];
            },

            // 生成示例URL
            generateExampleUrl() {
                this.officialForm.url = 'https://hk4e-api.mihoyo.com/event/gacha_info/api/getGachaLog?authkey=XXXXX';
            }
        },

        created() {
            this.loadDefaults();
        }
    };

    // 注册导入组件
    if (typeof gachaApp !== 'undefined') {
        gachaApp.component('import-tab', {
            name: 'import-tab',
            mixins: [importModule],
            template: `
                <div class="tab-content fade-in">
                    <div class="import-container">
                        <div class="import-header">
                            <h3>🚀 导入抽卡数据</h3>
                            <p>选择导入方式，开始分析你的抽卡历史</p>
                        </div>

                        <el-tabs v-model="activeTab" type="card">
                            <!-- 官方API导入 -->
                            <el-tab-pane label="官方API导入" name="official">
                                <div class="import-section">
                                    <div class="import-form">
                                        <div class="form-item">
                                            <label>选择账户</label>
                                            <el-select v-model="selectedAccountId" placeholder="选择要导入的账户">
                                                <el-option v-for="acc in $root.accounts" :key="acc.id" :label="acc.account_name" :value="acc.id"></el-option>
                                            </el-select>
                                        </div>

                                        <div class="form-item">
                                            <label>抽卡链接</label>
                                            <el-input v-model="officialForm.url" type="url" placeholder="输入你的抽卡历史记录链接...">
                                                <template #append>
                                                    <el-button @click="generateExampleUrl">示例</el-button>
                                                </template>
                                            </el-input>
                                            <small class="form-text">链接应包含 gacha_info/api/getGachaLog</small>
                                        </div>

                                        <div class="form-actions">
                                            <el-button @click="importOfficialApi" type="primary" :loading="importing" :disabled="!isReadyToImport || importing">
                                                <i class="el-icon-download"></i> 开始导入
                                            </el-button>
                                        </div>
                                    </div>
                                </div>
                            </el-tab-pane>

                            <!-- 文件导入 -->
                            <el-tab-pane label="文件导入" name="file">
                                <div class="import-section">
                                    <div class="upload-area" @click="$refs.fileInput.click()">
                                        <i class="el-icon-upload"></i>
                                        <p class="upload-text">点击或拖拽文件到此处</p>
                                        <p class="upload-subtext">支持.json, .csv, .txt格式</p>
                                    </div>

                                    <input ref="fileInput" type="file" multiple @change="handleFileSelect" accept=".json,.csv,.txt" style="display: none;">

                                    <div class="form-actions">
                                        <el-button @click="$refs.fileInput.click()" :loading="importing">选择文件</el-button>
                                        <el-button type="primary" @click="importFromFile" :loading="importing" :disabled="!isReadyToImport || !fileForm.files.length">
                                            开始导入
                                        </el-button>
                                    </div>
                                </div>
                            </el-tab-pane>

                            <!-- 手动录入 -->
                            <el-tab-pane label="手动录入" name="manual">
                                <div class="import-section">
                                    <div class="manual-form">
                                        <div class="form-item">
                                            <label>选择账户</label>
                                            <el-select v-model="selectedAccountId" placeholder="选择账户">
                                                <el-option v-for="acc in $root.accounts" :key="acc.id" :label="acc.account_name" :value="acc.id"></el-option>
                                            </el-select>
                                        </div>

                                        <h4>抽卡记录</h4>
                                        <div v-for="(item, index) in manualForm.items" :key="index" class="manual-item">
                                            <el-form :model="item" label-position="left">
                                                <el-row :gutter="16">
                                                    <el-col :span="8">
                                                        <el-form-item label="物品名称">
                                                            <el-input v-model="item.name" placeholder="输入物品名称"></el-input>
                                                        </el-form-item>
                                                    </el-col>
                                                    <el-col :span="6">
                                                        <el-form-item label="物品类型">
                                                            <el-select v-model="item.item_type">
                                                                <el-option label="五星角色" value="五星角色"></el-option>
                                                                <el-option label="五星武器" value="五星武器"></el-option>
                                                                <el-option label="四星角色" value="四星角色"></el-option>
                                                                <el-option label="四星武器" value="四星武器"></el-option>
                                                                <el-option label="三星武器" value="三星武器"></el-option>
                                                            </el-select>
                                                        </el-form-item>
                                                    </el-col>
                                                    <el-col :span="5">
                                                        <el-form-item label="保底计数">
                                                            <el-input-number v-model="item.pity" :min="0"></el-input-number>
                                                        </el-form-item>
                                                    </el-col>
                                                    <el-col :span="5">
                                                        <el-button v-if="manualForm.items.length > 1" @click="removeManualItem(index)" type="danger" size="small" circle>
                                                            <i class="el-icon-delete"></i>
                                                        </el-button>
                                                    </el-col>
                                                </el-row>
                                            </el-form>
                                        </div>

                                        <div class="manual-actions">
                                            <el-button @click="addManualItem" size="small">
                                                <i class="el-icon-plus"></i> 添加记录
                                            </el-button>
                                        </div>
                                    </div>

                                    <div class="form-actions">
                                        <el-button type="primary" @click="importFromManual" :loading="importing" :disabled="!isReadyToImport">
                                            <i class="el-icon-check"></i> 录入数据
                                        </el-button>
                                    </div>
                                </div>
                            </el-tab-pane>
                        </el-tabs>

                        <div class="import-log" v-if="importing">
                            <h4>导入日志</h4>
                            <div class="log-content">
                                <div v-for="(msg, index) in log" :key="index" class="log-item">
                                    <span class="timestamp">{{ new Date().toLocaleTimeString() }}</span>
                                    <span class="log-text">{{ msg }}</span>
                                </div>
                                <div v-if="!importComplete" class="log-loading">正在处理...</div>
                            </div>
                            <el-progress :percentage="progress" :stroke-width="10"></el-progress>
                        </div>
                    </div>
                </div>
            `
        });
    }
})();