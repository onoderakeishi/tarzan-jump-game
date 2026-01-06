import pygame
import math

# --- クラス定義 ---
class Particle:
    """ 主人公のボール """
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.vx = 0
        self.vy = 0
        self.mass = 1.0

    def update(self):
        #重力を加える
        self.vy += 0.5 
        
        #空気抵抗
        self.vx *= 0.99
        self.vy *= 0.99

        #速度分だけ位置を動かす
        self.x += self.vx
        self.y += self.vy

    def draw(self, screen):
        pygame.draw.circle(screen, (255, 100, 100), (int(self.x), int(self.y)), 15)


class FixedMass(Particle):
    """ 天井の支点 """
    def update(self):
        pass


class Spring:
    """ ロープ """
    def __init__(self, p1, p2, length, k):
        self.p1 = p1 #主人公のボール
        self.p2 = p2 #支点
        self.length = length #自然長
        self.k = k #バネ定数

    def update(self):
        #2点間の距離
        dx = self.p2.x - self.p1.x
        dy = self.p2.y - self.p1.y
        dist = math.sqrt(dx*dx + dy*dy)

        #ゼロで割り防止
        if dist == 0: return

        #フックの法則
        diff = dist - self.length
        force = self.k * diff

        #力をX成分とY成分に分解
        fx = force * (dx / dist)
        fy = force * (dy / dist)

        #力を加える
        self.p1.vx += fx
        self.p1.vy += fy

    def draw(self, screen):
        pygame.draw.line(screen, (0, 200, 0), 
                         (int(self.p1.x), int(self.p1.y)), 
                         (int(self.p2.x), int(self.p2.y)), 4)


def main():
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    clock = pygame.time.Clock()

    #主人公を作る
    player = Particle(400, 300)
    
    #バネと支点を入れるリスト
    springs = []
    fixed_points = []

    while True:
        screen.fill((200, 255, 255))

        # --- イベント処理 ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return

            #マウスを押した瞬間ロープ発射
            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = pygame.mouse.get_pos()
                
                #クリックした場所に支点を作る
                anchor = FixedMass(mx, my)
                fixed_points.append(anchor)

                #現在の主人公との距離を計算
                dx = anchor.x - player.x
                dy = anchor.y - player.y
                current_dist = math.sqrt(dx*dx + dy*dy)

                #その距離でバネをつなぐ
                rope = Spring(player, anchor, current_dist, k=0.5) 
                springs.append(rope)

            #マウスを離した瞬間ロープ解除
            if event.type == pygame.MOUSEBUTTONUP:
                springs.clear()
                fixed_points.clear()

        
        # --- 物理演算 ---
        for s in springs:
            s.update()
        
        #主人公を動かす
        player.update()

        #床の代わり（下に落ちないように仮設置）
        if player.y > 580:
            player.y = 580
            player.vy *= -0.5

        # --- 描画処理 ---
        for s in springs:
            s.draw(screen)
        
        for fp in fixed_points:
            # 支点を小さな黒丸で描く
            pygame.draw.circle(screen, (0,0,0), (int(fp.x), int(fp.y)), 5)

        player.draw(screen)

        pygame.display.update()
        clock.tick(60)

if __name__ == "__main__":
    main()