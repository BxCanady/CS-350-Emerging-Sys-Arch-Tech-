# State Machine Implementation

## Overview
This directory contains the state machine implementation for **CS-350: Emerging System Architectures & Technologies**. The project demonstrates deterministic finite state machine (FSM) logic applied to embedded architecture and real-time control system concepts.

## Objectives
- Design and implement state transitions, inputs, and output logic.
- Model hardware/system state behaviors in response to asynchronous triggers or sensor polling.
- Ensure deterministic performance, proper reset conditions, and handling of edge cases/invalid states.

## Architecture & States
- **Initial State:** System reset and initialization setup.
- **Active States:** Functional operational modes and state transition handling based on input conditions.
- **Error / Fault Handling:** Fallback states for unexpected input sequences or error events.

## Getting Started
1. **Compilation:** Compile the source code using your target environment or cross-compiler toolchain.
2. **Execution:** Flash or execute the binary on the target board/emulator.
3. **Testing:** Observe state transitions via debugging output, console logs, or connected hardware indicators.
