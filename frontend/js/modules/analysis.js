// analysis.js - 数据分析模块
(function() {
    'use strict';

    // 数据分析组件
    const analysis = {
        data() {
            return {
                // 数据选项
                dataOptions: {
                    accountId: null,
                    gameType: 'genshin',
                    dateRange: [],
                    chartType: 'pie',
                    useCache: true
                },

                // 分析结果
                analysisData: null,
                loading: false,
                error: null,

                // 已加载的数据（避免重复请求）
                loadedData: {}
            };
        },

        computed: {
            availableAccounts() {
                return this.$root.accounts.filter(acc => acc.game_type === this.dataOptions.gameType);
            },

            hasData() {
                return this.analysisData && this.analysisData.basic_stats;
            },

            // 计算欧皇度
            luckinessScore() {
                if (!this.analysisData || !this.analysisData.basic_stats) return 0;

                const stats = this.analysisData.basic_stats;
                const pulls = stats.total_pulls || 0;
                const fiveStar = stats.five_star_count || 0;

                if (pulls === 0) return 0;

                // 基础幸运度计算：五星抽卡率
                const baseLuckiness = Math.round((fiveStar / pulls) * 1000);

                // 保底分析
                const pityStats = this.analysisData.pity_stats;
                const avgPity = pityStats ? pityStats.stats?.average_pity || 0 : 0;

                // 总欧皇度（综合考虑抽卡率和保底情况）
                const luckiness = Math.min(95, Math.max(5, baseLuckiness / 10 + avgPity < 80 ? 20 : 0));

                return Math.round(luckiness);
            }
        },

        watch: {
            '$root.currentAccountId': {
                immediate: true,
                handler(accountId) {
                    if (accountId) {
                        this.dataOptions.accountId = accountId;
                        this.refreshAnalysis();
                    }
                }
            },

            'dataOptions': {
                deep: true,
                handler() {
                    this.refreshAnalysis();
                }
            }
        },

        methods: {
            // 刷新分析数据
            async refreshAnalysis() {
                if (!this.dataOptions.accountId) {
                    this.analysisData = null;
                    return;
                }

                try {
                    this.loading = true;
                    this.error = null;

                    // 获取缓存Key
                    const cacheKey = this.getCacheKey();

                    // 检查缓存
                    if (this.loadedData[cacheKey] && this.dataOptions.useCache) {
                        this.analysisData = this.loadedData[cacheKey];
                        return;
                    }

 // 请求新的分析数据 - 使用 RESTful 路径
      const url = `/api/accounts/${this.dataOptions.accountId}/analysis`;
      const params = {};
      if (this.dataOptions.gameType) {
        params.gacha_type = this.dataOptions.gameType;
      }

      const response = await axios.get(url, { params });
      this.analysisData = response.data.data || response.data;

                    // 缓存数据
                    this.loadedData[cacheKey] = response.data;

                } catch (error) {
                    console.error('获取分析数据失败:', error);
                    this.$root.showMessage('获取分析数据失败', 'error');
                    this.error = '获取分析数据失败';
                } finally {
                    this.loading = false;
                }
            },

            // 获取缓存Key
            getCacheKey() {
                return `${this.dataOptions.accountId}_${this.dataOptions.gameType}_${
                    this.dataOptions.dateRange.join('_') || 'all'
                }`;
            },

            // 清空缓存
            clearCache() {
                this.loadedData = {};
                this.$root.showMessage('缓存已清空', 'info');
            },

            // 导出分析结果
            exportAnalysis(format = 'json') {
                if (!this.analysisData) {
                    this.$root.showMessage('暂无数据可导出', 'warning');
                    return;
                }

                let data, fileName;

                if (format === 'json') {
                    data = JSON.stringify(this.analysisData, null, 2);
                    fileName = `gacha_analysis_${new Date().toISOString()}.json`;
                } else if (format === 'csv') {
                    data = this.convertToCSV(this.analysisData);
                    fileName = `gacha_analysis_${new Date().toISOString()}.csv`;
                }

                // 创建下载链接
                const blob = new Blob([data], { type: 'text/plain' });
                const url = URL.createObjectURL(blob);
                const link = document.createElement('a');
                link.href = url;
                link.download = fileName;
                link.click();

                URL.revokeObjectURL(url);
            },

            // 转换为CSV格式
            convertToCSV(data) {
                const headers = ['Item Name', 'Type', 'Rarity', 'Pull Time', 'Pity'];
                const rows = data.items?.map(item => [
                    item.name,
                    item.item_type,
                    item.item_level,
                    item.pull_time,
                    item.pity
                ]) || [];

                const csvContent = [
                    headers.join(','),
                    ...rows.map(row => row.map(field => `"${field}"`).join(','))
                ].join('\n');

                return csvContent;
            },

            // 格式化统计数据
            formatStatsValue(value, unit = '', decimals = 2) {
                if (value === null || value === undefined) return '-';

                if (typeof value === 'number' && value % 1 !== 0) {
                    return value.toFixed(decimals);
                }

                return `${value.toLocaleString()}${unit}`;
            },

            // 格式化百分比
            formatPercentage(value, decimals = 2) {
                if (value === null || value === undefined) return '-';
                return `${(value * 100).toFixed(decimals)}%`;
            }
        }
    };

    // 注册分析组件
    if (typeof gachaApp !== 'undefined') {
        gachaApp.component('analysis-tab', {
            name: 'analysis-tab',
            mixins: [analysis],
            template: `
                <div class="tab-content fade-in">
                    <div v-if="loading" class="analysis-loading">
                        <div class="loading-spinner"></div>
                        <p>正在分析数据...</p>
                    </div>

                    <div v-else-if="error" class="analysis-error">
                        <div class="error-content">
                            <p>{{ error }}</p>
                            <el-button @click="refreshAnalysis(null)">重试</el-button>
                        </div>
                    </div>

                    <div v-else-if="hasData" class="analysis-content">
                        <!-- 分析选项 -->
                        <div class="analysis-config widget-card">
                            <h3>📊 分析选项</h3>

                            <el-row :gutter="20">
                                <el-col :span="8">
                                    <div class="form-item">
                                        <label>选择账户</label>
                                        <el-select v-model="dataOptions.accountId" placeholder="选择要分析的账户">
                                            <el-option v-for="acc in availableAccounts" :key="acc.id" :label="acc.account_name" :value="acc.id"></el-option>
                                        </el-select>
                                    </div>
                                </el-col>

                                <el-col :span="8">
                                    <div class="form-item">
                                        <label>图表类型</label>
                                        <el-radio-group v-model="dataOptions.chartType">
                                            <el-radio-button label="pie">饼图</el-radio-button>
                                            <el-radio-button label="bar">柱状图</el-radio-button>
                                            <el-radio-button label="line">折线图</el-radio-button>
                                        </el-radio-group>
                                    </div>
                                </el-col>

                                <el-col :span="8">
                                    <div class="form-item">
                                        <label>缓存设置</label>
                                        <el-switch v-model="dataOptions.useCache" active-text="启用缓存"></el-switch>
                                    </div>
                                </el-col>
                            </el-row>

                            <div class="analysis-actions">
                                <el-button @click="clearCache()" size="small">清空缓存</el-button>
                                <el-button @click="exportAnalysis('json')" icon="el-icon-download" size="small">导出JSON</el-button>
                                <el-button @click="exportAnalysis('csv')" icon="el-icon-download" size="small">导出CSV</el-button>
                            </div>
                        </div>

                        <!-- 数据概览 -->
                        <el-row :gutter="20" class="summary-section">
                            <el-col :span="8">
                                <div class="stats-card">
                                    <h4>总抽卡数</h4>
                                    <div class="number-display">
                                        <span class="number-value">{{ formatStatsValue(analysisData.basic_stats.total_pulls) }}</span>
                                        <span class="number-unit">次</span>
                                    </div>
                                </div>
                            </el-col>

                            <el-col :span="8">
                                <div class="stats-card">
                                    <h4>欧皇度</h4>
                                    <div class="number-display">
                                        <span class="number-value text-warning">{{ luckinessScore }}%</span>
                                    </div>
                                </div>
                            </el-col>

                            <el-col :span="8">
                                <div class="stats-card">
                                    <h4>平均保底</h4>
                                    <div class="number-display">
                                        <span class="number-value">{{ formatStatsValue(analysisData.pity_stats?.stats?.average_pity || 0) }}</span>
                                        <span class="number-unit">抽</span>
                                    </div>
                                </div>
                            </el-col>
                        </el-row>

                        <el-row :gutter="20" class="detail-section">
                            <el-col :span="6">
                                <div class="stats-card">
                                    <h4>五星数量</h4>
                                    <div class="number-display">
                                        <span class="number-value text-success">{{ formatStatsValue(analysisData.basic_stats.five_star_count) }}</span>
                                        <span class="number-unit">
                                            ({{ formatPercentage(analysisData.basic_stats.five_star_rate) }})
                                        </span>
                                    </div>
                                </div>
                            </el-col>
                            <el-col :span="6">
                                <div class="stats-card">
                                    <h4>四星数量</h4>
                                    <div class="number-display">
                                        <span class="number-value">{{ formatStatsValue(analysisData.basic_stats.four_star_count) }}</span>
                                        <span class="number-unit">
                                            ({{ formatPercentage(analysisData.basic_stats.four_star_rate) }})
                                        </span>
                                    </div>
                                </div>
                            </el-col>
                            <el-col :span="6">
                                <div class="stats-card">
                                    <h4>三星数量</h4>
                                    <div class="number-display">
                                        <span class="number-value">{{ formatStatsValue(analysisData.basic_stats.three_star_count) }}</span>
                                        <span class="number-unit">
                                            ({{ formatPercentage(analysisData.basic_stats.three_star_rate) }})
                                        </span>
                                    </div>
                                </div>
                            </el-col>
                            <el-col :span="6">
                                <div class="stats-card">
                                    <h4>未出五星保底</h4>
                                    <div class="number-display">
                                        <span class="number-value text-danger">{{ analysisData.current_pity || 0 }}</span>
                                        <span class="number-unit">抽</span>
                                    </div>
                                </div>
                            </el-col>
                        </el-row>

                        <!-- 图表区域 -->
                        <div class="chart-section widget-card">
                            <h3>📈 抽卡分布</h3>
                            <div class="chart-container" id="starDistributionChart"></div>
                        </div>

                        <!-- 保底分析 -->
                        <div class="pity-section widget-card" v-if="analysisData.pity_stats">
                            <h3>🎯 保底分析</h3>

                            <el-row :gutter="20">
                                <el-col :span="8">
                                    <div class="pity-stat">
                                        <h4>最低保底</h4>
                                        <span class="number-value">{{ analysisData.pity_stats.stats.min_pity }}</span>
                                        <span class="number-unit">抽</span>
                                    </div>
                                </el-col>
                                <el-col :span="8">
                                    <div class="pity-stat">
                                        <h4>最高保底</h4>
                                        <span class="number-value">{{ analysisData.pity_stats.stats.max_pity }}</span>
                                        <span class="number-unit">抽</span>
                                    </div>
                                </el-col>
                                <el-col :span="8">
                                    <div class="pity-stat">
                                        <h4>平均保底</h4>
                                        <span class="number-value">{{ formatStatsValue(analysisData.pity_stats.stats.average_pity, '', 1) }}</span>
                                        <span class="number-unit">抽</span>
                                    </div>
                                </el-col>
                            </el-row>

                            <!-- 保底分布图 -->
                            <div class="pity-chart-container">
                                <h4>保底分布图</h4>
                                <div class="chart-container small" id="pityDistributionChart"></div>
                            </div>
                        </div>

                        <!-- 抽卡历史表格 -->
                        <div class="history-section widget-card" v-if="analysisData.items && analysisData.items.length > 0">
                            <h3>📝 抽卡历史记录</h3>
                            <el-table :data="analysisData.items.slice(0, 50)" style="width: 100%">
                                <el-table-column prop="pull_time" label="时间" width="180">
                                    <template #default="{ row }">
                                        <el-tag size="small">{{ new Date(row.pull_time).toLocaleString('zh-CN').replace(' ', ' ') }}</el-tag>
                                    </template>
                                </el-table-column>
                                <el-table-column prop="name" label="物品名称"></el-table-column>
                                <el-table-column prop="item_type" label="类型">
                                    <template #default="{ row }">
                                        <el-tag :type="row.item_level === 5 ? 'success' : row.item_level === 4 ? 'warning' : 'info'">
                                            {{ row.item_type }}
                                        </el-tag>
                                    </template>
                                </el-table-column>
                                <el-table-column prop="item_level" label="稀有度" width="60">
                                    <template #default="{ row }">
                                        <el-tag effect="dark">{{ row.item_level }}</el-tag>
                                    </template>
                                </el-table-column>
                                <el-table-column prop="pity" label="保底" width="60">
                                    <template #default="{ row }">
                                        <span class="number">{{ row.pity }}</span>
                                    </template>
                                </el-table-column>
                            </el-table>
                            <div style="text-align: center; margin-top: 16px;">
                                <p class="text-muted">显示最近 50 条记录</p>
                            </div>
                        </div>
                    </div>

                    <div v-else class="empty-state">
                        <div class="empty-icon">📊</div>
                        <p>暂无分析数据</p>
                        <small>请先导入抽卡数据或选择其他账户</small>
                    </div>
                </div>
            `
        });
    }
})();