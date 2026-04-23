# Vendored Dependencies

本目录存放无法通过内网 pip 源安装的第三方开源库源码。

## 结构

```
vendor/
└── graphify/      # https://github.com/safishamsi/graphify
    ├── graphify/  # Python 包（核心代码）
    └── pyproject.toml
```

## 为什么 vendor 而不是 pip 安装？

企业内网 pip 镜像不包含该依赖，因此将源码直接内嵌到项目中，通过
`[tool.hatch.build.targets.wheel] packages` 一并打包。

## 如何升级 graphify

1. 从开源仓库下载新版本的 zip 包（或在可访问外网的机器上 clone）
2. **全量覆盖** `vendor/graphify/` 目录：
   ```bash
   rm -rf vendor/graphify
   cp -r /path/to/new-graphify vendor/graphify
   ```
3. 重新安装：
   ```bash
   pip install -e .
   ```

> 注意：升级时 `.git/`、`tests/`、`docs/`、`worked/` 等目录已在 `.gitignore`
> 中排除，不会被 git 追踪，无需手动清理。
