#include <Arduino.h>
#include <avr/pgmspace.h>
#include "sprite_sheets.h"

struct Sprite {
    int x, y;
    int w, h;
    uint8_t color, color1, color2;
    uint8_t frame;
    uint8_t z;
    bool multicolor;
    bool active;
    const uint8_t *sheet;
};

Sprite sprites[8];
int scrollX = 0;
int scrollY = 0;

void nano64_reset_sprites() {
    for (int i=0;i<8;i++) {
        sprites[i].x = 0;
        sprites[i].y = 0;
        sprites[i].w = 8;
        sprites[i].h = 8;
        sprites[i].color  = 5;
        sprites[i].color1 = 2;
        sprites[i].color2 = 3;
        sprites[i].frame = 0;
        sprites[i].z = 0;
        sprites[i].multicolor = true;
        sprites[i].active = false;
        sprites[i].sheet = playerSpriteSheet;
    }
}

void nano64_sprite_cmd(uint8_t idx, int x, int y, uint8_t col) {
    if (idx >= 8) return;
    sprites[idx].x = x;
    sprites[idx].y = y;
    sprites[idx].color = col;
    sprites[idx].active = true;
}

void nano64_spritemove_cmd(uint8_t idx, int dx, int dy) {
    if (idx >= 8 || !sprites[idx].active) return;
    sprites[idx].x += dx;
    sprites[idx].y += dy;
}

void nano64_spriteframe_cmd(uint8_t idx, uint8_t frame) {
    if (idx >= 8 || !sprites[idx].active) return;
    sprites[idx].frame = frame;
}

void nano64_scroll_cmd(int dx, int dy) {
    scrollX += dx;
    scrollY += dy;
}

bool nano64_sprite_collide(uint8_t a, uint8_t b) {
    if (!sprites[a].active || !sprites[b].active) return false;
    Sprite &sa = sprites[a];
    Sprite &sb = sprites[b];
    return (sa.x < sb.x + sb.w &&
            sa.x + sa.w > sb.x &&
            sa.y < sb.y + sb.h &&
            sa.y + sa.h > sb.y);
}

void nano64_check_collisions() {
    for (uint8_t i=0;i<8;i++) {
        for (uint8_t j=i+1;j<8;j++) {
            if (nano64_sprite_collide(i,j)) {
                tone(3, 440, 30); // simple collision sound
            }
        }
    }
}

uint8_t sprite2bpp_get(const uint8_t *sheet, uint8_t frame, int w, int h, int x, int y) {
    int idx = y * w + x;
    int byteIndex = idx >> 2;
    int shift = (3 - (idx & 3)) * 2;
    uint16_t base = frame * (w*h/4);
    uint8_t byte = pgm_read_byte(&sheet[base + byteIndex]);
    return (byte >> shift) & 0x03;
}

void nano64_render_sprite(const Sprite &s, uint8_t *buf, int stride) {
    for (int yy=0; yy<s.h; yy++) {
        for (int xx=0; xx<s.w; xx++) {
            uint8_t code = sprite2bpp_get(s.sheet, s.frame, s.w, s.h, xx, yy);
            if (code == 0) continue;
            uint8_t col =
                (code == 1) ? s.color  :
                (code == 2) ? s.color1 :
                              s.color2;
            int sx = s.x + xx;
            int sy = s.y + yy;
            if (sx < 0 || sy < 0) continue;
            buf[sy * stride + sx] = col;
        }
    }
}

extern const uint8_t programBytecode[];
extern const uint16_t programLength;

void nano64_run_bytecode() {
    uint16_t pc = 0;
    while (pc < programLength) {
        uint8_t op = programBytecode[pc++];

        switch (op) {
            case 0x12: {
                uint8_t idx = programBytecode[pc++];
                int x = programBytecode[pc++];
                int y = programBytecode[pc++];
                uint8_t col = programBytecode[pc++];
                nano64_sprite_cmd(idx,x,y,col);
                break;
            }
            case 0x13: {
                uint8_t idx = programBytecode[pc++];
                int dx = (int8_t)programBytecode[pc++];
                int dy = (int8_t)programBytecode[pc++];
                nano64_spritemove_cmd(idx,dx,dy);
                break;
            }
            case 0x14: {
                uint8_t idx = programBytecode[pc++];
                uint8_t frame = programBytecode[pc++];
                nano64_spriteframe_cmd(idx,frame);
                break;
            }
            case 0x15: {
                int dx = (int8_t)programBytecode[pc++];
                int dy = (int8_t)programBytecode[pc++];
                nano64_scroll_cmd(dx,dy);
                break;
            }
            case 0xFF:
                return;
        }
    }
}

void nano64_animate_sprites() {
    for (int i=0;i<8;i++) {
        if (!sprites[i].active) continue;
        sprites[i].frame = (sprites[i].frame + 1) & 3; // 4 frames
    }
}

void nano64_render(uint8_t *buf, int stride) {
    for (int i=0;i<8;i++) {
        if (sprites[i].active)
            nano64_render_sprite(sprites[i], buf, stride);
    }
}
