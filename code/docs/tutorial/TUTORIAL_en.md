# StaTable Tutorial — Complete Edition

Version: 2.0
Date: 2026-10-04
Target: StaTable v3.3.0 or later
Audience: Designers new to StaTable

---

## Table of Contents

### Introduction
1. How This Tool Thinks
2. Subject: A Vending Machine Control Program

### Main — Building the Skeleton
3. Step 1: Create a Project
4. Step 2: Build the Skeleton (States + Events)

### Main — Filling the Matrix
5. Step 3: Build Transitions (Starting from the Driver Layer)
6. Step 4: Finish the Cells (First Role Function Registration)
7. Step 5: Finish the States
8. Step 6: Complete the Other Layers Similarly

### Main — Completing
9. Step 7: Verify with Diagrams
10. Step 8: Generate C Code
11. Step 9: Integrate into Embedded
12. Step 10: Save the Project

### Advanced
13. Reusing Existing Projects
14. Iterative Development

### Summary
15. Task × Feature Cross-Reference
16. FAQ
17. Next Steps

### Appendix
A. Marker Reference
B. Terminology Mapping
C. Glossary
D. Changelog

---

# Introduction

---

## 1. How This Tool Thinks

### 1.1 What StaTable Does

StaTable is a tool that **defines program parts, assembles them into a
state-transition matrix, and builds a working program from them**.

- **Parts** = Role functions (what the system can do)
- **Assembly** = state transitions (when each part is used)
- **Finished product** = a state machine (emitted as C code)

It is especially well suited to programs like the following:

| Suitable program type | Examples |
|---|---|
| Clearly defined state transitions | Vending machines, washing machines, elevators |
| Event-driven behavior | Interrupt handlers, communication protocols |
| Embedded systems | MCU firmware in general |
| MISRA C:2012 compliance required | Automotive, medical, industrial equipment |

### 1.2 The "Parts" and "Assembly" Analogy

Think of it like building an electronic circuit board.

    +-----------------------------------------------+
    |  StaTable = a breadboard                      |
    |                                               |
    |  +-------------+    +---------------+         |
    |  | Parts box   |    | Wiring panel  |         |
    |  | (Role funcs)|    | (transition   |         |
    |  |             |    |  matrix)      |         |
    |  | - coin test |    |               |         |
    |  | - dispense  |    | Idle|Sel|Pay  |         |
    |  | - change    |    | ----+---+---  |         |
    |  | - error     |    | Sel | O |     |         |
    |  | - motor     |    | Pay |   | O   |         |
    |  +-------------+    +---------------+         |
    +-----------------------------------------------+

1. First, **stock the parts box** (define functions)
2. Next, **place parts on the wiring panel** (fill in the transition matrix)
3. The circuit diagram (state machine) is assembled

### 1.3 Overall Workflow (Skeleton then Fill)

The recommended workflow, leveraging StaTable's strengths:

    Step 1: Create a project
           |
    Step 2: Build the skeleton (states + events)
           |  -> The transition matrix frame appears automatically
           |
    Step 3: Fill in transitions (cell by cell)
           |  -> Add role functions on the spot as needed
           |
    Step 4: Finish the cells (actions, relations)
           |
    Step 5: Finish the states (entry / exit)
           |
    Step 6: Complete (verify -> generate C -> integrate)

#### Why "Skeleton then Fill"?

| # | Reason |
|---|---|
| 1 | Registering states and events **auto-generates the matrix frame** |
| 2 | You can work **while looking at the design diagram** (supports exploratory design) |
| 3 | **Add role functions as needed** (do not create unused parts) |
| 4 | You can start even if the paper design is incomplete |

### 1.4 Terminology (Role Function = a Part)

In this tutorial, StaTable terms are used as follows:

| StaTable term | In this tutorial | Meaning |
|---|---|---|
| **Role function** | **Part (capability)** | Something the system can do |
| **State** | State | A mode of operation |
| **Event** | Trigger | A signal that changes state |
| **Transition** | Transition | "When event X arrives in state A, go to state B" |
| **Layer** | Layer | Grouping by role (Driver / Middleware / Application) |
| **Namespace** | Namespace | Which layer a part belongs to |

#### Example of "Role Function = Part" (Vending Machine)

| Abstraction | Form | Example |
|---|---|---|
| High | Capability | "Validate a coin" |
| Medium | Operation | `ValidateCoin()` |
| Low | C function | `int RoleFunc_Middleware_ValidateCoin(...)` |

The tutorial starts at the **"capability" level** and gradually makes
things concrete.

#### Relationship Diagram of Terms

       Layer
          |
          | contains
          v
    Role function (part)
          |
          | used by
          v
    Transition  <--  State x Event
          |
          | aggregated into
          v
    State Machine

---

## 2. Subject: A Vending Machine Control Program

### 2.1 What to Build (Product Overview)

We will build a **vending machine control program**.

#### Basic Behavior

1. A customer selects a product
2. The customer inserts coins
3. If enough money is inserted, dispense the product
4. If there is change, return it
5. Return to the idle state

#### Error Handling

- Product jam
- Out of change
- Power failure
- Invalid coin

#### Why Use a Vending Machine as the Subject?

| # | Reason |
|---|---|
| 1 | **Concrete state transitions** - Idle, Select, Pay, Dispense, Done |
| 2 | **Rich events** - button, coin, timeout, error |
| 3 | **Clear "parts"** - coin validation, product dispensing, change calculation |
| 4 | **Easy to sketch** - anyone can imagine the behavior |
| 5 | **Natural error handling** - jam, out of change, power failure |

### 2.2 Three-Layer Architecture

A vending machine is composed of **three layers**. Each layer is
**self-contained**, and role functions are not shared across layers.

#### Responsibilities of Each Layer

| Layer | Responsibility | Main Functions |
|---|---|---|
| **Application** | Sales flow control | Product selection, purchase confirmation, change requests |
| **Middleware** | Device abstraction | Coin validation, dispensing control, change calculation |
| **Driver** | Hardware control | Motor drive, sensor read, LCD write, key read |

#### Layer Independence (Important)

Role functions of each layer are **used only within that layer**.

    GOOD design (layer independence)
       Application layer: uses only Application role functions
       Middleware layer:  uses only Middleware role functions
       Driver layer:      uses only Driver role functions

    BAD design (inter-layer dependency)
       Application layer: directly calls Driver role functions

**Why layer independence matters:**

| # | Reason |
|---|---|
| 1 | **Each layer can be tested independently** |
| 2 | **Easier to reuse for other products** |
| 3 | **Clear maintenance scope** |
| 4 | **Helps keep MISRA C:2012 complexity low** |

### 2.3 What States Exist?

We design the states of each layer on paper.

#### Application Layer States

| # | State | Description |
|---|---|---|
| 1 | `Idle` | Waiting (for customer) |
| 2 | `ProductSelected` | Product selected |
| 3 | `AwaitingPayment` | Awaiting payment |
| 4 | `Dispensing` | Dispensing product |
| 5 | `ReturningChange` | Returning change |
| 6 | `Error` | Error state |

#### Middleware Layer States

