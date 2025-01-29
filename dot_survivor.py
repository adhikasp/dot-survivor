import pygame
import random
import math

# Initialize Pygame
pygame.init()

# Constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
PLAYER_SPEED = 5
ENEMY_SPEED = 2
PROJECTILE_SPEED = 7
ZOOM_SPEED = 0.98  # Zoom out by 2% every second
MIN_ZOOM = 0.2  # Maximum zoom out (20% of original size)
INITIAL_WORLD_SIZE = 800  # Starting world size (same as screen)
MAX_WORLD_SIZE = 4000    # Maximum world size when fully zoomed out

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)

# Set up the display
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Dot Survivors")
clock = pygame.time.Clock()

# Add new constants after the existing ones
UPGRADES = [
    "Split Shot",
    "Chain Shot",
    "Explosion Shot"
]

class Camera:
    def __init__(self):
        self.zoom = 1.0
        self.x = SCREEN_WIDTH // 2
        self.y = SCREEN_HEIGHT // 2

    def apply_zoom(self, dt):
        self.zoom = max(MIN_ZOOM, self.zoom * (ZOOM_SPEED ** dt))

    def world_to_screen(self, x, y):
        # Convert world coordinates to screen coordinates
        screen_x = (x - self.x) * self.zoom + SCREEN_WIDTH // 2
        screen_y = (y - self.y) * self.zoom + SCREEN_HEIGHT // 2
        return screen_x, screen_y

    def screen_to_world(self, screen_x, screen_y):
        # Convert screen coordinates to world coordinates
        x = (screen_x - SCREEN_WIDTH // 2) / self.zoom + self.x
        y = (screen_y - SCREEN_HEIGHT // 2) / self.zoom + self.y
        return x, y

class Player:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.radius = 20
        self.speed = PLAYER_SPEED
        self.projectiles = []
        self.last_shot = 0
        self.shoot_delay = 500  # Milliseconds between shots
        self.upgrades = {
            "Split Shot": 0,
            "Chain Shot": 0,
            "Explosion Shot": 0
        }

    def move(self, keys, camera):
        if keys[pygame.K_w]: self.y -= self.speed
        if keys[pygame.K_s]: self.y += self.speed
        if keys[pygame.K_a]: self.x -= self.speed
        if keys[pygame.K_d]: self.x += self.speed

    def shoot(self):
        current_time = pygame.time.get_ticks()
        if current_time - self.last_shot > self.shoot_delay:
            # Create initial projectile
            projectile = Projectile(self.x, self.y)
            
            # Apply upgrades
            projectile.chain_count = self.upgrades["Chain Shot"]
            projectile.explosion_radius = self.upgrades["Explosion Shot"] * 30
            
            # Add split shots
            self.projectiles.append(projectile)
            split_count = self.upgrades["Split Shot"]
            if split_count > 0:
                angle = math.atan2(projectile.dy, projectile.dx)
                spread = 0.2  # Spread angle in radians
                for i in range(split_count):
                    # Only add one additional projectile per level
                    new_angle = angle + spread * (i + 1)
                    self.projectiles.append(Projectile(self.x, self.y, new_angle))
            
            self.last_shot = current_time

    def draw(self, screen, camera):
        screen_x, screen_y = camera.world_to_screen(self.x, self.y)
        pygame.draw.circle(screen, BLUE, (int(screen_x), int(screen_y)), 
                         int(self.radius * camera.zoom))

class Enemy:
    def __init__(self, camera, player):
        self.radius = 15
        
        # Spawn enemies in a circle around the player
        spawn_distance = 800  # Distance from player to spawn enemies
        angle = random.uniform(0, 2 * math.pi)
        
        self.x = player.x + math.cos(angle) * spawn_distance
        self.y = player.y + math.sin(angle) * spawn_distance
        
        self.speed = ENEMY_SPEED

    def move_towards_player(self, player):
        dx = player.x - self.x
        dy = player.y - self.y
        dist = math.sqrt(dx * dx + dy * dy)
        if dist != 0:
            self.x += (dx / dist) * self.speed
            self.y += (dy / dist) * self.speed

    def draw(self, screen, camera):
        screen_x, screen_y = camera.world_to_screen(self.x, self.y)
        pygame.draw.circle(screen, RED, (int(screen_x), int(screen_y)), 
                         int(self.radius * camera.zoom))

class Projectile:
    def __init__(self, x, y, angle=None):
        self.x = x
        self.y = y
        self.speed = PROJECTILE_SPEED
        self.radius = 5
        self.chain_count = 0  # Number of remaining chains
        self.split_count = 0  # Number of splits
        self.explosion_radius = 0  # Explosion radius (0 means no explosion)
        
        # If angle is provided, use it; otherwise shoot towards mouse
        if angle is not None:
            self.dx = math.cos(angle) * self.speed
            self.dy = math.sin(angle) * self.speed
        else:
            mouse_x, mouse_y = pygame.mouse.get_pos()
            dx = mouse_x - x
            dy = mouse_y - y
            dist = math.sqrt(dx * dx + dy * dy)
            self.dx = (dx / dist) * self.speed if dist != 0 else 0
            self.dy = (dy / dist) * self.speed if dist != 0 else 0

    def move(self):
        self.x += self.dx
        self.y += self.dy

    def draw(self, screen, camera):
        screen_x, screen_y = camera.world_to_screen(self.x, self.y)
        pygame.draw.circle(screen, WHITE, (int(screen_x), int(screen_y)), 
                         int(self.radius * camera.zoom))

def show_upgrade_selection(screen, upgrades):
    selection = None
    options = random.sample(UPGRADES, 3)
    
    while selection is None:
        screen.fill(BLACK)
        
        # Draw title
        font = pygame.font.Font(None, 48)
        title = font.render("Choose an Upgrade!", True, WHITE)
        screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 100))
        
        # Draw options
        font = pygame.font.Font(None, 36)
        for i, option in enumerate(options):
            y_pos = 250 + i * 100
            rect = pygame.Rect(SCREEN_WIDTH//4, y_pos, SCREEN_WIDTH//2, 60)
            pygame.draw.rect(screen, WHITE, rect, 2)
            
            text = f"{option} (Level {upgrades[option] + 1})"
            text_surface = font.render(text, True, WHITE)
            screen.blit(text_surface, (rect.centerx - text_surface.get_width()//2, 
                                     rect.centery - text_surface.get_height()//2))
        
        pygame.display.flip()
        
        for event in pygame.event.get():
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                for i, option in enumerate(options):
                    rect = pygame.Rect(SCREEN_WIDTH//4, 250 + i * 100, SCREEN_WIDTH//2, 60)
                    if rect.collidepoint(mouse_pos):
                        selection = option
                        
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
    
    return selection

def main():
    player = Player(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
    camera = Camera()
    enemies = []
    score = 0
    last_upgrade_score = 0
    enemy_spawn_timer = 0
    last_time = pygame.time.get_ticks()
    running = True
    game_paused = False

    while running:
        current_time = pygame.time.get_ticks()
        dt = (current_time - last_time) / 1000.0  # Convert to seconds
        last_time = current_time

        if game_paused:
            upgrade = show_upgrade_selection(screen, player.upgrades)
            player.upgrades[upgrade] += 1
            game_paused = False
            continue

        # Update camera position to follow player
        camera.x = player.x
        camera.y = player.y
        
        # Update camera zoom
        camera.apply_zoom(dt)
        
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                # Convert mouse position to world coordinates for shooting
                mouse_x, mouse_y = pygame.mouse.get_pos()
                world_mouse_x, world_mouse_y = camera.screen_to_world(mouse_x, mouse_y)
                player.shoot()

        # Get keyboard input
        keys = pygame.key.get_pressed()
        player.move(keys, camera)

        # Spawn enemies
        if pygame.time.get_ticks() - enemy_spawn_timer > 1000:  # Spawn enemy every second
            enemies.append(Enemy(camera, player))
            enemy_spawn_timer = pygame.time.get_ticks()

        # Update projectiles
        for projectile in player.projectiles[:]:
            projectile.move()
            # Remove projectiles that are too far from the player
            dx = projectile.x - player.x
            dy = projectile.y - player.y
            if math.sqrt(dx * dx + dy * dy) > 2000:  # Remove if more than 2000 units away
                player.projectiles.remove(projectile)

        # Update enemies
        for enemy in enemies[:]:
            enemy.move_towards_player(player)
            
            # Check collision with projectiles
            for projectile in player.projectiles[:]:
                dx = enemy.x - projectile.x
                dy = enemy.y - projectile.y
                distance = math.sqrt(dx * dx + dy * dy)
                
                # Check direct hit or explosion radius
                if (distance < enemy.radius + projectile.radius or 
                    (projectile.explosion_radius and distance < projectile.explosion_radius)):
                    enemies.remove(enemy)
                    
                    # Handle chain shot
                    if projectile.chain_count > 0:
                        nearest_enemy = None
                        nearest_dist = float('inf')
                        for next_enemy in enemies:
                            dx = next_enemy.x - projectile.x
                            dy = next_enemy.y - projectile.y
                            dist = math.sqrt(dx * dx + dy * dy)
                            if dist < nearest_dist:
                                nearest_dist = dist
                                nearest_enemy = next_enemy
                        
                        if nearest_enemy:
                            new_projectile = Projectile(projectile.x, projectile.y)
                            dx = nearest_enemy.x - projectile.x
                            dy = nearest_enemy.y - projectile.y
                            dist = math.sqrt(dx * dx + dy * dy)
                            new_projectile.dx = (dx / dist) * PROJECTILE_SPEED
                            new_projectile.dy = (dy / dist) * PROJECTILE_SPEED
                            new_projectile.chain_count = projectile.chain_count - 1
                            new_projectile.explosion_radius = projectile.explosion_radius
                            player.projectiles.append(new_projectile)
                    
                    player.projectiles.remove(projectile)
                    score += 100
                    
                    # Check for upgrade
                    if score - last_upgrade_score >= 500:
                        last_upgrade_score = score
                        game_paused = True
                    break

            # Check collision with player
            dx = player.x - enemy.x
            dy = player.y - enemy.y
            distance = math.sqrt(dx * dx + dy * dy)
            if distance < player.radius + enemy.radius:
                running = False

        # Draw everything
        screen.fill(BLACK)
        player.draw(screen, camera)
        for enemy in enemies:
            enemy.draw(screen, camera)
        for projectile in player.projectiles:
            projectile.draw(screen, camera)

        # Draw score (fixed position on screen, not affected by camera)
        font = pygame.font.Font(None, 36)
        score_text = font.render(f"Score: {score}", True, WHITE)
        screen.blit(score_text, (10, 10))

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    main() 