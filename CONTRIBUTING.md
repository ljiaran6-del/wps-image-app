# 贡献指南

感谢你对 WPS图片复刻版 感兴趣！

## 如何贡献

### 提交 Issue

如果你发现 bug 或有新功能建议，请提交 Issue。

提交 bug 时请包含：
- 操作系统版本
- Python 版本
- 复现步骤
- 期望结果 vs 实际结果
- 相关报错信息或截图

### 提交 Pull Request

1. Fork 本仓库
2. 创建你的分支：`git checkout -b feature/xxx` 或 `fix/xxx`
3. 提交改动：`git commit -m "描述你的改动"`
4. 推送到你的 Fork：`git push origin feature/xxx`
5. 提交 Pull Request

## 开发环境

```bash
python -m venv venv
.\venv\Scripts\pip install -r requirements.txt
.\venv\Scripts\python src\main.py
```

## 代码风格

- 保持简洁，避免过度设计
- 新增功能时尽量保持与现有工具系统一致
- 修改 UI 时测试深色主题下的可读性
