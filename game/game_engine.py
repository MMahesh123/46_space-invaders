import pygame
import random
import os
from .player import Player
from .enemy import EnemyGrid
from .bullet import Bullet

# Game Engine

WHITE = (255, 255, 255)
GREEN = (0, 200, 0)
RED = (220, 60, 60)

class GameEngine:
    def __init__(self, width, height):
        self.width = width
        self.height = height

        self.font = pygame.font.SysFont("Arial", 30)
        self.exit_requested = False
        self.difficulty_selection = False
        self._load_sounds()
        self.reset_game("medium")

    def _load_sounds(self):
        self.fire_sound = None
        self.enemy_destroyed_sound = None
        self.game_over_sound = None

        try:
            if pygame.mixer.get_init() is None:
                pygame.mixer.init()
        except pygame.error:
            return

        sound_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "sounds")
        sound_files = {
            "fire_sound": "fire.wav",
            "enemy_destroyed_sound": "enemy_destroyed.wav",
            "game_over_sound": "game_over.wav",
        }

        for attribute, filename in sound_files.items():
            try:
                setattr(self, attribute, pygame.mixer.Sound(os.path.join(sound_dir, filename)))
            except (pygame.error, OSError):
                pass

    def _play_sound(self, sound):
        if sound is not None:
            try:
                sound.play()
            except pygame.error:
                pass

    def _set_game_over(self):
        if not self.game_over:
            self.game_over = True
            self._play_sound(self.game_over_sound)

    def reset_game(self, difficulty):
        difficulty_settings = {
            "easy": (1.0, 0.005),
            "medium": (1.5, 0.01),
            "hard": (2.5, 0.02),
        }
        enemy_speed, enemy_fire_chance = difficulty_settings[difficulty]

        self.player = Player(self.width // 2 - 20, self.height - 50, 40, 20)
        self.enemy_grid = EnemyGrid(self.width, speed=enemy_speed)
        self.player_bullets = []
        self.enemy_bullets = []
        self._shoot_cooldown = 0
        self.enemy_fire_chance = enemy_fire_chance
        self.score = 0
        self.game_over = False
        self.difficulty_selection = False
        self.exit_requested = False

    def handle_event(self, event):
        if self.difficulty_selection:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    self.reset_game("easy")
                elif event.key == pygame.K_2:
                    self.reset_game("medium")
                elif event.key == pygame.K_3:
                    self.reset_game("hard")
                elif event.key == pygame.K_ESCAPE:
                    self.exit_requested = True
            return

        if self.game_over:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    self.difficulty_selection = True
                elif event.key == pygame.K_ESCAPE:
                    self.exit_requested = True
            return

        if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
            if self._shoot_cooldown <= 0:
                bullet_x = self.player.center_x() - 2
                self.player_bullets.append(Bullet(bullet_x, self.player.y, direction=-1))
                self._shoot_cooldown = 15
                self._play_sound(self.fire_sound)

    def handle_input(self):
        if self.game_over or self.difficulty_selection:
            return

        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.player.move(-self.player.speed, self.width)
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.player.move(self.player.speed, self.width)

    def update(self):
        if self.game_over or self.difficulty_selection:
            return

        if self._shoot_cooldown > 0:
            self._shoot_cooldown -= 1

        self.enemy_grid.move()

        for enemy in self.enemy_grid.alive_enemies():
            if random.random() < self.enemy_fire_chance:
                bullet_x = enemy.x + enemy.width // 2
                self.enemy_bullets.append(Bullet(bullet_x, enemy.y + enemy.height, direction=1))

        for bullet in self.player_bullets:
            bullet.move()
        for bullet in self.enemy_bullets:
            bullet.move()

        self.player_bullets = [b for b in self.player_bullets if not b.off_screen(self.height)]
        self.enemy_bullets = [b for b in self.enemy_bullets if not b.off_screen(self.height)]

        remaining_bullets = []
        for bullet in self.player_bullets:
            hit = False
            for enemy in self.enemy_grid.alive_enemies():
                if bullet.rect().colliderect(enemy.rect()):
                    enemy.alive = False
                    self.score += 1
                    self._play_sound(self.enemy_destroyed_sound)
                    hit = True
                    break

            if not hit:
                remaining_bullets.append(bullet)

        self.player_bullets = remaining_bullets

        for bullet in self.enemy_bullets:
            if bullet.rect().colliderect(self.player.rect()):
                self._set_game_over()
                break

        if self.enemy_grid.reached_bottom(self.player.y):
            self._set_game_over()

    def render(self, screen):
        pygame.draw.rect(screen, GREEN, self.player.rect())

        for enemy in self.enemy_grid.alive_enemies():
            pygame.draw.rect(screen, WHITE, enemy.rect())

        for bullet in self.player_bullets:
            pygame.draw.rect(screen, WHITE, bullet.rect())
        for bullet in self.enemy_bullets:
            pygame.draw.rect(screen, RED, bullet.rect())

        score_text = self.font.render(f"Score: {self.score}", True, WHITE)
        screen.blit(score_text, (10, 10))

        if self.game_over:
            overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 190))
            screen.blit(overlay, (0, 0))

            title = self.font.render("GAME OVER", True, WHITE)
            final_score = self.font.render(f"Final score: {self.score}", True, WHITE)
            instruction = self.font.render("R: Play Again    ESC: Exit", True, WHITE)

            screen.blit(title, title.get_rect(center=(self.width // 2, self.height // 2 - 60)))
            screen.blit(final_score, final_score.get_rect(center=(self.width // 2, self.height // 2)))
            screen.blit(instruction, instruction.get_rect(center=(self.width // 2, self.height // 2 + 60)))

        if self.difficulty_selection:
            overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 220))
            screen.blit(overlay, (0, 0))

            title = self.font.render("SELECT DIFFICULTY", True, WHITE)
            easy = self.font.render("1: Easy", True, WHITE)
            medium = self.font.render("2: Medium", True, WHITE)
            hard = self.font.render("3: Hard", True, WHITE)
            instruction = self.font.render("ESC: Exit", True, WHITE)

            center_x = self.width // 2
            screen.blit(title, title.get_rect(center=(center_x, self.height // 2 - 120)))
            screen.blit(easy, easy.get_rect(center=(center_x, self.height // 2 - 45)))
            screen.blit(medium, medium.get_rect(center=(center_x, self.height // 2)))
            screen.blit(hard, hard.get_rect(center=(center_x, self.height // 2 + 45)))
            screen.blit(instruction, instruction.get_rect(center=(center_x, self.height // 2 + 120)))
