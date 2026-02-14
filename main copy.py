#ターザンロープアクションゲーム

import math
import random
import pygame

#ゲームバランスを調整するとき用の定数を定義
ROPE_ANGLE = 50        #ロープ発射角度
KICK_STRENGTH = 1.5    #ブーストの強さ（低下：より難しい）
GOAL_X = 10000        #ゴール地点のX座標

#クラス定義
class World:
    def __init__(self, width, height, gravity=0.35):
        self.width = width
        self.height = height
        self.gravity = pygame.Vector2(0, gravity)
        self.dt = 1.0


class Player:
    """ 主人公 """
    def __init__(self, x, y, world):
        self.world = world
        self.pos = pygame.Vector2(x, y)
        self.vel = pygame.Vector2(0, 0)
        self.radius = 12

    #もともとx,y,vx,vyで作っていたため、プロパティを作った
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

    def update(self, speed_limit=10):
        self.vel += self.world.gravity * self.world.dt

        #速度制限（コンボで上昇可能）
        if self.vel.length() > speed_limit:
            self.vel.scale_to_length(speed_limit)

        #位置更新
        self.pos += self.vel * self.world.dt

    def draw(self, screen, scroll_x, powerup_active=False):
        draw_x = int(self.x - scroll_x)     #スクロール分を引く
        draw_y = int(self.y)
        
        # パワーアップ中はオーラを表示
        if powerup_active:
            glow = (math.sin(pygame.time.get_ticks() * 0.01) + 1) / 2
            aura_radius = int(self.radius + 8 + glow * 5)
            pygame.draw.circle(screen, (255, 100, 255, 128), (draw_x, draw_y), aura_radius)
        
        pygame.draw.circle(screen, (255, 204, 153), (draw_x, draw_y), self.radius)
        #目をつけて、速度の正負によって向きをわかりやすくした
        eye_offset = 5 if self.vx >= 0 else -5
        pygame.draw.circle(screen, (0,0,0), (draw_x + eye_offset, draw_y - 4), 3)


class Particle:
    """汎用パーティクルエフェクト"""
    def __init__(self, x, y, vx, vy, color, size=3, life=30, gravity=0.2):
        self.pos = pygame.Vector2(x, y)
        self.vel = pygame.Vector2(vx, vy)
        self.color = color
        self.size = size
        self.life = life
        self.max_life = life
        self.gravity = gravity

    def update(self):
        self.vel.y += self.gravity
        self.pos += self.vel
        self.life -= 1

    def draw(self, screen, scroll_x):
        if self.life <= 0:
            return
        alpha_ratio = self.life / max(1, self.max_life)
        current_size = max(1, int(self.size * alpha_ratio))
        draw_x = int(self.pos.x - scroll_x)
        draw_y = int(self.pos.y)
        
        # 色の明るさをライフに応じて変化
        if len(self.color) == 3:
            r, g, b = self.color
            r = int(r * alpha_ratio)
            g = int(g * alpha_ratio)
            b = int(b * alpha_ratio)
            pygame.draw.circle(screen, (r, g, b), (draw_x, draw_y), current_size)
        else:
            pygame.draw.circle(screen, self.color, (draw_x, draw_y), current_size)


class TrailParticle:
    """プレイヤーの残像エフェクト"""
    def __init__(self, x, y, radius, life=15):
        self.pos = pygame.Vector2(x, y)
        self.radius = radius
        self.life = life
        self.max_life = life

    def update(self):
        self.life -= 1

    def draw(self, screen, scroll_x):
        if self.life <= 0:
            return
        alpha_ratio = self.life / max(1, self.max_life)
        draw_x = int(self.pos.x - scroll_x)
        draw_y = int(self.pos.y)
        
        # 半透明の円を描画
        s = pygame.Surface((self.radius * 2 + 4, self.radius * 2 + 4), pygame.SRCALPHA)
        alpha = int(150 * alpha_ratio)
        pygame.draw.circle(s, (255, 204, 153, alpha), (self.radius + 2, self.radius + 2), self.radius)
        screen.blit(s, (draw_x - self.radius - 2, draw_y - self.radius - 2))


