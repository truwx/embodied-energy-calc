import pandas as pd
import numpy as np
def calculate_department_consumption(household_data_path, io_data_path):
    """
    计算每个用户在42个部门的消费数据，结合两组消费类型数据，区分农村和城镇居民

    参数:
    household_data_path: 居民消费数据文件路径
    io_data_path: 投入产出表数据文件路径

    返回:
    result_df: 包含每个用户42部门消费数据的DataFrame
    """
    # 读取居民消费数据
    print("读取居民消费数据...")
    household_df = pd.read_excel(household_data_path,sheet_name = "清洗后")

    # 检查必要的列是否存在
    required_columns = ['fid22', 'urban22', '食品', '衣着', '居住', '家庭设备用品',
                        '医疗保健', '文教娱乐', '交通通信', '其他']
    for col in required_columns:
        if col not in household_df.columns:
            raise ValueError(f"居民消费数据中缺少必要的列: {col}")

    # 读取投入产出表数据
    print("读取投入产出表数据...")
    io_df = pd.read_excel(io_data_path,sheet_name = "比例")

    # 检查投入产出表是否有正确的列
    required_io_columns = ['部门', '农村居民1', '城镇居民1', '消费类型1',
                           '农村居民2', '城镇居民2', '消费类型2']
    if not set(required_io_columns).issubset(io_df.columns):
        missing = [col for col in required_io_columns if col not in io_df.columns]
        raise ValueError(f"投入产出表缺少必要的列: {missing}")

    # 获取42个部门的名称（去重）
    departments = io_df['部门'].unique().tolist()

    if len(departments) != 42:
        print(f"警告: 投入产出表中的部门数量为{len(departments)}，不是预期的42个")

    # 创建结果DataFrame，先包含ID和户口类型
    result_df = household_df[['fid22', 'urban22']].copy()

    # 初始化所有部门的消费为0
    for dept in departments:
        result_df[dept] = 0.0

    # 定义处理不同消费类型组的函数
    def process_consumption_group(rural_col, urban_col, type_col):
        """处理一组消费类型数据并返回各部门消费增量"""
        temp_df = pd.DataFrame(0.0, index=household_df.index, columns=departments)

        for dept in departments:
            dept_data = io_df[io_df['部门'] == dept]

            for _, row in dept_data.iterrows():
                consumption_type = row[type_col]
                rural_ratio = row[rural_col]
                urban_ratio = row[urban_col]

                if consumption_type in household_df.columns:
                    # 判断居民类型
                    rural_mask = (household_df['urban22'] != 1) & (household_df['urban22'] != '城镇')
                    urban_mask = (household_df['urban22'] == 1) | (household_df['urban22'] == '城镇')

                    # 累加消费
                    temp_df.loc[rural_mask, dept] += household_df.loc[rural_mask, consumption_type] * rural_ratio
                    temp_df.loc[urban_mask, dept] += household_df.loc[urban_mask, consumption_type] * urban_ratio

        return temp_df

    # 处理第一组消费类型数据
    print("处理第一组消费类型数据...")
    group1_data = process_consumption_group('农村居民1', '城镇居民1', '消费类型1')

    # 处理第二组消费类型数据
    print("处理第二组消费类型数据...")
    group2_data = process_consumption_group('农村居民2', '城镇居民2', '消费类型2')

    # 两组数据相加得到最终结果
    result_df[departments] = group1_data + group2_data

    print("计算完成")
    return result_df

household_data = "2022CFPS.xlsx"
io_data = "2023年全国投入产出表.xlsx"

# 执行计算
result = calculate_department_consumption(household_data, io_data)