| # | State | Description |
|---|---|---|
| 1 | `MwIdle` | Waiting |
| 2 | `CoinAccepting` | Accepting coins |
| 3 | `Dispensing` | Dispensing control |
| 4 | `ChangeCalculating` | Calculating change |

#### Driver Layer States

| # | State | Description |
|---|---|---|
| 1 | `HwIdle` | Hardware idle |
| 2 | `HwActive` | Hardware active |
| 3 | `HwError` | Hardware error |

### 2.4 What Changes State? (Events)

We design the events of each layer on paper.

#### Application Layer Events

| # | Event | Description |
|---|---|---|
| 1 | `SELECT` | Product selection button pressed |
| 2 | `COIN_IN` | Coin insertion detected |
| 3 | `CONFIRM` | Purchase confirmed |
| 4 | `DISPENSE_DONE` | Dispensing complete |
| 5 | `CHANGE_DONE` | Change return complete |
| 6 | `CANCEL` | Cancel |
| 7 | `ERROR` | Error occurred |
| 8 | `RESET` | Error reset |

#### Middleware Layer Events

| # | Event | Description |
|---|---|---|
| 1 | `MW_START_COIN` | Start accepting coins |
| 2 | `MW_COIN_VALID` | Valid coin detected |
| 3 | `MW_COIN_INVALID` | Invalid coin detected |
| 4 | `MW_START_DISPENSE` | Start dispensing |
| 5 | `MW_DISPENSE_DONE` | Dispensing complete |
| 6 | `MW_START_CHANGE` | Start change return |
| 7 | `MW_CHANGE_DONE` | Change return complete |

#### Driver Layer Events

| # | Event | Description |
|---|---|---|
| 1 | `HW_ENABLE` | Enable hardware |
| 2 | `HW_DISABLE` | Disable hardware |
| 3 | `HW_MOTOR_START` | Start motor |
| 4 | `HW_MOTOR_STOP` | Stop motor |
| 5 | `HW_ERROR` | Hardware error detected |

### 2.5 What Functions (Parts) Are Needed?

We list the required functions for each layer on paper.

#### Application Layer Functions

| # | Function | Description |
|---|---|---|
| 1 | `ShowProductList` | Display the product list |
| 2 | `HighlightProduct` | Highlight the selected product |
| 3 | `CalculateTotal` | Calculate the total price |
| 4 | `CheckSufficientFunds` | Check whether funds are sufficient |
| 5 | `RequestDispense` | Request dispensing |
| 6 | `RequestChange` | Request change return |
| 7 | `ShowError` | Display an error |
| 8 | `ResetSystem` | Reset the system |

#### Middleware Layer Functions

| # | Function | Description |
|---|---|---|
| 1 | `ValidateCoin` | Validate a coin |
| 2 | `AccumulateCoin` | Accumulate inserted coins |
| 3 | `DispenseProduct` | Dispensing control |
| 4 | `StopDispense` | Stop dispensing |
| 5 | `CalculateChange` | Calculate change |
| 6 | `DispenseChange` | Return change |

#### Driver Layer Functions

| # | Function | Description |
|---|---|---|
| 1 | `InitHardware` | Initialize hardware |
| 2 | `ReadCoinSensor` | Read the coin sensor |
| 3 | `DriveMotor` | Drive the motor |
| 4 | `StopMotor` | Stop the motor |
| 5 | `WriteLcd` | Write to the LCD |
| 6 | `ReadKeypad` | Read the keypad |

### 2.6 Completion Image (Paper Sketch)

#### Application Layer State Diagram

    [SELECT]
        |
    +----------+         +---------------+
    |   Idle   | ------> |ProductSelected|
    +----------+         +---------------+
         ^                     |
         | [RESET]             | [COIN_IN]
         |                     v
    +----------+         +---------------+
    |  Error   | <------ |AwaitingPayment|
    +----------+ [ERROR] +---------------+
         ^                     |
         |                     | [CONFIRM]
         |                     v
         |               +---------------+
         |               |  Dispensing   |
         |               +---------------+
         |                     |
         |                     | [DISPENSE_DONE]
         |                     v
         |               +---------------+
         |               |ReturningChange|
         |               +---------------+
         |                     |
         |                     | [CHANGE_DONE]
         |                     v
         +----------------- back to Idle

#### Relationship of the Three Layers (Execution Order)

    1. Driver layer (highest priority, hardware control)
           |
    2. Middleware layer (device processing)
           |
    3. Application layer (sales logic)

This order is configured in **Layer Settings** (explained in Step 7).

---
# Main - Building the Skeleton

---

## 3. Step 1: Create a Project

### 3.1 Launch StaTable

#### Action

From a terminal (or command prompt), run:

    cd StaTable/code
    python -m statable

#### Result

A **sample project** (Application tab) is displayed.

- 4 states (Idle / Active / Error / Halt)
- 5 events (START / STOP / ERROR / TIMER0_OVERFLOW / Done)
- 6 transitions
- 9 role functions

These are **not used in this tutorial**, so we will remove them in the next step.

### 3.2 Start a New Project

#### Action

1. Select menu **File > New Project...** (or **Ctrl+N**)
2. An **unsaved changes dialog** appears:

       +-------------------------------------------------+
       |  !  Unsaved Changes                             |
       |                                                 |
       |  The current project has unsaved changes.       |
       |  Do you want to save them before continuing?    |
       |                                                 |
       |       [ Save ]  [ Discard ]  [ Cancel ]         |
       +-------------------------------------------------+

   | Button | Behavior |
   |-------|------|
   | **Save** | Save the current project and continue |
   | **Discard** | Continue without saving (choose this if the sample is unwanted) |
   | **Cancel** | Abort and return to the previous screen |

   > **Note**: The sample project is loaded right after startup, so
   > `windowModified` is `True`. If you do not need the sample, choose
   > **Discard**.

3. Choose **Discard**

#### Result

| Item | Change |
|------|------|
| Tabs | Only one empty `Application` tab |
| States / Events / Transitions | All empty (0) |
| Shared library | Empty |
| Global definitions | Empty |
| Code generation settings | Default |
| Window title | `Untitled[*] - StaTable` |
| Status bar | `New project created` for 3 seconds |

**You now have a clean slate.**

### 3.3 Prepare Three Tabs (Layers)

#### 3.3.1 Tab Name = Layer Name

**In StaTable, the tab name is used as the "layer name" directly.**

| Tab name | Auto-assigned `layer_name` |
|-------|--------------------------|
| `Application` | `"Application"` |
| `Driver` | `"Driver"` |
| `Middleware` | `"Middleware"` |

#### Why It Matters

| # | Reason |
|---|---|
| 1 | **Becomes the namespace candidate for role functions** — all tab names appear in the dropdown of the role function dialog |
| 2 | **Used in generated C code file names** — e.g. `statable_transitions_Driver.c` |
| 3 | **Target of layer priority settings** — configure per-layer execution order in Layer Settings |

#### Naming Recommendations

- Short, clear names
- Examples: `Application`, `Driver`, `Middleware`
- Examples: `App`, `Drv`, `Mw` (abbreviations are fine, but keep them consistent)

#### 3.3.2 Confirm the Current Tab

The `Application` tab has already been created (auto-generated for the new project).
It has **`layer_name = "Application"`** automatically.

#### 3.3.3 Add the Driver Tab

