import time, csv, sys 
import random, os
import subprocess, pygame
from pygame.locals import *
import threading, queue
# Set audio driver based on OS to avoid issues
if os.name == 'nt':  # Windows
    os.environ['SDL_AUDIODRIVER'] = 'dsound'  # Use DirectSound on Windows
else:
    os.environ['SDL_AUDIODRIVER'] = 'dummy'  # Use dummy on other systems to avoid ALSA issues
# Import the shell module (must be in the same folder)
import Shell

# --- Fix 1: Added necessary init for sound/display ---
try:
    pygame.mixer.pre_init(44100, -16, 2, 512)
    pygame.init()
    pygame.mixer.init() # Recommended to init mixer once, not inside function
    audio_enabled = True
except Exception as e:
    print(f"Audio initialization failed: {e}. Running without audio.")
    pygame.init()  # Init without mixer
    audio_enabled = False
size = (1000, 500)
screen = pygame.display.set_mode(size, pygame.RESIZABLE) 
clock = pygame.time.Clock() 

class TextBox:
    def __init__(self, x, y, w, h, font_size=28, max_length=256):
        self.rect = pygame.Rect(x, y, w, h)
        self.color_inactive = pygame.Color('lightskyblue3')
        self.color_active = pygame.Color('dodgerblue2')
        self.color = self.color_inactive
        self.text = ''
        self.font = pygame.font.Font(None, font_size)
        self.active = False
        self.max_length = max_length
        self.cursor_visible = True
        self.cursor_timer = 0
        self.cursor_interval = 500  # milliseconds

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            # Toggle the active variable based on click inside rect
            if self.rect.collidepoint(event.pos):
                self.active = True
                self.color = self.color_active
            else:
                self.active = False
                self.color = self.color_inactive

        if event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            elif event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
                # You can handle submit here; for now, unfocus
                self.active = False
                self.color = self.color_inactive
            else:
                # Use event.unicode to respect shift/case
                if len(self.text) < self.max_length and event.unicode:
                    self.text += event.unicode

    def update(self, dt):
        # Blink cursor based on time delta (dt in milliseconds)
        self.cursor_timer += dt
        if self.cursor_timer >= self.cursor_interval:
            self.cursor_timer %= self.cursor_interval
            self.cursor_visible = not self.cursor_visible

    def draw(self, surface):
        # Draw background and border
        pygame.draw.rect(surface, pygame.Color('white'), self.rect)
        pygame.draw.rect(surface, self.color, self.rect, 2)

        # Render text
        txt_surf = self.font.render(self.text, True, pygame.Color('black'))
        surface.blit(txt_surf, (self.rect.x + 5, self.rect.y + (self.rect.h - txt_surf.get_height()) // 2))

        # Draw cursor if active
        if self.active and self.cursor_visible:
            text_width = self.font.size(self.text)[0]
            cx = self.rect.x + 5 + text_width
            cy = self.rect.y + 5
            ch = self.rect.h - 10
            pygame.draw.rect(surface, pygame.Color('black'), (cx, cy, 2, ch))


class Terminal:
    """Simple terminal area with output lines and an input TextBox."""
    def __init__(self, x, y, w, h, font_size=20, max_lines=100):
        self.rect = pygame.Rect(x, y, w, h)
        self.output_rect = pygame.Rect(x, y, w, h - 40)
        self.input_box = TextBox(x + 2, y + h - 38, w - 4, 36, font_size=20)
        self.font = pygame.font.Font(None, font_size)
        self.lines = []
        self.max_lines = max_lines

    def write(self, text):
        # Break incoming text into lines and append
        for part in text.splitlines():
            self.lines.append(part)
        # Keep within max_lines
        if len(self.lines) > self.max_lines:
            self.lines = self.lines[-self.max_lines:]

    def handle_event(self, event):
        self.input_box.handle_event(event)

        # If Enter pressed and input_box became inactive (we unfocus on Enter), send command
        if event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            if self.input_box.text:
                cmd = self.input_box.text
                self.write(f"(Cmd) {cmd}")
                put_input(cmd)
                self.input_box.text = ''

    def update(self, dt):
        self.input_box.update(dt)

    def draw(self, surface):
        # Draw output background
        pygame.draw.rect(surface, pygame.Color('black'), self.output_rect)
        # Render last lines from bottom up
        padding = 5
        y = self.output_rect.y + padding
        # Clip to area
        visible_lines = self.lines[-(self.output_rect.h // (self.font.get_linesize() or 1)):]
        for i, line in enumerate(visible_lines):
            txt_surf = self.font.render(line, True, pygame.Color('white'))
            surface.blit(txt_surf, (self.output_rect.x + 5, y + i * self.font.get_linesize()))

        # Draw input box
        self.input_box.draw(surface)



def SFX_player(Folder2, SFX_name):
    if not audio_enabled:
        return  # Skip if audio not available
    script_dir = os.path.dirname(os.path.abspath(__file__))
    sound_path = os.path.join(Folder2, SFX_name)
    try:
        my_sound = pygame.mixer.Sound(sound_path)
        my_sound.play()
        
        # Optional: wait for it to finish if this is a blocking call
        # while channel.get_busy():
        #     pygame.time.wait(100)
    except pygame.error as e:
        print(f"Cannot open sound file: {sound_path}")
        print(e)

# --- Fix 2: Renamed 'Sprite' to 'Sprite_name' in args, fixed variable names ---
def Sprite_loader(Display, Folder1, Folder2, Sprite_name, X_pos, Y_pos, Width, Height): 
    Spritefile = Sprite_name + ".png" # Fixed variable mismatch
    Sprite_path = os.path.join(Folder1, Folder2, Spritefile) 
    
    try:
        sprite_img = pygame.image.load(Sprite_path).convert_alpha() # Good practice
        sprite_img = pygame.transform.scale(sprite_img, (Width, Height)) # Fixed 'width' (lowercase) to 'Width'
        Display.blit(sprite_img, (X_pos, Y_pos)) 
    except pygame.error as e:
        print(f"Cannot load image: {Sprite_path}")
        print(e)

# --- Main Loop Setup ---
running = True 
# Dynamic tabs system
tabs = []  # each tab: {'id': str, 'label': str, 'rect': pygame.Rect, 'content': any}
current_panel = None

def add_tab(tab_id: str, label: str, content):
    """Add a tab. `content` can be a string key (e.g. 'terminal') or a callable(draw_surface, rect).
    The new tab will be appended and become the active tab."""
    tab = {'id': tab_id, 'label': label, 'rect': pygame.Rect(0, 0, 140, 40), 'content': content}
    tabs.append(tab)
    global current_panel
    current_panel = tab_id

# Add initial tabs
add_tab('terminal', 'Terminal (F1)', 'terminal')
add_tab('other', 'Other (F2)', 'other')
SFX_Toggle = False
count = 0 
text_box = TextBox(50, 50, 400, 40)
# Queues for communicating with the shell thread
input_queue = queue.Queue()

def put_input(s: str):
    # Put a line into the input queue for the shell to read
    input_queue.put(s + '\n')


class StdinFromQueue:
    def __init__(self, q: queue.Queue):
        self.q = q

    def readline(self):
        # Block until a line is available
        try:
            line = self.q.get()
            return line
        except Exception:
            return ''


class StdoutToTerminal:
    def __init__(self, terminal):
        self.terminal = terminal

    def write(self, text):
        # Handle ANSI clear-screen sequence (ESC 'c' == '\033c')
        if not text:
            return
        # If the shell prints the clear sequence, clear the terminal buffer
        if '\x1bc' in text or '\033c' in text:
            self.terminal.lines.clear()
            # Remove the control sequence so the intro or other text prints cleanly
            text = text.replace('\x1bc', '').replace('\033c', '')

        # Writes may be called with fragments; forward remaining text to terminal
        if text:
            self.terminal.write(text)

    def flush(self):
        pass

# Create terminal area
terminal = Terminal(20, 110, 760, 360)

# Start the shell in a background thread
def shell_thread_target():
    try:
        app = Shell.MyInteractiveShell(UserName="Guest")
        # Set the callback for creating tabs
        Shell.create_tab_callback = add_tab
        # Use .stdin.readline() instead of raw_input so we can feed lines from a queue
        app.use_rawinput = False
        # Attach custom stdin/stdout
        app.stdin = StdinFromQueue(input_queue)
        app.stdout = StdoutToTerminal(terminal)
        # Also set sys.stdin/sys.stdout inside the thread to be safe
        sys_stdin_saved = sys.stdin
        sys_stdout_saved = sys.stdout
        sys.stdin = app.stdin
        sys.stdout = app.stdout
        try:
            app.cmdloop()
        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            terminal.write(f"Shell thread exception:\n{tb}\n")
        finally:
            sys.stdin = sys_stdin_saved
            sys.stdout = sys_stdout_saved
    except Exception as e:
        terminal.write(f"Shell thread error: {e}\n")

shell_thread = threading.Thread(target=shell_thread_target, daemon=True)
shell_thread.start()

screen_size = pygame.display.get_surface().get_size()
padding = 12
font = pygame.font.SysFont(None, 28)


while running: 
    for event in pygame.event.get(): 
        mouse_pos = pygame.mouse.get_pos()
        if event.type == pygame.QUIT: 
            running = False 
        elif event.type == pygame.VIDEORESIZE:
            size = (event.w, event.h)
            screen = pygame.display.set_mode(size, pygame.RESIZABLE)


        # 2. Check for a mouse button press event
        if event.type == pygame.MOUSEBUTTONDOWN:
            event_mouse_pos = event.pos

            # text box always receives mouse events
            text_box.handle_event(event)

            # Clicking any tab switches panels
            for t in tabs:
                if t['rect'].collidepoint(event_mouse_pos):
                    current_panel = t['id']
                    # unfocus terminal input when switching away
                    if t['id'] != 'terminal':
                        terminal.input_box.active = False
                    break

            # Terminal only receives events when active panel is terminal
            if current_panel == 'terminal':
                terminal.handle_event(event)

        # Let the terminal/textbox process keyboard events too
        if event.type == pygame.KEYDOWN:
            text_box.handle_event(event)
            if current_panel == 'terminal':
                terminal.handle_event(event)

    # --- Drawing ---
    screen.fill("lightblue")
    # Update terminal and textbox (pass milliseconds since last frame)
    dt = clock.get_time()

    # Compute content area for panels
    content_area = pygame.Rect(20, 80, screen.get_width() - 40, screen.get_height() - 100)

    # Position tabs horizontally with padding
    tx = 20
    ty = 20
    tab_gap = 8
    for t in tabs:
        t['rect'].topleft = (tx, ty)
        tx += t['rect'].width + tab_gap

    text_box.update(dt)

    # If terminal is active, resize its internal rects to match content_area before updating
    if current_panel == 'terminal':
        terminal.rect = content_area.copy()
        terminal.output_rect = pygame.Rect(content_area.x, content_area.y, content_area.w, content_area.h - 40)
        terminal.input_box.rect = pygame.Rect(content_area.x + 2, content_area.y + content_area.h - 38, content_area.w - 4, 36)
        terminal.update(dt)

    # Draw tabs
    for t in tabs:
        is_active = (t['id'] == current_panel)
        color = pygame.Color('grey20') if is_active else pygame.Color('grey50')
        pygame.draw.rect(screen, color, t['rect'])
        lbl = font.render(t['label'], True, (255, 255, 255))
        screen.blit(lbl, (t['rect'].x + 8, t['rect'].y + 8))

    # Draw active panel content
    if current_panel == 'terminal':
        terminal.draw(screen)
    else:
        # Find the current tab
        current_tab = next((t for t in tabs if t['id'] == current_panel), None)
        if current_tab:
            content = current_tab['content']
            if callable(content):
                content(screen, content_area)
            elif content == 'other':
                pygame.draw.rect(screen, pygame.Color('white'), content_area)
                info = font.render('Other panel content goes here.', True, pygame.Color('black'))
                screen.blit(info, (content_area.x + 10, content_area.y + 10))
            else:
                # Default: show the content as text
                pygame.draw.rect(screen, pygame.Color('white'), content_area)
                info = font.render(f'Panel: {content}', True, pygame.Color('black'))
                screen.blit(info, (content_area.x + 10, content_area.y + 10))
        else:
            pygame.draw.rect(screen, pygame.Color('white'), content_area)
            info = font.render('Unknown panel.', True, pygame.Color('black'))
            screen.blit(info, (content_area.x + 10, content_area.y + 10))

    pygame.display.flip() 
    clock.tick(60) 

pygame.quit()
