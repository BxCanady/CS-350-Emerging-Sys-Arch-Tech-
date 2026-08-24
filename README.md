# CS-350-Emerging-Sys-Arch-Tech-
Emerging Systems Architecture &amp; Technology. Includes labs, code samples for smart thermostat

# Smart Thermostat System

## Project Summary

The Smart Thermostat project was designed to simulate the core functions of a thermostat using a Raspberry Pi and connected hardware components. The system uses an AHT20 temperature sensor to monitor the room temperature, buttons to control the thermostat mode and adjust the setpoint, LEDs to indicate heating and cooling activity, and a 16x2 LCD to display system information.

The main problem the project addressed was creating an embedded system that could monitor temperature, respond to user input, and provide clear feedback through physical hardware. The project also required the software to manage different operating states, including **off, heat, and cool**, while keeping the hardware outputs synchronized with those states.

## What Did I Do Particularly Well?

I did particularly well with troubleshooting and integrating the different hardware components with the software. One of the biggest challenges was getting the AHT20 sensor, GPIO buttons, LEDs, LCD, and state machine to work together reliably.

I also improved the system by identifying issues with I2C communication and GPIO resource management. For example, I added synchronization around sensor access to prevent multiple processes from accessing the I2C bus at the same time. I also added cleanup functionality to release GPIO resources when the program exits.

Another area I did well was connecting the state-machine logic directly to the thermostat requirements. The red LED indicates heating, the blue LED indicates cooling, and the LEDs change between pulsing and solid states depending on whether the thermostat has reached its setpoint.

## Where Could I Improve?

One area I could improve is the initial system design and planning. Some of the troubleshooting could have been reduced by identifying concurrency, resource cleanup, and hardware-state requirements earlier in the development process.

I could also improve the organization of the code by separating hardware interfaces, state-machine logic, display management, and error handling into more modular components. This would make the project easier to expand and test in the future.

## What Tools and/or Resources Am I Adding to My Support Network?

This project expanded my use of Raspberry Pi documentation, Python documentation, `gpiozero`, Adafruit libraries, Linux command-line tools, and hardware datasheets. I also became more comfortable using terminal output and error messages as debugging resources instead of treating them simply as failures.

Documentation and technical references are especially important because I may not always remember every specific function, register, or hardware configuration. Understanding the underlying logic and knowing how to find the correct technical information is an important part of my development process.

## What Skills From This Project Will Be Transferable?

Several skills from this project can transfer directly to future software and embedded systems projects. These include:

* Python programming
* GPIO hardware control
* I2C communication
* PWM
* State-machine design
* Event-driven programming
* Multithreading and synchronization
* Hardware and software troubleshooting
* Error handling
* Linux command-line tools
* Reading technical documentation
* Integrating hardware components with software

One of the most transferable skills is troubleshooting. I learned that I do not necessarily need to know every technical detail immediately. If I understand the system's logic, I can break the problem down, research the missing information, test possible solutions, and determine the cause.

## How Did I Make the Project Maintainable, Readable, and Adaptable?

I focused on organizing the thermostat around clearly defined states and functions so that individual parts of the system could be changed without completely rewriting the application. Functions were used for tasks such as reading temperature, managing the display, processing button input, and controlling the LEDs.

I also used meaningful variable and function names and added comments to explain important sections of the code. Error handling was added around hardware communication so that temporary sensor failures would not immediately terminate the application.

The state-machine design also makes the project adaptable. Additional thermostat modes, sensors, displays, or cloud connectivity could be added without completely changing the basic architecture. This makes the project a useful foundation for future embedded or IoT applications.