class Star:
    """背景の星エフェクト"""
    def __init__(self, x, y):
        self.pos = pygame.Vector2(x, y)
        self.size = random.randint(1, 3)
        self.twinkle_offset = random.random() * math.pi * 2

    def draw(self, screen, scroll_x):
        draw_x = int(self.pos.x - scroll_x * 0.1)  # パララックス効果
        draw_y = int(self.pos.y)
        
        # またたき
        glow = (math.sin(pygame.time.get_ticks() * 0.003 + self.twinkle_offset) + 1) / 2
        alpha = int(100 + 155 * glow)
        
        s = pygame.Surface((self.size * 2 + 2, self.size * 2 + 2), pygame.SRCALPHA)
        pygame.draw.circle(s, (255, 255, 200, alpha), (self.size + 1, self.size + 1), self.size)
        screen.blit(s, (draw_x % self.world.width if hasattr(self, 'world') else draw_x, draw_y))


# Particles removed for simpler visuals (no animated particles)





class Collectible:
    """単純なコイン類"""
    def __init__(self, x, y):
        self.pos = pygame.Vector2(x, y)
        self.radius = 8
        self.collected = False

    def check_collect(self, player):
        if self.collected:
            return False
        if player.pos.distance_to(self.pos) < self.radius + player.radius:
            self.collected = True
            return True
        return False

    def draw(self, screen, scroll_x):
        if self.collected:
            return
        draw_x = int(self.pos.x - scroll_x)
        draw_y = int(self.pos.y)
        # 回転アニメーション
        angle = pygame.time.get_ticks() * 0.005
        glow = (math.sin(angle * 2) + 1) / 2
        color = (255, int(223 + 32 * glow), 0)
        pygame.draw.circle(screen, color, (draw_x, draw_y), self.radius)
        pygame.draw.circle(screen, (255, 255, 255), (draw_x-2, draw_y-2), 3)


class PowerUp:
    """スピードブーストのパワーアップ"""
    def __init__(self, x, y):
        self.pos = pygame.Vector2(x, y)
        self.radius = 12
        self.collected = False

    def check_collect(self, player):
        if self.collected:
            return False
        if player.pos.distance_to(self.pos) < self.radius + player.radius:
            self.collected = True
            return True
        return False

    def draw(self, screen, scroll_x):
        if self.collected:
            return
        draw_x = int(self.pos.x - scroll_x)
        draw_y = int(self.pos.y)
        # 星形のパワーアップ
        angle = pygame.time.get_ticks() * 0.003
        for i in range(5):
            a1 = angle + i * (2 * math.pi / 5)
            a2 = angle + (i + 0.5) * (2 * math.pi / 5)
            p1 = (draw_x + math.cos(a1) * self.radius, draw_y + math.sin(a1) * self.radius)
            p2 = (draw_x + math.cos(a2) * self.radius * 0.5, draw_y + math.sin(a2) * self.radius * 0.5)
            if i == 4:
                p3 = (draw_x + math.cos(angle) * self.radius, draw_y + math.sin(angle) * self.radius)
            else:
                p3 = (draw_x + math.cos(a1 + 2 * math.pi / 5) * self.radius, draw_y + math.sin(a1 + 2 * math.pi / 5) * self.radius)
            pygame.draw.polygon(screen, (255, 50, 255), [(draw_x, draw_y), p1, p2])
        pygame.draw.circle(screen, (255, 255, 255), (draw_x, draw_y), 5)


