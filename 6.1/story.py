import pygame
import random
import logging
from constants import SCREEN_WIDTH, SCREEN_HEIGHT, BLACK

# 设置日志
logging.basicConfig(filename="game_errors.log", level=logging.ERROR)

class StoryEvent:
    def __init__(self):
        self.active = False
        self.triggered = False  # 标记是否已触发
        self.events = [
            {
                "text": "Partner is jealous! Choose: 1. Apologize 2. Ignore",
                "options": ["Apologize", "Ignore"],
                "effects": [
                    lambda duck: setattr(duck, "charm", duck.charm + 2),
                    lambda duck: duck.partners.pop(0) if duck.partners else None
                ]
            },
            {
                "text": "A duck confesses to you! Choose: 1. Accept 2. Reject",
                "options": ["Accept", "Reject"],
                "effects": [
                    lambda duck: setattr(duck, "charm", duck.charm + 5),
                    lambda duck: setattr(duck, "reputation", duck.reputation - 10)
                ]
            },
            {
                "text": "Help a human child? Choose: 1. Help 2. Ignore",
                "options": ["Help", "Ignore"],
                "effects": [
                    lambda duck: setattr(duck, "reputation", duck.reputation + 15),
                    lambda duck: setattr(duck, "reputation", duck.reputation - 5)
                ]
            },
            {
                "npc_type": "lady_duck",
                "text": "The lady duck admires you! Choose: 1. Flirt 2. Be Polite",
                "options": ["Flirt", "Be Polite"],
                "effects": [
                    lambda duck: setattr(duck, "charm", duck.charm + 10),
                    lambda duck: setattr(duck, "reputation", duck.reputation + 5)
                ]
            },
            {
                "npc_type": "broccoli_general",
                "text": "Broccoli Prince offers an alliance! Choose: 1. Accept 2. Decline",
                "options": ["Accept", "Decline"],
                "effects": [
                    lambda duck: setattr(duck, "attack_power", duck.attack_power + 10),
                    lambda duck: setattr(duck, "reputation", duck.reputation - 10)
                ]
            },
            {
                "npc_type": "human_child",
                "text": "The human child needs help! Choose: 1. Protect 2. Ignore",
                "options": ["Protect", "Ignore"],
                "effects": [
                    lambda duck: setattr(duck, "reputation", duck.reputation + 20),
                    lambda duck: setattr(duck, "charm", duck.charm - 5)
                ]
            }
        ]
        self.current_event = None
        self.choice = None

    def trigger(self, duck, screen, font, npc_type=None):
        try:
            if self.triggered:
                return  # 避免重复触发
            self.active = True
            self.triggered = True
            if npc_type:
                matching_events = [event for event in self.events if event.get("npc_type") == npc_type]
                self.current_event = random.choice(matching_events) if matching_events else random.choice(self.events)
            else:
                self.current_event = random.choice([event for event in self.events if "npc_type" not in event])
            text = font.render(self.current_event["text"], True, BLACK)
            screen.blit(text, (SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT // 2))
            pygame.display.flip()
        except Exception as e:
            logging.error(f"Failed to trigger story event: {e}")
            self.active = False
            self.triggered = False

    def handle_choice(self, choice, duck):
        try:
            self.choice = choice
            self.current_event["effects"][choice - 1](duck)
            print(f"选择了 {self.current_event['options'][choice - 1]}")
            self.active = False
            self.triggered = False
        except Exception as e:
            logging.error(f"Failed to handle story choice: {e}")
            self.active = False
            self.triggered = False

    def reset(self):
        self.active = False
        self.triggered = False
        self.current_event = None
        self.choice = None