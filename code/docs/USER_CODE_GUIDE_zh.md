# StaTable 用户代码编写指南



本指南系统性地总结了如何对 StaTable 生成的 C 代码

**添加自定义逻辑、包含文件和辅助函数**。



- 适用版本: **StaTable v3.3.0 及以后**

- 目标读者: 嵌入式工程师（具备 C99 / MISRA C:2012 基础知识）

- 相关文档:

&#x20; - TUTORIAL_ja.md — 教程总览

&#x20; - SPEC_SDK_API_ja.md — SDK / 公开 API

&#x20; - SPEC_AUDIT_ja.md — 标记契约详解

&#x20; - SPEC_CODEGEN_v3.md — 代码生成内部规范

&#x20; - OSAL_PORTING_GUIDE_ja.md — RTOS 移植



---



## 1. 用户代码保护的整体机制



### 1.1 为什么需要标记



StaTable 从 State Machine 设计自动生成 C 代码。

每当设计变更重新生成代码时，**用户手写的实现会丢失**，

这是一个严重问题。



为防止这种情况，StaTable 在生成代码中嵌入**标记**。



&#x20;   /* [[STABLE_USER_CODE_START:Driver_ReadCoinSensor]] */

&#x20;   /* 用户在此处编写实现 */

&#x20;   /* [[STABLE_USER_CODE_END:Driver_ReadCoinSensor]] */



重新生成时，StaTable 会:



1\. 从既有文件中**提取标记之间的内容**

2\. **重新插入**到新生成代码的对应标记之间



这样，**设计变更 → 重新生成 → 用户代码保留** 就实现了自动化。



### 1.2 三种标记



| 标记类型 | 用途 | 位置 |

|---|---|---|

| 函数级 | 角色函数 / ISR 的实现 | 各函数内部 |

| 文件级 | 添加 #include、文件级声明 | include 段之后 |

| 文件末尾 | 辅助函数、静态数据 | 文件末尾 |



---



## 2. 标记清单



| # | 标记 | 用途 |

|---|---|---|

| 1 | STABLE_USER_CODE_START / END | 文件级 |

| 2 | STABLE_USER_CODE_START:<name> / END:<name> | 函数级 |

| 3 | STABLE_USER_CODE_TAIL_START / END | 文件末尾 |



name 的格式:



- 角色函数: Layer_FunctionName （例: Driver_ReadCoinSensor）

- ISR: InterruptName （例: TIMER0）

- 状态动作: Layer_Kind_State_custom （例: Driver_Do_Waiting_custom）



---



## 3. 函数级: 角色函数的实现



### 3.1 生成的模板



StaTable 按以下形式生成各角色函数。



&#x20;   int RoleFunc_Driver_ReadCoinSensor(

&#x20;       const TransitionContext_Driver_t *transition,

&#x20;       SystemContext_t *ctx)

&#x20;   {

&#x20;       STATE_Driver_t from_state = STATE_Driver_MAX;

&#x20;       EVENT_Driver_t event = EVENT_Driver_NONE;

&#x20;       if (transition != NULL) {

&#x20;           from_state = transition->from_state;

&#x20;           event = transition->event;

&#x20;       }



&#x20;       const uint16_t transition_id = Transition_GetId(

&#x20;           transition, call_sites_ReadCoinSensor, ...);



&#x20;       uint32_t *const balance = \&ctx->data.balance;

&#x20;       uint32_t *const price = \&ctx->data.price;

&#x20;       /* ... 其他变量 ... */



&#x20;       int ret = 0;



&#x20;       /* [[STABLE_USER_CODE_START:Driver_ReadCoinSensor]] */

&#x20;       (void)from_state;

&#x20;       (void)event;

&#x20;       (void)transition_id;

&#x20;       (void)balance;

&#x20;       /* ... 未使用变量抑制 ... */



&#x20;       /* Write user implementation code here */

&#x20;       /* [[STABLE_USER_CODE_END:Driver_ReadCoinSensor]] */



&#x20;       return ret;

&#x20;   }



### 3.2 局部变量声明（C99）



由于是 **C99 规范**，可以在块内任意位置声明变量。



推荐: 使用嵌套块



&#x20;   /* [[STABLE_USER_CODE_START:Driver_ReadCoinSensor]] */

&#x20;   (void)from_state;

&#x20;   (void)event;

&#x20;   /* 不使用的变量的 (void) 保留 */

&#x20;   (void)stock;

&#x20;   (void)item_id;

&#x20;   (void)error_code;

