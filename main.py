#ターザンロープアクションゲーム

import math
import random
import pygame

#ゲームバランスを調整するとき用の定数を定義
ROPE_ANGLE = 50        #ロープ発射角度
KICK_STRENGTH = 1.0    #ブーストの強さ
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

        #位置更新
        self.pos += self.vel * self.world.dt

    def draw(self, screen, scroll_x):
        draw_x = int(self.x - scroll_x)     #スクロール分を引く
        draw_y = int(self.y)
        pygame.draw.circle(screen, (255, 204, 153), (draw_x, draw_y), self.radius)
        #目をつけて、速度の正負によって向きをわかりやすくした
        eye_offset = 5 if self.vx >= 0 else -5
        pygame.draw.circle(screen, (0,0,0), (draw_x + eye_offset, draw_y - 4), 3)


class Spark:
    """小さなパーティクル効果（ロープ接続時など）"""
    def __init__(self, pos, vel, life=30):
        self.pos = pygame.Vector2(pos)
        self.vel = pygame.Vector2(vel)
        self.life = life
        self.max_life = life

    def update(self):
        # 軽い重力と減速
        self.vel += pygame.Vector2(0, 0.15)
        self.pos += self.vel
        self.life -= 1

    def draw(self, screen, scroll_x):
        if self.life <= 0:
            return
        alpha = int(255 * (self.life / max(1, self.max_life)))
        s = pygame.Surface((4, 4), pygame.SRCALPHA)
        s.fill((255, 215, 0, alpha))
        screen.blit(s, (int(self.pos.x - scroll_x), int(self.pos.y)))


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
        start = (int(self.anchor.x - scroll_x), int(self.anchor.y))
        end = (int(self.player.x - scroll_x), int(self.player.y))
        pygame.draw.line(screen, (34, 139, 34), start, end, 3)


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
            pygame.draw.rect(screen, (139, 69, 19), draw_rect) #茶色


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

        for i in range(start_i, end_i):
            base_x = i * spike_w - scroll_x     #ゲーム世界の絶対値座標-カメラ位置
            #ギザギザの三角形
            p1 = (base_x, self.world.height)
            p2 = (base_x + spike_w/2, self.y)       #トゲの先端
            p3 = (base_x + spike_w, self.world.height)
            pygame.draw.polygon(screen, (0, 100, 0), [p1, p2, p3])


class AppMain:
    def __init__(self):
        pygame.init()
        self.world = World(800, 600, gravity=0.25)
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
                    # 接続時の小さなエフェクト
                    for i in range(10):
                        vel = pygame.Vector2(random.uniform(-2, 2), random.uniform(-4, -1))
                        self.effects.append(Spark(self.rope.anchor, vel, life=random.randint(15, 35)))

        else:
            #マウスを離したらロープ解除
            self.rope = None

        #物理演算
        self.player.update()
        if self.rope:
            self.rope.update()

        # 天井との当たり判定（上下方向）
        ceil_y = self.ceiling.get_ceiling_y(self.player.x)
        if ceil_y is not None:
            ceiling_bottom = ceil_y
            if self.player.y - self.player.radius < ceiling_bottom:
                self.player.y = ceiling_bottom + self.player.radius
                if self.player.vy < 0:
                    self.player.vy = 0

        # 天井との当たり判定（左右方向）
        collision = self.ceiling.check_horizontal_collision(self.player)
        if collision:
            side, rect = collision
            if side == 'left':
                # 右側から衝突
                self.player.x = rect.left - self.player.radius
                if self.player.vx < 0:
                    self.player.vx = 0
            elif side == 'right':
                # 左側から衝突
                self.player.x = rect.right + self.player.radius
                if self.player.vx > 0:
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
        # グラデーション風の空背景
        for i in range(self.world.height):
            t = i / self.world.height
            r = int(135 * (1 - t) + 25 * t)
            g = int(206 * (1 - t) + 25 * t)
            b = int(235 * (1 - t) + 112 * t)
            pygame.draw.line(self.screen, (r, g, b), (0, i), (self.world.width, i))

        # パララックスクラウド
        for c in self.clouds:
            cx = c.x - self.scroll_x * 0.3
            cy = c.y
            pygame.draw.ellipse(self.screen, (255, 255, 255), (cx % (self.world.width + 200) - 100, cy, 140, 60))

        self.ceiling.draw(self.screen, self.scroll_x)
        self.spikes.draw(self.screen, self.scroll_x)

        #ゴールラインの描画
        # ゴールを点滅させて目立たせる
        glow = (math.sin(pygame.time.get_ticks() * 0.005) + 1) / 2
        goal_color = (int(255 * (0.6 + 0.4 * glow)), int(215 * (0.6 + 0.4 * glow)), 0)
        goal_rect = pygame.Rect(GOAL_X - self.scroll_x, 0, 50, self.world.height)
        pygame.draw.rect(self.screen, goal_color, goal_rect)

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
            self.rope.draw(self.screen, self.scroll_x)
        self.player.draw(self.screen, self.scroll_x)

        # エフェクト描画
        for e in self.effects:
            e.draw(self.screen, self.scroll_x)

        #スコアやメッセージを表示
        score_text = self.font.render(f"DIST: {self.score} / {GOAL_X}", True, (255, 255, 255))
        self.screen.blit(score_text, (20, 20))

        # 進捗バー
        bar_w = 300
        bar_h = 16
        bar_x = 20
        bar_y = 20 + 60
        ratio = max(0.0, min(1.0, self.player.x / max(1, GOAL_X)))
        pygame.draw.rect(self.screen, (50, 50, 50), (bar_x, bar_y, bar_w, bar_h))
        pygame.draw.rect(self.screen, (50, 205, 50), (bar_x, bar_y, int(bar_w * ratio), bar_h))
        pygame.draw.rect(self.screen, (255, 255, 255), (bar_x, bar_y, bar_w, bar_h), 2)

        # FPS 表示（小さなフォント）
        fps_text = self.font_small.render(f"FPS: {int(self.clock.get_fps())}", True, (255, 255, 255))
        self.screen.blit(fps_text, (self.world.width - 100, 10))

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