def calculate_energy_consumption(consumption_df, energy_intensity_path, leontief_matrix_path):
    """
    计算每个居民的42部门隐含能源消费及总能源消耗

    参数:
    consumption_df: 之前计算得到的居民42部门消费DataFrame（单位：元）
    energy_intensity_path: 能源消耗强度数据文件路径（单位：吨/万元）
    leontief_matrix_path: 列昂惕夫逆矩阵数据文件路径

    返回:
    energy_df: 包含每个居民42部门隐含能源消费及总消耗的DataFrame
    """
    # 读取能源消耗强度数据
    print("读取能源消耗强度数据...")
    energy_intensity = pd.read_excel(energy_intensity_path,sheet_name = "2022E")

    # 检查能源消耗强度数据必要列
    required_energy_cols = ['部门', 'E（单位产出能源消耗强度）（吨标准煤/万元）']
    if not set(required_energy_cols).issubset(energy_intensity.columns):
        missing = [col for col in required_energy_cols if col not in energy_intensity.columns]
        raise ValueError(f"能源消耗强度数据缺少必要的列: {missing}")

    # 读取列昂惕夫逆矩阵（42x42，无行索引和列索引）
    print("读取列昂惕夫逆矩阵...")
    leontief_df = pd.read_excel(leontief_matrix_path,sheet_name = "列昂惕夫逆矩阵",header=None)

    # 检查列昂惕夫逆矩阵维度
    if leontief_df.shape != (42, 42):
        raise ValueError(f"列昂惕夫逆矩阵应为42x42，实际为{leontief_df.shape}")

    # 获取部门列表
    departments = energy_intensity['部门'].tolist()

    if len(departments) != 42:
        raise ValueError(f"能源消耗强度数据中的部门数量应为42，实际为{len(departments)}")

    # 确保部门顺序一致
    consumption_departments = consumption_df.columns[2:].tolist()
    if set(departments) != set(consumption_departments):
        raise ValueError("能源消耗强度数据与居民消费数据中的部门不匹配")

    # 提取能源消耗强度（吨/万元）
    intensity_array = np.array(energy_intensity['E（单位产出能源消耗强度）（吨标准煤/万元）'].values, dtype=np.float64)

    # 列昂惕夫逆矩阵转换为数组
    leontief_matrix = leontief_df.values.astype(np.float64)

    # 提取居民消费数据（单位：元），并转换为万元
    consumption_data = consumption_df[departments].values.astype(np.float64) / 10000  # 元 → 万元

    # 计算隐含能源消费
    leontief_consumption = np.dot(consumption_data, leontief_matrix.T)
    energy_consumption = leontief_consumption * intensity_array

    # 创建结果DataFrame
    energy_df = consumption_df[['fid22', 'urban22']].copy()
    energy_df[departments] = energy_consumption

    # 计算每个居民家庭的能源总消耗（新增步骤）
    energy_df['总能源消耗（吨）'] = energy_df[departments].sum(axis=1)

    print("隐含能源消费及总消耗计算完成")
    return energy_df

# 输入文件路径
energy_intensity_path = "2022E.xlsx"
leontief_matrix_path = "2023年全国投入产出表.xlsx"

# 执行计算
energy_result = calculate_energy_consumption(result, energy_intensity_path, leontief_matrix_path)


def calculate_consumption_type_energy(energy_df, department_mapping_path):
    """
    计算每个居民各消费类型的能源消耗，支持部门按比例分配给多个消费类型

    参数:
    energy_df: 包含居民42部门能源消耗的DataFrame
    department_mapping_path: 消费类型与部门对应关系数据的文件路径（包含分配比例）

    返回:
    type_energy_df: 包含每个居民各消费类型能源消耗的DataFrame
    """
    # 读取消费类型与部门的对应关系（包含分配比例）
    print("读取消费类型与部门的对应关系...")
    mapping_df = pd.read_excel(department_mapping_path)

    # 检查映射数据必要列
    required_mapping_cols = ['消费类型', '部门', '分配比例']
    if not set(required_mapping_cols).issubset(mapping_df.columns):
        missing = [col for col in required_mapping_cols if col not in mapping_df.columns]
        raise ValueError(f"映射数据缺少必要的列: {missing}")

    # 验证分配比例总和是否合理（每个部门在所有消费类型中的分配比例之和应为1）
    dept_groups = mapping_df.groupby('部门')['分配比例'].sum()
    invalid_depts = dept_groups[~np.isclose(dept_groups, 1.0)].index.tolist()
    if invalid_depts:
        raise ValueError(f"以下部门的分配比例总和不等于1: {invalid_depts}")

    # 获取8个消费类型
    consumption_types = mapping_df['消费类型'].unique().tolist()
    if len(consumption_types) != 8:
        print(f"警告: 映射数据中的消费类型数量为{len(consumption_types)}，不是预期的8个")

    # 获取42部门列表（从能源消耗数据中提取）
    departments_in_energy = [col for col in energy_df.columns if col not in ['fid22', 'urban22']]

    # 检查映射数据中的部门是否都在能源消耗数据中
    mapping_departments = mapping_df['部门'].unique().tolist()
    for dept in mapping_departments:
        if dept not in departments_in_energy:
            raise ValueError(f"映射数据中的部门'{dept}'不在能源消耗数据中")

    # 创建结果DataFrame，保留ID和户口类型
    type_energy_df = energy_df[['fid22', 'urban22']].copy()
    # 初始化8个消费类型的能源消耗为0
    for consumption_type in consumption_types:
        type_energy_df[consumption_type] = 0.0

    # 按部门和消费类型的对应关系分配能源消耗
    print("计算各消费类型的能源消耗...")
    for _, row in mapping_df.iterrows():
        consumption_type = row['消费类型']
        dept = row['部门']
        ratio = row['分配比例']

        # 将该部门的能源消耗按比例分配给对应的消费类型
        type_energy_df[consumption_type] += energy_df[dept] * ratio

    print("各消费类型能源消耗计算完成")
    return type_energy_df



# 消费类型与部门对应关系数据文件路径（包含分配比例）
mapping_path = "部门-消费类型对应表.xlsx"

# 执行计算
type_energy_result = calculate_consumption_type_energy(energy_result, mapping_path)
energy_result.to_excel("2022年居民42部门隐含能消耗及总消耗.xlsx",index = False)
type_energy_result.to_excel("2022年居民各消费类型隐含能消耗.xlsx",index = False)