import pygame
import pygame.math
import math
import random

# ===============================================================
# 設定パラメータ
# ===============================================================
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
WORLD_WIDTH = 12000      
GOAL_X = 11000           
ROPE_ANGLE = 50          

# 物理設定（フワフワ・エネルギー保存）
GRAVITY = 0.25           
AIR_RESISTANCE = 0.995   
ROPE_FRICTION = 1.0      

MAX_SPEED = 18.0         
KICK_STRENGTH = 4.0      
SPIKE_HEIGHT = 50        # イバラの高さ

# 色定義（ジャングルカラー）
COLOR_BG = (135, 206, 235)      # スカイブルー
COLOR_PLAYER = (255, 204, 153)  # 肌色
COLOR_ROPE = (34, 139, 34)      # ツルの緑（ForestGreen）
COLOR_WOOD = (139, 69, 19)      # 木の幹（SaddleBrown）
COLOR_LEAF = (50, 205, 50)      # 葉っぱ（LimeGreen）
COLOR_LEAF_DARK = (0, 100, 0)   # 暗い葉っぱ（DarkGreen）
COLOR_GOAL = (255, 215, 0)      # ゴールの黄金色
COLOR_SPIKE = (0, 100, 0)       # イバラ（DarkGreen）
COLOR_FRUIT = (255, 255, 0)     # バナナ（Yellow）
COLOR_GUIDE_OK = (0, 255, 255)
COLOR_GUIDE_NG = (255, 0, 0)

# ===============================================================
# クラス定義
# ===============================================================

class Particle:
    """プレイヤー（ターザン）"""
    def __init__(self, x, y):
        self.pos = pygame.math.Vector2(x, y)
        self.vel = pygame.math.Vector2(0, 0)
        self.mass = 1.0
        self.radius = 12
        self.trail = [] 
        self.max_trail_length = 15

    def update(self, friction):
        self.vel.y += GRAVITY
        self.vel *= friction
        
        speed = self.vel.length()
        if speed > MAX_SPEED:
            self.vel.scale_to_length(MAX_SPEED)
        
        self.pos += self.vel

        # 軌跡更新
        self.trail.append((self.pos.x, self.pos.y))
        if len(self.trail) > self.max_trail_length:
            self.trail.pop(0)

    def draw(self, screen, scroll_x):
        # 軌跡（風のエフェクト）
        if len(self.trail) > 1:
            points = [(p[0] - scroll_x, p[1]) for p in self.trail]
            # 白い半透明っぽい線（Pygameで透明度は重いので細い線で表現）
            pygame.draw.lines(screen, (255, 255, 255), False, points, 2)

        draw_pos = (int(self.pos.x - scroll_x), int(self.pos.y))
        
        # 本体（肌色）
        pygame.draw.circle(screen, COLOR_PLAYER, draw_pos, self.radius)
        # 腰みの（茶色）
        pygame.draw.arc(screen, (160, 82, 45), 
                        (draw_pos[0]-12, draw_pos[1]-12, 24, 24), 
                        math.pi, 0, 10)
        # 目
        eye_offset = 6 if self.vel.x >= 0 else -6
        pygame.draw.circle(screen, (0, 0, 0), (draw_pos[0] + eye_offset, draw_pos[1] - 4), 3)


class Fruit:
    """スコアアイテム（バナナ）"""
    def __init__(self, x, y):
        self.pos = pygame.math.Vector2(x, y)
        self.radius = 12
        self.active = True
        self.angle = 0

    def check_collision(self, player):
        if not self.active: return False
        dist = (self.pos - player.pos).length()
        if dist < self.radius + player.radius + 5:
            self.active = False
            return True
        return False

    def draw(self, screen, scroll_x):
        if not self.active: return
        draw_x = self.pos.x - scroll_x
        draw_y = self.pos.y
        
        if -50 < draw_x < SCREEN_WIDTH + 50:
            # ゆらゆら動く
            self.angle += 0.1
            offset_y = math.sin(self.angle) * 5
            
            # バナナっぽい黄色い丸
            pygame.draw.circle(screen, COLOR_FRUIT, (int(draw_x), int(draw_y + offset_y)), self.radius)
            # ヘタ
            pygame.draw.line(screen, (0, 0, 0), (int(draw_x), int(draw_y + offset_y - 10)), (int(draw_x+3), int(draw_y + offset_y - 15)), 2)