&#x20;   (void)g_system_tick;



&#x20;   /* 在嵌套块中声明变量 */

&#x20;   {

&#x20;       uint32_t coin_in = 100;

&#x20;       *coin_value = coin_in;

&#x20;       *balance += coin_in;

&#x20;       if (*balance >= *price) {

&#x20;           ret = 1;

&#x20;       }

&#x20;   }

&#x20;   /* [[STABLE_USER_CODE_END:Driver_ReadCoinSensor]] */



优点: C89 也合法、变量作用域更窄提升可读性、不受重新生成影响。



替代: C99 中途声明



&#x20;   (void)g_system_tick;



&#x20;   uint32_t coin_in = 100;   /* C99 合法 */



若项目要求 C89 规范，则必须使用嵌套块。



### 3.3 (void) 抑制行的处理



生成代码包含**抑制未使用变量警告的行**。



&#x20;   (void)from_state;   /* suppress unused warning */



**使用某变量后应删除其对应的 (void) 行**。保留也无害，

但为可读性建议删除。



| 操作 | 结果 |

|---|---|

| 保留 (void)balance; 同时使用 *balance | 可运行但冗余 |

| 删除 (void)balance; 同时使用 *balance | 推荐 |

| 未使用时删除 (void) | -Wunused-variable 警告 |



### 3.4 实例: 硬币传感器读取



&#x20;   /* [[STABLE_USER_CODE_START:Driver_ReadCoinSensor]] */

&#x20;   (void)from_state;

&#x20;   (void)event;

&#x20;   (void)transition_id;

&#x20;   (void)stock;

&#x20;   (void)item_id;

&#x20;   (void)error_code;

&#x20;   (void)g_system_tick;



&#x20;   {

&#x20;       /* 从硬件寄存器（用户定义）读取硬币类型 */

&#x20;       uint32_t coin_in = Hw_CoinAcceptor_ReadValue();

&#x20;       if (coin_in > 0) {

&#x20;           *coin_value = coin_in;

&#x20;           *balance += coin_in;

&#x20;           ret = 1;   /* 允许转换 */

&#x20;       }

&#x20;   }

&#x20;   /* [[STABLE_USER_CODE_END:Driver_ReadCoinSensor]] */



---



## 4. 文件级: 添加 include（v3.3.0 新功能）



### 4.1 背景



在函数级标记内写 #include 仅在该函数内有效。

若想**在整个文件的所有函数中都可用**，需要使用

**文件级标记**。



### 4.2 生成的模板（v3.3.0 及以后）



.c 文件的 include 段之后会输出空的文件级标记。



&#x20;   /*==============================================================

&#x20;    *  Include files

&#x20;    *==============================================================*/



&#x20;   #include "statable_role_functions_Driver.h"

&#x20;   #include "Middleware/statable_role_functions_Middleware.h"

&#x20;   #include "Application/statable_role_functions_Application.h"



&#x20;   /* [[STABLE_USER_CODE_START]] */

&#x20;   /* [[STABLE_USER_CODE_END]] */



&#x20;   /*==============================================================

&#x20;    *  Role function implementations

&#x20;    *==============================================================*/



### 4.3 手写添加 include



&#x20;   /* [[STABLE_USER_CODE_START]] */

&#x20;   #include "my_hardware.h"

&#x20;   #include "custom_types.h"

&#x20;   /* [[STABLE_USER_CODE_END]] */



这样 my_hardware.h 的内容就能被同一文件内**所有 RoleFunc 引用**。



### 4.4 重新生成时的保留



文件级标记内的内容在重新生成时会**自动保护**。



&#x20;   首次生成 → 空标记

&#x20;     ↓

&#x20;   用户添加 #include

&#x20;     ↓

&#x20;   设计变更 → 重新生成

&#x20;     ↓

&#x20;   标记内的 #include 被保留 ✅



### 4.5 验证方法



StaTable 提供官方测试来机械验证此行为。



&#x20;   cd code

&#x20;   python tools\\test_user_code_roundtrip.py



该命令自动执行:



1\. 从 XML 生成 C 代码

2\. 向文件级标记注入 #include "user_roundtrip_test.h"

3\. 执行**重新生成**（合并）

4\. 检查 include 是否保留

5\. gcc 编译 + ARM 链接



Exit code 0 表示全部 PASS。



---



## 5. 文件末尾: 辅助函数



### 5.1 TAIL 标记



生成文件末尾有用户专用区域。



&#x20;   /* [[STABLE_USER_CODE_TAIL_START]] */