**Action**:

1. Menu **File > New State Machine** (or the toolbar **New tab** button)
2. Enter the tab name: `Driver`
3. Click OK
4. A new tab **Driver** appears

**Auto-assigned values**:
- `layer_name`: `Driver` (from the tab name)
- `layer_priority`: `5` (default; changed later)

#### 3.3.4 Add the Middleware Tab

Similarly:

1. Menu **File > New State Machine**
2. Tab name: `Middleware`
3. OK

#### Result

    +----------+----------+----------------+
    | Driver   |Middleware| Application    |
    +----------+----------+----------------+

Three tabs are lined up.

### 3.4 Confirm What Is Empty

Switch between tabs and confirm that **everything is empty**.

#### Items to Check

| Item | Expected value |
|------|--------|
| State list tab | 0 |
| Role function tab | 0 |
| Transition matrix | Empty (0 columns, 0 rows) |
| Mermaid diagram | Only `[*]` (no initial state) |

#### How the Matrix Looks (Example: Application tab)

    (no columns, no rows)

Because no states or events are registered, the **matrix is empty**.

**Step 1 is now complete. Next, we build the skeleton.**

---
## 4. Step 2: Build the Skeleton (States + Events)

### 4.1 Why Start with States and Events

StaTable's **transition matrix is auto-generated**:

    Transition matrix
    +-- Columns = states in the State list
    +-- Rows    = events in the Event definitions

In other words, **registering states and events makes the matrix frame appear**.

#### Advantages of Building the Skeleton First

| # | Advantage |
|---|---|
| 1 | **The big picture becomes visible** - you can see which cells should have transitions |
| 2 | **Design scope becomes clear** - you know the scale of states x events |
| 3 | **Role functions can be deferred** - add them when needed |
| 4 | **Design while looking at the cells** - strong for exploratory design |

#### Work Order

For each layer (Driver / Middleware / Application), repeat:

    1. Register states    -> columns of the matrix
    2. Register events    -> rows of the matrix
    3. Look at the matrix -> confirm the big picture

### 4.2 Why Start from the Driver Layer

The order of building the three layers has a reason rooted in **the actual behavior of a vending machine**.

#### Decomposing Vending Machine Behavior

Even a single action like "dispense a product" can be decomposed by layer.

    [Application layer]
      Customer pressed "confirm purchase"
           |  "dispense the product"
    [Middleware layer]
      Decrement stock, command the dispensing mechanism
           |  "rotate the motor"
    [Driver layer]
      Rotate the motor by a specified angle, detect completion via sensor

**Higher-layer behavior is composed of lower-layer behavior.**

#### Concrete Example: "Dispense a Product"

| Layer | What it does | Role function examples |
|---|---------|--------------|
| Application | Receives purchase confirmation, requests dispense | `RequestDispense` |
| Middleware | Stock check -> dispensing control -> completion notify | `DispenseProduct` |
| Driver | Motor rotate -> sensor read -> stop | `DriveMotor`, `ReadSensor` |

**Unless the lower layer (Driver) capabilities are fixed, higher layers (Middleware / Application)
cannot be designed.**

#### Driver Layer Defines "What the Machine Can Do"

The Driver layer is the layer that defines **what the machine can physically do**.

| Layer | What it defines | Vending machine examples |
|---|-------------|----------------|
| **Driver** | Physical capability | Rotate motor, read sensor, write LCD |
| **Middleware** | Device operation | Validate coin, dispense product, calculate change |
| **Application** | Business logic | Product selection, purchase confirmation, change return |

