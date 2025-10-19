import pandas as pd
from typing import Dict, List

class TaxDictGenerator:
    """财税票数据字典生成器"""
    
    def __init__(self, excel_path: str):
        self.excel_path = excel_path
        self.all_tables = {}
        self._load_data()
    
    def _load_data(self):
        """加载所有表的字段信息"""
        xl = pd.ExcelFile(self.excel_path)
        
        # 跳过汇总表和代码表
        skip_sheets = ['表汇总', '注册币种码表', '登记注册类型代码', '证件类型代码', 
                      '税款状态代码', '税款属性代码', '项目名称代码', '征收品目代码',
                      '违法违章类型代码', '违法违章状态代码', '违法违章手段代码', 
                      '税务报表类型', '财务报表类型', '商品编码表']
        
        for sheet_name in xl.sheet_names:
            if sheet_name in skip_sheets:
                continue
            
            try:
                # 读取表信息（前4行）
                df_header = pd.read_excel(self.excel_path, sheet_name=sheet_name, header=None, nrows=3)
                table_cn_name = df_header.iloc[0, 1] if len(df_header) > 0 else sheet_name
                table_en_name = df_header.iloc[1, 1] if len(df_header) > 1 else ''
                table_desc = df_header.iloc[2, 1] if len(df_header) > 2 else ''
                
                # 读取字段信息（从第5行开始）
                df_fields = pd.read_excel(self.excel_path, sheet_name=sheet_name, header=4)
                
                self.all_tables[sheet_name] = {
                    'table_cn_name': table_cn_name,
                    'table_en_name': table_en_name,
                    'table_desc': table_desc,
                    'fields': df_fields
                }
                
                print(f"已加载: {sheet_name} ({table_cn_name}) - {len(df_fields)} 个字段")
            except Exception as e:
                print(f"加载 {sheet_name} 失败: {e}")
    
    def get_table_list(self):
        """获取所有表列表"""
        result = []
        for sheet_name, info in self.all_tables.items():
            result.append({
                '工作表名': sheet_name,
                '表中文名': info['table_cn_name'],
                '表英文名': info['table_en_name'],
                '字段数': len(info['fields'])
            })
        return pd.DataFrame(result)
    
    def search_fields(self, keywords: List[str]) -> pd.DataFrame:
        """根据关键字搜索字段"""
        results = []
        
        for sheet_name, info in self.all_tables.items():
            df = info['fields']
            for _, row in df.iterrows():
                field_name = str(row.get('字段名', ''))
                field_cn_name = str(row.get('字段中文名', ''))
                
                # 检查是否匹配关键字
                for keyword in keywords:
                    if keyword in field_name or keyword in field_cn_name:
                        results.append({
                            '表名': sheet_name,
                            '表中文名': info['table_cn_name'],
                            '字段名': field_name,
                            '字段中文名': field_cn_name,
                            '数据类型': row.get('数据类型', ''),
                            '备注': row.get('备注', ''),
                            '使用建议': row.get('使用建议', '')
                        })
                        break
        
        return pd.DataFrame(results)
    
    def generate_field_dict(self, selected_fields: Dict[str, List[str]]) -> Dict:
        """
        生成字段字典
        
        Args:
            selected_fields: {表名: [字段名列表]}
        
        Returns:
            字典数据
        """
        field_dict = {}
        field_info = []
        
        for sheet_name, field_names in selected_fields.items():
            if sheet_name not in self.all_tables:
                print(f"警告: 表 {sheet_name} 不存在")
                continue
            
            table_info = self.all_tables[sheet_name]
            df = table_info['fields']
            
            for field_name in field_names:
                # 查找字段
                row = df[df['字段名'] == field_name]
                if len(row) == 0:
                    print(f"警告: 字段 {sheet_name}.{field_name} 不存在")
                    continue
                
                row = row.iloc[0]
                field_cn_name = row.get('字段中文名', '')
                
                # 添加到字典
                dict_key = f"{field_cn_name}"
                field_dict[dict_key] = field_name
                
                field_info.append({
                    '表名': sheet_name,
                    '表中文名': table_info['table_cn_name'],
                    '字段名': field_name,
                    '字段中文名': field_cn_name,
                    '数据类型': row.get('数据类型', ''),
                    '是否主键': row.get('是否主键', ''),
                    '是否必填': row.get('是否必填', ''),
                    '备注': row.get('备注', '')
                })
        
        return {
            'field_dict': field_dict,
            'field_info': pd.DataFrame(field_info)
        }
    
    def export_to_excel(self, data: Dict, output_file: str):
        """导出到Excel"""
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            # 字段映射表
            df_mapping = pd.DataFrame([
                {'字段中文名': k, '字段英文名': v} 
                for k, v in data['field_dict'].items()
            ])
            df_mapping.to_excel(writer, sheet_name='字段映射', index=False)
            
            # 字段详细信息
            data['field_info'].to_excel(writer, sheet_name='字段详情', index=False)
        
        print(f'Excel文件已生成: {output_file}')


if __name__ == "__main__":
    # 初始化生成器
    generator = TaxDictGenerator(r'C:\Users\21437\Downloads\财税票数据字典-20250417.xlsx')
    
    # 查看所有表
    print("\n所有数据表:")
    print(generator.get_table_list().to_string())