&#x20;   /* Write user-added code here (helper functions, etc.) */

&#x20;   /* [[STABLE_USER_CODE_TAIL_END]] */



### 5.2 用途



- static 辅助函数

- 文件作用域常量表

- 宏定义



&#x20;   /* [[STABLE_USER_CODE_TAIL_START]] */



&#x20;   /* 内部用: 判断硬币类型 */

&#x20;   static uint8_t classify_coin(uint32_t value)

&#x20;   {

&#x20;       if (value == 10)  return 1;

&#x20;       if (value == 50)  return 2;

&#x20;       if (value == 100) return 3;

&#x20;       return 0;

&#x20;   }



&#x20;   /* [[STABLE_USER_CODE_TAIL_END]] */



### 5.3 注意事项



- TAIL 位于**文件末尾**，因此**其前面的函数无法引用**

&#x20; （可先声明后使用，但会变复杂）

- 想从角色函数使用的辅助函数，应将**原型声明放在文件级标记**中，

&#x20; **函数体放在 TAIL** 中，这是常见做法



&#x20;   /* [[STABLE_USER_CODE_START]] */

&#x20;   #include "my_hardware.h"

&#x20;   /* 原型声明 */

&#x20;   static uint8_t classify_coin(uint32_t value);

&#x20;   /* [[STABLE_USER_CODE_END]] */



&#x20;   /* ... 角色函数群 ... */



&#x20;   /* [[STABLE_USER_CODE_TAIL_START]] */

&#x20;   static uint8_t classify_coin(uint32_t value) { /* ... */ }

&#x20;   /* [[STABLE_USER_CODE_TAIL_END]] */



---



## 6. 编译·链接验证



### 6.1 语法验证



&#x20;   cd code

&#x20;   python tools\\verify_c_syntax.py --root output --compiler gcc --std c99 --strict



### 6.2 ARM 链接验证



&#x20;   python tools\\verify_arm_link.py --root output



使用 Cortex-M 链接脚本进行实际链接验证。检测未解析符号。



### 6.3 集成测试



&#x20;   python tools\\test_user_code_roundtrip.py



一次性执行:



1\. 生成

2\. 用户代码注入

3\. 重新生成（合并）

4\. 保留检查

5\. gcc 编译

6\. ARM 链接



---



## 7. 故障排查



### Q1. 用户代码在重新生成后消失了



检查:



1\. 标记拼写错误（STABLE_USER_CODE_START 等）

2\. 标记的**嵌套**（START 内是否写了 START）

3\. code_merger.py 日志中是否出现 Replaced file user code



### Q2. 局部变量声明出现警告



症状: -Wdeclaration-after-statement 警告



原因: 以 C89 模式编译



对策: 用嵌套块 { ... } 包围，或指定 -std=c99 以上



### Q3. 文件级标记中添加的 include 找不到



症状: fatal error: my_hardware.h: No such file or directory



原因: 包含路径未设置



对策: 添加 -I 选项，或在 CMakeLists / Makefile 中指定路径



### Q4. 函数级标记出现多个



症状: 相同 name 的标记出现在多个位置



对策: name 必须唯一。同一角色函数被多个单元格

调用时，生成侧应合并为一个。



### Q5. TAIL 标记内的函数从角色函数看不到



原因: C 的声明顺序（TAIL 在文件末尾）



对策: 将原型声明放在文件级标记中（参见 5.3）



---



## 8. FAQ



### Q. 用户代码有 MISRA 违规，生成侧会检测吗？



A. StaTable 的 MISRA 检查以**生成代码**为对象。

用户代码在同一文件内，也在 cppcheck 的扫描范围内，

但 **MISRA 合规是用户责任**。



### Q. 不小心删除了标记本身？



A. 下次生成时**标记会恢复**，内容会丢失。

请不要删除标记，只编辑内部的代码。



### Q. 想手动重写整个文件



A. 不推荐。下次生成会覆盖大部分。

如确有需要，请将生成目录置于 Git 管理外，

**手动合并**。



### Q. 想在标记之间使用其他标记（嵌套）



A. 不支持。请保持扁平结构。



### Q. 可以删除所有 (void) 行吗？



A. 未使用变量会出现警告。**只删除使用的变量的 (void)**。



---



## 变更历史



| 版本 | 日期 | 内容 |

|---|---|---|

| v3.3.0 | 2026-10-04 | 添加文件级标记说明 |

| v1.0 | 2026-10-04 | 初版创建 |



---



*本指南配合 StaTable v3.3.0 发布而创建。*