class Rope:
    """ ロープ"""
    def __init__(self, anchor_x, anchor_y, player, world):
        self.world = world
        self.anchor = pygame.Vector2(anchor_x, anchor_y)
        self.player = player

        #ロープの長さは、ロープがかかった瞬間の距離で固定する
        self.length = self.player.pos.distance_to(self.anchor)
        if self.length < 10:
            self.length = 10       #ロープの長さが0にならないようにする

    def update(self):
        #現在のプレイヤーと支点の距離を測る
        diff = self.player.pos - self.anchor
        dist = diff.length()

        #もしロープの長さより遠くに行こうとした場合
        if dist > self.length:
            #強制的にプレイヤーの位置を引き戻したい
            if dist > 0:
                correction = diff.normalize() * self.length #ロープの長さ分のベクトルをつくる
                self.player.pos = self.anchor + correction  #支点からのベクトルにする

                normal = diff.normalize()    #ロープ方向の単位ベクトル
                dot = self.player.vel.dot(normal)  #内積で速度成分を計算
                #速度成分がロープ方向に向いていたら、その分だけ引く
                if dot > 0:
                    self.player.vel -= normal * dot

    def draw(self, screen, scroll_x):
        # screen coordinates
        start_v = pygame.Vector2(self.anchor.x - scroll_x, self.anchor.y)
        end_v = pygame.Vector2(self.player.x - scroll_x, self.player.y)

        # draw rope shadow
        shadow_offset = pygame.Vector2(2, 3)
        pygame.draw.line(screen, (20, 20, 20), (start_v + shadow_offset), (end_v + shadow_offset), 6)

        # main rope (braided look by drawing alternating thin highlights)
        rope_color = (170, 120, 60)
        pygame.draw.line(screen, rope_color, start_v, end_v, 4)

        # small highlight along rope
        highlight = (230, 200, 150)
        dir_vec = (end_v - start_v)
        length = dir_vec.length()
        if length > 0:
            unit = dir_vec.normalize()
            perp = pygame.Vector2(-unit.y, unit.x) * 1.5
            pygame.draw.line(screen, highlight, start_v + perp, end_v + perp, 2)

            # decorative segments to suggest twist: small alternating dots along rope
            seg_w = 14
            seg_count = max(1, int(length / seg_w))
            for i in range(seg_count + 1):
                t = i / seg_count
                pos = start_v + unit * (t * length)
                color_dot = (140, 90, 40) if i % 2 == 0 else (200, 160, 110)
                pygame.draw.circle(screen, color_dot, (int(pos.x), int(pos.y)), 2)

        # draw simple tie/knot at anchor to match ceiling hooks
        ax = int(self.anchor.x - scroll_x)
        ay = int(self.anchor.y)
        # small shadow under ring
        pygame.draw.circle(screen, (20, 20, 20), (ax+2, ay+4), 6)
        # ring where rope ties
        pygame.draw.circle(screen, (60, 60, 60), (ax, ay), 6)
        pygame.draw.circle(screen, (180, 180, 180), (ax, ay), 3)
        # short knot connector (visual only; rope line drawn above)
        pygame.draw.line(screen, (40, 30, 20), (ax, ay+4), (ax, ay+8), 2)


