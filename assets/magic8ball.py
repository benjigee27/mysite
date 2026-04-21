import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import random, math, time, subprocess, threading
import speech_recognition as sr

# -------------------- Setup --------------------
pygame.init()
pygame.freetype.init()
info = pygame.display.Info()
WIDTH, HEIGHT = info.current_w, info.current_h
screen = pygame.display.set_mode((WIDTH, HEIGHT), DOUBLEBUF | OPENGL | FULLSCREEN)

recognizer = sr.Recognizer()
recognizer.pause_threshold = 1.5 
mic = sr.Microphone()

def set_3d():
    glMatrixMode(GL_PROJECTION); glLoadIdentity()
    gluPerspective(45, WIDTH / HEIGHT, 0.1, 150.0)
    glMatrixMode(GL_MODELVIEW); glLoadIdentity()
    glEnable(GL_DEPTH_TEST); glDisable(GL_LIGHTING)

def set_2d():
    glMatrixMode(GL_PROJECTION); glLoadIdentity()
    glOrtho(0, WIDTH, HEIGHT, 0, -1, 1)
    glMatrixMode(GL_MODELVIEW); glLoadIdentity()
    glDisable(GL_DEPTH_TEST); glDisable(GL_LIGHTING)

quad = gluNewQuadric()
ball_radius = 3.5
stars = [[random.uniform(-70, 70), random.uniform(-50, 50), random.uniform(-120, -20), 1 if random.random() > 0.8 else 0, random.uniform(0, 6.28)] for _ in range(900)]
particles, impact_particles, voice_sparks = [], [], []
impact_triggered = False

# -------------------- Logic --------------------
voice_status = ""
voice_envelope = 0.0 

def listen_logic():
    global q_text, state, start_t, cur_ans, voice_status, placeholder
    voice_status = "LISTENING..."
    try:
        with mic as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.4)
            audio = recognizer.listen(source, timeout=None, phrase_time_limit=12)
        
        voice_status = "TRANSCRIBING..."
        text = recognizer.recognize_google(audio)
        q_text = text.upper(); placeholder = False; voice_status = ""
        state, start_t, cur_ans = "shaking", time.time(), random.choice(answers)
        play_sound("Pop.aiff")
    except Exception:
        voice_status = "RETRY..."; time.sleep(0.8); voice_status = ""

# -------------------- Renderers --------------------
def trigger_impact():
    for _ in range(200):
        angle = random.uniform(0, math.pi * 2)
        speed = random.uniform(0.1, 0.3)
        impact_particles.append([0, 0, -11.5, math.cos(angle)*speed, math.sin(angle)*speed, random.uniform(0.7, 1.3), 0.94, random.uniform(1.0, 4.0)])

def draw_visuals(speed, shake, warp, envelope):
    glDisable(GL_DEPTH_TEST); glBegin(GL_LINES)
    t = time.time()
    for s in stars:
        dist_to_center = math.sqrt(s[0]**2 + s[1]**2)
        wave = math.sin(t * 8 - dist_to_center * 0.2 + s[4]) * (envelope * 2.5) if s[3] == 1 else 0
        alpha = 0.12 + (envelope * 0.6 if s[3] == 1 else 0)
        glColor4f(0.8, 0.9, 1.0, alpha)
        sx = s[0] * (1.0 - warp*0.3) + (shake * 0.03)
        sy = s[1] * (1.0 - warp*0.3)
        vx, vy = sx + wave, sy + wave
        glVertex3f(vx, vy, s[2]); glVertex3f(vx, vy, s[2] - (speed * 0.5))
    glEnd()
    glEnable(GL_BLEND); glBlendFunc(GL_SRC_ALPHA, GL_ONE)
    for vs in voice_sparks:
        glPointSize(vs[6]); glColor4f(0.0, 1.0, 1.0, vs[5])
        glBegin(GL_POINTS); glVertex3f(vs[0], vs[1], vs[2]); glEnd()
    for ip in impact_particles:
        glPointSize(ip[7]); glBegin(GL_POINTS); glColor4f(0.0, ip[5]*0.8, 1.0, ip[5]*0.7); glVertex3f(ip[0], ip[1], ip[2]); glEnd()
    glPointSize(2.5); glBegin(GL_POINTS)
    for p in particles:
        col = (0.0, 0.9, 1.0) if p[6] else (0.1, 0.2, 0.7)
        glColor4f(col[0], col[1], col[2], p[5]*0.8); glVertex3f(p[0], p[1], p[2])
    glEnd(); glDisable(GL_BLEND); glEnable(GL_DEPTH_TEST)

def draw_ball(shake):
    glPushMatrix(); glTranslatef(shake, 0, -15); glColor3f(0, 0, 0); gluSphere(quad, ball_radius, 64, 64); glPopMatrix()

