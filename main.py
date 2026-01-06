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
        self.vy += 0.2
        
        #空気抵抗
        self.vx *= 0.99
        self.vy *= 0.99

        #速度分だけ位置を動かす
        self.x += self.vx
        self.y += self.vy

    def draw(self, screen):
        pygame.draw.circle(screen, (255, 100, 100), (int(self.x), int(self.y)), 8)


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


def get_ceiling_y(x):
    """ 指定したx座標の天井の高さを返す関数 """
    # 今は単純に、どこでも高さ50とする
    return 50

def main():
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    clock = pygame.time.Clock()

    #主人公を作る
    player = Particle(200, 300)
    
    #バネと支点を入れるリスト
    springs = []
    fixed_points = []

    while True:
        screen.fill((200, 255, 255))

        #緑色の四角で天井を描いておく
        pygame.draw.rect(screen, (34, 139, 34), (0, 0, 800, 50))

        # --- イベント処理 ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return

            #マウスを押した瞬間ロープ発射
            if event.type == pygame.MOUSEBUTTONDOWN:
                # 1. 天井の高さを調べる（今はどこでも50）
                ceil_y = get_ceiling_y(player.x)
                
                # 2. プレイヤーから天井までの距離 (高さ)
                height_diff = player.y - ceil_y
                
                # 天井より上にいたら発射できない
                if height_diff > 0:
                    # 3. 角度計算 (50度をラジアンに変換)
                    angle_deg = 50
                    angle_rad = math.radians(angle_deg)
                    
                    # 4. 三角関数で「横にどれくらい先か(dx)」を計算
                    # dx = 高さ * tan(角度)
                    dx = height_diff * math.tan(angle_rad)
                    
                    target_x = player.x + dx
                    
                    # 5. 支点を作成
                    anchor = FixedMass(target_x, ceil_y)
                    fixed_points.append(anchor)

                    # 6. バネを作成
                    # 距離は三平方の定理で計算 (current_dist)
                    dist = math.sqrt(dx*dx + height_diff*height_diff)
                    rope = Spring(player, anchor, dist, k=0.5)
                    springs.append(rope)

                    # 【変更点2】ブースト（加速）機能！
                    # ロープがついた瞬間、少しだけ速度を足してあげる
                    # 接線方向（ロープと直角な方向）に力を加えるのが物理的に正しいですが
                    # ここではゲーム的に「進行方向に加速」するだけでも十分です！
                    player.vx += 4.0 
                    player.vy -= 2.0 # 少し体を持ち上げる

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