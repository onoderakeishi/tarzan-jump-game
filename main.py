import math
import random
import pygame

#定数定義
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
GRAVITY = 0.25
ROPE_ANGLE = 50     #常に斜め50度上を狙うようにした
KICK_STRENGTH = 2   #ブーストの強さ
GOAL_X = 10000      #ゴールまでの距離

#クラス定義
class Particle:
    """ 主人公 """
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.vx = 0
        self.vy = 0
        self.radius = 12

    def update(self):
        self.vy += GRAVITY      #重力をかける

        #速度制限
        speed = math.sqrt(self.vx**2 + self.vy**2)
        if speed > 18.0:
            ratio = 18.0 / speed
            self.vx *= ratio
            self.vy *= ratio

        self.x += self.vx
        self.y += self.vy

    def draw(self, screen, scroll_x):
        draw_x = int(self.x - scroll_x)     #スクロール分を引く
        draw_y = int(self.y)
        pygame.draw.circle(screen, (255, 204, 153), (draw_x, draw_y), self.radius)
        #目をつけて、速度の正負によって向きをわかりやすくした
        eye_offset = 5 if self.vx >= 0 else -5
        pygame.draw.circle(screen, (0,0,0), (draw_x + eye_offset, draw_y - 4), 3)


class Rope:
    """ ロープ"""
    def __init__(self, anchor_x, anchor_y, player):
        self.anchor_x = anchor_x
        self.anchor_y = anchor_y
        self.player = player

        #ロープの長さは、ロープがかかった瞬間の距離で固定します
        dx = player.x - anchor_x
        dy = player.y - anchor_y
        self.length = math.sqrt(dx*dx + dy*dy)
        if self.length < 10:
            self.length = 10       #ロープの長さが0にならないようにする

    def update(self):
        #現在のプレイヤーと支点の距離を測る
        dx = self.player.x - self.anchor_x
        dy = self.player.y - self.anchor_y
        dist = math.sqrt(dx*dx + dy*dy)

        #もしロープの長さより遠くに行こうとした場合
        if dist > self.length:
            #強制的にプレイヤーの位置を引き戻す
            ratio = self.length / dist
            self.player.x = self.anchor_x + dx * ratio
            self.player.y = self.anchor_y + dy * ratio

            #ロープ方向の速度成分を消す
            nx = dx / dist  #ロープ方向の単位ベクトル
            ny = dy / dist  #ロープ方向の単位ベクトル
            dot = self.player.vx * nx + self.player.vy * ny #内積で速度成分を計算
            if dot > 0: #外に向かう速度成分があれば消す
                self.player.vx -= nx * dot
                self.player.vy -= ny * dot

    def draw(self, screen, scroll_x):
        start = (int(self.anchor_x - scroll_x), int(self.anchor_y))
        end = (int(self.player.x - scroll_x), int(self.player.y))
        pygame.draw.line(screen, (34, 139, 34), start, end, 3)
        pygame.draw.circle(screen, (50, 205, 50), start, 6) #支点を描く


class CeilingMap:
    """ 天井マップ """
    def __init__(self):
        self.blocks = [] 
        #スタート地点の天井を作る
        self.blocks.append(pygame.Rect(-200, 0, 800, 50))
        
        #12000px先まで天井を作る
        current_x = 600     #最初の天井のx座標
        while current_x < 12000:
            w = random.randint(100, 350)        #ランダムに天井の幅を決める
            h = random.randint(50, 200)         #ランダムに天井の高さを決める   
            self.blocks.append(pygame.Rect(current_x, 0, w, h))
            current_x += w + random.randint(50, 200) #天井と天井の間の隙間を作る

    def get_ceiling_y(self, x):         #指定したx座標の天井のy座標を返す
        for rect in self.blocks:
            if rect.left <= x <= rect.right:
                return rect.bottom
        return None

    def draw(self, screen, scroll_x):
        for rect in self.blocks:
            if rect.right - scroll_x < 0:
                continue
            if rect.left - scroll_x > SCREEN_WIDTH:
                continue
            draw_rect = pygame.Rect(rect.x - scroll_x, rect.y, rect.width, rect.height)
            pygame.draw.rect(screen, (139, 69, 19), draw_rect) #茶色


class SpikeFloor:
    """ トゲトゲの床 """
    def __init__(self):
        self.y = SCREEN_HEIGHT - 30 #下から30px

    def check_hit(self, player):
        #プレイヤーの下端がとげより下に行ったらTrue(とげに当たった判定)を返す
        if player.y + player.radius > self.y + 10:
            return True
        return False

    def draw(self, screen, scroll_x):
        #ギザギザを描く
        spike_w = 30
        start_i = int(scroll_x / spike_w)       #描き始めるのは何番目のトゲからか?
        end_i = start_i + int(SCREEN_WIDTH / spike_w) + 2       #何番目のトゲまで描けばいいか?(予備で2個追加)

        for i in range(start_i, end_i):
            base_x = i * spike_w - scroll_x     #ゲーム世界の絶対値座標-カメラ位置
            #ギザギザの三角形
            p1 = (base_x, SCREEN_HEIGHT)
            p2 = (base_x + spike_w/2, self.y)       #トゲの先端
            p3 = (base_x + spike_w, SCREEN_HEIGHT)
            pygame.draw.polygon(screen, (0, 100, 0), [p1, p2, p3])


