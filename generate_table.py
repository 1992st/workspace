from docx import Document
from docx.shared import Pt, RGBColor, Inches, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml.ns import qn

# 创建文档
doc = Document()

# 设置文档标题
title = doc.add_heading('课程表', 0)
title.alignment = WD_ALIGN_PARAGRAPH.CENTER

# 创建表格
table = doc.add_table(rows=14, cols=6)
table.style = 'Light Grid Accent 1'

# 设置表格宽度
for row in table.rows:
    row.height = Cm(0.8)
for i, column in enumerate(table.columns):
    column.width = Cm(2.8 if i == 0 else 2.5)

# 表头
header_cells = table.rows[0].cells
header_data = ['时间', '星期一', '星期二', '星期三', '星期四', '星期五']
for i, cell in enumerate(header_cells):
    cell.text = header_data[i]
    cell.paragraphs[0].runs[0].font.bold = True
    cell.paragraphs[0].runs[0].font.size = Pt(11)
    cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
    cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER

# 上午部分数据
morning_data = [
    ['8:00-8:35\n课前准备', '周倩如', '8:20-8:45\n课前准备', '阳宇', '黄丹丹', '黄丹丹'],
    ['8:35-9:05\n第1节', '升旗', '8:50-9:30\n数学（阳宇）', '数学（阳宇）', '美术（罗彤）', '英语（周倩如）'],
    ['9:05-9:45\n第2节', '数学（阳宇）', '9:40-10:20\n道法（李思妤）', '道法（李思妤）', '体育1（刘红）', '体育1（刘红）'],
    ['9:55-10:35\n大课间', '', '', '', '', ''],
    ['10:45-11:25\n第3节', '音乐（周倩如）', '10:45-11:20\n综合（班会）（周倩如）', '综合（班会）（周倩如）', '语文（周倩如）', '数学（阳宇）'],
    ['11:35-12:10\n第4节', '英语（周倩如）', '11:30-12:10\n音乐（阳宇）', '音乐（阳宇）', '英语（周倩如）', '信息（华志兵）'],
]

# 填充上午数据
for row_idx, row_data in enumerate(morning_data, start=1):
    for col_idx, cell_data in enumerate(row_data):
        cell = table.rows[row_idx].cells[col_idx]
        cell.text = cell_data
        cell.paragraphs[0].runs[0].font.size = Pt(9)
        cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
        cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER

# 下午部分数据
afternoon_data = [
    ['12:10-12:30\n午餐', '12:10-12:30\n午餐', '12:30-12:40\n午餐', '12:30-12:40\n午餐', '12:40-13:45\n午休', '12:40-13:45\n午休'],
    ['12:30-12:40\n劳动实践', '12:40-13:45\n午休', '12:40-13:45\n午休', '12:40-13:45\n午休', '', ''],
    ['14:00-14:40\n第5节', '体育（刘红）', '14:00-14:40\n语文（李丹）', '数学（阳宇）', '道法（李思妤）', '体育1（刘红）'],
    ['14:50-15:30\n第6节', '心理（陈红）', '14:50-15:30\n体育（阳宇）', '科学（陈红）', '语文（李丹）', '科学（陈红）'],
    ['15:30-16:00\n眼保健操/室内体操', '', '', '', '', ''],
    ['16:00-16:40\n延时一', '周倩如', '黄丹丹', '校本课程', '黄丹丹', '黄丹丹'],
    ['16:50-17:30\n延时二', '阳宇', '周倩如', '校本课程', '周倩如', '阳宇'],
]

# 填充下午数据
for row_idx, row_data in enumerate(afternoon_data, start=7):
    for col_idx, cell_data in enumerate(row_data):
        cell = table.rows[row_idx].cells[col_idx]
        cell.text = cell_data
        cell.paragraphs[0].runs[0].font.size = Pt(9)
        cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
        cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER

# 合并"大课间"行的单元格（第4行）
table.rows[3].cells[1].merge(table.rows[3].cells[2])
table.rows[3].cells[1].merge(table.rows[3].cells[2])
table.rows[3].cells[1].merge(table.rows[3].cells[2])

# 合并"午休"行的单元格（第8行）
table.rows[7].cells[1].merge(table.rows[7].cells[2])
table.rows[7].cells[1].merge(table.rows[7].cells[2])
table.rows[7].cells[1].merge(table.rows[7].cells[2])

# 合并"眼保健操"行的单元格（第11行）
table.rows[10].cells[1].merge(table.rows[10].cells[2])
table.rows[10].cells[1].merge(table.rows[10].cells[2])
table.rows[10].cells[1].merge(table.rows[10].cells[2])

# 保存文档
doc.save('/Volumes/zhangstExtern/openclaw/workspace/stone/课程表.docx')
print('Word 文档已生成：课程表.docx')