class RigidRope:
    """剛体ロープ（ツル）"""
    def __init__(self, anchor, particle, fixed_length=None):
        self.anchor = pygame.math.Vector2(anchor)
        self.particle = particle
        
        if fixed_length:
            self.length = fixed_length
        else:
            self.length = (self.particle.pos - self.anchor).length()
        if self.length < 10: self.length = 10

    def update(self):
        diff = self.particle.pos - self.anchor
        dist = diff.length()
        if dist < 1: return

        if dist > self.length:
            direction = diff.normalize()
            self.particle.pos = self.anchor + direction * self.length
            
            radial_speed = self.particle.vel.dot(direction)
            if radial_speed > 0:
                self.particle.vel -= direction * radial_speed

    def draw(self, screen, scroll_x):
        start = (self.anchor.x - scroll_x, self.anchor.y)
        end = (self.particle.pos.x - scroll_x, self.particle.pos.y)
        # ツルなので緑色で少し太く
        pygame.draw.line(screen, COLOR_ROPE, start, end, 3)
        # 接続点に葉っぱの飾り
        pygame.draw.circle(screen, COLOR_LEAF, (int(start[0]), int(start[1])), 6)


class CeilingMap:
    """
    天井マップ（森のデザイン）
    """
    def __init__(self):
        self.blocks = [] # (rect, leaves_list) のタプルを格納
        
        # スタート地点
        self.add_block(-500, 0, 1000, 50)
        
        current_x = 500
        while current_x < WORLD_WIDTH + 1000:
            block_w = random.randint(100, 350)
            block_h = random.randint(50, 300)
            self.add_block(current_x, 0, block_w, block_h)
            
            current_x += block_w
            gap_w = random.randint(50, 200)
            current_x += gap_w

    def add_block(self, x, y, w, h):
        """ブロックと装飾用の葉っぱを生成してリストに追加"""
        rect = pygame.Rect(x, y, w, h)
        leaves = []
        
        # ブロックの下端や側面にランダムに葉っぱ（円）を配置して「茂み」を作る
        # 下端に沿って配置
        num_leaves = int(w / 20)
        for i in range(num_leaves + 1):
            lx = x + random.randint(0, w)
            ly = y + h - random.randint(0, 20) # 下端付近
            radius = random.randint(15, 30)
            color = random.choice([COLOR_LEAF, COLOR_LEAF, COLOR_LEAF_DARK]) # 明るい緑多め
            leaves.append({'pos': (lx, ly), 'r': radius, 'color': color})
            
        self.blocks.append({'rect': rect, 'leaves': leaves})

    def get_ceiling_y_at(self, x):
        for b in self.blocks:
            rect = b['rect']
            if rect.left <= x <= rect.right:
                return rect.bottom
        return None

    def check_collision(self, player):
        p_rect = pygame.Rect(player.pos.x - player.radius, player.pos.y - player.radius,
                             player.radius*2, player.radius*2)
        for b in self.blocks:
            rect = b['rect']
            if rect.right < player.pos.x - 50: continue
            if rect.left > player.pos.x + 50: break 
            
            if rect.colliderect(p_rect):
                if player.vel.y < 0 and player.pos.y > rect.bottom - 10:
                    player.pos.y = rect.bottom + player.radius
                    player.vel.y *= -0.5
                    return True
        return False

    def draw(self, screen, scroll_x):
        # 画面内のブロックだけ描画
        for b in self.blocks:
            rect = b['rect']
            
            # 画面外判定
            if rect.right - scroll_x < 0 or rect.left - scroll_x > SCREEN_WIDTH:
                continue

            draw_rect = rect.copy()
            draw_rect.x -= scroll_x
            
            # 1. 幹（木の部分）を描画
            pygame.draw.rect(screen, COLOR_WOOD, draw_rect)
            
            # 2. 葉っぱ（茂み）を描画
            for leaf in b['leaves']:
                lx, ly = leaf['pos']
                lr = leaf['r']
                lcol = leaf['color']
                # 葉っぱもスクロールさせる
                pygame.draw.circle(screen, lcol, (int(lx - scroll_x), int(ly)), lr)


