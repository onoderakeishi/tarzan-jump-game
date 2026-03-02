#ターザンロープアクションゲーム

import math
import random
import pygame

#ゲームバランスを調整するとき用の定数を定義
ROPE_ANGLE = 50        #ロープ発射角度
KICK_STRENGTH = 2.2    #ブーストの強さ
GOAL_X = 15000        #ゴール地点のX座標

#クラス定義
class World:
    def __init__(self, width, height, gravity=0.4):
        self.width = width
        self.height = height
        self.gravity = pygame.Vector2(0, gravity)
        self.dt = 1.0


class Particle:
    """ 主人公 """
    def __init__(self, x, y, world):
        self.world = world
        self.pos = pygame.Vector2(x, y)
        self.vel = pygame.Vector2(0, 0)
        self.radius = 12

    @property
    def x(self): return self.pos.x
    @x.setter
    def x(self, v): self.pos.x = v

    @property
    def y(self): return self.pos.y
    @y.setter
    def y(self, v): self.pos.y = v

    @property
    def vx(self): return self.vel.x
    @vx.setter
    def vx(self, v): self.vel.x = v

    @property
    def vy(self): return self.vel.y
    @vy.setter
    def vy(self, v): self.vel.y = v

    def update(self):
        self.vel += self.world.gravity * self.world.dt

        #速度制限
        if self.vel.length() > 10:
            self.vel.scale_to_length(10)

        #位置更新
        self.pos += self.vel * self.world.dt

    def draw(self, screen, scroll_x):
        draw_x = int(self.x - scroll_x)
        draw_y = int(self.y)
        pygame.draw.circle(screen, (255, 200, 100), (draw_x, draw_y), self.radius)
        
        #目
        eye_offset = 5 if self.vx >= 0 else -5
        pygame.draw.circle(screen, (0, 0, 0), (draw_x + eye_offset, draw_y - 3), 2)


class Rope:
    """ ロープ"""
    def __init__(self, anchor_x, anchor_y, player, world):
        self.world = world
        self.anchor = pygame.Vector2(anchor_x, anchor_y)
        self.player = player

        #ロープの長さは、ロープがかかった瞬間の距離で固定する
        self.length = self.player.pos.distance_to(self.anchor)
        if self.length < 10:
            self.length = 10

    def update(self):
        #現在のプレイヤーと支点の距離を測る
        diff = self.player.pos - self.anchor
        dist = diff.length()

        #もしロープの長さより遠くに行こうとした場合
        if dist > self.length:
            if dist > 0:
                correction = diff.normalize() * self.length
                self.player.pos = self.anchor + correction

                normal = diff.normalize()
                dot = self.player.vel.dot(normal)
                if dot > 0:
                    self.player.vel -= normal * dot

    def draw(self, screen, scroll_x):
        start_x = int(self.anchor.x - scroll_x)
        start_y = int(self.anchor.y)
        end_x = int(self.player.x - scroll_x)
        end_y = int(self.player.y)
        
        pygame.draw.line(screen, (100, 70, 40), (start_x, start_y), (end_x, end_y), 3)
        pygame.draw.circle(screen, (80, 80, 80), (start_x, start_y), 5)


class CeilingMap:
    """ 天井マップ """
    def __init__(self, world):
        self.world = world
        self.blocks = []

        #スタート地点の天井
        start_rect = pygame.Rect(-200, 0, 800, 50)
        self.blocks.append(start_rect)

        #ゴールまで天井を生成
        current_x = 600
        while current_x < GOAL_X:
            w = random.randint(80, 150)
            h = random.randint(50, 150)
            rect = pygame.Rect(current_x, 0, w, h)
            self.blocks.append(rect)
            current_x += w + random.randint(200, 500)

    def get_ceiling_y(self, x):
        for rect in self.blocks:
            if rect.left <= x <= rect.right:
                return rect.bottom
        return None

    def draw(self, screen, scroll_x):
        for rect in self.blocks:
            if rect.right - scroll_x < 0 or rect.left - scroll_x > self.world.width:
                continue
            draw_rect = pygame.Rect(rect.x - scroll_x, rect.y, rect.width, rect.height)
            pygame.draw.rect(screen, (100, 60, 30), draw_rect)


class SpikeFloor:
    """ トゲトゲの床 """
    def __init__(self, world):
        self.world = world
        self.y = self.world.height - 30

    def check_hit(self, player):
        if player.y + player.radius > self.y:
            return True
        return False

    def draw(self, screen, scroll_x):
        #床を描く
        pygame.draw.rect(screen, (100, 50, 0), (0, self.y, self.world.width, self.world.height - self.y))
        
        #トゲを描く
        spike_w = 30
        start_i = int(scroll_x / spike_w)
        end_i = start_i + int(self.world.width / spike_w) + 2

        for i in range(start_i, end_i):
            base_x = i * spike_w - scroll_x
            p1 = (base_x, self.world.height)
            p2 = (base_x + spike_w/2, self.y)
            p3 = (base_x + spike_w, self.world.height)
            pygame.draw.polygon(screen, (150, 75, 0), [p1, p2, p3])