class CeilingMap:
    """ 天井マップ（改良版）
    - ブロックごとに複数の接続ノード（attach_points）を生成
    - 吊り下がる石筍（stalactites）をランダムに配置して地形を複雑化
    """
    def __init__(self, world):
        self.world = world
        self.blocks = []  # each block: dict with rect and attach_points

        #スタート地点の天井を作る
        start_rect = pygame.Rect(-200, 0, 800, 50)
        self.blocks.append({'rect': start_rect, 'attach_points': [start_rect.left + 200]})

        #12000px先まで天井を作る（より難しく）
        current_x = 600
        while current_x < 12000:
            # さらに小さいブロック幅にして、隙間をさらに広くする -> より難易度上昇
            w = random.randint(60, 250)
            h = random.randint(50, 200)
            rect = pygame.Rect(current_x, 0, w, h)

            # attach points: some x positions where rope can attach (avoid near edges)
            attach_points = []
            for _ in range(random.randint(1, max(1, w // 140))):
                ax = random.randint(rect.left + 12, rect.right - 12)
                attach_points.append(ax)

            # no stalactites: keep only attach points for simplicity
            self.blocks.append({'rect': rect, 'attach_points': attach_points})
            current_x += w + random.randint(120, 400)

    def get_ceiling_y(self, x):
        for b in self.blocks:
            rect = b['rect']
            if rect.left <= x <= rect.right:
                # base ceiling bottom
                bottom = rect.bottom
                # return base ceiling bottom (no stalactite collision)
                return bottom
        return None

    def get_nearest_attach(self, x, max_dist=300):
        """指定xの近くで接続できる支点(x,y)を返す。見つからなければNoneを返す。"""
        best = None
        best_d = max_dist
        for b in self.blocks:
            rect = b['rect']
            for ax in b['attach_points']:
                d = abs(ax - x)
                if d < best_d:
                    best_d = d
                    best = (ax, rect.bottom)
        return best

    def draw(self, screen, scroll_x):
        for b in self.blocks:
            rect = b['rect']
            if rect.right - scroll_x < 0:
                continue
            if rect.left - scroll_x > self.world.width:
                continue
            draw_rect = pygame.Rect(rect.x - scroll_x, rect.y, rect.width, rect.height)
            # base rock/wood ceiling
            pygame.draw.rect(screen, (100, 60, 30), draw_rect)

            # add mottled highlights to give texture
            for i in range(0, draw_rect.width, 24):
                rx = draw_rect.x + i + (i % 12)
                ry = draw_rect.y + (i % 6)
                pygame.draw.ellipse(screen, (110, 70, 40), (rx, ry, 20, 8))


class SpikeFloor:
    """ トゲトゲの床 """
    def __init__(self, world):
        self.world = world
        self.y = self.world.height - 30 #下から30px

    def check_hit(self, player):
        #プレイヤーの下端がとげより下に行ったらTrue(とげに当たった判定)を返す
        if player.y + player.radius > self.y + 10:
            return True
        return False

    def draw(self, screen, scroll_x):
        #ギザギザを描く（地面にジャングルの手前植物を追加）
        spike_w = 30
        start_i = int(scroll_x / spike_w)       #描き始めるのは何番目のトゲからか?
        end_i = start_i + int(self.world.width / spike_w) + 2       #何番目のトゲまで描けばいいか?(予備で2個追加)

        # draw static lava band
        lava_rect = pygame.Rect(0, self.y, self.world.width, self.world.height - self.y)
        pygame.draw.rect(screen, (120, 30, 10), lava_rect)

        for i in range(start_i, end_i):
            base_x = i * spike_w - scroll_x     #ゲーム世界の絶対値座標-カメラ位置
            # stylized lava spike (deterministic variation using base_x)
            tip_h = int((math.sin(base_x * 0.05) + 1.0) * 12) + 8
            p1 = (base_x, self.world.height)
            p2 = (base_x + spike_w/2, self.y - tip_h)
            p3 = (base_x + spike_w, self.world.height)
            pygame.draw.polygon(screen, (200, 70, 20), [p1, p2, p3])

            # inner glow near tip
            inner_tip_h = max(4, int(tip_h * 0.5))
            ip2 = (base_x + spike_w/2, self.y - inner_tip_h)
            ip1 = (base_x + spike_w*0.25, self.world.height - 6)
            ip3 = (base_x + spike_w*0.75, self.world.height - 6)
            pygame.draw.polygon(screen, (255, 150, 50), [ip1, ip2, ip3])

            # small hot spot at spike top
            glow_x = int(base_x + spike_w/2)
            glow_y = int(self.y - tip_h + 6)
            pygame.draw.circle(screen, (255, 200, 80), (glow_x, glow_y), 3)


class AppMain:
    def __init__(self):
        pygame.init()
        self.world = World(800, 600, gravity=0.25)
        self.screen = pygame.display.set_mode((self.world.width, self.world.height))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont(None, 60)       #フォントを用意
        self.font_small = pygame.font.SysFont(None, 22)
        self.score = 0
        self.coin = 0
        self.combo = 0
        self.combo_timer = 0
        self.speed_bonus = 0
        self.powerup_timer = 0
        self.scroll_x = 0
        self.rope = None
        # エフェクト用のリスト
        self.particles = []
        self.trails = []
        self.stars = []
        self.collectibles = []
        self.powerups = []
        self.shake_timer = 0
        self.shake_intensity = 0
        
        # 背景の星を生成
        for _ in range(50):
            sx = random.randint(0, 12000)
            sy = random.randint(10, 300)
            self.stars.append(Star(sx, sy))
        
        self.paused = False
        self.reset_game()       #ゲームオーバー後の再スタートに使えるように関数で用意
        self.state = "READY" #クリックでスタートするので、ゲーム開始前の状態を用意
        self.last_leaf_spawn = 0

    def reset_game(self):
        self.ceiling = CeilingMap(self.world)
        self.spikes = SpikeFloor(self.world)

        #スタート地点の天井の高さを調べる
        start_x = 200
        ceil_y = self.ceiling.get_ceiling_y(start_x)
        if ceil_y is None: ceil_y = 50      #もしスタート地点に天井がなかったら、高さを50にする
        
        self.player = Player(start_x, ceil_y + 150, self.world)       #天井から150px下に配置
        #最初からぶら下がった状態でスタート
        self.rope = Rope(start_x, ceil_y, self.player, self.world)
        
        self.scroll_x = 0
        self.state = "PLAYING" #状態をプレイ中にする
        self.score = 0
        self.coin = 0
        self.combo = 0
        self.combo_timer = 0
        self.speed_bonus = 0
        self.powerup_timer = 0
        self.particles.clear()
        self.trails.clear()
        self.shake_timer = 0
        self.shake_intensity = 0

        # collectibles を生成: 各ブロックの接続点から少し離れた位置にランダム配置
        self.collectibles = []
        self.powerups = []
        for b in self.ceiling.blocks:
            rect = b['rect']
            for ax in b['attach_points']:
                if random.random() < 0.25:
                    cx = ax + random.randint(-40, 40)
                    cy = rect.bottom + random.randint(80, 140)
                    self.collectibles.append(Collectible(cx, cy))
                # パワーアップは稀に出現
                elif random.random() < 0.08:
                    px = ax + random.randint(-30, 30)
                    py = rect.bottom + random.randint(100, 160)
                    self.powerups.append(PowerUp(px, py))

    def get_rope_target(self):
        start_y = self.player.y - 100    #とりあえず高さ100px上を基準にしてみる
        if start_y > self.player.y - 10:
            start_y = self.player.y - 10
        
        dy = self.player.y - start_y    #目標点までの高さ差
        aim_vec = pygame.Vector2(0, -1).rotate(ROPE_ANGLE)    #50度傾ける

        if abs(aim_vec.y) > 0.001:
            ratio = dy / abs(aim_vec.y)
            dx = aim_vec.x * ratio
        else:
            dx = 0
        
        target_x = self.player.x + dx
        return target_x
            

    def update(self):
        #ESCキーで終了
        key_pressed = pygame.key.get_pressed()
        if key_pressed[pygame.K_ESCAPE]:
            pygame.event.post(pygame.event.Event(pygame.QUIT))

        # 一時停止中は更新を行わない
        if self.paused:
            return

        #READY状態のとき、クリックされたらPLAYINGに変える
        if self.state == "READY":
            if pygame.mouse.get_pressed()[0]:
                self.state = "PLAYING"
            return

        #GAMEOVERまたはGOALのときのリスタート処理
        if self.state == "GAMEOVER" or self.state == "GOAL":
            if pygame.mouse.get_pressed()[0]:
                self.reset_game()
            return

        #入力処理
        mouse_pressed = pygame.mouse.get_pressed()[0]
        
        if mouse_pressed:
            #クリックしていて、ロープがまだない場合
            if self.rope is None:
                #狙う場所を計算(斜め50度)
                target_x = self.get_rope_target()
                # allow attaching anywhere on the ceiling near the aim point
                # 1) try exact target
                ceil_y = self.ceiling.get_ceiling_y(target_x)
                # 2) if nothing found, probe sideways within +/-200px to find nearest ceiling above player
                if ceil_y is None:
                    best = None
                    best_d = 9999
                    probe_range = 200
                    step = 8
                    for dx in range(-probe_range, probe_range + 1, step):
                        tx = target_x + dx
                        ty = self.ceiling.get_ceiling_y(tx)
                        if ty is not None and ty < self.player.y:
                            d = abs(dx)
                            if d < best_d:
                                best_d = d
                                best = (tx, ty)
                    if best:
                        target_x, ceil_y = best
                
                #天井があるかつ自分より上にあったら発射成功
                if ceil_y is not None and ceil_y < self.player.y:
                    self.rope = Rope(target_x, ceil_y, self.player, self.world)
                    
                    # コンボ増加
                    self.combo += 1
                    self.combo_timer = 120  # 2秒間（60FPS想定）
                    
                    # ロープ接続時のパーティクルエフェクト
                    for i in range(20):
                        angle = random.random() * math.pi * 2
                        speed = random.uniform(1, 4)
                        vx = math.cos(angle) * speed
                        vy = math.sin(angle) * speed - 2
                        color = random.choice([(255, 215, 0), (255, 255, 100), (200, 200, 255)])
                        self.particles.append(Particle(target_x, ceil_y, vx, vy, color, 
                                                      size=random.randint(2, 5), 
                                                      life=random.randint(20, 40)))
                    
                    #加速させる(接線方向に力を加える)
                    rope_vec = self.rope.anchor - self.player.pos   #プレイヤーから支点へのベクトル

                    if rope_vec.length() > 0:
                        normal = rope_vec.normalize()    #ロープ方向の単位ベクトル
                        tangent = normal.rotate(90)  #接線方向の単位ベクトル

                        if tangent.x < 0:
                            tangent =- tangent   #右向きにブーストしたいので、x成分が正になるようにする

                        # パワーアップ中とコンボでブースト強化
                        combo_boost = 1.0 + (self.combo - 1) * 0.15  # コンボごとに15%増加
                        powerup_boost = 1.5 if self.powerup_timer > 0 else 1.0
                        boost = KICK_STRENGTH * combo_boost * powerup_boost
                        self.player.vel += tangent * boost
                    # 接続時の小さなエフェクト
                    # no particle effects for simpler visuals

        else:
            #マウスを離したらロープ解除
            if self.rope is not None:
                # ロープ解除時のエフェクト
                for i in range(10):
                    angle = random.random() * math.pi * 2
                    speed = random.uniform(0.5, 2)
                    vx = math.cos(angle) * speed
                    vy = math.sin(angle) * speed
                    self.particles.append(Particle(self.rope.anchor.x, self.rope.anchor.y, 
                                                  vx, vy, (100, 200, 100), 
                                                  size=2, life=20))
            self.rope = None

        #物理演算
        # コンボに応じて速度制限を上げる（コンボごとに+1）
        speed_limit = 10 + min(self.combo, 10)  # 最大20まで
        self.player.update(speed_limit)
        if self.rope:
            self.rope.update()

        # 天井との当たり判定（すり抜け防止）
        ceil_y = self.ceiling.get_ceiling_y(self.player.x)
        if ceil_y is not None:
            ceiling_bottom = ceil_y
            if self.player.y - self.player.radius < ceiling_bottom:
                self.player.y = ceiling_bottom + self.player.radius
                if self.player.vy < 0:
                    self.player.vy = 0
        
        # パーティクル更新
        for p in list(self.particles):
            p.update()
            if p.life <= 0:
                self.particles.remove(p)
        
        # 残像エフェクト更新
        for t in list(self.trails):
            t.update()
            if t.life <= 0:
                self.trails.remove(t)
        
        # 速度が速い時に残像を追加
        speed = self.player.vel.length()
        if speed > 6 and len(self.trails) < 30:
            if random.random() < 0.3:
                self.trails.append(TrailParticle(self.player.x, self.player.y, 
                                                self.player.radius, life=10))
        
        # 画面シェイク更新
        if self.shake_timer > 0:
            self.shake_timer -= 1

        # コンボタイマー更新
        if self.combo_timer > 0:
            self.combo_timer -= 1
        else:
            self.combo = 0
        
        # パワーアップタイマー更新
        if self.powerup_timer > 0:
            self.powerup_timer -= 1
            # パワーアップ中はキラキラエフェクトを放出
            if random.random() < 0.3:
                angle = random.random() * math.pi * 2
                offset = random.uniform(10, 20)
                px = self.player.x + math.cos(angle) * offset
                py = self.player.y + math.sin(angle) * offset
                vx = random.uniform(-1, 1)
                vy = random.uniform(-2, 0)
                self.particles.append(Particle(px, py, vx, vy, 
                                              (255, 200, 255), 
                                              size=2, life=20, gravity=0))

        # スピードボーナス計算
        speed = self.player.vel.length()
        if speed > 7:
            self.speed_bonus += int((speed - 7) * 2)

        # コレクティブルの取得判定
        for c in self.collectibles:
            if not c.collected and c.check_collect(self.player):
                self.coin += 1
                # コンボボーナス適用
                bonus = 100 * (1 + self.combo * 0.5)
                self.score += int(bonus)
                # コイン取得エフェクト
                for i in range(15):
                    angle = random.random() * math.pi * 2
                    speed = random.uniform(1, 3)
                    vx = math.cos(angle) * speed
                    vy = math.sin(angle) * speed - 1
                    self.particles.append(Particle(c.pos.x, c.pos.y, vx, vy, 
                                                  (255, 223, 0), 
                                                  size=random.randint(2, 4), 
                                                  life=random.randint(15, 30)))
        
        # パワーアップの取得判定
        for p in self.powerups:
            if not p.collected and p.check_collect(self.player):
                self.powerup_timer = 180  # 3秒間のパワーアップ
                self.score += 500
                # 派手なパワーアップ取得エフェクト
                for i in range(30):
                    angle = random.random() * math.pi * 2
                    speed = random.uniform(2, 5)
                    vx = math.cos(angle) * speed
                    vy = math.sin(angle) * speed
                    color = random.choice([(255, 50, 255), (255, 100, 255), (200, 50, 200)])
                    self.particles.append(Particle(p.pos.x, p.pos.y, vx, vy, color, 
                                                  size=random.randint(3, 6), 
                                                  life=random.randint(30, 50)))
                # 画面シェイク
                self.shake_timer = 10
                self.shake_intensity = 5
                
        #トゲに当たったらゲームオーバー
        if self.spikes.check_hit(self.player):
            self.state = "GAMEOVER"
            # ゲームオーバー時の爆発エフェクト
            for i in range(50):
                angle = random.random() * math.pi * 2
                speed = random.uniform(2, 8)
                vx = math.cos(angle) * speed
                vy = math.sin(angle) * speed
                color = random.choice([(255, 100, 0), (255, 50, 0), (255, 200, 0)])
                self.particles.append(Particle(self.player.x, self.player.y, vx, vy, color, 
                                              size=random.randint(3, 8), 
                                              life=random.randint(30, 60)))
            # 強い画面シェイク
            self.shake_timer = 20
            self.shake_intensity = 10

        #スクロールの処理
        #プレイヤーが画面の左から1/3より右に行ったら、カメラも右に動かす
        target_scroll = self.player.x - self.world.width / 3
        self.scroll_x += (target_scroll - self.scroll_x) * 0.1      #0.1をかけて少し遅れてついてくるようにする

        #右に進んだ最大距離をスコアにする
        if self.player.x > self.score:
            self.score = int(self.player.x)
        
        #ゴール判定
        if self.player.x > GOAL_X:
            if self.state != "GOAL":
                # ゴール到達時の花火エフェクト
                for i in range(100):
                    angle = random.random() * math.pi * 2
                    speed = random.uniform(3, 10)
                    vx = math.cos(angle) * speed
                    vy = math.sin(angle) * speed
                    color = random.choice([(255, 0, 0), (0, 255, 0), (0, 0, 255), 
                                          (255, 255, 0), (255, 0, 255), (0, 255, 255)])
                    self.particles.append(Particle(self.player.x, self.player.y, vx, vy, color, 
                                                  size=random.randint(4, 8), 
                                                  life=random.randint(40, 80), 
                                                  gravity=0.15))
            self.state = "GOAL"

    def draw(self):
        # 画面シェイクのオフセット計算
        shake_x = 0
        shake_y = 0
        if self.shake_timer > 0:
            shake_x = random.randint(-self.shake_intensity, self.shake_intensity)
            shake_y = random.randint(-self.shake_intensity, self.shake_intensity)
        
        # 背景を単色で塗る（簡潔に）
        self.screen.fill((120, 180, 255))
        
        # 背景の星を描画
        for star in self.stars:
            star.draw(self.screen, self.scroll_x)

        self.ceiling.draw(self.screen, self.scroll_x - shake_x)
        self.spikes.draw(self.screen, self.scroll_x - shake_x)
        
        # 残像エフェクトを描画（プレイヤーより先に）
        for trail in self.trails:
            trail.draw(self.screen, self.scroll_x - shake_x)

        # collectibles
        for c in self.collectibles:
            c.draw(self.screen, self.scroll_x - shake_x)
        
        # powerups
        for p in self.powerups:
            p.draw(self.screen, self.scroll_x - shake_x)

        #ゴールラインの描画
        goal_rect = pygame.Rect(GOAL_X - self.scroll_x, 0, 50, self.world.height)
        pygame.draw.rect(self.screen, (255, 215, 0), goal_rect) #黄色にする

        #ガイド線(プレイ中でロープを出していない時だけ表示する)
        if self.state == "PLAYING" and self.rope is None:
            #今クリックしたらどこに刺さるか計算する
            target_x = self.get_rope_target()
            ceil_y = self.ceiling.get_ceiling_y(target_x)

            start_pos = (self.player.x - self.scroll_x, self.player.y)
            
            #発射可能なら水色、無理なら赤でガイド線を表示する
            if ceil_y is not None and ceil_y < self.player.y:
                #発射可能
                color = (0, 255, 255)
                end_pos = (target_x - self.scroll_x, ceil_y)
            else:
                #発射が無理だったら、100pxだけ表示
                color = (255, 0, 0)
                start_vec = pygame.Vector2(self.player.x, self.player.y)
                aim_vec = pygame.Vector2(0, -1).rotate(ROPE_ANGLE)
                end_vec = start_vec + aim_vec * 100

                start_pos = (self.player.x - self.scroll_x, self.player.y)
                end_pos = (end_vec.x - self.scroll_x, end_vec.y)
            
            pygame.draw.line(self.screen, color, start_pos, end_pos, 2)

        #プレイヤーとロープを表示
        if self.rope:
            self.rope.draw(self.screen, self.scroll_x - shake_x)
        self.player.draw(self.screen, self.scroll_x - shake_x, self.powerup_timer > 0)

        # パーティクルエフェクトを描画
        for particle in self.particles:
            particle.draw(self.screen, self.scroll_x - shake_x)

        #スコアやメッセージを表示
        # HUD: 距離 + コイン
        dist_text = self.font_small.render(f"DIST: {int(self.player.x)} / {GOAL_X}", True, (255, 255, 255))
        coin_text = self.font_small.render(f"COINS: {self.coin}", True, (255, 223, 0))
        score_text = self.font_small.render(f"SCORE: {self.score + self.speed_bonus}", True, (255, 255, 255))
        self.screen.blit(dist_text, (20, 20))
        self.screen.blit(coin_text, (20, 44))
        self.screen.blit(score_text, (20, 68))
        
        # コンボ表示（コンボが2以上の時のみ）
        if self.combo >= 2:
            combo_size = min(80, 40 + self.combo * 5)
            combo_font = pygame.font.SysFont(None, combo_size)
            combo_color = (255, min(255, int(100 + self.combo * 20)), 0)
            combo_text = combo_font.render(f"{self.combo}x COMBO!", True, combo_color)
            # 画面中央上部に表示
            combo_x = self.world.width // 2 - combo_text.get_width() // 2
            combo_y = 100
            # 影をつける
            shadow = combo_font.render(f"{self.combo}x COMBO!", True, (0, 0, 0))
            self.screen.blit(shadow, (combo_x + 3, combo_y + 3))
            self.screen.blit(combo_text, (combo_x, combo_y))
        
        # パワーアップ状態表示
        if self.powerup_timer > 0:
            powerup_text = self.font_small.render("POWER UP!", True, (255, 50, 255))
            flash = int((self.powerup_timer % 20) / 10)
            if flash == 0:
                self.screen.blit(powerup_text, (self.world.width - 150, 20))

        #状態ごとのメッセージ表示
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
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_p:
                        self.paused = not self.paused
                    if event.key == pygame.K_ESCAPE:
                        pygame.event.post(pygame.event.Event(pygame.QUIT))
            self.update()
            self.draw()
            self.clock.tick(60)

if __name__ == "__main__":
    AppMain().run()