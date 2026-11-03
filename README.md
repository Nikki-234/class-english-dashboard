# Class English Dashboard ｜ 班级英语学习仪表盘生成器

一个面向英语教师的**单文件 HTML 班级学情仪表盘生成工具**：准备好成绩表 xlsx，运行一条命令，即可生成功能完整的仪表盘网页——教师用浏览器打开即可编辑数据、追踪每个学生的学习进度。

## 目录结构

```
class-english-dashboard/
├── SKILL.md                          # Claude Code Skill 描述
├── README.md                         # 本文件
├── LICENSE                           # MIT
├── scripts/
│   └── generate.py                   # 成绩表 xlsx → 单文件 HTML
├── assets/
│   └── dashboard-template.html       # 仪表盘模板（含数据占位符）
├── references/
│   └── roster-schema.md              # 成绩表 xlsx 格式说明
└── 成绩表1.xlsx                       # 示例数据（高二(5)班）
```

## 快速开始

需要 Python 3 和 `openpyxl`：

```bash
pip3 install openpyxl

# 生成仪表盘
python3 scripts/generate.py 成绩表1.xlsx 高二5班仪表盘.html

# 自定义标题与班级名
python3 scripts/generate.py 成绩表1.xlsx 输出.html --class-name "高二(5)班" --title "高二(5)班英语学情看板"
```

生成的 HTML 用浏览器打开即可，无需服务器、无需联网。

## 脚本做了什么

```
[1/4] 读取成绩表: 成绩表1.xlsx
      读取到 40 名学生
      识别到班级: 高二(5)班
[2/4] 分析完成:
      平均分 122.3 | 中位 123.0 | 最高 144 | 最低 108 | σ 7.8
      分数段: >=135 2人 | 125-134 11人 | 115-124 17人 | <115 10人
      四项达标率: 听 71.2% | 读 74.3% | 写 69.2% | 词 72.8%
      弱项分布: Writing 25人 | Listening 12人 | Reading 3人
[3/4] 注入模板
      已写入 高二5班仪表盘.html (61,048 字节)
[4/4] 验证 JS 语法: OK
```

## 仪表盘功能

| 模块 | 说明 |
|---|---|
| KPI 条 | 均分、中位、极差、σ、A+ 区 / C 区人数、距高考目标差、Tier 分布 |
| 分数段分布 | 4 个分数段横向条，颜色对应 Tier 色板 |
| 四项分项达标率 | 听 / 读 / 写 / 词，含 80% 目标线 |
| 弱项分布 | 按 Writing / Listening / Reading 分组计数 |
| 本周班级进度 | 汇总教师在抽屉中填入的完成百分比 |
| 学生名单表 | 40 行 × 12 列，**单元格可直接编辑** |
| 详情抽屉 | 学习进度 / 提升策略 / 教师备注 三 Tab |
| 交互 | 搜索、Tier 筛选、5 种排序 |
| 持久化 | localStorage 自动保存 |
| 备份 | JSON 导入导出、一键重置 |

## 编辑交互

| 操作 | 效果 |
|---|---|
| 单击可编辑单元格 | 进入编辑（输入框或下拉） |
| Enter | 确认 |
| Esc | 取消 |
| 失焦 | 自动保存并触发全局重算 |
| 点击行空白处 | 打开该学生详情抽屉 |

修改任一单元格后，KPI 条、分数段、四项达标率、班级进度会**立即重算**——派生值与源数据始终一致，不会出现"改了分数但统计没变"的错位。

## 成绩表格式

见 [references/roster-schema.md](references/roster-schema.md)。核心要求：

- 表头行含 `ID` 与 `Name` 两列（脚本在前 20 行内自动定位）
- A–N 列顺序固定：ID / 姓名 / Tier / 当前分 / 目标分 / 词汇 / 词汇目标 / 听 / 听目标 / 读 / 读目标 / 写 / 写目标 / 弱项
- 分项用 `23/30` 格式，弱项用 `Writing` / `Listening` / `Reading`

## 依赖

- **必需**：Python 3 + `openpyxl`
- **可选**：Node.js（仅用于生成时验证 JS 语法；未安装时脚本自动跳过该步骤，不影响交付）

## License

MIT