def draw_triangle_system(shake, blue_mix, mouse_tilt, state, reveal_p):
    glPushMatrix()
    tx, ty = mouse_tilt
    glTranslatef(shake * 0.85 + tx, ty, -15 + ball_radius + 0.05)
    sway = 0 if blue_mix > 0 else math.sin(time.time() * 1.5) * 1.8
    glRotatef(sway + (tx * 15), 0, 1, 0); glRotatef(-ty * 15, 1, 0, 0)
    v1, v2, v3 = (-1.4, -0.9, 0), (1.4, -0.9, 0), (0, 1.3, 0)
    glColor3f(0, 0, 0); glBegin(GL_TRIANGLES); glVertex3f(*v1); glVertex3f(*v2); glVertex3f(*v3); glEnd()
    if blue_mix > 0:
        glEnable(GL_BLEND); glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glColor4f(0.0, 0.3, 0.6, 0.7 * blue_mix)
        glBegin(GL_TRIANGLES); glVertex3f(v1[0], v1[1], 0.01); glVertex3f(v2[0], v2[1], 0.01); glVertex3f(v3[0], v3[1], 0.01); glEnd()
        glDisable(GL_BLEND)
    glLineWidth(4); glColor3f(0.0, 0.2, 0.8)
    glBegin(GL_LINE_LOOP); glVertex3f(v1[0], v1[1], 0.02); glVertex3f(v2[0], v2[1], 0.02); glVertex3f(v3[0], v3[1], 0.02); glEnd()
    glEnable(GL_BLEND); glBlendFunc(GL_SRC_ALPHA, GL_ONE)
    glow = (math.sin(time.time() * 4) * 0.4 + 0.6)
    if state == "revealing" and reveal_p >= 1.0: glow = 1.0
    if state == "fading": glow *= blue_mix 
    glColor4f(0.0, 1.0, 1.0, glow)
    glLineWidth(6); glBegin(GL_LINE_LOOP); glVertex3f(v1[0], v1[1], 0.03); glVertex3f(v2[0], v2[1], 0.03); glVertex3f(v3[0], v3[1], 0.03); glEnd()
    glDisable(GL_BLEND); glPopMatrix()

def render_ui_text(text, center, font, color=(0, 255, 255), alpha=1.0, reveal_p=1.0, max_width=None, is_triangle=False, locked=False, align_right=False):
    if not text: return
    limit = int(len(text) * reveal_p); display_text = text[:limit]
    if not display_text: return
    temp_surf, _ = font.render(display_text, fgcolor=color)
    t_size = font.size
    if max_width and temp_surf.get_width() > max_width: t_size = int(font.size * (max_width / temp_surf.get_width()))
    final_alpha = 255 if locked else int(255 * alpha)
    surf, _ = font.render(display_text, fgcolor=(color[0], color[1], color[2], final_alpha), size=t_size)
    w, h = surf.get_size()
    if is_triangle:
        for line_y in range(0, h, 3): pygame.draw.line(surf, (0, 0, 0, 100), (0, line_y), (w, line_y))
    t_data = pygame.image.tostring(surf, "RGBA", True)
    glEnable(GL_TEXTURE_2D); glEnable(GL_BLEND); glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    tid = glGenTextures(1); glBindTexture(GL_TEXTURE_2D, tid)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, w, h, 0, GL_RGBA, GL_UNSIGNED_BYTE, t_data)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    x = center[0] - w if align_right else center[0] - w//2
    y = center[1] - h//2
    glBegin(GL_QUADS); glTexCoord2f(0, 1); glVertex2f(x, y); glTexCoord2f(1, 1); glVertex2f(x+w, y); glTexCoord2f(1, 0); glVertex2f(x+w, y+h); glTexCoord2f(0, 0); glVertex2f(x, y+h); glEnd(); glDeleteTextures([tid]); glDisable(GL_TEXTURE_2D)

# -------------------- Main Loop --------------------
def play_sound(file):
    subprocess.Popen(['afplay', f"/System/Library/Sounds/{file}"], stderr=subprocess.DEVNULL)

title_font = pygame.freetype.SysFont("Courier", 70, bold=True); ans_font = pygame.freetype.SysFont("Courier", 45, bold=True); ui_font = pygame.freetype.SysFont("Courier", 35, bold=True); voice_font = pygame.freetype.SysFont("Courier", 22, bold=True); dev_font = pygame.freetype.SysFont("Courier", 18, bold=False)
answers = ["YES", "ABSURD NO", "MAYBE SO", "NOT LIKELY", "RE-CONCENTRATE", "OUTLOOK GOOD", "WITHOUT DOUBT", "DEFINITELY", "SIGNS POINT TO YES", "REPLY HAZY"]
state, q_text, placeholder, active = "idle", "ASK THE VOID...", True, False
cur_ans, blue_mix, shake_off, star_speed, start_t = "", 0, 0, 1.0, 0
clock = pygame.time.Clock()