class SpikeFloor:
    """イバラの床"""
    def __init__(self):
        self.height = SPIKE_HEIGHT
        self.y = SCREEN_HEIGHT - self.height

    def check_collision(self, player):
        if player.pos.y + player.radius > self.y + 10: # 少しめり込み許容
            return True
        return False

    def draw(self, screen, scroll_x):
        # イバラ（ギザギザ）を描画
        spike_width = 30
        start_idx = int(scroll_x // spike_width)
        end_idx = int((scroll_x + SCREEN_WIDTH) // spike_width) + 1
        
        for i in range(start_idx, end_idx):
            base_x = i * spike_width - scroll_x
            
            # ランダムな高さにして自然な茂みっぽく
            # (描画のたびにランダムだと揺れてしまうので、x座標から疑似ランダムを作る)
            h_offset = (i * 13 % 15) 
            
            p1 = (base_x, SCREEN_HEIGHT)
            p2 = (base_x + spike_width/2, self.y - h_offset) # 頂点
            p3 = (base_x + spike_width, SCREEN_HEIGHT)
            
            pygame.draw.polygon(screen, COLOR_SPIKE, [p1, p2, p3])


class AppMain:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Jungle Tarzan")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont(None, 40)
        self.big_font = pygame.font.SysFont(None, 80)
        self.reset_game()

    def reset_game(self):
        self.ceiling_map = CeilingMap()
        self.spikes = SpikeFloor()
        self.score = 0
        
        # フルーツ生成
        self.fruits = []
        for i in range(10, int(GOAL_X / 300)):
            x = i * 300 + random.randint(-100, 100)
            y = random.randint(150, 450)
            self.fruits.append(Fruit(x, y))

        start_x = 200
        start_ceil_y = self.ceiling_map.get_ceiling_y_at(start_x)
        if start_ceil_y is None: start_ceil_y = 50
        
        start_anchor = (start_x, start_ceil_y)
        start_player_pos = (start_x - 200, start_ceil_y + 150)
        
        self.player = Particle(*start_player_pos)
        self.rope = RigidRope(start_anchor, self.player)
        
        self.scroll_x = self.player.pos.x - SCREEN_WIDTH / 2
        self.state = "READY"

    def handle_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return True
            if event.type == pygame.MOUSEBUTTONDOWN:
                if self.state == "READY":
                    self.state = "PLAYING"
                elif self.state in ["GAMEOVER", "GOAL"]:
                    self.reset_game()
        return False

    def update(self):
        if self.state == "READY": return
        if self.state != "PLAYING": return

        # --- ロープ処理 ---
        mouse_pressed = pygame.mouse.get_pressed()[0]
        if mouse_pressed:
            if self.rope is None:
                theta = math.radians(ROPE_ANGLE)
                estimated_dy = self.player.pos.y - 100 
                if estimated_dy < 10: estimated_dy = 10
                dx = estimated_dy / math.tan(theta)
                target_x = self.player.pos.x + dx
                
                ceil_y = self.ceiling_map.get_ceiling_y_at(target_x)
                if ceil_y is not None:
                    if ceil_y < self.player.pos.y:
                        anchor_pos = (target_x, ceil_y)
                        self.rope = RigidRope(anchor_pos, self.player)
                        self.apply_boost()
        else:
            self.rope = None

        # --- 物理 ---
        if self.rope:
            current_friction = ROPE_FRICTION
        else:
            current_friction = AIR_RESISTANCE

        self.player.update(current_friction)
        
        if self.rope:
            self.rope.update()

        # --- 判定 ---
        self.ceiling_map.check_collision(self.player)
        
        for f in self.fruits:
            if f.check_collision(self.player):
                self.score += 100 

        if self.spikes.check_collision(self.player):
            self.state = "GAMEOVER"

        # --- スクロール ---
        target_scroll = self.player.pos.x - SCREEN_WIDTH / 2
        self.scroll_x += (target_scroll - self.scroll_x) * 0.1

        # --- ゴール ---
        if self.player.pos.x > GOAL_X:
            self.score += 1000 
            self.state = "GOAL"

    def apply_boost(self):
        diff = self.player.pos - self.rope.anchor
        if diff.length() == 0: return
        tangent = pygame.math.Vector2(-diff.y, diff.x).normalize()
        if tangent.x < 0: tangent = -tangent
        self.player.vel += tangent * KICK_STRENGTH

    def draw(self):
        self.screen.fill(COLOR_BG)

        # マップ描画
        self.ceiling_map.draw(self.screen, self.scroll_x)
        self.spikes.draw(self.screen, self.scroll_x)

        # フルーツ
        for f in self.fruits:
            f.draw(self.screen, self.scroll_x)

        # ガイド
        if self.state == "PLAYING" and not self.rope:
            theta = math.radians(ROPE_ANGLE)
            estimated_dy = self.player.pos.y - 100 
            if estimated_dy < 10: estimated_dy = 10
            dx = estimated_dy / math.tan(theta)
            target_x = self.player.pos.x + dx
            
            ceil_y = self.ceiling_map.get_ceiling_y_at(target_x)
            
            if ceil_y is not None and ceil_y < self.player.pos.y:
                guide_color = COLOR_GUIDE_OK
                end_pos = (target_x - self.scroll_x, ceil_y)
            else:
                guide_color = COLOR_GUIDE_NG
                end_pos = (target_x - self.scroll_x, self.player.pos.y - estimated_dy)

            start_pos = (self.player.pos.x - self.scroll_x, self.player.pos.y)
            pygame.draw.line(self.screen, guide_color, start_pos, end_pos, 2)

        # ゴールゲート
        goal_rect = pygame.Rect(GOAL_X - self.scroll_x, 0, 50, SCREEN_HEIGHT)
        pygame.draw.rect(self.screen, COLOR_GOAL, goal_rect)

        # キャラクター
        if self.rope:
            self.rope.draw(self.screen, self.scroll_x)
        self.player.draw(self.screen, self.scroll_x)

        # UI
        score_text = self.font.render(f"FRUIT: {self.score}", True, (255, 215, 0))
        # 縁取り（読みやすくする）
        outline_text = self.font.render(f"FRUIT: {self.score}", True, (0, 0, 0))
        self.screen.blit(outline_text, (22, 22))
        self.screen.blit(score_text, (20, 20))
        
        dist_text = self.font.render(f"Dist: {int(self.player.pos.x)} / {GOAL_X}", True, (255, 255, 255))
        self.screen.blit(dist_text, (20, 60))

        if self.state == "READY":
            msg = self.big_font.render("JUNGLE TARZAN", True, (0, 100, 0))
            sub = self.font.render("Click to Start", True, (0, 0, 0))
            self.screen.blit(msg, (SCREEN_WIDTH/2 - 250, SCREEN_HEIGHT/2 - 50))
            self.screen.blit(sub, (SCREEN_WIDTH/2 - 100, SCREEN_HEIGHT/2 + 20))
            
        elif self.state == "GAMEOVER":
            msg = self.big_font.render("GAME OVER", True, (200, 0, 0))
            self.screen.blit(msg, (SCREEN_WIDTH/2 - 200, SCREEN_HEIGHT/2 - 50))
            
        elif self.state == "GOAL":
            msg = self.big_font.render("GOAL!!!", True, (255, 215, 0))
            score_msg = self.font.render(f"Total Score: {self.score}", True, (255, 255, 255))
            self.screen.blit(msg, (SCREEN_WIDTH/2 - 120, SCREEN_HEIGHT/2 - 50))
            self.screen.blit(score_msg, (SCREEN_WIDTH/2 - 120, SCREEN_HEIGHT/2 + 20))

        pygame.display.update()

    def run(self):
        while True:
            if self.handle_input():
                break
            self.update()
            self.draw()
            self.clock.tick(60)
        pygame.quit()

if __name__ == "__main__":
    AppMain().run()