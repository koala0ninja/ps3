import pygame
import time
import os
import sys
import subprocess # To call sixpair if needed

# --- Configuration ---
SCREEN_WIDTH = 480  # Adjust if using a different display
SCREEN_HEIGHT = 320 # Adjust if using a different display
BG_COLOR = (30, 30, 30)
FG_COLOR = (200, 200, 200)
HIGHLIGHT_COLOR = (0, 255, 0)
STICK_AREA_COLOR = (50, 50, 50)
STICK_COLOR = (255, 0, 0)
TEXT_COLOR = (220, 220, 220)
INFO_COLOR = (255, 255, 0) # Yellow for instructions
ERROR_COLOR = (255, 0, 0) # Red for errors

# --- Pygame Initialization ---
pygame.init()
pygame.joystick.init()

# --- Display Setup ---
# Attempt to hide mouse cursor
pygame.mouse.set_visible(False)
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT)) # Use 0,0 for fullscreen potentially pygame.FULLSCREEN
pygame.display.set_caption("PS3 Controller Tester")
font_large = pygame.font.Font(None, 36)
font_medium = pygame.font.Font(None, 28)
font_small = pygame.font.Font(None, 20)

# --- Controller State ---
joystick = None
joystick_name = "No Controller Found"
num_axes = 0
num_buttons = 0
num_hats = 0
axes_state = []
buttons_state = []
hats_state = []
connected = False
pairing_step = 0 # 0=Idle, 1=Need USB, 2=Need PS btn (USB), 3=Need unplug, 4=Need PS btn (Wireless)

# --- GUI Layout (Visual Representation) ---
# Coordinates are approximate - adjust for your screen size
# Button Positions (x, y, radius)
button_layout = {
    0: (380, 150, 12), # Cross
    1: (415, 120, 12), # Circle
    2: (345, 120, 12), # Square
    3: (380, 90, 12),  # Triangle
    4: (80, 60, 10),   # L1
    5: (400, 60, 10),  # R1
    6: (80, 35, 8),    # L2 Button (visual only, axis used for value)
    7: (400, 35, 8),   # R2 Button (visual only, axis used for value)
    8: (170, 180, 8),  # Select
    9: (230, 180, 8),  # Start
    10: (200, 150, 10),# PS Button
    11: (100, 220, 8), # L3 (Stick Click) - Place near stick
    12: (300, 220, 8), # R3 (Stick Click) - Place near stick
}
button_labels = { # Short labels near buttons
    0: "X", 1: "O", 2: "S", 3: "T", 4: "L1", 5: "R1", 6: "L2", 7: "R2",
    8: "Sel", 9: "Sta", 10: "PS", 11: "L3", 12: "R3"
}

# Stick Positions (x, y, area_radius, dot_radius)
stick_l_layout = (100, 220, 40, 5)
stick_r_layout = (300, 220, 40, 5)

# D-Pad Position (center_x, center_y, segment_width, segment_height)
dpad_layout = (100, 120, 15, 20) # More visual D-Pad

# Trigger Bar Positions (x, y, width, height)
l2_bar_layout = (120, 35, 80, 15)
r2_bar_layout = (280, 35, 80, 15)

# --- Controller Axis Mapping (Standard DualShock 3 - ASSUMED) ---
# !! This might be incorrect for some clones !!
AXIS_LEFT_X = 0
AXIS_LEFT_Y = 1
AXIS_RIGHT_X = 3
AXIS_RIGHT_Y = 4
AXIS_L2 = 2
AXIS_R2 = 5

# --- Helper Functions ---
def draw_text(text, font, position, color=TEXT_COLOR, center=False):
    surf = font.render(text, True, color)
    rect = surf.get_rect()
    if center:
        rect.center = position
    else:
        rect.topleft = position
    screen.blit(surf, rect)

