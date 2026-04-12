// charts.js - 图表模块
(function() {
    'use strict';

    window.ChartUtil = {
        // 初始化ECharts实例
        initChart(container) {
            return echarts.init(container);
        },

        // 销毁图表实例
        disposeChart(chart) {
            if (chart && chart.dispose) {
                chart.dispose();
            }
        },

        // 通用饼图配置
        getPieOption(data, title = '饼图') {
            return {
                title: {
                    text: title,
                    left: 'center',
                    textStyle: {
                        fontSize: 16,
                        fontWeight: 'normal'
                    }
                },
                tooltip: {
                    trigger: 'item',
                    formatter: '{a} <br/>{b}: {c} ({d}%)'
                },
                legend: {
                    bottom: '5%',
                    left: 'center'
                },
                series: [{
                    name: title,
                    type: 'pie',
                    radius: ['40%', '70%'],
                    avoidLabelOverlap: false,
                    itemStyle: {
                        borderRadius: 10,
                        borderColor: '#fff',
                        borderWidth: 2
                    },
                    label: {
                        show: false,
                        position: 'center'
                    },
                    emphasis: {
                        label: {
                            show: true,
                            fontSize: '30',
                            fontWeight: 'bold'
                        }
                    },
                    labelLine: {
                        show: false
                    },
                    data: data
                }]
            };
        },

        // 通用柱状图配置
        getBarOption(data, title = '柱状图', xAxisKey = 'name', yAxisKey = 'value') {
            return {
                title: {
                    text: title,
                    left: 'center'
                },
                tooltip: {
                    trigger: 'axis',
                    axisPointer: {
                        type: 'shadow'
                    }
                },
                xAxis: {
                    type: 'category',
                    data: data.map(d => d[xAxisKey])
                },
                yAxis: {
                    type: 'value'
                },
                series: [{
                    data: data.map(d => d[yAxisKey]),
                    type: 'bar',
                    itemStyle: {
                        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                            { offset: 0, color: '#83bff6' },
                            { offset: 0.5, color: '#188df0' },
                            { offset: 1, color: '#188df0' }
                        ])
                    },
                    emphasis: {
                        itemStyle: {
                            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                                { offset: 0, color: '#2378f7' },
                                { offset: 0.7, color: '#2378f7' },
                                { offset: 1, color: '#83bff6' }
                            ])
                        }
                    }
                }]
            };
        },

        // 通用折线图配置
        getLineOption(data, title = '折线图', xAxisKey = 'name', yAxisKey = 'value') {
            return {
                title: {
                    text: title,
                    left: 'center'
                },
                tooltip: {
                    trigger: 'axis',
                    axisPointer: {
                        type: 'line',
                        animation: false,
                        label: {
                            backgroundColor: '#505765'
                        }
                    }
                },
                xAxis: {
                    type: 'category',
                    data: data.map(d => d[xAxisKey])
                },
                yAxis: {
                    type: 'value',
                    name: '抽卡数'
                },
                series: [{
                    name: title,
                    type: 'line',
                    data: data.map(d => d[yAxisKey]),
                    smooth: true,
                    symbol: 'circle',
                    symbolSize: 8,
                    lineStyle: {
                        width: 3,
                        color: '#409EFF'
                    },
                    itemStyle: {
                        color: '#409EFF',
                        borderColor: '#fff',
                        borderWidth: 2
                    },
                    emphasis: {
                        focus: 'series'
                    }
                }]
            };
        },

        // 散点图配置（抽卡分布）
        getScatterOption(data, title = '抽卡分布') {
            return {
                title: {
                    text: title,
                    left: 'center'
                },
                tooltip: {
                    position: 'top',
                    formatter: function(params) {
                        return `第 ${params.value[0]} 抽: ${params.value[1]} 次`;
                    }
                },
                xAxis: {
                    type: 'value',
                    min: 0,
                    name: '抽卡位置',
                    nameTextStyle: {
                        color: '#909399'
                    }
                },
                yAxis: {
                    type: 'value',
                    min: 0,
                    name: '次数',
                    nameTextStyle: {
                        color: '#909399'
                    }
                },
                visualMap: {
                    min: 0,
                    max: Math.max(...data.map(d => d[1])),
                    calculable: true,
                    orient: 'horizontal',
                    left: 'center',
                    bottom: '15%',
                    inRange: {
                        color: ['#50a3ba', '#eac736', '#d94e5d']
                    }
                },
                series: [{
                    name: '抽卡分布',
                    type: 'scatter',
                    data: data,
                    symbolSize: function(data) {
                        return Math.sqrt(data[1]) * 10;
                    },
                    itemStyle: {
                        opacity: 0.8,
                        shadowBlur: 10,
                        shadowOffsetX: 0,
                        shadowOffsetY: 0,
                        shadowColor: 'rgba(0, 0, 0, 0.3)'
                    }
                }]
            };
        },

        // 柱状图对比
        getCompareBarOption(series1, series2, title = '对比分析') {
            return {
                title: {
                    text: title,
                    left: 'center'
                },
                tooltip: {
                    trigger: 'axis',
                    axisPointer: {
                        type: 'shadow'
                    }
                },
                legend: {
                    data: [series1.name, series2.name]
                },
                xAxis: {
                    type: 'category',
                    data: series1.data.map(d => d.name)
                },
                yAxis: {
                    type: 'value'
                },
                series: [
                    {
                        name: series1.name,
                        type: 'bar',
                        data: series1.data.map(d => d.value),
                        itemStyle: {
                            color: '#409EFF'
                        }
                    },
                    {
                        name: series2.name,
                        type: 'bar',
                        data: series2.data.map(d => d.value),
                        itemStyle: {
                            color: '#67C23A'
                        }
                    }
                ]
            };
        }
    };

    // 抽卡分析专用图表
    window.GachaCharts = {
        // 渲染星级分布饼图
        renderStarRatePie(container, stats) {
            const data = [
                { name: '五星', value: stats.five_star_count || 0 },
                { name: '四星', value: stats.four_star_count || 0 },
                { name: '三星', value: stats.three_star_count || 0 }
            ];

            const option = ChartUtil.getPieOption(data, '抽卡分布');
            const chart = ChartUtil.initChart(container);
            chart.setOption(option);
            return chart;
        },

        // 渲染抽卡趋势折线图
        renderPullTrend(container, data) {
            const chartData = data.map((d, index) => ({
                name: index + 1,
                value: d
            }));

            const option = ChartUtil.getLineOption(chartData, '抽卡趋势');
            const chart = ChartUtil.initChart(container);
            chart.setOption(option);
            return chart;
        },

        // 渲染保底分析散点图
        renderPityScatter(container, pityData) {
            const chartData = pityData.map(d => [d.position, d.frequency]);
            const option = ChartUtil.getScatterOption(chartData, '保底分布');
            const chart = ChartUtil.initChart(container);
            chart.setOption(option);
            return chart;
        },

        // 渲染月度对比柱状图
        renderMonthlyComparison(container, data1, data2, label1, label2) {
            const option = ChartUtil.getCompareBarOption(
                { name: label1, data: data1 },
                { name: label2, data: data2 },
                '月度抽卡对比'
            );
            const chart = ChartUtil.initChart(container);
            chart.setOption(option);
            return chart;
        },

        // 渲染欧皇度分析
        renderLuckinessChart(container, data) {
            const option = {
                title: {
                    text: '欧皇度分析',
                    left: 'center'
                },
                series: [{
                    type: 'gauge',
                    startAngle: 180,
                    endAngle: 0,
                    min: 0,
                    max: 100,
                    radius: '80%',
                    center: ['50%', '70%'],
                    axisLine: {
                        lineStyle: {
                            width: 30,
                            color: [
                                [0.3, '#67e0e3'],
                                [0.7, '#37a2da'],
                                [1, '#fd666d']
                            ]
                        }
                    },
                    pointer: {
                        itemStyle: {
                            color: 'auto'
                        }
                    },
                    axisTick: {
                        distance: -30,
                        length: 8,
                        lineStyle: {
                            color: '#fff',
                            width: 2
                        }
                    },
                    splitLine: {
                        distance: -30,
                        length: 30,
                        lineStyle: {
                            color: '#fff',
                            width: 4
                        }
                    },
                    axisLabel: {
                        color: 'auto',
                        distance: 40,
                        fontSize: 20
                    },
                    detail: {
                        valueAnimation: true,
                        formatter: '{value}%',
                        color: 'auto',
                        fontSize: 30
                    },
                    data: [{
                        value: data.luckiness,
                        name: '幸运值'
                    }]
                }]
            };

            const chart = ChartUtil.initChart(container);
            chart.setOption(option);
            return chart;
        }
    };
})();