#### Analogy

    Driver layer     = "This machine can rotate a motor, read a sensor"
                       (= a catalog of the machine's capabilities)
           | combined
    Middleware layer = "Therefore, it can validate coins, dispense products"
           | combined
    Application layer= "Therefore, it can sell products"

**In short**:
- Driver layer is close to a **hardware spec sheet** (close to physics)
- Middleware layer is a **device operation manual** (combination of capabilities)
- Application layer is a **business flow** (product behavior)

**Starting from the Driver layer = fixing the machine's capabilities first.**
Once this is fixed, higher layers can focus on "how to combine these capabilities".

#### Conversely, Starting from the Application Layer

    [Application layer] "I want to dispense a product on confirm"
           | but...
    [Middleware layer] "What exactly does 'dispense a product' mean?"
           | but...
    [Driver layer] "We have not decided how to rotate the motor yet"
           ^ this is undecided

**You would design higher layers while the implementation of "dispense" is
still undecided, leading to major rework later.**

#### Design Order for the Vending Machine and Its Rationale

| Order | Layer | What to decide | Once decided... |
|------|-----|-------------|----------|
| 1 | **Driver** | How to control motor / sensors / LCD | Middleware can call "rotate motor" |
| 2 | **Middleware** | Coin validation, dispensing, change calculation | Application can call "dispense product" |
| 3 | **Application** | Customer interaction, sales flow | The whole program is complete |

#### A Working Deliverable at Each Stage

Building from the Driver layer produces **working deliverables at each stage**.

| Stage | What can be verified |
|------|--------------|
| Driver complete | Motor rotates, LCD shows text, keys can be read |
| Middleware complete | Inserting a coin triggers validation, one product is dispensed |
| Application complete | The actual sales flow runs |

**Starting from the Application layer means no working deliverable until the very end.**

#### Team Development Advantages

When developing a vending machine with multiple people:

| Role | Phase | Content |
|------|------|------|
| Driver owner | First half | Complete hardware control |
| Middleware owner | Middle | Start once Driver is done |
| Application owner | Second half | Start once Middleware is done |

**If the Driver owner moves first, others can work in parallel without waiting.**

#### Relationship with Layer Independence

This design order is also consistent with "layer independence" described in the introduction.

- The Driver layer does not know the Application layer exists.
- The Middleware layer does not know the Application layer exists.
- The Application layer does not know the details of Driver / Middleware.

**"Build from the bottom" = "build from the side that is not depended upon"**
naturally maintains layer independence.

### 4.3 Register Driver Layer States and Events

Start from the lowest layer (Driver).

#### 4.3.1 Open the Driver Tab

**Action**: Click the **Driver** tab in the tab bar.

#### 4.3.2 Register Driver Layer States

**Feature used**: SettingsPanel > **State list** tab > **Add** button

**States to register (3)**:

| # | Name | Description | entry function | exit function | Type |
|---|------|-------------|---------------|---------------|------|
| 1 | `HwIdle` | Hardware idle | (empty) | (empty) | `normal` |
| 2 | `HwActive` | Hardware active | (empty) | (empty) | `normal` |
| 3 | `HwError` | Hardware error | (empty) | (empty) | `normal` |

**Procedure**:

1. Click the **Add** button
2. A row is added
3. Click the **Name** column and enter `HwIdle`
4. Enter `Hardware idle` in the **Description** column
5. Leave **Type** at `normal` (default)
6. Add `HwActive` and `HwError` similarly

> **Tip**: Leave entry / exit **empty at this stage**.
> In Step 5 we will add role functions as needed.

#### 4.3.3 Register Driver Layer Events

**Feature used**: SettingsPanel > **Role function** tab > **Event definitions...** button

**Events to register (5)**:

| # | Event name | Delivery type | Description |
|---|-----------|--------------|-------------|
| 1 | `HW_ENABLE` | `DIRECT` | Enable hardware |
| 2 | `HW_DISABLE` | `DIRECT` | Disable hardware |
| 3 | `HW_MOTOR_START` | `DIRECT` | Start motor |
| 4 | `HW_MOTOR_STOP` | `DIRECT` | Stop motor |
| 5 | `HW_ERROR` | `QUEUE` | Hardware error detected |

**Procedure**:

1. Click the **Event definitions...** button
2. EventDefinitionDialog opens
3. Add the 5 events above with **Add**
4. Click OK

> **How to choose Delivery type**:
> - `DIRECT`: handled directly from interrupt (responsiveness-oriented)
> - `QUEUE`: via queue (priority control possible)
> - `DOUBLE`: both
>
> Driver layer prioritizes responsiveness, so `DIRECT` is the default;
> error notifications use `QUEUE`.

#### 4.3.4 Confirm the Driver Layer Matrix

**Action**: Close the SettingsPanel (or click on the matrix)

**Result**:

              | HwIdle | HwActive | HwError
    ----------+--------+----------+---------
    HW_ENABLE |
    HW_DISABLE|
    HW_MOTOR_ |
      START   |
    HW_MOTOR_ |
      STOP    |
    HW_ERROR  |

**An empty matrix (3 columns x 5 rows)** appears. This is the skeleton.

### 4.4 Register Middleware Layer States and Events

Register Middleware layer the same way as Driver.
For detailed procedures, refer to **4.3**.

#### States to Register (4)

| # | Name | Description | Type |
|---|------|-------------|------|
| 1 | `MwIdle` | Waiting | `normal` |
| 2 | `CoinAccepting` | Accepting coins | `normal` |
| 3 | `Dispensing` | Dispensing control | `normal` |
| 4 | `ChangeCalculating` | Calculating change | `normal` |

#### Events to Register (7)

| # | Event name | Delivery type | Description |
|---|-----------|--------------|-------------|
| 1 | `MW_START_COIN` | `DIRECT` | Start accepting coins |
| 2 | `MW_COIN_VALID` | `DIRECT` | Valid coin detected |
| 3 | `MW_COIN_INVALID` | `DIRECT` | Invalid coin detected |
| 4 | `MW_START_DISPENSE` | `DIRECT` | Start dispensing |
| 5 | `MW_DISPENSE_DONE` | `DIRECT` | Dispensing complete |
| 6 | `MW_START_CHANGE` | `DIRECT` | Start change return |
| 7 | `MW_CHANGE_DONE` | `DIRECT` | Change return complete |

#### Confirm the Matrix

After registration, an empty **4 columns x 7 rows** matrix appears.

### 4.5 Register Application Layer States and Events

Register Application layer similarly.
For detailed procedures, refer to **4.3**.

#### States to Register (6)

| # | Name | Description | Type |
|---|------|-------------|------|
| 1 | `Idle` | Waiting (for customer) | `normal` |
| 2 | `ProductSelected` | Product selected | `normal` |
| 3 | `AwaitingPayment` | Awaiting payment | `normal` |
| 4 | `Dispensing` | Dispensing product | `normal` |
| 5 | `ReturningChange` | Returning change | `normal` |
| 6 | `Error` | Error state | `normal` |

#### Events to Register (8)

| # | Event name | Delivery type | Description |
|---|-----------|--------------|-------------|
| 1 | `SELECT` | `DIRECT` | Product selection button pressed |
| 2 | `COIN_IN` | `DIRECT` | Coin insertion detected |
| 3 | `CONFIRM` | `DIRECT` | Purchase confirmed |
| 4 | `DISPENSE_DONE` | `DIRECT` | Dispensing complete |
| 5 | `CHANGE_DONE` | `DIRECT` | Change return complete |
| 6 | `CANCEL` | `DIRECT` | Cancel |
| 7 | `ERROR` | `QUEUE` | Error occurred |
| 8 | `RESET` | `DIRECT` | Error reset |

#### Confirm the Matrix

After registration, an empty **6 columns x 8 rows** matrix appears.

### 4.6 Confirm All Layer Matrices

Switch between the three tabs and confirm the **skeleton is in place**.

#### Verification Table

| Layer | States | Events | Matrix |
|---|-------|-----------|-----------|
| Driver | 3 | 5 | 3 x 5 |
| Middleware | 4 | 7 | 4 x 7 |
| Application | 6 | 8 | 6 x 8 |
| **Total** | **13** | **20** | - |

#### Skeleton Completion Checklist

- [ ] Driver tab: 3 states + 5 events registered
- [ ] Middleware tab: 4 states + 7 events registered
- [ ] Application tab: 6 states + 8 events registered
- [ ] Matrix frames are visible on each tab
- [ ] Mermaid diagram shows only states on each tab

#### Things Not Done Yet

| Item | Where |
|------|---------|
| Adding transitions | Step 3 (Chapter 5) |
| Cell actions | Step 4 (Chapter 6) |
| entry / exit | Step 5 (Chapter 7) |
| Role function registration | Step 4 onwards (add as needed) |
| Layer priority settings | Step 7 (Chapter 9) |

**The skeleton is complete. Next, we fill in the matrix.**

---
# Main - Filling the Matrix

---

## 5. Step 3: Build Transitions (Starting from the Driver Layer)

### 5.1 How to Read the Matrix

Look at the **MatrixTableWidget**:

              | HwIdle | HwActive | HwError
    ----------+--------+----------+---------
    HW_ENABLE |
    HW_DISABLE|
    HW_MOTOR_ |
      START   |
    HW_MOTOR_ |
      STOP    |
    HW_ERROR  |

- **Columns** = states (auto-generated from the State list)
- **Rows** = events (auto-generated from Event definitions)
- **Cell** = what happens at that (state, event) pair (i.e. a transition)

### 5.2 Add a Transition to a Cell

#### Transitions to Add in the Driver Layer

| # | State | Event | Target | Condition | Mode |
|---|------|---------|--------|------|--------|
| 1 | HwIdle | HW_ENABLE | HwActive | (none) | Commit |
| 2 | HwActive | HW_DISABLE | HwIdle | (none) | Commit |
| 3 | HwActive | HW_ERROR | HwError | (none) | Commit |
| 4 | HwError | HW_DISABLE | HwIdle | (none) | Commit |

> **Note**: `HW_MOTOR_START` / `HW_MOTOR_STOP` **do not change the state**, so
> we do not add them as transitions. We handle them as "cell actions" (explained in Step 4).

### 5.3 Transition Modes (Commit / Tentative)

Transitions come in two modes.

| Mode | Meaning | When to use |
|-------|------|---------|
| **Commit** | Once this transition fires, do not evaluate subsequent transitions in the same cell | Normal transitions (default) |
| **Tentative** | Can be overridden by later transitions | Exceptional transitions |

**For the vending machine**:
- All transitions use **Commit**
- Only evaluate Tentative carefully when a cell has multiple transitions (not applicable here)

### 5.4 Transition Condition Expression

A transition can have a **condition expression**. The transition fires only when the condition is `true`.

| Example | Meaning |
|----|------|
| (empty) | Unconditional (always fires) |
| `current_speed >= target_speed` | Speed is at or above target |
| `coin_total >= price` | Inserted amount is at or above price |
| `retry_count < 3` | Retry count is less than 3 |

**For the Driver layer**:
- No condition expressions this time (only unconditional transitions)
- Higher layers (Application) will use condition expressions

### 5.5 Transition Labels (T1, T2, ...)

When a cell has multiple transitions, identify them by **label**.

| Label | Use |
|-------|------|
| `T1` | First transition |
| `T2` | Second transition |

**For the Driver layer**:
- One per cell, so the label is always `T1`

### 5.6 Concrete Operation Steps

#### Editing Cell (HwIdle, HW_ENABLE)

1. **Double-click** the cell at column **HwIdle** x row **HW_ENABLE**
2. **ActionEditorDialog** opens (5 tabs)
3. Select the **Transitions** tab
4. Click the **Add** button
5. Enter the following values:

   | Field | Value |
   |-----------|-----|
   | Source | `HwIdle` |
   | Event | `HW_ENABLE` |
   | Target | `HwActive` |
   | Condition | (empty) |
   | Mode | `Commit` |
   | Title | `HW enable` |
   | Label | `T1` |

6. Click OK
7. The cell now shows `HW enable (HW_ENABLE) [Commit] <T1>`

#### Add the Remaining Three Transitions Similarly

- (HwActive, HW_DISABLE) -> HwIdle
- (HwActive, HW_ERROR) -> HwError
- (HwError, HW_DISABLE) -> HwIdle

### 5.7 Confirm the Driver Layer Matrix

              | HwIdle              | HwActive             | HwError
    ----------+---------------------+----------------------+---------------------
    HW_ENABLE | HW enable [Commit]  |                      |
              | <T1>                |                      |
    HW_DISABLE|                     | HW disable [Commit]  | HW recover [Commit]
              |                     | <T1>                 | <T1>
    HW_MOTOR_ |                     | (cell action)        |
      START   |                     |                      |
    HW_MOTOR_ |                     | (cell action)        |
      STOP    |                     |                      |
    HW_ERROR  |                     | HW error [Commit]    |
              |                     | <T1>                 |

**The Driver layer transitions are complete.**

---
## 6. Step 4: Finish the Cells (First Role Function Registration)

### 6.1 What Are Cell Actions

**Cell actions** are processing that runs independently of transitions.

| Type | Execution timing |
|------|--------------|
| `before_transitions` | **Before** evaluating transitions in that cell |
| `after_transitions` | **After** evaluating transitions in that cell |

#### Difference between Transitions and Cell Actions

| Item | Transition | Cell action |
|------|------|--------------|
| Purpose | Change state | Side processing |
| Example | HwIdle to HwActive | Motor rotate, log output |
| Condition | Controllable via expression | Always executed |
| Effect | Determines next state | Side effects only |

### 6.2 Add a Cell Action

#### Cell Actions to Add in the Driver Layer

| # | Cell | Timing | Function |
|---|------|-----------|------|
| 1 | (HwActive, HW_MOTOR_START) | before | DriveMotor |
| 2 | (HwActive, HW_MOTOR_STOP) | before | StopMotor |
| 3 | (HwError, HW_ERROR) | after | WriteLcd |

### 6.3 Register Role Functions on the Spot

**Important**: When adding a cell action, if the role function is not yet
registered, add it right there.

#### Procedure

1. Double-click cell (HwActive, HW_MOTOR_START)
2. ActionEditorDialog > Pre / Post Actions tab
3. Click the Add (Pre) button
4. The role function selection dialog opens
5. Search for DriveMotor - not found
6. Click Cancel to close
7. Cancel the ActionEditorDialog too
8. SettingsPanel > Role function tab
9. Add the role function with the Add button:

   | Field | Value |
   |-----------|-----|
   | Function name | DriveMotor |
   | Namespace | Driver |
   | Display name | Drive motor |
   | Description | Rotate the motor by a specified angle |

10. OK
11. Double-click the cell again, select DriveMotor in the picker

#### Role Functions Needed in the Driver Layer (5)

| # | Function name | Namespace | Display name |
|---|--------------|-----------|--------------|
| 1 | InitHardware | Driver | Initialize hardware |
| 2 | DriveMotor | Driver | Drive motor |
| 3 | StopMotor | Driver | Stop motor |
| 4 | WriteLcd | Driver | Write LCD |
| 5 | ReadKeypad | Driver | Read keypad |

#### Role of Namespace

Role functions have a Namespace. This indicates which layer the part belongs to.

| Setting | Effect |
|------|------|
| Namespace = Driver | Treated as Driver.DriveMotor |
| Namespace = (empty) | Treated as DriveMotor |

### 6.4 Add Cell Relations

| Type | Meaning |
|------|------|
| sequential | Evaluate in order (default) |
| exclusive | At most one fires |
| group | Grouped, shared condition factored out |

For the Driver layer: one per cell, so no relation is needed.

---

## 7. Step 5: Finish the States

### 7.1 entry / exit Actions

| Action | Timing |
|-----------|-----------|
| entry | When the state is entered |
| exit | When the state is exited |

### 7.2 Set entry / exit

#### Driver Layer entry / exit

| # | State | entry | exit |
|---|------|-------|------|
| 1 | HwIdle | InitHardware | (none) |
| 2 | HwActive | (none) | StopMotor |
| 3 | HwError | WriteLcd | (none) |

#### Procedure

1. SettingsPanel > State list tab
2. Double-click the entry function column of the HwIdle row
3. ActionEditDialog opens
4. Select InitHardware
5. OK

### 7.3 Driver Layer Completion Checklist

- [ ] States 3 (HwIdle / HwActive / HwError)
- [ ] Events 5 (HW_ENABLE / HW_DISABLE / HW_MOTOR_START / HW_MOTOR_STOP / HW_ERROR)
- [ ] Transitions 4
- [ ] Cell actions 3
- [ ] entry / exit 3
- [ ] Role functions 5

---

## 8. Step 6: Complete the Other Layers Similarly

### 8.1 Middleware Layer Transitions

| # | State | Event | Target | Condition | Mode |
|---|------|---------|--------|------|--------|
| 1 | MwIdle | MW_START_COIN | CoinAccepting | (none) | Commit |
| 2 | CoinAccepting | MW_COIN_VALID | MwIdle | (none) | Commit |
| 3 | CoinAccepting | MW_COIN_INVALID | MwIdle | (none) | Commit |
| 4 | MwIdle | MW_START_DISPENSE | Dispensing | (none) | Commit |
| 5 | Dispensing | MW_DISPENSE_DONE | MwIdle | (none) | Commit |
| 6 | MwIdle | MW_START_CHANGE | ChangeCalculating | (none) | Commit |
| 7 | ChangeCalculating | MW_CHANGE_DONE | MwIdle | (none) | Commit |

#### Cell Actions

| # | Cell | Timing | Function |
|---|------|-----------|------|
| 1 | (CoinAccepting, MW_COIN_VALID) | before | AccumulateCoin |
| 2 | (Dispensing, MW_DISPENSE_DONE) | before | StopDispense |
| 3 | (ChangeCalculating, MW_CHANGE_DONE) | before | DispenseChange |

#### entry / exit

| # | State | entry | exit |
|---|------|-------|------|
| 1 | CoinAccepting | ValidateCoin | (none) |
| 2 | Dispensing | DispenseProduct | (none) |
| 3 | ChangeCalculating | CalculateChange | (none) |

#### Middleware Layer Role Functions (6)

| # | Function name | Namespace |
|---|--------------|-----------|
| 1 | ValidateCoin | Middleware |
| 2 | AccumulateCoin | Middleware |
| 3 | DispenseProduct | Middleware |
| 4 | StopDispense | Middleware |
| 5 | CalculateChange | Middleware |
| 6 | DispenseChange | Middleware |

### 8.2 Application Layer Transitions

| # | State | Event | Target | Condition | Mode |
|---|------|---------|--------|------|--------|
| 1 | Idle | SELECT | ProductSelected | (none) | Commit |
| 2 | ProductSelected | COIN_IN | AwaitingPayment | (none) | Commit |
| 3 | AwaitingPayment | CONFIRM | Dispensing | (none) | Commit |
| 4 | Dispensing | DISPENSE_DONE | ReturningChange | change_amount > 0 | Commit |
| 5 | Dispensing | DISPENSE_DONE | Idle | change_amount == 0 | Commit |
| 6 | ReturningChange | CHANGE_DONE | Idle | (none) | Commit |
| 7 | (any state) | ERROR | Error | (none) | Commit |
| 8 | Error | RESET | Idle | (none) | Commit |

### 8.3 Cell Relations (Application Layer)

The (Dispensing, DISPENSE_DONE) cell has two transitions:
- T1: ReturningChange (condition: change_amount > 0)
- T2: Idle (condition: change_amount == 0)

Because they are mutually exclusive, use `exclusive`.

| Cell | Relation |
|------|---------|
| (Dispensing, DISPENSE_DONE) | exclusive |

### 8.4 Application Layer Role Functions (8)

| # | Function name | Namespace |
|---|--------------|-----------|
| 1 | ShowProductList | Application |
| 2 | HighlightProduct | Application |
| 3 | CalculateTotal | Application |
| 4 | CheckSufficientFunds | Application |
| 5 | RequestDispense | Application |
| 6 | RequestChange | Application |
| 7 | ShowError | Application |
| 8 | ResetSystem | Application |

### 8.5 Cell Actions and entry / exit (Application Layer)

#### Cell Actions

| # | Cell | Timing | Function |
|---|------|-----------|------|
| 1 | (Idle, SELECT) | before | ShowProductList |
| 2 | (ProductSelected, COIN_IN) | after | HighlightProduct |
| 3 | (AwaitingPayment, CONFIRM) | before | CheckSufficientFunds |
| 4 | (Error, RESET) | before | ResetSystem |

#### entry / exit

| # | State | entry | exit |
|---|------|-------|------|
| 1 | ProductSelected | HighlightProduct | (none) |
| 2 | Dispensing | RequestDispense | (none) |
| 3 | ReturningChange | RequestChange | (none) |
| 4 | Error | ShowError | (none) |

### 8.6 All Three Layers Complete

| Layer | States | Events | Transitions | Cell actions | entry/exit | Role funcs |
|---|-----|---------|------|--------------|-----------|----------|
| Driver | 3 | 5 | 4 | 3 | 3 | 5 |
| Middleware | 4 | 7 | 7 | 3 | 3 | 6 |
| Application | 6 | 8 | 8 | 4 | 4 | 8 |
| **Total** | **13** | **20** | **19** | **10** | **10** | **19** |

**All three layers are assembled.**

---

## 9. Step 7: Verify with Diagrams

### 9.1 How to Read the Mermaid Diagram

StaTable displays state transition diagrams in a **horizontal layout**
(left to right).

    +------+   START    +------+   TIMER   +------+
    | Idle | ---------> |Blink | --------> |Off   |
    +------+            +------+           +------+

#### Why Horizontal

| # | Reason |
|---|------|
| 1 | **Intuitive flow** - time goes left to right |
| 2 | **Uses screen width** - monitors are wide |
| 3 | **Easy to compare states** - same row |
| 4 | **Matches matrix** - same order as columns |

### 9.2 Verify Each Layer's Diagram

Switch between the three tabs and check that they **match the paper sketch**.

#### Verification Items

| # | Item |
|---|---------|
| 1 | All states are reachable |
| 2 | No terminal states (that cannot be exited) |
| 3 | All intended transitions are drawn |
| 4 | Conditions are displayed correctly |

### 9.3 Set Layer Priority

Configure the execution order of layers at runtime.

#### Procedure

1. Menu **Edit > Layer Settings...**
2. LayerSettingsDialog opens
3. Set each layer priority:

   | Layer | Priority | Meaning |
   |---|-------|------|
   | Driver | 1 | Highest (hardware control) |
   | Middleware | 5 | Middle |
   | Application | 9 | Lowest (sales logic) |

   > **Priority meaning**: smaller numbers run first (1-9)

4. OK

#### Execution Order

    1. Driver layer state machine
           |
    2. Middleware layer state machine
           |
    3. Application layer state machine

### 9.4 Fixing Problems

| Problem | Cause | Fix |
|------|------|------|
| No transition in diagram | Cell is empty | Double-click the cell and add a transition |
| Isolated state | Transition undefined | Add a transition to that state |
| Condition not shown | Empty condition | Enter a condition in the transition editor |
| Duplicate labels | Same label used multiple times | Renumber with T1, T2, ... |

---
# Main - Completing

---

## 10. Step 8: Generate C Code

### 10.1 Configure the Output Location

1. Menu **Code generation > Generation settings...** (**Ctrl+Shift+G**)
2. CodeGenerationSettingsDialog opens
3. **Output settings** tab
4. Configure:

   | Field | Value |
   |------|-----|
   | Output directory | (e.g. C:\projects\vending_machine\output) |
   | Folder structure | by_layer (recommended) |
   | Save with merge | check |

5. OK

### 10.2 Generate

1. Menu **Code generation > Code generation...** (**Ctrl+G**)
2. CodeGenerationDialog opens
3. Click the **Generate** button
4. Confirm the completion message

### 10.3 Verify Generated Files

#### by_layer Structure

    output/
    +-- Driver/
    |   +-- statable_types_Driver.h
    |   +-- statable_transitions_Driver.c / .h
    |   +-- statable_role_functions_Driver.c / .h
    +-- Middleware/
    |   +-- (same 5 files)
    +-- Application/
    |   +-- (same 5 files)
    +-- include/
    |   +-- statable_types_common.h
    +-- src/
    |   +-- statable_init.c
    |   +-- statable_event_queue.c
    |   +-- statable_interrupt.c
    |   +-- statable_timer.c
    |   +-- Untitled_run.c
    +-- common/
        +-- osal.h / osal.c
        +-- statable_all.h

> **Note**: 15 layer-specific files + 10 common files = **25 files total**.

### 10.4 Cell Function Example

From statable_transitions_Driver.c:

    static STATE_Driver_t t_HwIdle_HW_ENABLE(
        const Transition_t* transition,
        TransitionContext_Driver_t* ctx)
    {
        STATE_Driver_t next_state = STATE_Driver_HwIdle;
        if (1) {
            next_state = STATE_Driver_HwActive;  /* [Commit] */
        }
        return next_state;
    }

### 10.5 User Code Area in Role Functions

From statable_role_functions_Driver.c:

    int RoleFunc_Driver_DriveMotor(
        const TransitionContext_Driver_t *transition,
        SystemContext_t *ctx)
    {
        (void)ctx;
        /* [[STABLE_USER_CODE_START:Driver_DriveMotor]] */
        /* Write user implementation code here */
        /* [[STABLE_USER_CODE_END:Driver_DriveMotor]] */
        return 0;
    }

> **Important**: Write user code between the STABLE_USER_CODE markers.
> Do not delete or rename the markers - user code will be lost on regeneration.

---

## 11. Step 9: Integrate into Embedded

### 11.1 Overview

    1. Call SystemContext_Init in main.c
    2. In the main loop, process each layer in priority order
    3. Write user code inside the markers of role functions

### 11.2 Minimal main.c

    #include "statable_all.h"
    #include "board.h"

    int main(void)
    {
        SystemContext_t ctx;
        board_init();
        SystemContext_Init(&ctx);
        __enable_irq();
        while (1) {
            EVENT_Driver_t drv_ev =
                StateMachine_GetNextEvent_Driver(&ctx);
            if (drv_ev != EVENT_Driver_NONE) {
                (void)StateMachine_Process_Driver(drv_ev, &ctx);
            }
            EVENT_Middleware_t mw_ev =
                StateMachine_GetNextEvent_Middleware(&ctx);
            if (mw_ev != EVENT_Middleware_NONE) {
                (void)StateMachine_Process_Middleware(mw_ev, &ctx);
            }
            EVENT_Application_t app_ev =
                StateMachine_GetNextEvent_Application(&ctx);
            if (app_ev != EVENT_Application_NONE) {
                (void)StateMachine_Process_Application(app_ev, &ctx);
            }
            board_background_task();
        }
    }

### 11.3 ISR and Timer Configuration Overview

#### Coin ISR Example

    void COIN_IRQHandler(void)
    {
        COIN_SENSOR->SR = 0;
        StateMachine_EnqueueEvent(
            &g_system_ctx,
            EVENT_Application_COIN_IN
        );
    }

#### Timer ISR Example

    void SysTick_Handler(void)
    {
        g_system_tick++;
        if ((g_system_tick % 1000) == 0) {
            StateMachine_EnqueueEvent(
                &g_system_ctx,
                EVENT_Application_TIMEOUT
            );
        }
    }

### 11.4 User Code Implementation in Role Functions

    int RoleFunc_Driver_DriveMotor(
        const TransitionContext_Driver_t *transition,
        SystemContext_t *ctx)
    {
        (void)ctx;
        /* [[STABLE_USER_CODE_START:Driver_DriveMotor]] */
        Motor_SetDirection(MOTOR_FORWARD);
        Motor_SetSpeed(200);
        Motor_Start();
        /* [[STABLE_USER_CODE_END:Driver_DriveMotor]] */
        return 0;
    }

### 11.5 See INTEGRATION_GUIDE_ja.md for Details

For integration details (NonRTOS / FreeRTOS / ISR configuration),
see INTEGRATION_GUIDE_ja.md.

---

## 12. Step 10: Save the Project

### 12.1 Save

1. Menu **File > Save Project...**
2. Choose a destination (e.g. VendingMachine.xml)
3. Save

### 12.2 What Is Saved

| Item | Content |
|---------|------|
| State machines | States / events / transitions / role functions |
| Global definitions | Variables / flags / interrupts / timers |
| Shared library | Role functions / conditions / literals |
| Project settings | Code generation settings |

### 12.3 User Code Handling

**Important**: User code (inside markers) is saved in **C files, not in the XML**.

    VendingMachine.xml        <- design info (read/write by StaTable)
    output/                   <- generated C code (including user code)
      +-- Driver/
          +-- statable_role_functions_Driver.c  <- user code

The XML contains only design info. User code remains in the C files.

---

# Advanced

---

## 13. Reusing Existing Projects

### 13.1 Reuse Scenario

**Scenario**: After developing a drink vending machine,
**reuse the same Driver / Middleware for a coffee machine**.

#### Product Differences

| Item | Drink machine (existing) | Coffee machine (new) |
|------|-----------------|---------------------|
| Product | Cans | Coffee (cup) |
| Selection | Buttons (per product) | Buttons (type) |
| Delivery | Product chute | Cup + brewing mechanism |
| Extra features | None | Hot water, milk, sugar |
| Application layer | Drink sales logic | Coffee brewing logic |

### 13.2 What Can / Cannot Be Reused

| Layer | Reuse | Reason |
|---|---------|------|
| Driver layer | Fully reusable | Motor, coin, LCD are the same |
| Middleware layer | Fully reusable | Dispensing, change calculation are the same |
| Application layer | New | Coffee brewing logic differs |

#### Time Savings

| Layer | New dev | Reuse |
|---|---------|------|
| Driver | 0% | 100% |
| Middleware | 0% | 100% |
| Application | 100% | 0% |
| **Total** | **33%** | **67%** |

**This is the biggest advantage of reuse design - you save 2/3 of development.**

### 13.3 Open the Existing Project

1. Menu **File > Open Project...**
2. Select VendingMachine.xml
3. Loaded

**Result**: All three layers are restored.

### 13.4 Replace Only the Application Layer

1. Select the **Application** tab
2. Edit states / events / transitions
3. Edit role functions of the Application layer only
4. **Do not touch** the Driver / Middleware tabs

---

## 14. Iterative Development

### 14.1 Design Change to Regeneration

    1. Change the design (add features / fix transitions)
           |
    2. Regenerate (Save Generated Code)
           |
    3. code_merger.py auto-merges
           |
    4. User code is preserved

### 14.2 User Code Protection (Merge)

    /* [[STABLE_USER_CODE_START:Driver_DriveMotor]] */
    Motor_SetSpeed(200);   <- user implementation
    /* [[STABLE_USER_CODE_END:Driver_DriveMotor]] */

Content between markers is **preserved** on regeneration.

#### Marker Types

| Marker | Purpose |
|---------|------|
| STABLE_USER_CODE_START / END | File-level |
| STABLE_USER_CODE_START:<name> / END:<name> | Function-level |
| STABLE_USER_CODE_TAIL_START / END | File tail |

### 14.3 Idempotency Guarantee

**Regenerating multiple times with the same design does not increase file size.**

Verified: tests/test_v2_4_p1_merge.py Test [3]

### 14.4 Validation and AI Diagnosis

1. Menu **Validate > Validation / AI diagnosis...** (**Ctrl+Shift+V**)
2. ValidationDialog opens
3. Click **Validate** to run

#### Rules Checked (35 total)

| Category | Rules |
|---------|---------|
| state | 4 |
| event | 2 |
| transition | 5 |
| role_function | 3 |
| variable | 3 |
| flag | 2 |
| queue | 2 |
| interrupt | 2 |
| timer | 2 |
| custom_type | 2 |
| cell | 8 |
| **Total** | **35** |

---
# Summary

---

## 15. Task x Feature Cross-Reference

### 15.1 Step List

| # | Step | Chapter |
|---|------|-----|
| 1 | Create a project | 3 |
| 2 | Build the skeleton (states + events) | 4 |
| 3 | Build transitions | 5 |
| 4 | Finish the cells | 6 |
| 5 | Finish the states | 7 |
| 6 | Complete the other layers | 8 |
| 7 | Verify with diagrams | 9 |
| 8 | Generate C code | 10 |
| 9 | Integrate into embedded | 11 |
| 10 | Save the project | 12 |

### 15.2 Feature List

| Task | Feature |
|------|---------|
| Create new project | File > New Project |
| Open project | File > Open Project |
| Save project | File > Save Project |
| Add new layer (tab) | File > New State Machine |
| Define state | SettingsPanel > State list |
| Define event | SettingsPanel > Event definitions |
| Define role function | SettingsPanel > Role function |
| Define variables | Edit > Global Definitions |
| Add transition | MatrixTable > double-click a cell |
| Add cell action | ActionEditorDialog > Pre/Post Actions |
| Add cell relation | ActionEditorDialog > Relations |
| Set entry / exit | State list > double-click a cell |
| Verify with diagram | MermaidWidget (auto-updated) |
| Generate C code | Code generation > Generate |
| Set layer priority | Edit > Layer Settings |
| Validate | Validate > Validation |

### 15.3 Shortcut List

| Shortcut | Feature |
|--------------|------|
| Ctrl+N | New Project |
| Ctrl+G | Code generation |
| Ctrl+Shift+G | Generation settings |
| Ctrl+Shift+S | Save generated code |
| Ctrl+Shift+V | Validation / AI diagnosis |

---

## 16. FAQ

**Q1. Why register all states and events first?**
A. Registering states and events auto-generates the matrix frame.
You can work while looking at the design diagram, which supports
exploratory design.

**Q2. Why start from the Driver layer?**
A. Because it matches the direction of dependencies. The Driver layer does
not know the Application layer exists, so building from the bottom
reduces rework. The Driver layer defines "what the machine can do",
and once this is fixed, higher layers proceed smoothly.

**Q3. When do I register role functions?**
A. Register them when needed. You do not have to create all up front.

**Q4. Can I have multiple state machines in one project?**
A. Yes. Each tab can have an independent StateMachine.

**Q5. Should role functions be shared across layers?**
A. Not recommended. To maintain layer independence, define functions
per layer.

**Q6. Why is the diagram horizontal?**
A. To express time left-to-right and use the wide monitor. The order
matches the matrix columns (states), making the correspondence easy
to see.

---

## 17. Next Steps

### 17.1 Learning Path

    This tutorial (completed)
           |
    INTEGRATION_GUIDE_ja.md (embedded integration)
           |
    SPEC_OVERVIEW_ja.md (detailed specification)

### 17.2 Reference Documents

| # | Purpose | Document |
|---|------|-----------------|
| 1 | Integrate generated code into embedded | INTEGRATION_GUIDE_ja.md |
| 2 | Validation rule details | SPEC_OVERVIEW_ja.md section 7.5 |
| 3 | MISRA compliance | SPEC_OVERVIEW_ja.md section 7.4 |
| 4 | GUI screen details | SPEC_SCREENS_ja.md |
| 5 | SDK usage | SPEC_SDK_API_en.md |
| 6 | User code guide | USER_CODE_GUIDE_en.md (this repository) |

---

# Appendix

---

## A. Marker Reference

| Marker | Purpose |
|---------|------|
| STABLE_USER_CODE_START / END | File-level user code area |
| STABLE_USER_CODE_START:<name> / END:<name> | Function-level user code area |
| STABLE_USER_CODE_TAIL_START / END | File tail user code area |

---

## B. Terminology Mapping

| StaTable term | General term | In this tutorial |
|--------------|-------------|----------------------|
| Role function | Function / method | Part (capability) |
| State | State | State |
| Event | Event / signal | Trigger |
| Transition | Transition | Transition |
| Layer | Layer | Layer |
| Namespace | Namespace | Namespace |
| Cell | Cell | Cell |

---

## C. Glossary

### C.1 Basic Terms

| Term | Description | Chapter |
|------|------|-------|
| Layer | State machine groups per tab | 2.2 |
| State | Mode of operation | 2.3 |
| Event | A trigger that changes state | 2.4 |
| Transition | "When event X arrives in state A, go to state B" | 5.2 |
| Cell | A (state, event) pair | 5.1 |

### C.2 Role Function Related

| Term | Description | Chapter |
|------|------|-------|
| Role function | Function used for condition evaluation and actions (a part) | 1.4 |
| namespace | The layer a role function belongs to | 6.3 |
| qualified_name | namespace.name form | 6.3 |
| Part | This tutorial's term for a role function | 1.4 |

### C.3 Transition Related

| Term | Description | Chapter |
|------|------|-------|
| Commit | early_return=True (stops subsequent transitions) | 5.3 |
| Tentative | early_return=False (can be overridden) | 5.3 |
| Condition expression | Condition for a transition to fire | 5.4 |
| Label (T1, T2, ...) | Identifier for transitions within a cell | 5.5 |

### C.4 Cell Related

| Term | Description | Chapter |
|------|------|-------|
| Cell action | Side processing independent of transitions | 6.1 |
| before_transitions | Before transition evaluation | 6.1 |
| after_transitions | After transition evaluation | 6.1 |
| Cell relation | Relationship between transitions in a cell | 6.4 |
| sequential | Evaluate in order | 6.4 |
| exclusive | At most one fires | 6.4 |
| group | Grouped, shared condition factored out | 6.4 |

### C.5 State Actions

| Term | Description | Chapter |
|------|------|-------|
| entry | Action when entering a state | 7.1 |
| exit | Action when exiting a state | 7.1 |

### C.6 Code Generation Related

| Term | Description | Chapter |
|------|------|-------|
| Marker | Comment for preserving user code | 10.5 |
| Merge | Integration of generated code and existing code | 14.2 |
| Idempotency | Same result no matter how many times executed | 14.3 |
| Cell function | static function that processes one cell | 10.4 |

### C.7 Drawing Related

| Term | Description | Chapter |
|------|------|-------|
| Mermaid | State diagram generation engine | 9.1 |
| Horizontal (LR) | Left-to-right state diagram | 9.1 |

### C.8 Standards Related

| Term | Description | Chapter |
|------|------|-------|
| MISRA C:2012 | Automotive C language standard | 14.4 |
| cppcheck | Static analysis tool | 14.4 |

### C.9 Other

| Term | Description | Chapter |
|------|------|-------|
| Tab | UI element representing a layer | 3.3 |
| Matrix | Transition matrix (state x event) | 4.1 |
| SettingsPanel | Right-side settings panel | 3.3 |
| MermaidWidget | Bottom diagram widget | 9.1 |
| ISR | Interrupt Service Routine | 11.3 |
| OSAL | OS Abstraction Layer | 10.4 |

---

## D. Changelog

| Version | Date | Content |
|-----------|------|------|
| 2.0 | 2026-10-04 | English complete edition. Structured as skeleton to matrix to completion |
| 1.2 | 2026-09-26 | XML reference version |

---

End of TUTORIAL_en.md v2.0