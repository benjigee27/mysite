**Magic 8 Ball in OpenGL**

A simple retro-futuristic 3D simulation inspired by DJO’s *DECIDE* album and vintage 8-ball toys, to explore using OpenGL and lighting \- I was experimenting with Tkinter in Python and wanted to expand to using basic 3D graphics.

**Technical Overview**

This project is a real-time 3D interactive simulation built from the ground up using Python and PyOpenGL. It explores the intersection of low-level graphics pipelines, asynchronous input handling, and mathematical physics. 

**Key Engineering Features**

**Multithreaded I/O**   
Utilised the threading library to offload Speech Recognition (Google Web API) to a background thread. This ensures the main OpenGL rendering loop remains at a consistent 60FPS, avoiding “frame-drops” during network-dependent transcription. 

**Mixed-Mode Rendering**  
Orchestrated a hybrid graphics pipeline that switches between a Perspective Projection (for 3D depth in the starfield and sphere) and an Orthographic Projection (for the 2D HUD)

**Mathematical Animations**  
Implemented a Damped Harmonic Oscillator model for the 8 ball’s ‘shake’ effect: 

**x*(t)* \= Asin(ω*t)e-yt***

Where **A** is amplitude, **ω** is frequency and ***y*** is the decay constant.

**Dynamic Particle Systems**  
Engineered custom particle emitters for “impact” and “voice sparks,” using simple Euler integration for velocity and alpha-decay. 

**Aesthetic Inspiration**

Drawing from the synth-wave visuals of the album *DECIDE,* the project utilises a high-contrast neon-cyan palette (0, 255, 255\) set against a ‘Deep Space’ background.   
The ‘reveal’ state uses alpha-blending and glassmorphism techniques to mimic the iconic floating triangle. 

**Installation & Execution**

1. Ensure you have Python 3.14 installed.  
2. Install dependencies: pip install pygame PyOpenGL PyOpenGL\_accelerate SpeechRecognition .  
3. Run the script: python magic8ball.py  
4. Controls: Press ‘**V**’ to speak your question or **Enter** to type it.

**Credits:**   
**Application designed and created by me, Benjamin Gee, 2026\.**   
**Inspired by DJO (Joe Keery) DECIDE album circa 2022\.**  