while True:
    now = time.time(); mx, my = pygame.mouse.get_pos()
    
    if voice_status == "LISTENING...":
        swell = (math.sin(now * 2.5) * 0.4 + 0.6) 
        voice_envelope = min(1.0, voice_envelope + 0.05) * swell
        if random.random() < 0.3:
            ang = random.uniform(0, 6.28)
            voice_sparks.append([math.cos(ang)*ball_radius, math.sin(ang)*ball_radius, -15, math.cos(ang)*0.05, math.sin(ang)*0.05, 1.0, random.uniform(2, 5)])
    else:
        voice_envelope = max(0.0, voice_envelope - 0.08)

    for vs in voice_sparks[:]:
        vs[0]+=vs[3]; vs[1]+=vs[4]; vs[5]-=0.02
        if vs[5] <= 0: voice_sparks.remove(vs)

    aspect = WIDTH / HEIGHT; world_h = 2 * math.tan(math.radians(45/2)) * 14; world_w = world_h * aspect
    m_x_3d = (mx / WIDTH - 0.5) * world_w; m_y_3d = -(my / HEIGHT - 0.5) * world_h
    for _ in range(2): particles.append([m_x_3d, m_y_3d, -14, random.uniform(-0.005, 0.005), random.uniform(-0.005, 0.005), 1.0, random.random() < 0.3])
    for p in particles[:]:
        p[0]+=p[3]; p[1]+=p[4]; p[5]-=0.02 
        if p[5] <= 0: particles.remove(p)
    for ip in impact_particles[:]:
        ip[0]+=ip[3]; ip[1]+=ip[4]; ip[3]*=ip[6]; ip[4]*=ip[6]; ip[5]-=0.015
        if ip[5] <= 0: impact_particles.remove(ip)
    
    mouse_tilt = ((mx - WIDTH/2) / WIDTH * 0.12, (my - HEIGHT/2) / HEIGHT * 0.12)

    for e in pygame.event.get():
        if e.type == QUIT: pygame.quit(); exit()
        if e.type == KEYDOWN:
            if e.key == K_ESCAPE: pygame.quit(); exit()
            if e.key == K_v and state == "idle" and voice_status == "":
                threading.Thread(target=listen_logic, daemon=True).start()
            if active:
                if e.key == K_RETURN and not placeholder:
                    state, start_t, cur_ans, impact_triggered = "shaking", now, random.choice(answers), False
                    play_sound("Pop.aiff")
                elif e.key == K_BACKSPACE: q_text = q_text[:-1]
                else:
                    if placeholder: q_text = ""; placeholder = False
                    q_text += e.unicode
        if e.type == MOUSEBUTTONDOWN: active = pygame.Rect(WIDTH//2-350, HEIGHT-180, 700, 80).collidepoint(e.pos)

    warp_val = 0; reveal_p = 1.0
    if state == "shaking":
        t = now - start_t; star_speed = 1.0 + (t * 12.0); warp_val = min(1.0, t / 1.5); shake_off = math.sin(t * 35) * math.exp(-t * 0.4) * 0.4
        if t > 1.8: state, star_speed, shake_off = "revealing", 1.0, 0; play_sound("Glass.aiff")
    elif state == "revealing":
        blue_mix = min(1.0, blue_mix + 0.03); reveal_p = min(1.0, (now - (start_t + 1.8)) * 2.2) 
        if reveal_p >= 0.8 and not impact_triggered: trigger_impact(); impact_triggered = True
        if now - start_t > 4.5: state = "fading"
    elif state == "fading":
        blue_mix -= 0.06
        if blue_mix <= 0: state, blue_mix, q_text, placeholder = "idle", 0, "ASK THE VOID...", True

    for s in stars:
        s[2] += 0.12 * star_speed
        if s[2] > 0: s[2] = -120

    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT); set_3d()
    draw_visuals(star_speed, shake_off, warp_val, voice_envelope)
    draw_ball(shake_off); draw_triangle_system(shake_off, blue_mix, mouse_tilt, state, reveal_p)
    set_2d(); neon_cyan = (0, 255, 255)
    render_ui_text("MAGIC 8-BALL", (WIDTH//2, 80), title_font, color=neon_cyan, locked=True)
    if voice_status: render_ui_text(voice_status, (WIDTH//2, 140), voice_font, color=(255, 100, 0), locked=True)
    else: render_ui_text("PRESS 'V' TO SPEAK", (WIDTH//2, 140), voice_font, color=neon_cyan, locked=True)
    pygame.draw.rect(screen, (0, 20, 45), (WIDTH//2-350, HEIGHT-180, 700, 80), border_radius=20)
    render_ui_text(q_text, (WIDTH//2, HEIGHT-140), ui_font, color=neon_cyan, locked=True)
    if state in ["revealing", "fading"]: 
        render_ui_text(cur_ans, (WIDTH//2, HEIGHT//2), ans_font, color=(255, 255, 255), alpha=blue_mix, reveal_p=reveal_p, max_width=180, is_triangle=True, locked=False)
    
    # DEV TAG - Bottom Right
    render_ui_text("magic 8 ball demo made by Ben G. (2026)", (WIDTH-20, HEIGHT-30), dev_font, color=neon_cyan, locked=True, align_right=True)
    
    pygame.display.flip(); clock.tick(60)