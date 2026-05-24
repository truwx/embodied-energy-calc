import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import gaussian_kde
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.ticker import MaxNLocator  # 用于设置整数刻度

def analyze_excel_kde(filename="result_urban-回弹和能源效率.xlsx"):
    # 读取 Excel 文件
    df_rebound = pd.read_excel(filename, sheet_name='回弹效应')
    df_efficiency = pd.read_excel(filename, sheet_name='能源效率')

    # 转换为长格式（方便处理）
    df_rebound_long = df_rebound.melt(id_vars='area', var_name='year', value_name='rebound')
    df_efficiency_long = df_efficiency.melt(id_vars='area', var_name='year', value_name='efficiency')

    # 清洗数据（去除缺失值）
    df_rebound_long.dropna(inplace=True)
    df_efficiency_long.dropna(inplace=True)

    # ========== 回弹效应 KDE 图数据准备 ==========
    x_year = df_rebound_long['year'].astype(int).values
    y_rebound = df_rebound_long['rebound'].values

    xy = np.vstack([x_year, y_rebound])
    kde = gaussian_kde(xy)
    xi, yi = np.mgrid[x_year.min():x_year.max():100j, y_rebound.min():y_rebound.max():100j]
    zi = kde(np.vstack([xi.ravel(), yi.ravel()]))

    # ========== 能源效率 vs 回弹效应 KDE 图数据准备 ==========
    # 合并两个表
    df_merged = pd.merge(df_rebound_long, df_efficiency_long, on=['area', 'year'])
    x_eff = df_merged['efficiency'].values
    y_reb = df_merged['rebound'].values

    xy2 = np.vstack([x_eff, y_reb])
    kde2 = gaussian_kde(xy2)
    xi2, yi2 = np.mgrid[x_eff.min():x_eff.max():100j, y_reb.min():y_reb.max():100j]
    zi2 = kde2(np.vstack([xi2.ravel(), yi2.ravel()]))

    # ========== 创建2×2子图网格 ==========
    fig = plt.figure(figsize=(14, 12),dpi = 300)  # 调整整体图大小以适应4个子图

    # 1. 回弹效应3D KDE图（第一行第一列）
    ax1 = fig.add_subplot(2, 2, 1, projection='3d')
    ax1.plot_surface(xi, yi, zi.reshape(xi.shape), cmap='viridis', alpha=0.8)
    ax1.set_xlabel('Year')
    ax1.set_ylabel('Energy Rebound')
    ax1.set_zlabel('Density')
    # 设置x轴为整数刻度
    ax1.xaxis.set_major_locator(MaxNLocator(integer=True))

    # 2. 回弹效应等高线图（第一行第二列）
    ax2 = fig.add_subplot(2, 2, 2)
    ax2.contourf(xi, yi, zi.reshape(xi.shape), levels=50, cmap='viridis')
    ax2.set_xlabel('Year')
    ax2.set_ylabel('Energy Rebound')
    fig.colorbar(ax2.contourf(xi, yi, zi.reshape(xi.shape), levels=50, cmap='viridis'),
                 ax=ax2, label='Density')
    # 3. 效率vs回弹3D KDE图（第二行第一列）
    ax3 = fig.add_subplot(2, 2, 3, projection='3d')
    ax3.plot_surface(xi2, yi2, zi2.reshape(xi2.shape), cmap='plasma', alpha=0.8)
    ax3.set_xlabel('Energy Efficiency')
    ax3.set_ylabel('Energy Rebound')
    ax3.set_zlabel('Density')

    # 4. 效率vs回弹等高线图（第二行第二列）
    ax4 = fig.add_subplot(2, 2, 4)
    ax4.contourf(xi2, yi2, zi2.reshape(xi2.shape), levels=50, cmap='plasma')
    ax4.set_xlabel('Energy Efficiency')
    ax4.set_ylabel('Energy Rebound')
    fig.colorbar(ax4.contourf(xi2, yi2, zi2.reshape(xi2.shape), levels=50, cmap='plasma'),
                 ax=ax4, label='Density')
    # 调整整体布局，避免元素重叠
    plt.tight_layout()

    # 保存组合图像
    # plt.savefig('combined_kde_plots_2x2.png', dpi=300, bbox_inches='tight')
    # 保存为PDF格式
    # plt.savefig('combined_kde_plots_2x2.pdf', format='pdf', bbox_inches='tight',dpi = 300)
    # 显示图像
    plt.show()


# 调用函数
analyze_excel_kde()