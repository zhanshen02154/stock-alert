
<a name="v3.1.0"></a>
## [v3.1.0](https://github.com/zhanshen02154/sock-alert/compare/v3.0.0...v3.1.0) (2026-06-15)

### Refactor

* 增加反思提示词
* 调整获取库存的返回值
* 完成多模块迭代优化，统一任务处理流程([#55](https://github.com/zhanshen02154/sock-alert/issues/55))
* **checkpointer:** 简化remove_all_checkpointers的异常处理


<a name="v3.0.0"></a>
## [v3.0.0](https://github.com/zhanshen02154/sock-alert/compare/v2.1.3...v3.0.0) (2026-05-17)

### Feat

* 增加qwen3.5-plus-2026-04-20的支持
* 增加对deepseek的支持
* 新增多智能体库存管理系统，支持知识库检索和扩展能力([#46](https://github.com/zhanshen02154/sock-alert/issues/46))
* **auth:** 支持从URL参数获取token并允许SSE接口无状态访问([#46](https://github.com/zhanshen02154/sock-alert/issues/46))
* **prompts:** 添加库存助手相关的提示配置文件([#46](https://github.com/zhanshen02154/sock-alert/issues/46))

### Fix

* 修复已完成任务列表的错误
* 修复跨域请求问题
* 删除worker_llm参数
* 修正提示词
* 修复依赖缺失问题

### Refactor

* update langfuse import to use langfuse.decorators.observe
* update langfuse import to use langfuse.decorators.observe
* 重构供应链智能体系统，适配新业务架构
* 重构工具模块，移除废弃基类并新增多类业务工具([#46](https://github.com/zhanshen02154/sock-alert/issues/46))
* 重构库存管理模块为LangGraph实现([#46](https://github.com/zhanshen02154/sock-alert/issues/46))
* **api_client:** 重构HTTP客户端为类方法并添加日志
* **data_query_agent:** 简化注释并添加查询结果到返回命令([#46](https://github.com/zhanshen02154/sock-alert/issues/46))
* **llm:** 重构LLM模块为工厂模式并添加验证功能([#46](https://github.com/zhanshen02154/sock-alert/issues/46))
* **prompts:** 重构提示词加载逻辑并新增获取接口
* **tools:** 重构工具模块为函数式实现并简化注册逻辑([#46](https://github.com/zhanshen02154/sock-alert/issues/46))


<a name="v2.1.3"></a>
## [v2.1.3](https://github.com/zhanshen02154/sock-alert/compare/v2.1.2...v2.1.3) (2026-05-06)

### Feat

* 新增相似度搜索
* 检查点缓存时间从配置获取([#40](https://github.com/zhanshen02154/sock-alert/issues/40))
* 新增检查点缓存时间([#40](https://github.com/zhanshen02154/sock-alert/issues/40))

### Fix

* 恢复max_input_tokens限制
* 防止重复创建__rag_chain

### Refactor

* 重构分割器
* 调整llm.py参数


<a name="v2.1.2"></a>
## [v2.1.2](https://github.com/zhanshen02154/sock-alert/compare/v2.1.1...v2.1.2) (2026-04-30)

### Feat

* 支持混合检索并优化错误处理 ([#35](https://github.com/zhanshen02154/sock-alert/issues/35))
* 实现自动生成会话标题功能 ([#34](https://github.com/zhanshen02154/sock-alert/issues/34))

### Fix

* 修复agent资源泄漏问题
* 修复多处资源泄漏问题


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

