import spiceypy as spice
import datetime
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from mpl_toolkits.mplot3d import Axes3D
import tkinter as tk
from tkinter import Button, Label, Toplevel, Message, Entry

# Load SPICE kernels (only once when starting the program)
spice.furnsh("C:/Users/vismay suman/Desktop/Programming/Space/Earth/naif0012.tls")
spice.furnsh("C:/Users/vismay suman/Desktop/Programming/Space/Earth/de430.bsp")
spice.furnsh("C:/Users/vismay suman/Desktop/Programming/Space/Earth/moon_pa_de421_1900-2050.bpc")

# Function to calculate the next eclipses
def calculate_next_eclipse(start_date, end_date):
    solar_eclipse = None
    lunar_eclipse = None
    step = 3600  # 1-hour step
    start_et = spice.str2et(start_date)
    end_et = spice.str2et(end_date)

    for et in np.arange(start_et, end_et, step):
        # Compute vectors relative to Earth
        earth_to_sun, _ = spice.spkgeo(targ=10, et=et, ref="J2000", obs=399)  # Sun relative to Earth
        earth_to_moon, _ = spice.spkgeo(targ=301, et=et, ref="J2000", obs=399)  # Moon relative to Earth
        sun_position = earth_to_sun[:3]
        moon_position = earth_to_moon[:3]
        
        # Compute distance and angles
        dist_earth_sun = spice.vnorm(sun_position)
        dist_earth_moon = spice.vnorm(moon_position)
        angle = spice.vsep(sun_position, moon_position)
        angle_deg = np.degrees(angle)

        # Shadow cone calculations (Earth radius ~6378 km, Sun radius ~695700 km)
        earth_umbra_angle = np.arcsin(6378.1 / dist_earth_sun)
        moon_shadow_angle = np.arcsin(1737.4 / dist_earth_moon)  # Moon radius ~1737.4 km

        # Solar Eclipse: Moon in line with Sun and Earth
        if angle_deg < np.degrees(earth_umbra_angle):  # Moon within Earth's umbral cone
            solar_eclipse = spice.etcal(et)

        # Lunar Eclipse: Moon within Earth's shadow
        earth_shadow_angle = np.arcsin(6378.1 / dist_earth_moon)
        if 180 - angle_deg < np.degrees(earth_shadow_angle):  # Moon in Earth's umbra
            lunar_eclipse = spice.etcal(et)

        if solar_eclipse and lunar_eclipse:
            break

    return solar_eclipse, lunar_eclipse


# Function to update the simulation plot
def start_simulation_plot(start_date, end_date):
    # Predict the next eclipses
    solar_eclipse, lunar_eclipse = calculate_next_eclipse(start_date, end_date)

    # Initialize plot
    fig = plt.figure(figsize=(10, 10))
    fig.patch.set_facecolor("black")  # Set the background color of the figure to black
    ax = fig.add_subplot(111, projection='3d')
    ax.set_facecolor("black")
    ax.set_xlim(-1.5e8, 1.5e8)
    ax.set_ylim(-1.5e8, 1.5e8)
    ax.set_zlim(-1.5e8, 1.5e8)
    ax.set_xlabel("X (km)", color="white")
    ax.set_ylabel("Y (km)", color="white")
    ax.set_zlabel("Z (km)", color="white")
    ax.set_title("Earth and Moon Trajectories with Sun at Origin", color="white")
    ax.grid(True, color="white")  # Enable gridlines with white color

    # Text area for real-time information
    info_text = plt.gcf().text(0.02, 0.02, "", fontsize=10, color="white", va='bottom', ha='left')

    # Precompute trajectories
    earth_trajectory = []
    moon_trajectory = []

    start_date_obj = datetime.datetime.strptime(start_date, '%Y-%m-%d')
    end_date_obj = datetime.datetime.strptime(end_date, '%Y-%m-%d')
    time_points = [start_date_obj + datetime.timedelta(hours=i) for i in range((end_date_obj - start_date_obj).days * 24)]

    for time_point in time_points:
        et = spice.str2et(time_point.strftime('%Y-%m-%dT%H:%M:%S'))
        earth_state, _ = spice.spkgeo(targ=399, et=et, ref="J2000", obs=10)  # Earth relative to Sun
        moon_state, _ = spice.spkgeo(targ=301, et=et, ref="J2000", obs=399)  # Moon relative to Earth
        earth_trajectory.append(earth_state[:3])
        moon_trajectory.append(np.add(earth_state[:3], moon_state[:3]))  # Moon relative to Sun

    earth_trajectory = np.array(earth_trajectory)
    moon_trajectory = np.array(moon_trajectory)

    # Plot precomputed trajectories with thicker lines
    earth_line, = ax.plot(earth_trajectory[:, 0], earth_trajectory[:, 1], earth_trajectory[:, 2], color='blue', linewidth=2, label="Earth Trajectory")
    moon_line, = ax.plot(moon_trajectory[:, 0], moon_trajectory[:, 1], moon_trajectory[:, 2], color='gray', linewidth=2, label="Moon Trajectory")
    earth_dot, = ax.plot([], [], [], 'bo', label="Earth (Now)", markersize=8)
    moon_dot, = ax.plot([], [], [], 'wo', label="Moon (Now)", markersize=4)
    sun_dot, = ax.plot([0], [0], [0], 'yo', markersize=20, label="Sun")
    ax.legend()

    # Animation update function
    def update(frame):
        now = datetime.datetime.now(datetime.timezone.utc)
        et = spice.str2et(now.strftime('%Y-%m-%dT%H:%M:%S'))
        earth_state, _ = spice.spkgeo(targ=399, et=et, ref="J2000", obs=10)
        moon_state, _ = spice.spkgeo(targ=301, et=et, ref="J2000", obs=399)

        current_earth_position = earth_state[:3]
        current_moon_position = np.add(earth_state[:3], moon_state[:3])
        current_earth_velocity = earth_state[3:]
        current_moon_velocity = moon_state[3:]

        # Update real-time position dots
        earth_dot.set_data([current_earth_position[0]], [current_earth_position[1]])
        earth_dot.set_3d_properties([current_earth_position[2]])
        moon_dot.set_data([current_moon_position[0]], [current_moon_position[1]])
        moon_dot.set_3d_properties([current_moon_position[2]])

        # Update text info
        info_text.set_text(
            f"Real-Time Position of Earth (km): {current_earth_position}\n"
            f"Real-Time Velocity of Earth (km/s): {current_earth_velocity}\n"
            f"Real-Time Position of Moon (km): {current_moon_position}\n"
            f"Real-Time Velocity of Moon (km/s): {current_moon_velocity}\n"
            f"Next Solar Eclipse: {solar_eclipse}\n"
            f"Next Lunar Eclipse: {lunar_eclipse}"
        )
        return earth_line, moon_line, earth_dot, moon_dot, info_text

    # Run animation
    ani = FuncAnimation(fig, update, interval=1000, cache_frame_data=False)
    plt.show()

