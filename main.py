#ターザンロープアクションゲーム

import math
import random
import pygame

#ゲームバランスを調整するとき用の定数を定義
ROPE_ANGLE = 50        #ロープ発射角度
KICK_STRENGTH = 2.2    #ブーストの強さ（爽快感アップ）
GOAL_X = 15000        #ゴール地点のX座標
TIME_LIMIT = 60        #制限時間（秒）
GRAVITY = 0.2          #重力（小さめでふわっと）
AIR_DRAG = 1.0         #空気抵抗（1.0に近いほど減速しない）

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

    def update(self):
        self.vel += self.world.gravity * self.world.dt

        #速度制限
        if self.vel.length() > 10:
            self.vel.scale_to_length(10)

        #ふわっとした操作感のための軽い空気抵抗
        self.vel *= AIR_DRAG

        #位置更新
        self.pos += self.vel * self.world.dt

    def draw(self, screen, scroll_x):
        draw_x = int(self.x - scroll_x)     #スクロール分を引く
        draw_y = int(self.y)
        
        # 速度に応じた色の変化
        speed = self.vel.length()
        color_intensity = int(min(255, 150 + speed * 10))
        player_color = (255, 220, 100 + int(speed * 5))
        
        # プレイヤーを描画（複数層のグロー効果）
        pygame.draw.circle(screen, (255, 200, 60), (draw_x, draw_y), self.radius + 4, 1)
        pygame.draw.circle(screen, (255, 160, 0), (draw_x, draw_y), self.radius + 2)
        pygame.draw.circle(screen, player_color, (draw_x, draw_y), self.radius)
        pygame.draw.circle(screen, (255, 255, 200), (draw_x, draw_y), self.radius - 2)
        
        # 目と口をつけて、表情を豊かに
        eye_offset = 6 if self.vx >= 0 else -6
        pygame.draw.circle(screen, (0, 0, 0), (draw_x + eye_offset, draw_y - 4), 2)
        pygame.draw.circle(screen, (255, 255, 255), (draw_x + eye_offset + 1, draw_y - 5), 1)


class Spark:
    """小さなパーティクル効果（ロープ接続時など）"""
    def __init__(self, pos, vel, life=30, color=(255, 215, 0), size=4):
        self.pos = pygame.Vector2(pos)
        self.vel = pygame.Vector2(vel)
        self.life = life
        self.max_life = life
        self.color = color
        self.size = size
        self.rotation = random.uniform(0, 360)
        self.rotation_speed = random.uniform(-10, 10)

    def update(self):
        # 軽い重力と減速
        self.vel += pygame.Vector2(0, 0.1) * (self.max_life / 30)  # 重力を柔軟に
        self.vel *= 0.98  # 空気抵抗
        self.pos += self.vel
        self.life -= 1
        self.rotation += self.rotation_speed

    def draw(self, screen, scroll_x):
        if self.life <= 0:
            return
        alpha = int(255 * (self.life / max(1, self.max_life)))
        progress = 1 - (self.life / max(1, self.max_life))
        
        # サイズが時間とともに変わる
        current_size = int(self.size * (1 + progress * 0.5))
        
        # 複数の円で立体感を出す
        s = pygame.Surface((current_size * 3, current_size * 3), pygame.SRCALPHA)
        
        # グロー層
        r, g, b = self.color
        glow_alpha = int(alpha * 0.3)
        glow_color = (r, g, b, glow_alpha)
        pygame.draw.circle(s, glow_color, (current_size + 1, current_size + 1), current_size + 2)
        
        # メイン層
        pygame.draw.circle(s, (r, g, b, alpha), (current_size + 1, current_size + 1), current_size)
        
        # ハイライト層
        highlight_color = (min(255, r + 50), min(255, g + 50), min(255, b + 50), alpha)
        pygame.draw.circle(s, highlight_color, (current_size + 1, current_size), current_size - 1)
        
        screen.blit(s, (int(self.pos.x - scroll_x - current_size - 1), int(self.pos.y - current_size - 1)))


