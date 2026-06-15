<a name="v3.1.0"></a>
## [v3.1.0](https://github.com/zhanshen02154/sock-alert/compare/v3.0.0...v3.1.0) (2026-06-14)

### Feat

* 新增 RAG 知识库优化召回率功能

### Fix

* 调整获取库存的返回值，修复 supply_chain 响应中 result 字段提取问题

### Refactor

* 完成多模块迭代优化，统一任务处理流程
* 增加反思提示词
* 简化 checkpointer 异常处理

### Docs

* 完善项目文档
* 修改 README 文件
* 新增 LICENSE 文件

<a name="v3.0.0"></a>
## [v3.0.0](https://github.com/zhanshen02154/sock-alert/compare/v2.1.3...v3.0.0) (2026-05-17)

### Feat

* 新增多智能体库存管理系统，支持知识库检索和增强能力
* 添加qwen3.5-plus-2026-04-20的支持
* 添加对deepseek的支持
* 添加agent提示词加载功能及配置获取方法
* 支持从URL参数获取token并修复USE接口无状态查询问题

### Fix

* 修复完成任务列表的错误
* 修复网络请求问题
* 删除worker_llm参数
* 修复提示词
* 修复库存和盘点查询相关逻辑
* 修复推荐缺失问题

### Refactor

* 重构供应链智能体系统，适配新业务场景
* 重构提示词加载逻辑并新增获取接口
* 重构工具模块，移除冗余基类并新增多类业务工具
* 简化数据查询agent并添加查询结果处理返回功能
* 重构HTTP客户端为类方法并添加日志
* 重构库存管理模块为LangGraph实现
* 重构工具模块为函数式实现并简化调用逻辑
* 重构LLM模块为工厂模式并添加验证功能
* 更新langfuse导入使用langfuse.decorators.observe

### Docs

* 更新自述文件
* 优化项目文档
* 更新README中差异表的对应描述
* update and restructure README.md
* 更新README文档，完善项目介绍与结构说明
* 重写CLAUDE.md文档，更新项目说明和使用指南
* 修复README中Memory模块的描述
* 更新项目目录结构和技术选型说明

### Chore

* 更新项目配置和构建文件
* 更新.dockerignore文件，排除.trae目录
* 在.gitignore中添加sql目录
* 在.gitignore中添加.trae/目录

### Build

* add langmem and asyncmy dependencies

### Style

* 优化嵌入模型代码文件格式

<a name="v2.1.3"></a>
## [v2.1.3](https://github.com/zhanshen02154/sock-alert/compare/v2.1.2...v2.1.3) (2026-05-06)

### Feat

* 新增相似度搜索
* 检查点缓存时间从配置获取 ([#40](https://github.com/zhanshen02154/sock-alert/issues/40))
* 新增检查点缓存时间 ([#40](https://github.com/zhanshen02154/sock-alert/issues/40))

### Fix

* 恢复max_input_tokens限制
* 防止重复创建__rag_chain

### Refactor

* 重构分割器
* 调整llm.py参数

### Chore

* 新增RAGAS依赖
* 新增docker-compose配置
* 更新忽略文件并添加开发环境docker配置

### Docs

* 新增本地开发指南
* 新增claude.md

### Style

* 优化嵌入模型代码文件格式


<a name="v2.1.2"></a>
## [v2.1.2](https://github.com/zhanshen02154/sock-alert/compare/v2.1.1...v2.1.2) (2026-04-30)

### Feat

* 支持混合检索并优化错误处理 ([#35](https://github.com/zhanshen02154/sock-alert/issues/35))
* 实现自动生成会话标题功能 ([#34](https://github.com/zhanshen02154/sock-alert/issues/34))

### Fix

* 修复Agent资源泄漏问题
* 修复多处资源泄漏问题 ([#37](https://github.com/zhanshen02154/sock-alert/issues/37))


<a name="v2.1.1"></a>
## [v2.1.1](https://github.com/zhanshen02154/sock-alert/compare/v2.1.0...v2.1.1) (2026-04-28)

### Fix

* 更新CORS允许的源地址


<a name="v2.1.0"></a>
## [v2.1.0](https://github.com/zhanshen02154/sock-alert/compare/v2.0.0...v2.1.0) (2026-04-28)

### Feat

* 新增RAG信息检索查询 ([#28](https://github.com/zhanshen02154/sock-alert/issues/28))
* 添加文本清洗工具函数

### Fix

* 将 pymilvus 版本降级至 2.6.9

### Refactor

* 移除无用的JWT工具类


<a name="v2.0.0"></a>
## [v2.0.0](https://github.com/zhanshen02154/sock-alert/compare/v1.0.0...v2.0.0) (2026-04-07)

### Feat

* 新增path日志
* 添加redis存储层
* 添加会话标题支持并优化数据结构
* 添加用户登录服务实现
* 添加发起补货申请工具
* 添加用户认证和会话管理API
* 添加JWT和密码加密工具类

### Fix

* 修复跨域请求
* 新增path日志
* 修复跨域请求问题

### Refactor

* 重构Agent运行机制
* 重构agent
* 修改工具状态枚举
* 修改工具状态枚举
* 修改查询库存工具
* 重构存储层
* 移除Gradio界面模块
* 重构配置加载逻辑
* 重构LLM客户端架构


<a name="v1.0.0"></a>
## v1.0.0 (2026-03-30)

### Feat

* 支持历史对话与会话管理
* 集成FastAPI并添加健康检查端点
* 初始化代码

### Fix

* 更新依赖配置以修复兼容性问题
* update pip index URL configuration for Dockerfile

### Refactor

* 统一注册工具