class AppMain:
    def __init__(self):
        pygame.init()
        self.world = World(800, 600)
        self.screen = pygame.display.set_mode((self.world.width, self.world.height))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont(None, 60)
        self.scroll_x = 0
        self.rope = None
        self.reset_game()
        self.state = "READY"

    def reset_game(self):
        self.ceiling = CeilingMap(self.world)
        self.spikes = SpikeFloor(self.world)

        start_x = 200
        ceil_y = self.ceiling.get_ceiling_y(start_x)
        if ceil_y is None: 
            ceil_y = 50
        
        self.player = Particle(start_x, ceil_y + 150, self.world)
        self.rope = Rope(start_x, ceil_y, self.player, self.world)
        
        self.scroll_x = 0
        self.state = "PLAYING"

    def get_rope_target(self):
        start_y = self.player.y - 100
        if start_y > self.player.y - 10:
            start_y = self.player.y - 10
        
        dy = self.player.y - start_y
        aim_vec = pygame.Vector2(0, -1).rotate(ROPE_ANGLE)

        if abs(aim_vec.y) > 0.001:
            ratio = dy / abs(aim_vec.y)
            dx = aim_vec.x * ratio
        else:
            dx = 0
        
        target_x = self.player.x + dx
        return target_x

    def update(self):
        #ESCキーで終了
        if pygame.key.get_pressed()[pygame.K_ESCAPE]:
            pygame.event.post(pygame.event.Event(pygame.QUIT))

        #READY状態
        if self.state == "READY":
            if pygame.mouse.get_pressed()[0]:
                self.state = "PLAYING"
            return

        #ゲームオーバー/ゴール後のリスタート
        if self.state == "GAMEOVER" or self.state == "GOAL":
            if pygame.mouse.get_pressed()[0]:
                self.reset_game()
            return

        #入力処理
        mouse_pressed = pygame.mouse.get_pressed()[0]
        
        if mouse_pressed:
            if self.rope is None:
                target_x = self.get_rope_target()
                ceil_y = self.ceiling.get_ceiling_y(target_x)
                
                if ceil_y is not None and ceil_y < self.player.y:
                    self.rope = Rope(target_x, ceil_y, self.player, self.world)
                    
                    #加速
                    rope_vec = self.rope.anchor - self.player.pos
                    if rope_vec.length() > 0:
                        normal = rope_vec.normalize()
                        tangent = normal.rotate(90)
                        if tangent.x < 0:
                            tangent = -tangent
                        self.player.vel += tangent * KICK_STRENGTH
        else:
            self.rope = None

        #物理演算
        self.player.update()
        if self.rope:
            self.rope.update()

        #天井との当たり判定
        ceil_y = self.ceiling.get_ceiling_y(self.player.x)
        if ceil_y is not None:
            if self.player.y - self.player.radius < ceil_y:
                self.player.y = ceil_y + self.player.radius
                if self.player.vy < 0:
                    self.player.vy = 0

        #スクロール
        target_scroll = self.player.x - self.world.width / 3
        self.scroll_x += (target_scroll - self.scroll_x) * 0.1

        #トゲに当たったらゲームオーバー
        if self.spikes.check_hit(self.player):
            self.state = "GAMEOVER"

        #ゴール判定
        if self.player.x > GOAL_X:
            self.state = "GOAL"

    def draw(self):
        self.screen.fill((150, 200, 255))

        self.ceiling.draw(self.screen, self.scroll_x)
        self.spikes.draw(self.screen, self.scroll_x)

        #ゴールライン
        goal_x = int(GOAL_X - self.scroll_x)
        pygame.draw.rect(self.screen, (255, 215, 0), (goal_x, 0, 50, self.world.height))

        #ガイド線
        if self.state == "PLAYING" and self.rope is None:
            target_x = self.get_rope_target()
            ceil_y = self.ceiling.get_ceiling_y(target_x)

            start_pos = (int(self.player.x - self.scroll_x), int(self.player.y))
            
            if ceil_y is not None and ceil_y < self.player.y:
                color = (0, 255, 255)
                end_pos = (int(target_x - self.scroll_x), int(ceil_y))
            else:
                color = (255, 0, 0)
                start_vec = pygame.Vector2(self.player.x, self.player.y)
                aim_vec = pygame.Vector2(0, -1).rotate(ROPE_ANGLE)
                end_vec = start_vec + aim_vec * 100
                end_pos = (int(end_vec.x - self.scroll_x), int(end_vec.y))
            
            pygame.draw.line(self.screen, color, start_pos, end_pos, 2)

        #ロープとプレイヤー
        if self.rope:
            self.rope.draw(self.screen, self.scroll_x)
        self.player.draw(self.screen, self.scroll_x)

        #スコア表示
        dist = int(self.player.x)
        text = self.font.render(f"{dist} / {GOAL_X}", True, (255, 255, 255))
        self.screen.blit(text, (20, 20))

        #状態メッセージ
        if self.state == "READY":
            msg = self.font.render("CLICK TO START", True, (0, 100, 0))
            self.screen.blit(msg, (self.world.width/2 - 200, self.world.height/2))
        elif self.state == "GAMEOVER":
            msg = self.font.render("GAME OVER", True, (255, 0, 0))
            self.screen.blit(msg, (self.world.width/2 - 130, self.world.height/2))
        elif self.state == "GOAL":
            msg = self.font.render("GOAL!!", True, (255, 215, 0))
            self.screen.blit(msg, (self.world.width/2 - 80, self.world.height/2))
            
        pygame.display.update()

    def run(self):
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return
            self.update()
            self.draw()
            self.clock.tick(60)

if __name__ == "__main__":
    AppMain().run()