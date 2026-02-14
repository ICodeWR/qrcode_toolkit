# 贡献指南

感谢您对 QR Toolkit 的兴趣！我们欢迎任何形式的贡献，包括但不限于：

- 报告问题
- 提交功能建议
- 提交代码改进
- 完善文档
- 翻译支持

## 开发环境设置

### 前置要求
- Python 3.8 或更高版本，推荐 3.13.0
- [uv](https://github.com/astral-sh/uv) 包管理器（推荐）或 pip
- Git

### 克隆项目

```bash

git clone https://github.com/ICodeWR/qrcode_toolkit.git
或者 
git clone https://gitee.com/ICodeWR/qrcode_toolkit.git

cd qrcode_toolkit
```

### 安装依赖

使用 uv（推荐）：
```bash
uv venv
uv pip install -e ".[dev]"
```

或使用 pip：
```bash
python -m venv venv
# source venv/bin/activate  # Linux/macOS
venv\Scripts\activate  # Windows
pip install -e ".[dev]"
```

### 运行测试

```bash
# 运行所有测试
pytest

# 带覆盖率报告
pytest --cov=core --cov=gui --cov-report=html

# 运行特定测试文件
pytest tests/test_database.py
```

## 代码规范

我们遵循以下规范：

1. **PEP 8** - Python代码风格指南
2. **类型注解** - 所有公共函数和类必须包含类型注解
3. **文档字符串** - 使用 Google 风格或 reStructuredText 格式
4. **提交信息** - 遵循 [Conventional Commits](https://www.conventionalcommits.org/)

### 文档字符串示例

```python
def function_name(param1: str, param2: int) -> bool:
    """
    函数功能的简短描述。

    更详细的描述，说明函数的行为、注意事项等。

    Args:
        param1: 参数1的描述
        param2: 参数2的描述

    Returns:
        返回值的描述

    Raises:
        ValueError: 何时会抛出此异常
    """
```

## 提交 Pull Request

1. **Fork** 本仓库
2. 创建您的特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交您的更改 (`git commit -m 'feat: Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开一个 **Pull Request**

### PR 检查清单

- [ ] 代码通过所有测试 (`pytest`)
- [ ] 代码通过类型检查 (`mypy .`)
- [ ] 添加了必要的单元测试
- [ ] 更新了相关文档
- [ ] 遵循了代码规范
- [ ] 提交信息符合规范

## 问题报告

如果您发现了 bug 或有功能建议，请 [创建 Issue](https://gitee.com/icodewr/qrcode_toolkit/issues)。

### Bug 报告模板

```
**描述问题**
清晰简洁地描述问题是什么。

**复现步骤**
1. 打开 '...'
2. 点击 '....'
3. 看到错误

**期望行为**
清晰简洁地描述您期望发生什么。

**截图**
如果适用，添加截图帮助解释问题。

**环境信息**
- 操作系统: [例如 Windows 11]
- Python 版本: [例如 3.13.0]
- QR Toolkit 版本: [例如 1.1.0]

**其他上下文**
添加任何其他关于问题的上下文。
```

### 功能建议模板

```
**功能描述**
清晰简洁地描述您想要的功能。

**使用场景**
描述什么场景下需要这个功能。

**实现思路**
如果您有实现思路，请在这里描述。

**替代方案**
描述您考虑过的任何替代解决方案或功能。
```

## 分支管理

- `main` - 主分支，保持稳定，只接受来自 `develop` 的合并
- `develop` - 开发分支，新功能的基础分支
- `feature/*` - 特性分支，从 `develop` 分支创建
- `bugfix/*` - bug修复分支
- `release/*` - 发布分支

## 版本规范

我们遵循 [语义化版本 2.0.0](https://semver.org/)：

- **主版本号**：不兼容的 API 修改
- **次版本号**：向下兼容的功能性新增
- **修订号**：向下兼容的问题修正

## 许可证

通过贡献代码，您同意您的贡献将采用与本项目相同的 MIT 许可证。

## 行为准则

请确保您阅读并遵守我们的 [行为准则](CODE_OF_CONDUCT.md)。我们致力于营造一个开放、友好的社区环境。

## 联系

如果您有任何问题，可以通过以下方式联系我们：

- **作者**：码上工坊
- **微信公众号**：码上工坊
- **项目主页**：
  - Gitee：[https://gitee.com/icodewr/qrcode_toolkit](https://gitee.com/icodewr/qrcode_toolkit)
  - GitHub：[https://github.com/ICodeWR/qrcode_toolkit](https://github.com/ICodeWR/qrcode_toolkit)

再次感谢您的贡献！🎉