class AppMain:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont(None, 60)       #フォントを用意
        self.score = 0
        self.scroll_x = 0
        self.rope = None
        self.reset_game()       #ゲームオーバー後の再スタートに使えるように関数で用意
        self.state = "READY" #クリックでスタートするので、ゲーム開始前の状態を用意

    def reset_game(self):
        self.ceiling = CeilingMap()
        self.spikes = SpikeFloor()

        #スタート地点の天井の高さを調べる
        start_x = 200
        ceil_y = self.ceiling.get_ceiling_y(start_x)
        if ceil_y is None: ceil_y = 50      #もしスタート地点に天井がなかったら、高さを50にする
        
        self.player = Particle(start_x, ceil_y + 150)       #天井から150px下に配置
        #最初からぶら下がった状態でスタート
        self.rope = Rope(start_x, ceil_y, self.player)
        
        self.scroll_x = 0
        self.state = "PLAYING" #状態をプレイ中にする
        self.score = 0

    def update(self):
        #ESCキーで終了
        key_pressed = pygame.key.get_pressed()
        if key_pressed[pygame.K_ESCAPE]:
            pygame.event.post(pygame.event.Event(pygame.QUIT))

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

        # --- 入力処理 ---
        mouse_pressed = pygame.mouse.get_pressed()[0]
        
        if mouse_pressed:
            #クリックしていて、ロープがまだない場合
            if self.rope is None:
                #狙う場所を計算(斜め50度)
                angle_rad = math.radians(ROPE_ANGLE)
                dy = self.player.y - 100 # とりあえず高さ100px上を目指す
                if dy < 10: dy = 10
                dx = dy / math.tan(angle_rad) # タンジェントで横距離を出す
                target_x = self.player.x + dx
                
                #そこに天井があるか確認する
                ceil_y = self.ceiling.get_ceiling_y(target_x)
                
                #天井があるかつ自分より上にあったら発射成功
                if ceil_y is not None and ceil_y < self.player.y:
                    self.rope = Rope(target_x, ceil_y, self.player)
                    
                    #加速させる(接線方向に力を加える)
                    diff_x = self.player.x - target_x
                    diff_y = self.player.y - ceil_y
                    dist = math.sqrt(diff_x**2 + diff_y**2)
                    
                    if dist > 0:
                        tan_x = -diff_y / dist
                        tan_y = diff_x / dist
                        #常に右側に向くように符号調整
                        if tan_x < 0:
                            tan_x = -tan_x
                            tan_y = -tan_y
                            
                        self.player.vx += tan_x * KICK_STRENGTH
                        self.player.vy += tan_y * KICK_STRENGTH

        else:
            #マウスを離したらロープ解除
            self.rope = None

        #物理演算
        self.player.update()
        if self.rope:
            self.rope.update()

        #トゲに当たったらゲームオーバー
        if self.spikes.check_hit(self.player):
            self.state = "GAMEOVER"

        #スクロールの処理
        #プレイヤーが画面の左から1/3より右に行ったら、カメラも右に動かす
        target_scroll = self.player.x - SCREEN_WIDTH / 3
        self.scroll_x += (target_scroll - self.scroll_x) * 0.1      #0.1をかけて少し遅れてついてくるようにする

        #右に進んだ最大距離をスコアにする
        if self.player.x > self.score:
            self.score = int(self.player.x)
        
        #ゴール判定
        if self.player.x > GOAL_X:
            self.state = "GOAL"

    def draw(self):
        self.screen.fill((135, 206, 235)) #背景は空色にする

        self.ceiling.draw(self.screen, self.scroll_x)
        self.spikes.draw(self.screen, self.scroll_x)

        #ゴールラインの描画
        goal_rect = pygame.Rect(GOAL_X - self.scroll_x, 0, 50, SCREEN_HEIGHT)
        pygame.draw.rect(self.screen, (255, 215, 0), goal_rect) #黄色にする

        #ガイド線(プレイ中でロープを出していない時だけ表示する)
        if self.state == "PLAYING" and self.rope is None:
            #今クリックしたらどこに刺さるかを、updateと同じ計算で求める
            angle_rad = math.radians(ROPE_ANGLE)
            dy = self.player.y - 100
            dy = max(dy, 10)
            dx = dy / math.tan(angle_rad)
            target_x = self.player.x + dx
            
            ceil_y = self.ceiling.get_ceiling_y(target_x)
            
            start_pos = (self.player.x - self.scroll_x, self.player.y)
            
            #発射可能なら水色、無理なら赤でガイド線を表示する
            if ceil_y is not None and ceil_y < self.player.y:
                color = (0, 255, 255) #発射可能
                end_pos = (target_x - self.scroll_x, ceil_y)
            else:
                color = (255, 0, 0) #発射無理
                end_pos = (target_x - self.scroll_x, self.player.y - dy)
            
            pygame.draw.line(self.screen, color, start_pos, end_pos, 2)

        #プレイヤーとロープを表示
        if self.rope:
            self.rope.draw(self.screen, self.scroll_x)
        self.player.draw(self.screen, self.scroll_x)

        #スコアやメッセージを表示
        score_text = self.font.render(f"DIST: {self.score} / {GOAL_X}", True, (255, 255, 255))
        self.screen.blit(score_text, (20, 20))

        #状態ごとのメッセージ表示
        if self.state == "READY":
            msg = self.font.render("CLICK TO START", True, (0, 100, 0))
            self.screen.blit(msg, (SCREEN_WIDTH/2 - 200, SCREEN_HEIGHT/2))

        elif self.state == "GAMEOVER":
            msg = self.font.render("GAME OVER", True, (255, 0, 0))
            self.screen.blit(msg, (SCREEN_WIDTH/2 - 130, SCREEN_HEIGHT/2))
            
        elif self.state == "GOAL":
            msg = self.font.render("GOAL!!", True, (255, 215, 0))
            self.screen.blit(msg, (SCREEN_WIDTH/2 - 80, SCREEN_HEIGHT/2))

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