# Function to show the formulas in a pop-up window
def show_formulas():
    formulas_window = Toplevel(root)
    formulas_window.title("Formulas Used")
    formulas_window.configure(bg="black")
    Message(formulas_window, text=( 
        "1. Orbital Mechanics:\n"
        "   - Kepler's Laws of Planetary Motion\n"
        "   - Newton's Law of Gravitation\n"
        "   - Orbital Equation: F = G(m1*m2)/r^2\n\n"
        "2. Eclipse Calculation:\n"
        "   - Angle between Sun, Earth, and Moon for Solar Eclipses\n"
        "   - Distance Calculation using SPICE Kernels\n"
        "   - Geometric Shadow Model for Lunar Eclipses"
    ), bg="black", fg="white", font=("Helvetica", 14), width=400, aspect=300).pack(pady=20)

# Create the Tkinter window with input fields for start and end dates, Start Simulation button, and Exit button
root = tk.Tk()
root.title("Earth-Moon Simulation")
root.attributes("-fullscreen", True)
root.configure(bg="black")

def start_simulation():
    start_date = start_date_entry.get()
    end_date = end_date_entry.get()
    start_simulation_plot(start_date, end_date)

def focus_on_end(event):
    end_date_entry.focus()

# Project description
description_text = """
Earth-Moon Simulation is an interactive visualization tool that tracks the real-time trajectories of Earth and its Moon 
around the Sun. The simulation allows users to observe the orbital paths, velocities, and potential eclipses of these celestial bodies. 
It provides accurate, scientifically-driven data based on SPICE kernels and displays the positions of the Earth and Moon relative to 
the Sun in a 3D plot, offering users a captivating, educational experience of celestial mechanics.
"""

description_label = Label(root, text=description_text, fg="white", bg="black", font=("Helvetica", 16), padx=20, pady=20, justify="left")
description_label.pack(pady=50)

# Input fields for start and end dates
input_frame = tk.Frame(root, bg="black")
input_frame.pack(pady=20)

start_date_label = Label(input_frame, text="Start Date (YYYY-MM-DD):", fg="white", bg="black", font=("Helvetica", 14))
start_date_label.grid(row=0, column=0, padx=10, pady=5)
start_date_entry = Entry(input_frame, font=("Helvetica", 14), width=30)
start_date_entry.grid(row=0, column=1, padx=10, pady=5)
start_date_entry.bind("<Return>", focus_on_end)

end_date_label = Label(input_frame, text="End Date (YYYY-MM-DD):", fg="white", bg="black", font=("Helvetica", 14))
end_date_label.grid(row=1, column=0, padx=10, pady=5)
end_date_entry = Entry(input_frame, font=("Helvetica", 14), width=30)
end_date_entry.grid(row=1, column=1, padx=10, pady=5)

# Buttons
start_button = Button(root, text="Start Simulation", command=start_simulation, bg="black", fg="white", font=("Helvetica", 18))
start_button.pack(pady=20)

formulas_button = Button(root, text="Show Formulas", command=show_formulas, bg="black", fg="white", font=("Helvetica", 18))
formulas_button.pack(pady=20)

def exit_program():
    root.quit()

exit_button = Button(root, text="Exit", command=exit_program, bg="black", fg="white", font=("Helvetica", 18))
exit_button.pack(pady=20)

# Start the Tkinter mainloop
root.mainloop()

# Unload SPICE kernels after the program is closed
spice.kclear()