def check_sixpair():
    """Calls the external sixpair utility. Returns True on success."""
    try:
        # Using sudo might be necessary depending on USB permissions
        # For simplicity, assume user ran setup script which might handle permissions,
        # or prompt user if it fails without sudo.
        # !! Security Risk: Avoid running GUI as root. Better to set udev rules. !!
        # For now, try without sudo, relying on standard permissions.
        print("Attempting to run sixpair...")
        # Use Popen to capture output/errors if needed
        process = subprocess.Popen(["sixpair"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate(timeout=5) # 5 second timeout
        print("sixpair stdout:", stdout.decode())
        print("sixpair stderr:", stderr.decode())
        if process.returncode == 0 and "Setting master bd_addr" in stdout.decode():
             print("sixpair successful.")
             return True
        else:
             print(f"sixpair failed with code {process.returncode}.")
             return False
    except FileNotFoundError:
        print("ERROR: 'sixpair' command not found. Was it installed correctly?")
        return False
    except subprocess.TimeoutExpired:
        print("ERROR: 'sixpair' command timed out.")
        return False
    except Exception as e:
        print(f"ERROR running sixpair: {e}")
        return False

def find_and_init_controller():
    global joystick, joystick_name, num_axes, num_buttons, num_hats
    global axes_state, buttons_state, hats_state, connected, pairing_step
    
    pygame.joystick.quit()
    pygame.joystick.init()
    count = pygame.joystick.get_count()

    if count > 0:
        joystick = pygame.joystick.Joystick(0)
        joystick.init()
        joystick_name = joystick.get_name()
        if "PLAYSTATION(R)3" not in joystick_name.upper(): # Basic check
             joystick_name += " (Unknown Type!)" # Flag if it's not named as expected
        num_axes = joystick.get_numaxes()
        num_buttons = joystick.get_numbuttons()
        num_hats = joystick.get_numhats()
        # Initialize state lists only if dimensions change or first connect
        if not connected or len(axes_state) != num_axes:
            axes_state = [0.0] * num_axes
        if not connected or len(buttons_state) != num_buttons:
            buttons_state = [0] * num_buttons
        if not connected or len(hats_state) != num_hats:
             hats_state = [(0,0)] * num_hats
        connected = True
        pairing_step = 0 # Reset pairing guide
        print(f"Connected: {joystick_name} | Axes: {num_axes}, Buttons: {num_buttons}, Hats: {num_hats}")
        return True
    else:
        joystick = None
        joystick_name = "No Controller Found"
        connected = False
        # Start pairing guide if no controller is found
        if pairing_step == 0:
            pairing_step = 1 # Initiate pairing guide
        return False

def update_input_state():
    if not connected or not joystick:
        return False
    
    try:
        for i in range(num_axes):
            axes_state[i] = joystick.get_axis(i)
        for i in range(num_buttons):
            buttons_state[i] = joystick.get_button(i)
        for i in range(num_hats):
            hats_state[i] = joystick.get_hat(i)
        return True
    except pygame.error as e:
        # Handle disconnection during update
        print(f"Pygame error updating state (likely disconnect): {e}")
        find_and_init_controller() # Try to re-find it
        return False

# --- Main Loop ---
running = True
last_check_time = time.time()
check_interval = 1.5 # Seconds check interval for connection

# Initial check
find_and_init_controller()

while running:
    # --- Event Handling ---
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE: # Allow quitting with ESC if keyboard attached
                running = False
        # --- Try to detect controller connect/disconnect ---
        # These events can be unreliable, so periodic checks are also used
        if event.type == pygame.JOYDEVICEADDED:
            print("Event: Controller Added")
            find_and_init_controller()
        if event.type == pygame.JOYDEVICEREMOVED:
            print("Event: Controller Removed")
            connected = False # Mark as disconnected immediately
            joystick = None
            joystick_name = "Controller Disconnected"
            if pairing_step == 0: pairing_step = 4 # Prompt to press PS button wirelessly

        # --- Handle PS button press during pairing guide ---
        if connected and pairing_step > 0: # If connected while guide was active
             pairing_step = 0 # Connection achieved, stop guide

        if event.type == pygame.JOYBUTTONDOWN and pairing_step in [2, 4]:
             if event.button == 10: # PS Button Index (usually 10)
                 if pairing_step == 2: # Was waiting for PS button via USB
                     # Optional: We could try calling sixpair here, but permissions are tricky.
                     # Let's assume user might need manual sixpair if BlueZ doesn't handle it.
                     # For now, just advance the guide.
                     print("PS Button pressed via USB, proceeding...")
                     pairing_step = 3 # Move to unplug step
                 elif pairing_step == 4: # Was waiting for PS button wirelessly
                     print("PS Button pressed wirelessly, attempting connection...")
                     # find_and_init_controller() should pick it up now or soon
                     # The check loop will handle the connection status update

    # --- Periodic Controller Check ---
    current_time = time.time()
    if not connected and (current_time - last_check_time > check_interval):
        find_and_init_controller()
        last_check_time = current_time
        # Reset pairing step if still no controller after a while
        if not connected and pairing_step == 0:
             pairing_step = 1


    # --- Update Input State ---
    if connected:
        if not update_input_state(): # If update fails (disconnect)
             continue # Skip drawing this frame, state is being reset

    # --- Drawing ---
    screen.fill(BG_COLOR)

    # --- Draw Pairing/Connection Guide ---
    if not connected:
        if pairing_step == 1:
            draw_text("Connect PS3 Controller via USB Cable", font_medium, (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 20), INFO_COLOR, center=True)
            draw_text("Then press the PS Button", font_medium, (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 20), INFO_COLOR, center=True)
            # Check if USB device is present (simple check, might not be reliable)
            # This part is tricky without deeper system access from python
            # We'll just wait for the user to press PS button for now.
            # Consider adding a timeout to move back to searching state?

        elif pairing_step == 2: # This state might be skipped if PS is pressed quickly
             draw_text("Press the PS Button Now", font_medium, (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2), INFO_COLOR, center=True)

        elif pairing_step == 3:
             draw_text("Pairing info sent (hopefully!).", font_medium, (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 40), TEXT_COLOR, center=True)
             draw_text("Now UNPLUG the USB cable.", font_medium, (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 10), INFO_COLOR, center=True)
             draw_text("Then press the PS Button again", font_medium, (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 20), INFO_COLOR, center=True)
             draw_text("to connect wirelessly.", font_medium, (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50), INFO_COLOR, center=True)
             # After a delay, move to step 4 automatically
             if current_time - last_check_time > 5: # Give 5 seconds to read
                 pairing_step = 4
                 last_check_time = current_time # Reset timer for next check

        elif pairing_step == 4:
             draw_text("Press PS Button to Connect Wirelessly", font_medium, (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 20), INFO_COLOR, center=True)
             draw_text("Searching...", font_small, (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 20), TEXT_COLOR, center=True)

    # --- Draw Controller Visuals when Connected ---
    elif connected:
        draw_text(f"Connected: {joystick_name}", font_small, (10, 10), FG_COLOR)

        # Draw Buttons
        for i in range(num_buttons):
            layout = button_layout.get(i)
            if layout:
                x, y, r = layout
                color = HIGHLIGHT_COLOR if buttons_state[i] else FG_COLOR
                pygame.draw.circle(screen, color, (x, y), r)
                pygame.draw.circle(screen, (50,50,50), (x, y), r, 1) # Outline
                # Draw labels nearby
                label = button_labels.get(i)
                if label:
                    draw_text(label, font_small, (x, y + r + 2), TEXT_COLOR, center=True)

        # Draw Sticks
        # Left
        lx, ly, lr, ldr = stick_l_layout
        pygame.draw.circle(screen, STICK_AREA_COLOR, (lx, ly), lr)
        pygame.draw.circle(screen, (20,20,20), (lx, ly), lr, 1) # Outline
        l_stick_x = axes_state[AXIS_LEFT_X] * (lr - ldr)
        l_stick_y = axes_state[AXIS_LEFT_Y] * (lr - ldr)
        pygame.draw.circle(screen, STICK_COLOR, (int(lx + l_stick_x), int(ly + l_stick_y)), ldr)
        # Right
        rx, ry, rr, rdr = stick_r_layout
        pygame.draw.circle(screen, STICK_AREA_COLOR, (rx, ry), rr)
        pygame.draw.circle(screen, (20,20,20), (rx, ry), rr, 1) # Outline
        r_stick_x = axes_state[AXIS_RIGHT_X] * (rr - rdr)
        r_stick_y = axes_state[AXIS_RIGHT_Y] * (rr - rdr)
        pygame.draw.circle(screen, STICK_COLOR, (int(rx + r_stick_x), int(ry + r_stick_y)), rdr)

        # Draw Triggers (L2/R2 Pressure) - as bars
        if num_axes > max(AXIS_L2, AXIS_R2): # Check if axes exist
            # Normalize -1.0 (rest) to 1.0 (pressed) -> 0.0 to 1.0
            l2_val = (axes_state[AXIS_L2] + 1.0) / 2.0
            r2_val = (axes_state[AXIS_R2] + 1.0) / 2.0
            # L2
            bx, by, bw, bh = l2_bar_layout
            pygame.draw.rect(screen, STICK_AREA_COLOR, (bx, by, bw, bh)) # BG
            pygame.draw.rect(screen, HIGHLIGHT_COLOR, (bx, by, bw * l2_val, bh)) # Fill
            pygame.draw.rect(screen, (20,20,20), (bx, by, bw, bh), 1) # Border
            draw_text(f"L2: {l2_val:.2f}", font_small, (bx + bw + 5, by + bh // 2 - 8))
            # R2
            bx, by, bw, bh = r2_bar_layout
            pygame.draw.rect(screen, STICK_AREA_COLOR, (bx, by, bw, bh)) # BG
            pygame.draw.rect(screen, HIGHLIGHT_COLOR, (bx, by, bw * r2_val, bh)) # Fill
            pygame.draw.rect(screen, (20,20,20), (bx, by, bw, bh), 1) # Border
            draw_text(f"R2: {r2_val:.2f}", font_small, (bx - 50, by + bh // 2 - 8)) # Adjusted label pos


        # Draw D-Pad (Hat) - More visual style
        if num_hats > 0:
            cx, cy, seg_w, seg_h = dpad_layout
            hat_x, hat_y = hats_state[0] # Get state of first hat
            
            # Define rects for each direction relative to center
            up_rect = pygame.Rect(cx - seg_w // 2, cy - seg_h * 1.5, seg_w, seg_h)
            down_rect = pygame.Rect(cx - seg_w // 2, cy + seg_h * 0.5, seg_w, seg_h)
            left_rect = pygame.Rect(cx - seg_w * 1.5, cy - seg_h // 2, seg_w, seg_h)
            right_rect = pygame.Rect(cx + seg_w * 0.5, cy - seg_h // 2, seg_w, seg_h)

            # Draw Base
            pygame.draw.rect(screen, FG_COLOR, up_rect, 0 if hat_y == 1 else -1, border_radius=3)
            pygame.draw.rect(screen, FG_COLOR, down_rect, 0 if hat_y == -1 else -1, border_radius=3)
            pygame.draw.rect(screen, FG_COLOR, left_rect, 0 if hat_x == -1 else -1, border_radius=3)
            pygame.draw.rect(screen, FG_COLOR, right_rect, 0 if hat_x == 1 else -1, border_radius=3)
            # Draw Highlight
            pygame.draw.rect(screen, HIGHLIGHT_COLOR, up_rect, 0 if hat_y == 1 else -1, border_radius=3)
            pygame.draw.rect(screen, HIGHLIGHT_COLOR, down_rect, 0 if hat_y == -1 else -1, border_radius=3)
            pygame.draw.rect(screen, HIGHLIGHT_COLOR, left_rect, 0 if hat_x == -1 else -1, border_radius=3)
            pygame.draw.rect(screen, HIGHLIGHT_COLOR, right_rect, 0 if hat_x == 1 else -1, border_radius=3)
            # Draw Outlines
            pygame.draw.rect(screen, (50,50,50), up_rect, 1, border_radius=3)
            pygame.draw.rect(screen, (50,50,50), down_rect, 1, border_radius=3)
            pygame.draw.rect(screen, (50,50,50), left_rect, 1, border_radius=3)
            pygame.draw.rect(screen, (50,50,50), right_rect, 1, border_radius=3)
            draw_text("D-PAD", font_small, (cx, cy + seg_h * 1.8), TEXT_COLOR, center=True)

        # Quit Instruction
        draw_text("Press L1+R1+START to Quit", font_small, (SCREEN_WIDTH // 2, SCREEN_HEIGHT - 15), INFO_COLOR, center=True)
        # Check for Quit Combo
        if buttons_state[button_layout.get(4)[0]] and buttons_state[button_layout.get(5)[0]] and buttons_state[button_layout.get(9)[0]]: # L1, R1, Start indices
             running = False


    # --- Update Display ---
    pygame.display.flip()

    # --- Frame Limiting ---
    time.sleep(0.016) # Aim for ~60 FPS

# --- Cleanup ---
print("Exiting tester.")
pygame.quit()
sys.exit()
