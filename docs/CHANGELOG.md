
<a name="v2.0.0"></a>
## [v2.0.0](https://github.com/zhanshen02154/sock-alert/compare/v1.0.0...v2.0.0) (2026-04-06)

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

### Refactor

* 重构Agent运行机制
* 重构agent
* 修改工具状态枚举
* 修改查询库存工具
* 重构存储层
* 移除Gradio界面模块
* 重构配置加载逻辑
* 重构LLM客户端架构


<a name="v1.0.0"></a>
## v1.0.0 (2026-03-27)

### Feat

* 支持历史对话与会话管理
* 集成FastAPI并添加健康检查端点
* 初始化代码

### Fix

* 更新依赖配置以修复兼容性问题
* update pip index URL configuration for Dockerfile

### Refactor

* 统一注册工具

