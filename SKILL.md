---
name: class-english-dashboard
description: 从成绩表 xlsx 生成单文件 HTML 班级英语学习仪表盘。当用户需要制作班级英语学情看板、学生英语学习进度追踪工具、学情分析可视化页面时使用。输出包含 KPI 条、分数段分布、四项分项达标率、弱项诊断、可编辑学生名单表与详情抽屉的单个 HTML 文件,教师可直接在浏览器中编辑并追踪每个学生的学习进度。
---

# Class English Dashboard

从班级成绩表生成功能完整的单文件 HTML 英语学情仪表盘。

## 快速生成（推荐）

```bash
python3 scripts/generate.py <成绩表.xlsx> <输出.html> [--title "自定义标题"] [--class-name "高二(5)班"]
```

脚本会自动：
1. 定位成绩表的表头行（自动识别 `ID` / `Name` 列），读取全部学生数据
2. 从标题行提取班级名（如 `高二(5)班`）
3. 计算班级统计（均分、中位、σ、分数段、四项达标率、弱项分布）
4. 注入 `assets/dashboard-template.html` 的 `/*STUDENT_DATA_PLACEHOLDER*/` 占位符
5. 用 `node --check` 验证 JS 语法
6. 输出单个 HTML 文件

示例：

```bash
python3 scripts/generate.py 成绩表1.xlsx 高二5班仪表盘.html
```

输出：

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
[4/4] 验证 JS 语法: OK
```

## 手动生成流程

1. **读取数据**：用 `openpyxl` 打开成绩表，找到含 `ID` 与 `Name` 的表头行
2. **组织数据**：按 [references/roster-schema.md](references/roster-schema.md) 的列顺序整理每名学生的字段
3. **注入模板**：读取 `assets/dashboard-template.html`，替换 `/*STUDENT_DATA_PLACEHOLDER*/` 为学生数组的 JSON
4. **语法验证**：提取 `<script>` 内容用 `node --check` 验证
5. **交付**：保存为单个 `.html` 文件

## 数据注入方式

模板中的占位符：

```js
const ORIGINAL = /*STUDENT_DATA_PLACEHOLDER*/;
```

替换为：

```js
const ORIGINAL = [{"id":"S01","name":"何丽","tier":"B","score":123,"target":131,
  "vocab":4643,"vocab_t":5500,"L_cur":23,"L_t":28,"L_max":30,
  "R_cur":31,"R_t":35,"R_max":40,"W_cur":16,"W_t":20,"W_max":25,
  "weakness":"Writing","progress_L":0,"progress_R":0,"progress_W":0,
  "progress_V":0,"note":""}];
```

## 功能清单

| 模块 | 说明 |
|---|---|
| KPI 条 | 均分、中位、极差、σ、A+ 区 / C 区人数、距目标差、Tier 分布 |
| 分数段分布 | 4 个分数段横向条，颜色对应 Tier 色板 |
| 四项分项达标率 | 听 / 读 / 写 / 词，含 80% 目标线 |
| 弱项分布 | 按 Writing / Listening / Reading 分组计数 |
| 本周班级进度 | 汇总教师填入的完成百分比 |
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

修改任一单元格后，KPI 条、分数段、四项达标率、班级进度会**立即重算**——派生值与源数据始终一致。

## 依赖

- Python 3 + `openpyxl`（`pip3 install openpyxl`）
- Node.js（可选，仅用于生成时的 JS 语法验证；缺失时脚本自动跳过该步）

##  Pitfalls

- **模板占位符必须完整**：`/*STUDENT_DATA_PLACEHOLDER*/` 被拆开会导致 JS 语法错误。`generate.py` 在写文件前会做 `node --check`。
- **弱项字段只接受三种值**：`Writing` / `Listening` / `Reading`。其他值会被归为 `Writing`。
- **`progress_*` 字段必须存在**：即使全为 0 也要写入，否则抽屉里的进度输入框会失效。
- **不要在 `data_only=False` 下读取**：xlsx 里的公式单元格需要 `data_only=True` 才能拿到缓存值。