class Rope:
    """ ロープ"""
    def __init__(self, anchor_x, anchor_y, player, world):
        self.world = world
        self.anchor = pygame.Vector2(anchor_x, anchor_y)
        self.player = player
        self.glow_intensity = 1.0

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
        
        # グロー効果を減速（エフェクト用）
        self.glow_intensity *= 0.95

    def draw(self, screen, scroll_x):
        start = (int(self.anchor.x - scroll_x), int(self.anchor.y))
        end = (int(self.player.x - scroll_x), int(self.player.y))
        
        # ロープを複数層で描画（美しいグロー効果）
        intensity = int(self.glow_intensity * 255)
        
        # 外側のグロー（目立つ色）
        glow_outer = (100 + intensity // 4, 200 + intensity // 5, 100)
        pygame.draw.line(screen, glow_outer, start, end, 8)
        
        # 中間層
        glow_mid = (50 + intensity // 3, 150 + intensity // 4, 50)
        pygame.draw.line(screen, glow_mid, start, end, 5)
        
        # ロープのコア（明るい色）
        rope_core = (100, 200, 100)
        pygame.draw.line(screen, rope_core, start, end, 3)
        
        # ハイライト
        pygame.draw.line(screen, (200, 255, 200), start, end, 1)


class CeilingMap:
    """ 天井マップ """
    def __init__(self, world):
        self.world = world
        self.blocks = [] 
        #スタート地点の天井を作る
        self.blocks.append(pygame.Rect(-200, 0, 800, 50))
        
        #15000px先まで天井を作る
        current_x = 600     #最初の天井のx座標
        while current_x < 15000:
            w = random.randint(60, 150)        #ランダムに天井の幅を決める
            h = random.randint(50, 200)         #ランダムに天井の高さを決める   
            self.blocks.append(pygame.Rect(current_x, 0, w, h))
            current_x += w + random.randint(250, 700) #天井と天井の間の隙間を作る

    def get_ceiling_y(self, x):         #指定したx座標の天井のy座標を返す
        for rect in self.blocks:
            if rect.left <= x <= rect.right:
                return rect.bottom
        return None

    def check_horizontal_collision(self, player):
        """天井ブロックの左右辺との横衝突判定。衝突情報を返す。
        Returns: (side, block_rect) or None
        side: 'left' または 'right'
        """
        for rect in self.blocks:
            # プレイヤーが天井ブロックのy範囲内か確認
            if player.y - player.radius < rect.bottom and player.y + player.radius > rect.top:
                # 左辺との衝突
                if player.x - player.radius < rect.left and player.x + player.radius > rect.left - 10:
                    return ('left', rect)
                # 右辺との衝突
                if player.x + player.radius > rect.right and player.x - player.radius < rect.right + 10:
                    return ('right', rect)
        return None

    def draw(self, screen, scroll_x):
        for rect in self.blocks:
            if rect.right - scroll_x < 0:
                continue
            if rect.left - scroll_x > self.world.width:
                continue
            draw_rect = pygame.Rect(rect.x - scroll_x, rect.y, rect.width, rect.height)
            
            # グラデーション風の茶色シェーディング
            base_color = (120, 60, 20)
            highlight_color = (160, 90, 30)
            shadow_color = (80, 40, 10)
            
            # メイン色
            pygame.draw.rect(screen, base_color, draw_rect)
            
            # ハイライト（上辺）
            pygame.draw.line(screen, highlight_color, 
                           (draw_rect.left, draw_rect.top), 
                           (draw_rect.right, draw_rect.top), 2)
            
            # シャドウ（下辺）
            pygame.draw.line(screen, shadow_color, 
                           (draw_rect.left, draw_rect.bottom - 1), 
                           (draw_rect.right, draw_rect.bottom - 1), 2)
            
            # 枠線を追加して立体感を出す
            pygame.draw.rect(screen, shadow_color, draw_rect, 1)


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
        #ギザギザを描く
        spike_w = 30
        start_i = int(scroll_x / spike_w)       #描き始めるのは何番目のトゲからか?
        end_i = start_i + int(self.world.width / spike_w) + 2       #何番目のトゲまで描けばいいか?(予備で2個追加)

        # 床の背景
        pygame.draw.rect(screen, (20, 80, 20), (0, self.y, self.world.width, self.world.height - self.y))
        
        for i in range(start_i, end_i):
            base_x = i * spike_w - scroll_x     #ゲーム世界の絶対値座標-カメラ位置
            #ギザギザの三角形（濃い緑）
            p1 = (base_x, self.world.height)
            p2 = (base_x + spike_w/2, self.y)       #トゲの先端
            p3 = (base_x + spike_w, self.world.height)
            
            # メイン色
            pygame.draw.polygon(screen, (0, 120, 0), [p1, p2, p3])
            
            # グロー効果（外枠）
            pygame.draw.line(screen, (100, 200, 100), p1, p2, 1)
            pygame.draw.line(screen, (100, 200, 100), p2, p3, 1)


class AppMain:
    def __init__(self):
        pygame.init()
        self.world = World(800, 600, gravity=GRAVITY)
        self.screen = pygame.display.set_mode((self.world.width, self.world.height))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont(None, 60)       #フォントを用意
        self.font_small = pygame.font.SysFont(None, 24)
        self.score = 0
        self.scroll_x = 0
        self.rope = None
        self.effects = []       # Spark 等のエフェクト
        self.clouds = [pygame.Vector2(random.randint(0, 12000), random.randint(20, 150)) for _ in range(8)]
        self.paused = False
        self.time_remaining = TIME_LIMIT  #残り時間
        self.shake_intensity = 0  # スクリーンシェイク用
        self.prev_player_pos = None  # トレイル生成用
        self.reset_game()       #ゲームオーバー後の再スタートに使えるように関数で用意
        self.state = "READY" #クリックでスタートするので、ゲーム開始前の状態を用意

    def reset_game(self):
        self.ceiling = CeilingMap(self.world)
        self.spikes = SpikeFloor(self.world)

        #スタート地点の天井の高さを調べる
        start_x = 200
        ceil_y = self.ceiling.get_ceiling_y(start_x)
        if ceil_y is None: ceil_y = 50      #もしスタート地点に天井がなかったら、高さを50にする
        
        self.player = Particle(start_x, ceil_y + 150, self.world)       #天井から150px下に配置
        #最初からぶら下がった状態でスタート
        self.rope = Rope(start_x, ceil_y, self.player, self.world)
        self.effects.clear()
        self.paused = False
        self.scroll_x = 0
        self.state = "PLAYING" #状態をプレイ中にする
        self.score = 0
        self.time_remaining = TIME_LIMIT  #残り時間をリセット
        self.shake_intensity = 0
        self.prev_player_pos = pygame.Vector2(self.player.x, self.player.y)

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

        # ポーズは run() の KEYDOWN でトグルされる
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
                ceil_y = self.ceiling.get_ceiling_y(target_x)
                
                #天井があるかつ自分より上にあったら発射成功
                if ceil_y is not None and ceil_y < self.player.y:
                    self.rope = Rope(target_x, ceil_y, self.player, self.world)
                    
                    #加速させる(接線方向に力を加える)
                    rope_vec = self.rope.anchor - self.player.pos   #プレイヤーから支点へのベクトル

                    if rope_vec.length() > 0:
                        normal = rope_vec.normalize()    #ロープ方向の単位ベクトル
                        tangent = normal.rotate(90)  #接線方向の単位ベクトル

                        if tangent.x < 0:
                            tangent =- tangent   #右向きにブーストしたいので、x成分が正になるようにする

                        self.player.vel += tangent * KICK_STRENGTH
                    
                    # 接続時の大量エフェクト（爽快感アップ）
                    self.shake_intensity = 3.0  # スクリーンシェイク
                    for i in range(20):  # パーティクル数を増加
                        vel = pygame.Vector2(random.uniform(-3, 3), random.uniform(-5, -1))
                        self.effects.append(Spark(self.rope.anchor, vel, life=random.randint(20, 40), 
                                                color=(255, 220, 100), size=5))
                    
                    # プレイヤー周辺にも粒が散る
                    for i in range(15):
                        vel = pygame.Vector2(random.uniform(-2.5, 2.5), random.uniform(-1, 3))
                        self.effects.append(Spark(self.player.pos, vel, life=random.randint(15, 35),
                                                color=(255, 150, 50), size=3))

        else:
            #マウスを離したらロープ解除
            self.rope = None

        #物理演算
        self.player.update()
        if self.rope:
            self.rope.update()
        
        # トレイルエフェクト（スウィング感を出す）
        if self.prev_player_pos is not None:
            dist = self.player.pos.distance_to(self.prev_player_pos)
            if dist > 2 and self.rope is not None:  # ロープ中かつ移動している
                trail_vel = pygame.Vector2(random.uniform(-0.5, 0.5), random.uniform(-0.5, 0.5))
                self.effects.append(Spark(self.player.pos, trail_vel, life=random.randint(10, 20),
                                        color=(200, 255, 150), size=2))
        
        self.prev_player_pos = pygame.Vector2(self.player.x, self.player.y)
        
        # スクリーンシェイクを減衰
        self.shake_intensity *= 0.9

        # 天井との当たり判定（上下方向）
        ceil_y = self.ceiling.get_ceiling_y(self.player.x)
        if ceil_y is not None:
            ceiling_bottom = ceil_y
            if self.player.y - self.player.radius < ceiling_bottom:
                self.player.y = ceiling_bottom + self.player.radius
                if self.player.vy < 0:
                    # 天井に衝突した時のエフェクト
                    impact_strength = abs(self.player.vy)
                    for i in range(int(impact_strength * 3)):
                        vel = pygame.Vector2(random.uniform(-2, 2), random.uniform(-3, 0))
                        self.effects.append(Spark(pygame.Vector2(self.player.x, ceiling_bottom), vel, 
                                                life=random.randint(10, 25), color=(150, 100, 50), size=2))
                    self.shake_intensity = max(self.shake_intensity, impact_strength * 0.5)
                    self.player.vy = 0

        # 天井との当たり判定（左右方向）
        collision = self.ceiling.check_horizontal_collision(self.player)
        if collision:
            side, rect = collision
            if side == 'left':
                # 右側から衝突
                self.player.x = rect.left - self.player.radius
                impact_strength = abs(self.player.vx)
                if self.player.vx < 0:
                    # 左側の壁に衝突したエフェクト
                    for i in range(int(impact_strength * 2)):
                        vel = pygame.Vector2(random.uniform(-1, 2), random.uniform(-2, 2))
                        self.effects.append(Spark(pygame.Vector2(rect.left, self.player.y), vel,
                                                life=random.randint(10, 20), color=(150, 100, 50), size=2))
                    self.shake_intensity = max(self.shake_intensity, impact_strength * 0.3)
                    self.player.vx = 0
            elif side == 'right':
                # 左側から衝突
                self.player.x = rect.right + self.player.radius
                impact_strength = abs(self.player.vx)
                if self.player.vx > 0:
                    # 右側の壁に衝突したエフェクト
                    for i in range(int(impact_strength * 2)):
                        vel = pygame.Vector2(random.uniform(-2, 1), random.uniform(-2, 2))
                        self.effects.append(Spark(pygame.Vector2(rect.right, self.player.y), vel,
                                                life=random.randint(10, 20), color=(150, 100, 50), size=2))
                    self.shake_intensity = max(self.shake_intensity, impact_strength * 0.3)
                    self.player.vx = 0

        # エフェクト更新
        for e in list(self.effects):
            e.update()
            if e.life <= 0:
                try:
                    self.effects.remove(e)
                except ValueError:
                    pass

        #トゲに当たったらゲームオーバー
        if self.spikes.check_hit(self.player):
            self.state = "GAMEOVER"

        #タイマーを更新（1フレーム = 1/60秒）
        self.time_remaining -= 1/60
        if self.time_remaining <= 0:
            self.time_remaining = 0
            self.state = "GAMEOVER"

        #スクロールの処理
        #プレイヤーが画面の左から1/3より右に行ったら、カメラも右に動かす
        target_scroll = self.player.x - self.world.width / 3
        self.scroll_x += (target_scroll - self.scroll_x) * 0.1      #0.1をかけて少し遅れてついてくるようにする

        #右に進んだ最大距離をスコアにする
        if self.player.x > self.score:
            self.score = int(self.player.x)
        
        #ゴール判定
        if self.player.x > GOAL_X:
            self.state = "GOAL"

    def draw(self):
        # スクリーンシェイク（画面揺らし）
        shake_x = random.uniform(-self.shake_intensity, self.shake_intensity) if self.shake_intensity > 0.1 else 0
        shake_y = random.uniform(-self.shake_intensity, self.shake_intensity) if self.shake_intensity > 0.1 else 0
        
        # グラデーション風の空背景（より鮮やかに）
        for i in range(self.world.height):
            t = i / self.world.height
            r = int(100 * (1 - t) + 50 * t)
            g = int(180 * (1 - t) + 100 * t)
            b = int(255 * (1 - t) + 140 * t)
            pygame.draw.line(self.screen, (r, g, b), (0, i), (self.world.width, i))
        
        # 遠景の山々（視差効果）
        for i, c in enumerate(self.clouds):
            mountain_y = 100 + i * 30
            mountain_height = 50 + i * 10
            mountain_x = c.x - (self.scroll_x - shake_x) * 0.15
            mountain_color = (min(255, int(100 + 20 * i)), min(255, int(150 + 20 * i)), min(255, int(120 + 20 * i)))
            # 山の形状を簡単に
            points = [
                (int(mountain_x - 100), self.world.height),
                (int(mountain_x), int(mountain_y - mountain_height)),
                (int(mountain_x + 100), self.world.height)
            ]
            pygame.draw.polygon(self.screen, mountain_color, points)

        # パララックスクラウド（より美しく）
        for i, c in enumerate(self.clouds):
            cx = c.x - (self.scroll_x - shake_x) * 0.3
            cy = c.y
            
            # 複数の円でクラウド形状を作成
            cloud_x = cx % (self.world.width + 200) - 100
            
            # クラウドのグロー
            pygame.draw.ellipse(self.screen, (200, 200, 200), (cloud_x - 10, cy - 10, 160, 80))
            # メインクラウド
            pygame.draw.ellipse(self.screen, (255, 255, 255), (cloud_x, cy, 140, 60))
            # ハイライト
            pygame.draw.arc(self.screen, (200, 220, 255), (cloud_x + 10, cy - 20, 120, 50), 1, 2, 2)

        # 有効なスクロール値（シェイク適用）
        effective_scroll = self.scroll_x - shake_x
        
        self.ceiling.draw(self.screen, effective_scroll)
        self.spikes.draw(self.screen, effective_scroll)

        #ゴールラインの描画
        # ゴールを点滅させて目立たせる
        glow = (math.sin(pygame.time.get_ticks() * 0.005) + 1) / 2
        goal_color = (int(255 * (0.6 + 0.4 * glow)), int(215 * (0.6 + 0.4 * glow)), 0)
        goal_rect = pygame.Rect(GOAL_X - effective_scroll, 0, 50, self.world.height)
        pygame.draw.rect(self.screen, goal_color, goal_rect)

        #ガイド線(プレイ中でロープを出していない時だけ表示する)
        if self.state == "PLAYING" and self.rope is None:
            #今クリックしたらどこに刺さるか計算する
            target_x = self.get_rope_target()
            ceil_y = self.ceiling.get_ceiling_y(target_x)

            start_pos = (self.player.x - effective_scroll, self.player.y)
            
            #発射可能なら水色、無理なら赤でガイド線を表示する
            if ceil_y is not None and ceil_y < self.player.y:
                #発射可能
                color = (0, 255, 255)
                end_pos = (target_x - effective_scroll, ceil_y)
            else:
                #発射が無理だったら、100pxだけ表示
                color = (255, 0, 0)
                start_vec = pygame.Vector2(self.player.x, self.player.y)
                aim_vec = pygame.Vector2(0, -1).rotate(ROPE_ANGLE)
                end_vec = start_vec + aim_vec * 100

                start_pos = (self.player.x - effective_scroll, self.player.y)
                end_pos = (end_vec.x - effective_scroll, end_vec.y)
            
            pygame.draw.line(self.screen, color, start_pos, end_pos, 2)

        #プレイヤーとロープを表示
        if self.rope:
            self.rope.draw(self.screen, effective_scroll)
        self.player.draw(self.screen, effective_scroll)

        # エフェクト描画
        for e in self.effects:
            e.draw(self.screen, effective_scroll)

        # HUD背景（半透明）
        hud_surface = pygame.Surface((self.world.width, 100), pygame.SRCALPHA)
        pygame.draw.rect(hud_surface, (0, 0, 0, 100), (0, 0, self.world.width, 100))
        self.screen.blit(hud_surface, (0, 0))
        
        # スコア表示（より大きく目立つ）
        score_text = self.font.render(f"DISTANCE: {self.score}", True, (100, 255, 100))
        score_shadow = self.font.render(f"DISTANCE: {self.score}", True, (0, 0, 0))
        self.screen.blit(score_shadow, (22, 22))
        self.screen.blit(score_text, (20, 20))
        
        # ゴールまでの距離を表示
        remaining = max(0, GOAL_X - self.score)
        remaining_pct = max(0, min(100, (1 - self.score / GOAL_X) * 100))
        goal_text = self.font_small.render(f"Goal: {remaining} ({int(remaining_pct)}%)", True, (200, 200, 100))
        self.screen.blit(goal_text, (20, 70))
        
        # タイマー表示（残り時間が少ないと赤くなる）
        time_color = (100, 255, 100) if self.time_remaining > 10 else (255, 100, 100)
        time_text = self.font.render(f"TIME: {max(0, int(self.time_remaining))}", True, time_color)
        time_shadow = self.font.render(f"TIME: {max(0, int(self.time_remaining))}", True, (0, 0, 0))
        self.screen.blit(time_shadow, (self.world.width - 222, 22))
        self.screen.blit(time_text, (self.world.width - 220, 20))

        # 進捗バー（より美しく）
        bar_w = 300
        bar_h = 20
        bar_x = 20
        bar_y = 20 + 100
        ratio = max(0.0, min(1.0, self.player.x / max(1, GOAL_X)))
        
        # バーの背景（グラデーション風）
        pygame.draw.rect(self.screen, (30, 30, 30), (bar_x - 2, bar_y - 2, bar_w + 4, bar_h + 4))
        pygame.draw.rect(self.screen, (50, 50, 50), (bar_x, bar_y, bar_w, bar_h))
        
        # バー（グロー付き）
        bar_fill_w = int(bar_w * ratio)
        if bar_fill_w > 0:
            pygame.draw.rect(self.screen, (100, 255, 100), (bar_x - 1, bar_y - 1, bar_fill_w + 2, bar_h + 2))
            pygame.draw.rect(self.screen, (100, 200, 100), (bar_x, bar_y, bar_fill_w, bar_h))
        
        # バーの枠線
        pygame.draw.rect(self.screen, (200, 255, 200), (bar_x, bar_y, bar_w, bar_h), 2)

        # FPS 表示（小さなフォント、角に配置）
        fps_text = self.font_small.render(f"FPS: {int(self.clock.get_fps())}", True, (200, 200, 200))
        self.screen.blit(fps_text, (self.world.width - 120, self.world.height - 25))

        # 状態ごとのメッセージ表示（オーバーレイ背景付き）
        if self.state == "READY":
            # 半透明の背景
            overlay = pygame.Surface((self.world.width, self.world.height), pygame.SRCALPHA)
            pygame.draw.rect(overlay, (0, 0, 0, 150), (0, 0, self.world.width, self.world.height))
            self.screen.blit(overlay, (0, 0))
            
            msg = self.font.render("CLICK TO START", True, (100, 255, 100))
            msg_shadow = self.font.render("CLICK TO START", True, (0, 100, 0))
            self.screen.blit(msg_shadow, (self.world.width/2 - 202, self.world.height/2 + 2))
            self.screen.blit(msg, (self.world.width/2 - 200, self.world.height/2))
            
            # サブテキスト
            sub_text = self.font_small.render("Swing from ceiling to ceiling and reach the goal!", True, (200, 200, 200))
            self.screen.blit(sub_text, (self.world.width/2 - 200, self.world.height/2 + 70))

        elif self.state == "GAMEOVER":
            # 半透明の背景
            overlay = pygame.Surface((self.world.width, self.world.height), pygame.SRCALPHA)
            pygame.draw.rect(overlay, (0, 0, 0, 150), (0, 0, self.world.width, self.world.height))
            self.screen.blit(overlay, (0, 0))
            
            msg = self.font.render("GAME OVER", True, (255, 100, 100))
            msg_shadow = self.font.render("GAME OVER", True, (100, 0, 0))
            self.screen.blit(msg_shadow, (self.world.width/2 - 132, self.world.height/2 + 2))
            self.screen.blit(msg, (self.world.width/2 - 130, self.world.height/2))
            
            # スコア表示
            score_msg = self.font_small.render(f"Distance: {self.score}m", True, (200, 200, 200))
            self.screen.blit(score_msg, (self.world.width/2 - 80, self.world.height/2 + 70))
            
            retry_msg = self.font_small.render("Click to retry", True, (150, 150, 255))
            self.screen.blit(retry_msg, (self.world.width/2 - 70, self.world.height/2 + 110))
            
        elif self.state == "GOAL":
            # 半透明の背景
            overlay = pygame.Surface((self.world.width, self.world.height), pygame.SRCALPHA)
            pygame.draw.rect(overlay, (0, 0, 0, 150), (0, 0, self.world.width, self.world.height))
            self.screen.blit(overlay, (0, 0))
            
            msg = self.font.render("GOAL!!", True, (255, 255, 100))
            msg_shadow = self.font.render("GOAL!!", True, (200, 150, 0))
            self.screen.blit(msg_shadow, (self.world.width/2 - 82, self.world.height/2 + 2))
            self.screen.blit(msg, (self.world.width/2 - 80, self.world.height/2))
            
            # 最終スコア
            score_msg = self.font_small.render(f"Distance: {self.score}m", True, (200, 255, 200))
            self.screen.blit(score_msg, (self.world.width/2 - 80, self.world.height/2 + 70))
            
            retry_msg = self.font_small.render("Click to play again", True, (255, 200, 100))
            self.screen.blit(retry_msg, (self.world.width/2 - 100, self.world.height/2 + 110))
        
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